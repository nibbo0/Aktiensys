from enum import Enum
from functools import partial

from quart import Blueprint, request, current_app, jsonify
import mariadb

from db import exceptions, stock
from db.manage import get_db


class ApiError(Enum):
    INPUT = 'invalid-input'
    STATE = 'invalid-state'
    NOT_FOUND = 'not-found'
    DATABASE = 'database'
    UNKNOWN = 'unknown-err'

    def http_code(self) -> int:
        match self:
            case self.INPUT:
                return 400
            case self.STATE:
                return 500
            case self.NOT_FOUND:
                return 404
            case self.DATABASE:
                return 500
            case self.UNKNOWN:
                return 500

    def as_response(self, msg: str = None) -> tuple[dict, int]:
        body = {"err": self.value}
        if msg is not None:
            body["msg"] = msg
        return body, self.http_code()


api = Blueprint('api', __name__, url_prefix="/api")


@api.route('/kurse/verlauf/', defaults={'stock_id': None})
@api.route('/kurse/verlauf/<int:stock_id>')
def get_stock_price(stock_id: int = None):
    # get the stock price history (or preview).
    db = get_db()
    history_len = request.args.get("eintraege", default=1, type=int)
    if not history_len > 0:
        return ApiError.INPUT.as_response("'eintraege' muss >0 sein.")
    get_price = partial(stock.get_price_history, db, fetch_rows=history_len)
    prices = {}
    if stock_id is None:
        for stock_data in stock.list_stocks(db):
            stock_id = stock_data["id"]
            prices[stock_id] = get_price(stock_id)
    else:
        # FIXME this should be handled in a separate function
        price = get_price(stock_id)
        if price is None:
            # FIXME this arm is never visited because even a nonexistent stock
            # just returns an empty list
            return ApiError.NOT_FOUND.as_response(
                f"Aktie mit id '{stock_id}' konnte nicht gefunden werden.")
        prices[stock_id] = price
    return prices


@api.route('/kurse/vorschau/', defaults={'stock_id': None})
@api.route('/kurse/vorschau/<int:stock_id>')
def get_stock_preview(stock_id: int = None):
    db = get_db()
    get_preview = partial(stock.get_price_preview, db, fetch_rows="first")
    previews = {}
    if stock_id is None:
        for stock_data in stock.list_stocks(db):
            stock_id = stock_data["id"]
            previews[stock_id] = get_preview(stock_id)
    else:
        previews[stock_id] = get_preview(stock_id)
    return previews


@api.route('/kurse/vorschau/<int:stock_id>', methods=['PUT'])
def set_stock_preview(stock_id: int):
    db = get_db()
    preview = request.args.get("wert", type=int)
    try:
        stock.set_price_preview(db, stock_id, preview)
    except exceptions.PreviewRetrievalError as e:
        return ApiError.STATE.as_response(e.message)
    return {stock_id: preview}


@api.route('/aktien/', methods=['POST'])
def create_stocks():
    db = get_db()
    stock_name = request.args.get("name", type=str)
    try:
        return {"id": stock.create_stock(db, stock_name)}
    except mariadb.IntegrityError as e:
        return ApiError.DATABASE.as_response(
            f"Database operation failed with error: `{e}`"
        )


@api.route('/aktien/')
def get_stocks():
    db = get_db()
    return stock.list_stocks(db)


@api.route('/aktien/<int:stock_id>')
def get_stock(stock_id: int):
    db = get_db()
    stocks = stock.show_stock(db, stock_id)
    if stocks is None:
        return ApiError.NOT_FOUND.as_response(
            f"Aktie mit id '{stock_id}' konnte nicht gefunden werden.")
    return stocks


@api.route('/aktien/<int:stock_id>/name', methods=['PUT'])
def set_stock_name(stock_id: int):
    db = get_db()
    name = request.args.get("name", type=str)
    try:
        stock.rename_stock(db, stock_id, name)
    except mariadb.IntegrityError as e:
        return ApiError.DATABASE.as_response(
            f"Database operation failed with error: `{e}`"
        )
    return "ok"


@api.route('/markt/update')
def reload_market_engine():
    num_loaded = current_app.config["MARKET_ENGINE"].reload_stocks(get_db())
    return str(num_loaded), 200


@api.route('/markt/status')
def get_market_engine_status():
    return jsonify(current_app.config["MARKET_ENGINE"].is_running())


@api.route('/markt/start')
def start_market_engine():
    current_app.config["MARKET_ENGINE"].threadsafe_start()
    return ('', 200)


@api.route('/markt/stop')
def stop_market_engine():
    current_app.config["MARKET_ENGINE"].threadsafe_stop()
    return ('', 200)

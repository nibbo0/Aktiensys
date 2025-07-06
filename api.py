from enum import Enum
from functools import partial, wraps
from traceback import format_exception

import mariadb
from quart import Blueprint, current_app, jsonify, request

from db import exceptions, stock
from db.manage import get_db


class ApiError(Enum):
    INPUT = 'invalid-input'
    STATE = 'invalid-state'
    NOT_FOUND = 'not-found'
    EMPTY = 'results-empty'
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
            case self.EMPTY:
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


@api.errorhandler(exceptions.DatabaseError)
def handle_db_error(error):
    if isinstance(error, exceptions.StockIdError):
        return ApiError.NOT_FOUND.as_response(
            f"Aktie konnte nicht gefunden werden: {error}"
        )
    if isinstance(error, exceptions.RowNotFoundError):
        return ApiError.NOT_FOUND.as_response(
            f"Wert konnte nicht gefunden werden: {error}"
        )
    if isinstance(error, exceptions.DBValueError):
        return ApiError.INPUT.as_response(f"unzulässiger Wert: {error}")
    else:
        return ApiError.UNKNOWN.as_response()


@api.errorhandler(mariadb.Error)
def handle_mariadb_error(error):
    current_app.logger.error("".join(format_exception(error)))
    return ApiError.DATABASE.as_response(
        error.__class__.__name__ + ": " + str(error)
    )


def return_rowcount(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        value = f(*args, **kwargs)
        if isinstance(value, int):
            return jsonify({"rowcount": value})
        return value
    return wrapper


@api.route('/kurse/verlauf/', defaults={'stock_id': None})
@api.route('/kurse/verlauf/<int:stock_id>')
def get_stock_price(stock_id: int = None):
    # get the stock price history (or preview).
    db = get_db()
    history_len = request.args.get("eintraege", default=10, type=int)
    if not history_len > 0:
        return ApiError.INPUT.as_response(
            "mindestens ein Eintrag muss abgerufen werden.")
    get_price = partial(stock.get_price_history, db, fetch_rows=history_len)
    if stock_id is None:
        prices = {}
        for stock_id in stock.list_stock_ids(db):
            prices[stock_id] = get_price(stock_id)
        return prices
    else:
        price = get_price(stock_id)
        if price is None:
            return ApiError.EMPTY.as_response("kein Verlauf verfügbar")
        return price


@api.route('/kurse/vorschau/', defaults={'stock_id': None})
@api.route('/kurse/vorschau/<int:stock_id>')
def get_stock_preview(stock_id: int = None):
    db = get_db()
    get_preview = partial(stock.get_price_preview, db, fetch_rows="first")
    if stock_id is None:
        previews = {}
        for stock_id in stock.list_stock_ids(db):
            previews[stock_id] = get_preview(stock_id)
        return previews
    else:
        preview = get_preview(stock_id)
        if preview is None:
            return ApiError.EMPTY.as_response("keine Vorschau verfügbar")
        return preview


@api.route('/kurse/vorschau/<int:stock_id>', methods=['PUT'])
@return_rowcount
def set_stock_preview(stock_id: int):
    db = get_db()
    preview = request.args.get("wert", type=int)
    if preview is None:
        return ApiError.INPUT.as_response("Parameter 'wert' muss ganzzahlig sein.")
    return stock.set_price_preview(db, stock_id, preview)


@api.route('/aktien/', methods=['POST'])
def create_stocks():
    db = get_db()
    stock_name = request.args.get("name", type=str)
    return {"id": stock.create_stock(db, stock_name)}


@api.route('/aktien/')
def get_stocks():
    db = get_db()
    return stock.list_stocks(db)


@api.route('/aktien/<int:stock_id>')
def get_stock(stock_id: int):
    db = get_db()
    return stock.show_stock(db, stock_id)


@api.route('/aktien/<int:stock_id>/name', methods=['PUT'])
@return_rowcount
def set_stock_name(stock_id: int):
    db = get_db()
    name = request.args.get("name", type=str)
    return stock.rename_stock(db, stock_id, name)


@api.route('/aktien/<int:stock_id>/farbe', methods=['PUT'])
@return_rowcount
def set_stock_color(stock_id: int):
    db = get_db()
    name = request.args.get("farbe", type=str)
    return stock.recolor_stock(db, stock_id, name)


@api.route('/markt/update')
def reload_market_engine():
    num_loaded = current_app.config["MARKET_ENGINE"].reload_stocks(get_db())
    return jsonify({"num_loaded": num_loaded})


@api.route('/markt/status')
def get_market_engine_status():
    is_running = current_app.config["MARKET_ENGINE"].is_running()
    return jsonify({"is_running": is_running})


@api.route('/markt/start')
def start_market_engine():
    current_app.config["MARKET_ENGINE"].threadsafe_start()
    return ('', 200)


@api.route('/markt/stop')
def stop_market_engine():
    current_app.config["MARKET_ENGINE"].threadsafe_stop()
    return ('', 200)

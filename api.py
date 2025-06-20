from enum import Enum
from functools import partial

from quart import Blueprint, request

from db import get_db, stock, exceptions


class ApiError(Enum):
    INPUT = 'invalid-input'
    STATE = 'invalid-state'

    def http_code(self) -> int:
        match self:
            case self.INPUT:
                return 400
            case self.STATE:
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
    get_price = partial(stock.get_price_history, db, num_entries=history_len)
    prices = {}
    if stock_id is None:
        for stock_id, _ in stock.list_stock(db):
            prices[stock_id] = get_price(stock_id)
    else:
        prices[stock_id] = get_price(stock_id)
    return prices


@api.route('/kurse/vorschau/', defaults={'stock_id': None})
@api.route('/kurse/vorschau/<int:stock_id>')
def get_stock_preview(stock_id: int = None):
    db = get_db()
    preview_len = 1
    get_preview = partial(stock.get_price_preview, db, num_entries=preview_len)
    previews = {}
    if stock_id is None:
        for stock_id, _ in stock.list_stock(db):
            previews[stock_id] = get_preview(stock_id)
    else:
        previews[stock_id] = get_preview(stock_id)
    return previews

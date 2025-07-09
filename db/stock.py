from datetime import datetime
from typing import Literal, Union

from mariadb import Connection
from quart import current_app
from string import hexdigits

from . import read_value, exceptions


def _ensure_stock(db: Connection, stock_id: int):
    sql = """SELECT 1 FROM stocks WHERE id = (?)"""
    if read_value(db, sql, stock_id, fetch_rows="first") is None:
        raise exceptions.StockIdError(stock_id)


def get_prices(db: Connection, stock_id: int,
               fetch_rows: Union[int, Literal["all", "first"]] = 1):
    sql = """SELECT * FROM prices
    WHERE stock_id = (?)
    ORDER BY valid_after DESC"""
    _ensure_stock(db, stock_id)
    return read_value(db, sql, stock_id, fetch_rows=fetch_rows)


def get_price_current(db: Connection, stock_id: int):
    sql = """SELECT * FROM prices
    WHERE stock_id = (?) AND valid_after <= UTC_TIMESTAMP()
    ORDER BY valid_after DESC
    """
    _ensure_stock(db, stock_id)
    return read_value(db, sql, stock_id, fetch_rows="first")


def get_price_history(db: Connection, stock_id: int,
                      fetch_rows: Union[int, Literal["all", "first"]] = 1):
    sql = """SELECT * FROM prices
    WHERE stock_id = (?) AND valid_after <= UTC_TIMESTAMP()
    ORDER BY valid_after DESC
    """
    _ensure_stock(db, stock_id)
    return read_value(db, sql, stock_id, fetch_rows=fetch_rows)


def get_price_preview(db: Connection, stock_id: int,
                      fetch_rows: Union[int, Literal["all", "first"]] = 1):
    sql = """SELECT price, valid_after FROM prices
    WHERE stock_id = (?) AND valid_after > UTC_TIMESTAMP()
    ORDER BY valid_after ASC
    """
    # FIXME returning more than one entry is contrary to the HTTP API which
    # only allows retrieving / editing of one preview value. This causes
    # inconsistency in behavior because cursor.fetchmany() handles absence of
    # results differently from cursor.fetchone().
    _ensure_stock(db, stock_id)
    return read_value(db, sql, stock_id, fetch_rows=fetch_rows)


def set_price_preview(db: Connection, stock_id: int, new_price: Union[int, float]):
    if not isinstance(new_price, (int, float)):
        raise exceptions.DBValueError("price", new_price)
    _ensure_stock(db, stock_id)
    with db.cursor() as cursor:
        preview = get_price_preview(db, stock_id, fetch_rows="first")
        if not preview:
            raise exceptions.RowNotFoundError()
        timestmp = preview["valid_after"]
        cursor.execute(
            """UPDATE prices
            SET price = (?)
            WHERE stock_id = (?) AND valid_after = (?)
            """,
            (new_price, stock_id, timestmp)
        )
        db.commit()
        return cursor.rowcount


def add_price_preview(db: Connection, stock_id: int, valid_after: datetime,
                      price: Union[int, float]):
    if not isinstance(valid_after, datetime):
        raise exceptions.DBValueError("valid_after", valid_after)
    if not isinstance(price, (int, float)):
        raise exceptions.DBValueError("price", price)
    _ensure_stock(db, stock_id)
    with db.cursor() as cursor:
        cursor.execute(
            """INSERT INTO prices (stock_id, valid_after, price)
            VALUES (?, ?, ?)""",
            (stock_id, valid_after, price)
        )
        db.commit()
        current_app.logger.info("pushed new preview (%.2f). valid_after: %s %s",
                                price, valid_after, valid_after.tzname())
        return cursor.rowcount


def show_stock(db: Connection, stock_id: int):
    _ensure_stock(db, stock_id)
    return read_value(db, """SELECT * FROM stocks WHERE id = (?)""", stock_id)


def list_stocks(db: Connection):
    return read_value(db, """SELECT * FROM stocks""", fetch_rows="all")


def list_stock_ids(db: Connection):
    return [stock["id"] for stock in list_stocks(db)]


def create_stock(db: Connection, name: str, color: str = None):
    if name is None:
        raise exceptions.DBValueError("name", None)
    if color is not None and not _is_hexcolor(color):
        raise exceptions.DBValueError("color", color)
    with db.cursor() as cursor:
        cursor.execute("""INSERT INTO stocks (name, color) VALUES (?, ?)""",
                       (name, color))
        new_id = cursor.lastrowid
    db.commit()
    return new_id


def rename_stock(db: Connection, stock_id: int, new_name: str):
    if new_name is None:
        raise exceptions.DBValueError("name", None)
    _ensure_stock(db, stock_id)
    with db.cursor() as cursor:
        cursor.execute(
            """UPDATE stocks
            SET name = (?)
            WHERE id = (?)
            """,
            (new_name, stock_id)
        )
        db.commit()
        return cursor.rowcount


def _is_hexcolor(s: str):
    [prefix, code] = s[:1], s[1:]
    if prefix != "#":
        return False
    if len(code) < 3 or len(code) > 6:
        return False
    return all([c in hexdigits for c in code])


def recolor_stock(db: Connection, stock_id: int, new_color: str):
    # ensure that color is either None or a valid hex color
    if new_color is not None and not _is_hexcolor(new_color):
        raise exceptions.DBValueError("color", new_color)
    _ensure_stock(db, stock_id)
    with db.cursor() as cursor:
        cursor.execute(
            """UPDATE stocks
            SET color = (?)
            WHERE id = (?)
            """,
            (new_color.upper(), stock_id)
        )
        db.commit()
        return cursor.rowcount

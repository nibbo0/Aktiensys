from mariadb import Connection
from mariadb.constants.CURSOR import READ_ONLY


from . import exceptions, read_value


def get_price_current(db: Connection, stock_id: int):
    sql = """SELECT * FROM prices
    WHERE stock_id = (?) AND valid_after <= NOW()
    ORDER BY valid_after DESC
    """
    return read_value(db, sql, stock_id, fetch_rows="first")


def get_price_history(db: Connection, stock_id: int, num_entries: int = 1):
    sql = """SELECT price, valid_after FROM prices
    WHERE stock_id = (?) AND valid_after <= NOW()
    ORDER BY valid_after DESC
    """
    return read_value(db, sql, stock_id, fetch_rows=num_entries)


def get_price_preview(db: Connection, stock_id: int, num_entries: int = 1):
    sql = """SELECT price, valid_after FROM prices
    WHERE stock_id = (?) AND valid_after > NOW()
    ORDER BY valid_after ASC
    """
    # FIXME returning more than one entry is contrary to the HTTP API which
    # only allows retrieving / editing of one preview value. This causes
    # inconsistency in behavior because cursor.fetchmany() handles no
    # results differently from cursor.fetchone().
    return read_value(db, sql, stock_id, fetch_rows=num_entries)


def set_price_preview(db: Connection, stock_id: int, new_value: int):
    with db.cursor() as cursor:
        preview = get_price_preview(db, stock_id, num_entries=1)
        if not preview:
            raise exceptions.PreviewRetrievalError(
                "Keine Vorschau zur Aktualisierung vorhanden.")
        price, timestmp = preview
        cursor.execute(
            """UPDATE price FROM prices
            SET price = (?)
            WHERE
                stock_id = (?) AND valid_after = (?)
            """,
            (new_value, stock_id, timestmp)
        )
        cursor.commit()
        return cursor.rowcount


def show_stock(db: Connection, stock_id: int):
    return read_value(db, """SELECT * FROM stocks WHERE id = (?)""", stock_id)


def list_stocks(db: Connection):
    return read_value(db, """SELECT * FROM stocks""", fetch_rows="all")


def create_stock(db: Connection, stock_name: str):
    with db.cursor() as cursor:
        cursor.execute("""INSERT INTO stocks (stock_name) VALUES (?)""",
                       (stock_name,))
        new_id = cursor.lastrowid
    db.commit()
    return new_id

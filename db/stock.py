from mariadb import Connection
from mariadb.constants.CURSOR import READ_ONLY


from . import exceptions


def get_price_current(db: Connection, stock_id: int):
    with db.cursor(cursor_type=READ_ONLY) as cursor:
        # FIXME fix time check by converting to unix timestamp
        cursor.execute(
            """SELECT price, valid_after FROM prices
            WHERE
                stock_id = (?) AND valid_after <= NOW()
            ORDER BY valid_after DESC
            """,
            (stock_id,)
        )
        return cursor.fetchone()


def get_price_history(db: Connection, stock_id: int, num_entries: int = 1):
    with db.cursor(cursor_type=READ_ONLY) as cursor:
        # FIXME fix time check by converting to unix timestamp
        cursor.execute(
            """SELECT price, valid_after FROM prices
            WHERE
                stock_id = (?) AND valid_after <= NOW()
            ORDER BY valid_after DESC
            """,
            (stock_id,)
        )
        return cursor.fetchmany(num_entries)


def get_price_preview(db: Connection, stock_id: int, num_entries: int = 1):
    with db.cursor(cursor_type=READ_ONLY) as cursor:
        # FIXME fix time check by converting to unix timestamp
        cursor.execute(
            """SELECT price, valid_after FROM prices
            WHERE
                stock_id = (?) AND valid_after > NOW()
            ORDER BY valid_after ASC
            """,
            (stock_id,)
        )
        # FIXME returning more than one entry is contrary to the HTTP API which
        # only allows retrieving / editing of one preview value. This causes
        # inconsistency in behavior because cursor.fetchmany() handles no
        # results differently from cursor.fetchone().
        return cursor.fetchmany(num_entries)


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


def list_stock(db: Connection):
    with db.cursor(cursor_type=READ_ONLY) as cursor:
        cursor.execute("""SELECT id, stock_name FROM stocks""")
        return cursor.fetchall()

from mariadb import Connection
from mariadb.constants.CURSOR import READ_ONLY


def get_price(db: Connection, stock_id: int):
    cursor = db.cursor(READ_ONLY)
    # FIXME fix time check by converting to unix timestamp
    cursor.execute(
        """SELECT value FROM prices
        WHERE
            stock_id = (?) AND valid_after <= NOW()
        ORDER BY valid_after DESC
        """,
        stock_id
    )
    return cursor.fetchone()


def get_price_history(db: Connection, stock_id: int, num_entries=1):
    cursor = db.cursor(READ_ONLY)
    # FIXME fix time check by converting to unix timestamp
    cursor.execute(
        """SELECT price FROM prices
        WHERE
            stock_id = (?) AND valid_after <= NOW()
        ORDER BY valid_after DESC
        """,
        stock_id
    )
    return cursor.fetchmany(num_entries)


def get_price_preview(db: Connection, stock_id: int, num_entries=1):
    cursor = db.cursor(READ_ONLY)
    # FIXME fix time check by converting to unix timestamp
    cursor.execute(
        """SELECT price FROM prices
        WHERE
            stock_id = (?) AND valid_after > NOW()
        ORDER BY valid_after ASC
        """,
        stock_id
    )
    return cursor.fetchmany(num_entries)

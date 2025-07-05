class DatabaseError(Exception):
    pass


class RowNotFoundError(DatabaseError, LookupError):
    pass


class StockIdError(RowNotFoundError):
    """Raised when attempting to access a stock_id that doesn't exist.

    `message` should be set to the stock_id that wasn't found.
    """
    pass


class DBValueError(DatabaseError, ValueError):
    """Raised when attempting to use a bad value in the database."""
    def __init__(self, column, value, message=None):
        self.column = column
        self.value = value
        if message is None:
            message = str(column) + ": " + ("null" if value is None else str(value))
        self.message = message
        super.__init__(self.message)

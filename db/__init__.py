from typing import Literal, Union
from datetime import datetime, timezone

import mariadb


def read_value(connection: mariadb.Connection, sql: str, *data,
               fetch_rows: Union[int, Literal["all", "first"]] = "first"):
    """Execute a readonly statment on the connection.

    Map the result to a [list of] dictionary with names based on the selected
    fields (or aliases). `fetch_rows` accepts three different types of values:
     - "first": Retrieve the first row and return it.
     - "all": Retrieve all rows (using fetchall).
     - `int`: Retrieve the specified number of rows.
    """
    with connection.cursor(
            cursor_type=mariadb.constants.CURSOR.READ_ONLY
    ) as cursor:
        # print(f"executing SQL:\n{sql}\nwith data: {data}")

        cursor.execute(sql, data)

        def try_set_timezones(values):
            for i in range(len(values)):
                if values[i] and isinstance(values[i], datetime):
                    values[i] = values[i].replace(tzinfo=timezone.utc)
            return values

        def map_dict(values):
            return dict(zip(cursor.metadata["field"], values))

        def parse_values(values):
            return map_dict(try_set_timezones(list(values)))

        if fetch_rows == "first":
            value = cursor.fetchone()
            if value is None:
                return None
            return parse_values(value)
        elif fetch_rows == "all":
            return [parse_values(v) for v in cursor.fetchall()]
        else:
            return [parse_values(v) for v in cursor.fetchmany(fetch_rows)]

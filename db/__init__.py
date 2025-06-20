import click
import mariadb
from quart import current_app, g, cli

from .tables import _create_tables, _drop_tables


def read_value(connection: mariadb.Connection, sql: str, *data, fetch_rows="first"):
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

        def map_dict(values):
            return dict(zip(cursor.metadata["field"], values))

        if fetch_rows == "first":
            value = cursor.fetchone()
            if value is None:
                return None
            return map_dict(value)
        elif fetch_rows == "all":
            return [map_dict(v) for v in cursor.fetchall()]
        else:
            return [map_dict(v) for v in cursor.fetchmany(fetch_rows)]


def _connect_db(use_db=True, include_user=True):
    conf = current_app.config["MARIADB_CONNECTION"].copy()
    if not use_db:
        conf.pop("db", None)
        conf.pop("database", None)
    if not include_user:
        conf.pop("user", None)
        conf.pop("password", None)
    connection = mariadb.connect(**conf)
    return connection


def close_db(exception=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def get_db():
    if 'db' not in g:
        g.db = _connect_db()
    return g.db


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db)


@click.command('init-db')
@click.option('--overwrite/--no-overwrite', default=False)
@cli.with_appcontext
def init_db(overwrite=False):
    """Connect to database and initialize table structure.

    This requires a valid user with access to the database to be configured in
    the config file.

    """
    db = get_db()
    if overwrite:
        num_dropped = _drop_tables(db, fail_on_missing=False)
        click.echo(f"dropped {num_dropped} tables.")
    num_created = _create_tables(db)
    click.echo(f"created {num_created} tables.")

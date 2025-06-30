import click
import mariadb
from quart import cli, current_app, g

from .tables import _create_tables, _drop_tables


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
        # FIXME causes an error when db is closed earlier
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

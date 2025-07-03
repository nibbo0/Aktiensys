from quart import Quart
import logging


def create_app(config=None):
    logging_config = {}

    from default_config import LOGGING as DEFAULT_LOGGING_CONFIG
    logging_config |= DEFAULT_LOGGING_CONFIG

    try:
        from config import LOGGING as CUSTOM_LOGGING_CONFIG
        logging_config |= CUSTOM_LOGGING_CONFIG
    except ImportError:
        pass

    if config:
        logging_config |= config.get('LOGGING', {})

    logging.config.dictConfig(logging_config)

    app = Quart(__name__, static_folder='static', template_folder='templates')

    app.config.from_pyfile('default_config.py')
    app.config.from_pyfile('config.py', silent=True)
    if config is not None:
        app.config.update(**config)

    from frontend import front
    app.register_blueprint(front)

    from api import api
    app.register_blueprint(api)

    from db import manage as db
    db.init_app(app)

    import market_engine
    market_engine.init_app(app)

    app.logger.info("Created app.")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

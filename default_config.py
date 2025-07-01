import logging
import os

MARIADB_CONNECTION = {
    "user": "dau_jones",
    "host": "localhost",
    # "password": r"YOUR SECURE PASSWORD HERE",
    "database": "dau_jones",
}


class MakeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,  # noqa: N803
                 encoding=None, delay=False, errors=None):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay,
                         errors)


LOGGING = {
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': logging.INFO,
            'formatter': 'default',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'default_config.MakeRotatingFileHandler',
            'level': logging.INFO,
            'formatter': 'default',
            'filename': 'logs/dau-jones.log',
        },
    },
    'root': {
        'level': logging.INFO,
        'handlers': ['file'],
    }
}

from market_engine import RandomMarketEngine
from datetime import timedelta

MARKET_ENGINE_CLASS = RandomMarketEngine
MARKET_ENGINE_PARAMS = {
    "interval": timedelta(minutes=15),
    "interval": timedelta(seconds=15),
    "price_range": range(1, 10),
}

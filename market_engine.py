import asyncio
import random
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Self, Union

import mariadb
from quart import Quart, current_app, has_app_context

from db import stock as stock_db
from db.manage import get_db


def flush_all_handlers(logger):
    for handler in logger.handlers:
        handler.flush()


def init_app(app: Quart):

    @app.before_serving
    async def start_engine():
        engine_class = app.config["MARKET_ENGINE_CLASS"]
        engine_params = app.config["MARKET_ENGINE_PARAMS"]

        engine = engine_class(app, **engine_params)

        engine_stocks = MarketEngineDBStock.all_from_db(get_db())
        engine.stocks = engine_stocks
        app.logger.info(f"loaded {len(engine_stocks)} stocks from db")

        app.config["MARKET_ENGINE"] = engine
        engine.start()


class MarketEngineStock(ABC):
    stock_id: int
    on_push_listeners: set[Callable]

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.on_push_listeners = set()

    def __eq__(self, o):
        if isinstance(o, self.__class__):
            return self.stock_id == o.stock_id
        return False

    def __repr__(self):
        return (self.__class__.__name__ +
                f"({ str(self.stock_id)}, listeners: {len(self.on_push_listeners)})")

    def push_value(self, new_price, new_valid):
        self._push_value(new_price, new_valid)
        self._on_push(new_price, new_valid)

    @abstractmethod
    def _push_value(self, new_price, new_valid):
        pass

    def _on_push(self, new_price, new_valid):
        for listener in self.on_push_listeners:
            listener(self, new_price, new_valid)


class MarketEngineDBStock(MarketEngineStock):
    """An interface to interact with stocks from the market engine.

    Can be used to push new stock values to the database. Stores listeners for
    pushes of new values. Tracks the most recently pushed preview. TODO It may
    be beneficial to track the preview furthest in the future.
    """
    previews: list[tuple[float, datetime]]
    history:  list[tuple[float, datetime]]

    def __init__(self, stock_id):
        super().__init__(stock_id)
        self.previews = []
        self.history = []

        self.refresh()

    @staticmethod
    def all_from_db(db: mariadb.Connection) -> list[Self]:
        stock_ids = stock_db.list_stock_ids(db)
        return [MarketEngineDBStock(stock_id) for stock_id in stock_ids]

    def _safe_get_db(self):
        return get_db()

    def refresh(self):
        try:
            previews = stock_db.get_price_preview(
                self._safe_get_db(), self.stock_id, fetch_rows="all"
            )
            history = stock_db.get_price_history(
                self._safe_get_db(), self.stock_id, fetch_rows="all"
            )
            self.previews = [v.values() for v in previews]
            self.history = [v.values() for v in history]
        except Exception as e:
            raise RuntimeError(
                f"Unable to refresh stock {self.stock_id} from database"
            ) from e

    def _push_value(self, new_price, new_valid):
        try:
            stock_db.add_price_preview(
                self._safe_get_db(), self.stock_id, new_valid, new_price
            )
            self.refresh()
        except Exception as e:
            raise RuntimeError(
                f"Unable to push new preview to stock {self.stock_id}"
            ) from e


class BaseMarketEngine(ABC):
    _app: Quart
    _loop: asyncio.BaseEventLoop
    _timers: dict[Callable, asyncio.TimerHandle]
    interval: float
    stocks: list[MarketEngineStock]

    # TODO define update function (or listeners) from caller?
    # TODO define overridable get_next_interval function?
    def __init__(self, app: Quart, interval: timedelta):
        """Initialize the market engine.

        The market engine is responsible for generating new stock prices and
        queuing the next generation step. Stock price validity is usually dated
        into the future. Algorithms may be defined through subclasses.

        Updates are done every `interval` unless stopped. Each update will come
        into effect when the automatically generated SQL timestamp is reached.
        Update notifications and the next update are triggered when the
        internal event loop clock reaches the equivalent internal timestamp.

        Note that differences in time measurement (e.g. leap seconds, system
        time settings) may cause the system time and event loop time to become
        unaligned.

        """
        self._app = app
        self._loop = asyncio.get_running_loop()
        self._timers: dict[Callable, asyncio.TimerHandle] = {}
        self.interval = interval
        self.stocks = []

    def _wrap_scheduled(self, callback: Callable, *args, **kwargs):
        def _scheduled_inner():
            callback(*args, **kwargs)
            # FIXME should this be done first?
            self._timers.pop(_scheduled_inner)
        return _scheduled_inner

    def _schedule(
            self, delay: Union[timedelta, int, float], callback: Callable
    ) -> asyncio.TimerHandle:
        if isinstance(delay, timedelta):
            delay = delay.total_seconds()
        # TODO warn about inaccuracies if delay is GT some margin (e.g. 12h)
        callback = self._wrap_scheduled(callback)
        timer = asyncio.get_running_loop().call_later(
            delay, callback
        )
        self._timers[callback] = timer
        return timer

    def _schedule_at_utc(
            self, when: datetime, callback: Callable
    ) -> asyncio.TimerHandle:
        # http://stackoverflow.com/questions/55592067/ddg#55593284
        return self._schedule(when - datetime.utcnow(), callback)

    def start(self, when: Union[float, None] = None):
        """Start the engine.

        Generate and apply prices every `self.interval`. If `when` is None,
        start the engine at `utcnow() + 1`.
        """
        if self._timers:
            raise RuntimeError("Engine is already running")
        if when is None:
            when = datetime.utcnow() + timedelta(seconds=1)
        current_app.logger.debug(f"starting engine at {when}")
        self._schedule_at_utc(when, self._run)

    def stop(self):
        for timer in self._timers.values():
            timer.cancel()

    def _run(self):
        """Recursively update price previews."""
        if not has_app_context():
            raise RuntimeError("Not within app context")

        current_app.logger.info("running engine internally")
        try:
            self._update_stocks(current_app)
            current_app.logger.info("updated stocks; scheduling next run in %dmin %ds",
                                    self.interval.total_seconds() // 60,
                                    self.interval.total_seconds() % 60)
            next_run = datetime.utcnow() + self.interval
            self._schedule_at_utc(next_run, self._run)
            current_app.logger.info("scheduled next run at %s", next_run)
        except Exception:
            current_app.logger.error(traceback.format_exc())

    def _update_stocks(self, context):
        """Update all the stocks managed by this instance."""
        try:
            for stock in self.stocks:
                self._update_stock(stock, context)
        except Exception as e:
            raise RuntimeError("Error occured while updating stocks") from e

    def _update_stock(self, stock: MarketEngineStock, context):
        """Generate a new price preview for `stock` and push it.

        Default behavior is to call `self._generate_price`, set the validity to
        `utcnow() + self.interval` and push via `stock.push_value`.
        """
        current_app.logger.debug("updating stock %d", stock.stock_id)
        new_price = self._generate_price(stock, context)
        new_valid = datetime.utcnow() + self.interval
        stock.push_value(new_price, new_valid)

    @abstractmethod
    def _generate_price(self, stock, context) -> float:
        pass


class RandomMarketEngine(BaseMarketEngine):
    def __init__(self, app, interval, price_range: range):
        super().__init__(app, interval)
        self.price_range = price_range

    def _generate_price(self, _stock, _context) -> float:
        return random.choice(self.price_range)

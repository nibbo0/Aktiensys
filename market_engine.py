import asyncio
import random
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
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
        engine.reload_stocks(get_db())

        app.config["MARKET_ENGINE"] = engine


class MarketEngineStock(ABC):
    stock_id: int
    on_push_listeners: set[Callable]
    prices: list[tuple[float, datetime]]

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self.on_push_listeners = set()
        self.prices = []

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

    def get_latest_price(self):
        try:
            after_sort = sorted(self.prices, key=lambda p: p[0], reverse=True)
            return after_sort[0][1]
        except IndexError:
            return None


class MarketEngineDBStock(MarketEngineStock):
    """An interface to interact with stocks from the market engine.

    Can be used to push new stock values to the database. Stores listeners for
    pushes of new values. Tracks the most recently pushed preview. TODO It may
    be beneficial to track the preview furthest in the future.
    """
    prices: list[tuple[float, datetime]]
    HISTORY_LEN: int = 10

    def __init__(self, stock_id):
        super().__init__(stock_id)

        self.refresh()

    @staticmethod
    def all_from_db(db: mariadb.Connection) -> list[Self]:
        stock_ids = stock_db.list_stock_ids(db)
        return [MarketEngineDBStock(stock_id) for stock_id in stock_ids]

    def _safe_get_db(self):
        return get_db()

    def refresh(self):
        try:
            prices = stock_db.get_prices(
                self._safe_get_db(), self.stock_id, fetch_rows=self.HISTORY_LEN
            )
            self.prices = [(v["valid_after"], int(v["price"])) for v in prices]
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


# FIXME not thread-safe!
class BaseMarketEngine(ABC):
    _app: Quart
    _loop: asyncio.BaseEventLoop
    _timers: dict[Callable, asyncio.TimerHandle]
    # FIXME thread-safety!
    interval: float
    _stocks: list[MarketEngineStock]

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
        self._stocks = []

    # FIXME thread-safety!
    def reload_stocks(self, db: mariadb.Connection):
        self._stocks = MarketEngineDBStock.all_from_db(db)
        num_loaded = len(self._stocks)
        current_app.logger.info(f"loaded {num_loaded} stocks from db")
        return num_loaded

    def get_num_stocks(self):
        return len(self._stocks)

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
        timer = self._loop.call_later(
            delay, callback
        )
        self._timers[callback] = timer
        return timer

    def _schedule_at_utc(
            self, when: datetime, callback: Callable
    ) -> asyncio.TimerHandle:
        # http://stackoverflow.com/questions/55592067/ddg#55593284
        return self._schedule(when - datetime.now(timezone.utc), callback)

    def is_running(self):
        return len(self._timers) > 0

    def start(self, when: Union[float, None] = None):
        """Start the engine.

        Generate and apply prices every `self.interval`. If `when` is None,
        start the engine at `now(utc) + 1`.
        """
        if self._timers:
            raise RuntimeError("Engine is already running")
        if when is None:
            when = datetime.now(timezone.utc) + timedelta(seconds=1)
        current_app.logger.debug(f"starting engine at {when}.")
        self._schedule_at_utc(when, self._run)

    def threadsafe_start(self, *args):
        self._loop.call_soon_threadsafe(self.start, *args)

    def stop(self):
        for timer in self._timers.values():
            timer.cancel()
        self._timers = {}
        current_app.logger.debug("stopped engine.")

    def threadsafe_stop(self, *args):
        self._loop.call_soon_threadsafe(self.stop, *args)

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
            next_run = datetime.now(timezone.utc) + self.interval
            self._schedule_at_utc(next_run, self._run)
            current_app.logger.info("scheduled next run at %s", next_run)
        except Exception:
            current_app.logger.error(traceback.format_exc())

    def _update_stocks(self, context):
        """Update all the stocks managed by this instance."""
        try:
            for stock in self._stocks:
                self._update_stock(stock, context)
        except Exception as e:
            raise RuntimeError("Error occured while updating stocks") from e

    def _update_stock(self, stock: MarketEngineStock, context):
        """Generate a new price preview for `stock` and push it.

        Default behavior is to call `self._generate_price`, set the validity to
        `now(utc) + self.interval` and push via `stock.push_value`.
        """
        current_app.logger.debug("updating stock %d", stock.stock_id)
        new_price = self._generate_price(stock, context)
        new_valid = datetime.now(timezone.utc) + self.interval
        stock.push_value(new_price, new_valid)

    @abstractmethod
    def _generate_price(self, stock, context) -> float:
        pass


class RandomMarketEngine(BaseMarketEngine):
    def __init__(self, app, interval, price_range: range):
        super().__init__(app, interval)
        self.price_range = price_range

    def _generate_price(self, _stock, _context) -> int:
        return random.choice(self.price_range)


class RandomChangeMarketEngine(BaseMarketEngine):
    def __init__(self, app, interval, max_change: int, min_value: int,
                 start_value: int, step: float = 1):
        super().__init__(app, interval)
        self.max_change = max_change
        self.min_value = min_value
        self.start_value = start_value
        self.step = step

    def _generate_price(self, _stock: MarketEngineStock, _context) -> int:
        last_price = _stock.get_latest_price() or self.start_value
        max_price = last_price + self.max_change
        min_price = max(self.min_value, last_price - self.max_change)
        return random.randrange(min_price, max_price, self.step)


class GaussChangeMarketEngine(BaseMarketEngine):
    def __init__(self, app, interval, sigma: float, min_value: int,
                 start_value: int, step: float = 1):
        super().__init__(app, interval)
        self.sigma = sigma
        self.min_value = min_value
        self.start_value = start_value
        self.step = step

    def _generate_price(self, _stock: MarketEngineStock, _context) -> int:
        last_price = _stock.get_latest_price() or self.start_value
        price = random.gauss(last_price, self.sigma)
        rounded = self.step * round(price / self.step)
        # if rounded < last_price:
        #     rounded += self.step
        current_app.logger.debug("generated gauss %.2f (rounded: %.2f) following %.2f",
                                 price, rounded, last_price)
        return max(self.min_value, rounded)

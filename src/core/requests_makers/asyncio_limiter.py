import asyncio
import time
from enum import Enum
from functools import wraps
from typing import Callable

from .exceptions import WindowTooManyRequests, RateTooManyRequests, SkipRequest


class RateLimitStrategy(Enum):
    WAIT = "wait"  # Ждать, пока можно будет выполнить
    RAISE = "raise"  # Выбросить исключение
    SKIP = "skip"  # Пропустить вызов


class BaseLimiter:
    """
    Базовый класс для всех лимитеров. Не используйте его в приложениях он работает как датакласс для наследников
    """
    def __init__(self, strategy: RateLimitStrategy = RateLimitStrategy.WAIT):
        self.strategy = strategy
        self._lock = asyncio.Lock()


calls = {}


class WindowRateLimiter(BaseLimiter):
    """
    Лимитер скользящего окна.
    """
    def __init__(
        self,
        max_calls: int,
        time_window: float,
        strategy: RateLimitStrategy = RateLimitStrategy.WAIT
    ):
        """
        max_calls: int - максимальное количество вызовов в окне
        time_window: float - время окна в секундах
        strategy: стратегия при превышении лимита
        """
        self.max_calls = max_calls
        self.time_window = time_window
        super().__init__(strategy)

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self._lock:
                current_time = time.time()
                _calls = [t for t in calls.get(func.__name__, []) if t > current_time - self.time_window]
                if len(_calls) >= self.max_calls:
                    match self.strategy:
                        case RateLimitStrategy.WAIT:
                            await asyncio.sleep(self.time_window - (current_time - _calls[0]))
                        case RateLimitStrategy.RAISE:
                            raise WindowTooManyRequests(self.max_calls, self.time_window)
                        case RateLimitStrategy.SKIP:
                            raise SkipRequest()
                _calls.append(current_time)
                calls[func.__name__] = _calls
            return await func(*args, **kwargs)
        return wrapper


class CallsPerSecondLimiter(BaseLimiter):
    """
    Лимитер вызовов в секунду.
    """
    def __init__(
        self,
        calls_per_second: float,
        strategy: RateLimitStrategy = RateLimitStrategy.WAIT
    ):
        """
        calls_per_second: float - максимальное количество вызовов в секунду
        strategy: RateLimitStrategy - стратегия при превышении лимита
        """
        self.interval = 1.0 / calls_per_second
        self.last_call_time = 0
        super().__init__(strategy)

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            async with self._lock:
                if time_since_last < self.interval:
                    match self.strategy:
                        case RateLimitStrategy.WAIT:
                            await asyncio.sleep(self.interval - time_since_last)
                        case RateLimitStrategy.RAISE:
                            raise RateTooManyRequests(self.interval)
                        case RateLimitStrategy.SKIP:
                            raise SkipRequest()
                self.last_call_time = time.time()
            return await func(*args, **kwargs)
        return wrapper

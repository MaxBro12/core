from time import time
from typing import Callable
from functools import wraps

from fastapi import HTTPException, status


def rate_limiter(max_requests: int = 10, time_delta: int = 30):
    """Простой ограничитель скорости запросов"""
    def decorator(func: Callable):
        calls = []
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time()
            calls[:] = [call for call in calls if current_time - call < time_delta]
            if len(calls) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit"
                )
            calls.append(current_time)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

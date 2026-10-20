import time
from functools import wraps

from fastapi import HTTPException


def token_global(
    rate: float = 1, capacity: int = 50, 
    extra_good_codes: tuple[int, ...] | None = None, 
    debuff_value: int = -1
):
    """
    rate - пополнение токенов в секунду (1 - 1 запрос в секунду, 0,1 - 1 запрос в 10 секунд)
    capacity - максимум токенов
    extra_good_codes - коды при которых ответ положительный и взымается базовое значение в -1 токен за запрос\
    если код 404 вычитается debuff_value
    debuff_value - значение на которое уменьшится карзина токенов при плохом статусе
    """
    tokens = capacity
    last = time.monotonic()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.monotonic()
            new_tokens = min(capacity, tokens + (now - last) * rate)
            if new_tokens < 1:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests",
                    headers={"Retry-After": str(int((1 - new_tokens) / rate) + 1)},
                )
            tokens = new_tokens - 1
            last = now
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def token_per_ip(
    rate: float = 1, capacity: int = 50, 
    extra_good_codes: tuple[int, ...] | None = None, 
    debuff_value: int = -1
):
    """
    rate - пополнение токенов в секунду (1 - 1 запрос в секунду, 0,1 - 1 запрос в 10 секунд)
    capacity - максимум токенов
    extra_good_codes - коды при которых ответ положительный и взымается базовое значение в -1 токен за запрос\
    если код 404 вычитается debuff_value
    debuff_value - значение на которое уменьшится карзина токенов при плохом статусе
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: request | none = none, **kwargs):
            raise NotImplementedError
        return wrapper
    return decorator


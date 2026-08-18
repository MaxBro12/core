from time import time
from typing import Callable
from functools import wraps
from dataclasses import is_dataclass, asdict

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


class CacheDecoratorException(Exception):
    """Исключение для CacheDecorator"""
    pass


class CantConvertBaseModel(CacheDecoratorException):
    """Исключение для BaseModel"""
    def __init__(self, model: DeclarativeBase):
        super().__init__(f'Cannot convert model {model.__name__} to dict')


def cache_path(expire: int = 1800, debug: bool = False):
    """Кэширование данных из эндпоинта через request.path. Это статичный ключ и легко работает с микросервисами.
    Требуется 'request: Request' в параметрах эндпойнта.
    Работает с int exp!"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> dict | None | HTTPException:
            # Получаем request и redis
            try:
                request = kwargs.get('request')
                redis = kwargs.get('redis') or request.app.state.redis

                # нету не реквеста не редиса логика кэша заканчивается
                if request is None or redis is None:
                    return await func(*args, **kwargs)
            except AttributeError:
                return await func(*args, **kwargs)

            # Получаем данные с редиса если они есть
            ans = await redis.get_json(
                f'{request.url.path}{f'?{request.url.query}' if request.url.query != "" else ""}',
                debug=debug
            )
            if ans is not None and ans.get('exp') and int(time()) < ans['exp']:
                return ans

            # Выполняем функцию
            ans = await func(*args, **kwargs)

            # Пустой ответ
            if ans is None:
                return None
            # HTTPException - игнорируем
            elif isinstance(ans, HTTPException):
                return ans
            # Dataclass - преобразуем в словарь
            elif is_dataclass(ans):
                ans = asdict(ans)
            # BaseModel - преобразуем в словарь
            elif isinstance(ans, BaseModel):
                ans = ans.model_dump()
            # SqlAlchemy model - преобразуем в словарь
            elif isinstance(ans, DeclarativeBase):
                m_dict = ans.__dict__
                if type(m_dict) is not dict:
                    raise CantConvertBaseModel(ans)
                ans = m_dict

            # Добавляем время истечения к ответу
            ans['exp'] = int(time() + expire)

            # Сохраняем ответ в кэш
            await redis.set_json(
                f'{request.url.path}{f'?{request.url.query}' if request.url.query != "" else ""}', ans,
                debug=debug
            )
            return ans
        return wrapper
    return decorator


def cache(key: str, expire: int = 1800, debug: bool = False): # 30 минут
    """Кэширование результатов эндпоинта. Для работы в эндпойнте требуется redis: RedisDep"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> dict | None | HTTPException:
            redis = kwargs.get('redis')
            if redis is None:
                return await func(*args, **kwargs)

            keys = ''
            for k, v in kwargs.items():
                if k in ('redis', 'db', 'session', 'token', 'request', 'response', 'exp', 'key'):
                    continue
                keys += f'{k}:{v}'

            r_ans = await redis.get_json(f'{key}:{keys}', debug=debug)
            if r_ans is not None and r_ans.get('exp') and time() < r_ans['exp']:
                return r_ans

            ans = await func(*args, **kwargs)

            # Пустой ответ
            if ans is None:
                return None
            # HTTPException - игнорируем
            elif isinstance(ans, HTTPException):
                return ans
            # Dataclass - преобразуем в словарь
            elif is_dataclass(ans):
                ans = asdict(ans)
            # BaseModel - преобразуем в словарь
            elif isinstance(ans, BaseModel):
                ans = ans.model_dump()
            # SqlAlchemy model - преобразуем в словарь
            elif isinstance(ans, DeclarativeBase):
                m_dict = ans.__dict__
                if type(m_dict) is not dict:
                    raise CantConvertBaseModel(ans)
                ans = m_dict

            # Добавляем время истечения к ответу
            ans['exp'] = time() + expire

            # Сохраняем ответ в кэш
            await redis.set_json(f'{key}:{keys}', ans, debug=debug)
            return ans
        return wrapper
    return decorator

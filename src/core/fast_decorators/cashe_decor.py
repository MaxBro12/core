from time import time
from typing import Callable
from functools import wraps
from dataclasses import is_dataclass, asdict

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


def cache(key: str, expire: int = 1800, debug: bool = False): # 30 минут
    """Кэширование результатов эндпоинта. Для работы в эндпойнте требуется redis: RedisDep"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
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
            if ans is None:
                return None
            elif is_dataclass(ans):
                ans = asdict(ans)
            elif isinstance(ans, BaseModel):
                ans = ans.model_dump()
            elif isinstance(ans, DeclarativeBase):
                ans = ans.__dict__
            ans['exp'] = time() + expire

            await redis.set_json(f'{key}:{keys}', ans, debug=debug)
            return ans
        return wrapper
    return decorator

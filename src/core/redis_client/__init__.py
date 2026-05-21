import logging

from .base import RedisClient
from .dependency import RedisDep, get_redis
from .exceptions import RedisException, RedisConnectionError


__all__ = (
    "RedisClient",
    "RedisException",
    "RedisConnectionError",
    "RedisDep",
    "get_redis",
)

logger = logging.getLogger('redis_client')
logger.addHandler(logging.NullHandler())

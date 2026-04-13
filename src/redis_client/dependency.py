from typing import AsyncGenerator, Annotated

from fastapi import Depends, Request

from .base import RedisClient


async def get_redis(request: Request) -> AsyncGenerator[RedisClient, None]:
    yield request.app.state.redis


RedisDep = Annotated[RedisClient, Depends(get_redis)]

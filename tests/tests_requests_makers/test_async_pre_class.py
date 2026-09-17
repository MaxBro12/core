import pytest

from src.core.redis_client import RedisClient
from src.core.requests_makers.asyncio_base_pre_class import HttpMakerAsyncBaseMiddle


async def test_init():
    a = HttpMakerAsyncBaseMiddle(
        '/test/', {'test': 1}, timeout_in_sec=123,
        redis_prefix='test'
    )
    assert a._base_url == '/test'
    assert a._headers['test'] == 1
    assert type(a._params) is dict
    assert a._timeout == 123
    assert a._redis_prefix == 'test'


async def test_redis(mock_http_session, redis_client: RedisClient):
    await redis_client.set_json('/test', {'ok': True})
    d = await HttpMakerAsyncBaseMiddle.redis_cache(
        redis=redis_client, key='/test',
        spec_app_prefix='test_prefix'
    )
    assert d is not None
    assert d['ok']


async def test_no_redis(mock_http_session, redis_client: RedisClient):
    await redis_client.set_json('/test', {'ok': True})
    d = await HttpMakerAsyncBaseMiddle.redis_cache(
        redis=redis_client, key='/wrong',
        spec_app_prefix='test_prefix'
    )
    assert d is None

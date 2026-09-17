import pytest

from src.core.redis_client import RedisClient
from src.core.requests_makers.asyncio_micro_base import HttpMakerAsyncMicroBase
from src.core.requests_makers.exceptions import MicroServiceUrlUnknown


async def test_init():
    a = HttpMakerAsyncMicroBase(
        '/test/', {'test': 1}, timeout_in_sec=123,
        redis_prefix='test'
    )
    assert a._base_url == '/test'
    assert a._headers['test'] == 1
    assert type(a._params) is dict
    assert a._timeout == 123
    assert a._redis_prefix == 'test'
    assert a._redis_client == None


async def test_init_no_url():
    with pytest.raises(MicroServiceUrlUnknown):
        HttpMakerAsyncMicroBase()


async def test_full_path():
    a = HttpMakerAsyncMicroBase('http://test.url')
    assert a._full_path('test') == 'http://test.url/test'


async def test_full_path_end_slash():
    a = HttpMakerAsyncMicroBase('http://test.url')
    assert a._full_path('test/') == 'http://test.url/test/'


async def test_full_path_with_slash():
    a = HttpMakerAsyncMicroBase('http://test.url/')
    assert a._full_path('test') == 'http://test.url/test'


async def test_full_path_path_slash():
    a = HttpMakerAsyncMicroBase('http://test.url')
    assert a._full_path('/test') == 'http://test.url/test'


async def test_redis(mock_http_session, redis_client: RedisClient):
    await redis_client.set_json('/test', {'ok': True})
    a = HttpMakerAsyncMicroBase('http:127.0.0.1', redis_prefix='test_prefix')
    d = await a._cache('/test', redis=redis_client)
    assert d is not None
    assert d['ok']


async def test_no_redis(mock_http_session, redis_client: RedisClient):
    await redis_client.set_json('/test', {'ok': True})
    a = HttpMakerAsyncMicroBase('http:127.0.0.1')
    d = await a._cache('/test', redis=None)
    assert d is None


async def test_make_raise():
    a = HttpMakerAsyncMicroBase('http:127.0.0.1')
    with pytest.raises(NotImplementedError):
        await a._make('/test', 'GET')

import pytest

from .tools import make_response
from src.core.redis_client import RedisClient
from src.core.requests_makers.exceptions import RequestMethodNotFoundException, MicroServiceUrlUnknown
from src.core.requests_makers.asyncio_micro_long import HttpMakerMicroAsyncLong


async def test_full_path():
    a = HttpMakerMicroAsyncLong('http://test.url')
    assert a.full_path('test') == 'http://test.url/test'


async def test_full_path_end_slash():
    a = HttpMakerMicroAsyncLong('http://test.url')
    assert a.full_path('test/') == 'http://test.url/test/'


async def test_full_path_with_slash():
    a = HttpMakerMicroAsyncLong('http://test.url/')
    assert a.full_path('test') == 'http://test.url/test'


async def test_full_path_path_slash():
    a = HttpMakerMicroAsyncLong('http://test.url')
    assert a.full_path('/test') == 'http://test.url/test'


async def test_full_path():
    with pytest.raises(MicroServiceUrlUnknown):
        HttpMakerMicroAsyncLong('')


async def test_get(mock_http_session):
    mock_http_session.get.return_value = make_response({'ok': True})
    a = HttpMakerMicroAsyncLong('http:127.0.0.1', session=mock_http_session)
    d = await a.get('/test')
    assert d.json['ok']


async def test_post(mock_http_session):
    mock_http_session.post.return_value = make_response({'ok': True})
    a = HttpMakerMicroAsyncLong('http:127.0.0.1', session=mock_http_session)
    d = await a.post('/test')
    assert d.json['ok']


async def test_wrong_method(mock_http_session):
    with pytest.raises(RequestMethodNotFoundException):
        a = HttpMakerMicroAsyncLong('http:127.0.0.1', session=mock_http_session)
        await a._make('/test', method='LABYBY')
    

async def test_redis(mock_http_session, redis_client: RedisClient):
    mock_http_session.post.return_value = make_response({'ok': False})
    await redis_client.set_json('/test', {'ok': True})
    a = HttpMakerMicroAsyncLong('http:127.0.0.1', session=mock_http_session, redis_prefix='test_prefix')
    d = await a.post('/test', redis=redis_client)
    assert d.json['ok']


async def test_not_redis(mock_http_session, redis_client: RedisClient):
    mock_http_session.post.return_value = make_response({'ok': True})
    await redis_client.set_json('/test', {'ok': False})
    a = HttpMakerMicroAsyncLong('http:127.0.0.1', session=mock_http_session, redis_prefix='test_prefix')
    d = await a.post('/test', redis=redis_client, key='wrong_key')
    assert d.json['ok']


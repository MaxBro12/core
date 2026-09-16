from src.core.requests_makers.asyncio_base import HttpMakerAsyncBase


async def test_full_path():
    a = HttpMakerAsyncBase('http://test.url')
    assert a._full_path('test') == 'http://test.url/test'


async def test_full_path_end_slash():
    a = HttpMakerAsyncBase('http://test.url')
    assert a._full_path('test/') == 'http://test.url/test/'


async def test_full_path_with_slash():
    a = HttpMakerAsyncBase('http://test.url/')
    assert a._full_path('test') == 'http://test.url/test'


async def test_full_path_path_slash():
    a = HttpMakerAsyncBase('http://test.url')
    assert a._full_path('/test') == 'http://test.url/test'


async def test_full_base_is_no():
    a = HttpMakerAsyncBase('')
    assert a._full_path('/test') == '/test'

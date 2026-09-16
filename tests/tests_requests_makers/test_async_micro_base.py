from src.core.requests_makers.asyncio_micro_base import HttpMakerAsyncMicroBase


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

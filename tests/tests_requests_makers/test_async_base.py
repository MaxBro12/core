import asyncio
from time import time
import pytest
from src.core.requests_makers.asyncio_base import HttpMakerAsyncBase
from src.core.requests_makers.exceptions import RequestMethodNotFoundException


async def test_init():
    a = HttpMakerAsyncBase('/test/', {'test': 1}, timeout_in_sec=123)
    assert a._base_url == '/test'
    assert a._headers['test'] == 1
    assert type(a._params) is dict
    assert a._timeout == 123


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


async def test_full_headers_combine():
    a = HttpMakerAsyncBase('', base_headers={'test': 1})
    t = a._full_haeders({'test2': 2})
    assert 'test' in t
    assert 'test2' in t
    assert 'test2' not in a._headers


async def test_full_headers_addet():
    a = HttpMakerAsyncBase('')
    t = a._full_haeders({'test2': 2})
    assert 'test2' in t
    assert 'test2' not in a._headers


async def test_full_headers_none():
    a = HttpMakerAsyncBase('', base_headers={'test': 1})
    t = a._full_haeders(None)
    assert 'test' in t
    assert len(t.keys()) == 1


async def test_full_headers_copy():
    h = {'test': 1}
    a = HttpMakerAsyncBase('', base_headers=h)
    t = a._full_haeders(None)
    assert 'test' in t
    assert t is not h


async def test_full_params_combine():
    a = HttpMakerAsyncBase('', base_params={'test': 1})
    t = a._full_params({'test2': 2})
    assert 'test' in t
    assert 'test2' in t
    assert 'test2' not in a._headers


async def test_full_params_addet():
    a = HttpMakerAsyncBase('')
    t = a._full_params({'test2': 2})
    assert 'test2' in t
    assert 'test2' not in a._headers


async def test_full_params_none():
    a = HttpMakerAsyncBase('', base_headers={'test': 1})
    t = a._full_haeders(None)
    assert 'test' in t
    assert len(t.keys()) == 1


async def test_full_params_copy():
    h = {'test': 1}
    a = HttpMakerAsyncBase('', base_params=h)
    t = a._full_params(None)
    assert 'test' in t
    assert t is not h


async def test_full_params_bool():
    a = HttpMakerAsyncBase('', base_params={'true': True})
    t = a._full_params({'false': False})
    assert t['true'] == 'true'
    assert t['false'] == 'false'


async def test_extract_method_correct(mock_http_session):
    a = HttpMakerAsyncBase('')
    try:
        a._extract_method('GET', mock_http_session)
    except RequestMethodNotFoundException:
        assert False, 'Method should exist'


async def test_extract_method_correct_lower(mock_http_session):
    a = HttpMakerAsyncBase('')
    try:
        a._extract_method('get', mock_http_session)
    except RequestMethodNotFoundException:
        assert False, 'Method should auto use UPPER'


async def test_extract_method_raise(mock_http_session):
    a = HttpMakerAsyncBase('')
    with pytest.raises(RequestMethodNotFoundException):
        a._extract_method('wrong_method', mock_http_session)


async def test_multi_call():
    async def a():
        await asyncio.sleep(1.5)
    async def b():
        await asyncio.sleep(1)
    st = time()
    await HttpMakerAsyncBase.multi_call(a(), b())
    assert time() - st <= 2

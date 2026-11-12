import asyncio
from time import time
import json
from pydantic import BaseModel
from dataclasses import dataclass, asdict
import pytest
from src.core.requests_makers.asyncio_base import HttpMakerAsyncBase
from src.core.requests_makers.exceptions import RequestMethodNotFoundException, UnsupportedObject, ResponseValidationError, ResponseKeyError
from src.core.requests_makers.response import ResponseData


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
        return 'a'
    async def b():
        await asyncio.sleep(1)
        return 'b'
    st = time()
    a = await HttpMakerAsyncBase.multi_call(a(), b())
    assert time() - st <= 2
    assert len(a) == 2
    assert a[0] == 'a'
    assert a[1] == 'b'


async def test_model_dump_dict():
    a = HttpMakerAsyncBase('')
    t = {'a': 10, 1: 100,  1.2: '100'}
    ans = a._model_to_json(t)

    assert {'a': 10, 1: 100,  1.2: '100'} == ans


async def test_model_dataclass():
    a = HttpMakerAsyncBase('')

    @dataclass
    class T1:
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456
    t1 = T1()

    @dataclass(frozen=True, slots=True)
    class T2:
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456
    t2 = T2()

    @dataclass(slots=True)
    class T3:
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456
    t3 = T3()

    @dataclass(frozen=True)
    class T4:
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456
    t4 = T4()

    t1_a = a._model_to_json(t1)
    t2_a = a._model_to_json(t2)
    t3_a = a._model_to_json(t3)
    t4_a = a._model_to_json(t4)

    t1_b = T1(**t1_a)
    t2_b = T2(**t2_a)
    t3_b = T3(**t3_a)
    t4_b = T4(**t4_a)

    assert t1 == t1_b
    assert t2 == t2_b
    assert t3 == t3_b
    assert t4 == t4_b


async def test_model_pydantic():
    a = HttpMakerAsyncBase('')
    class TestModel(BaseModel):
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456
    t = TestModel()
    t_a = a._model_to_json(t)
    t_b = TestModel(**t_a)
    assert t == t_b


async def test_model_incorrect():
    a = HttpMakerAsyncBase('')

    class Model:
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456

    with pytest.raises(UnsupportedObject):
        a._model_to_json(Model())


async def test_model_none():
    a = HttpMakerAsyncBase('')
    assert a._model_to_json(None) is None


async def test_json_to_model_correct():
    a = HttpMakerAsyncBase('')

    @dataclass
    class Model:
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456

    ans = a._json_to_model(ResponseData('test_url', 200, {}, {
        'a': False,
        'a2': True,
        'b': '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}',
        'c': 1.123456
    }), {200: Model})

    assert type(ans) is Model
    assert ans.a is False
    assert ans.a2 is True
    assert ans.b == Model().b
    assert ans.c == Model().c


async def test_json_to_model_correct_by_model():
    a = HttpMakerAsyncBase('')

    class Model(BaseModel):
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456

    ans = a._json_to_model(ResponseData('test_url', 200, {}, {
        'a': False,
        'a2': True,
        'b': '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}',
        'c': 1.123456
    }), {200: Model})

    assert type(ans) is Model
    assert ans.a is False
    assert ans.a2 is True
    assert ans.b == Model().b
    assert ans.c == Model().c


async def test_json_to_model_wrong_field():
    a = HttpMakerAsyncBase('')

    @dataclass
    class Model:
        a: int
        a2: bool = False
        c: float = 1.123456

    with pytest.raises(ResponseValidationError):
        a._json_to_model(ResponseData('test_url', 200, {}, {
            'a2': True,
            'c': 1.123456
        }), {200: Model})


async def test_json_to_model_wrong_field_by_model():
    a = HttpMakerAsyncBase('')

    class Model(BaseModel):
        a: int
        a2: bool = False
        c: float = 1.123456

    with pytest.raises(ResponseValidationError):
        a._json_to_model(ResponseData('test_url', 200, {}, {
            'a2': True,
            'c': 1.123456
        }), {200: Model})


async def test_json_to_model_wrong_field_by_class():
    a = HttpMakerAsyncBase('')

    class Model:
        a: int
        a2: bool = False
        c: float = 1.123456

    with pytest.raises(ResponseValidationError):
        a._json_to_model(ResponseData('test_url', 200, {}, {
            'a2': True,
            'c': 1.123456
        }), {200: Model})


async def test_json_to_model_no_model():
    a = HttpMakerAsyncBase('')

    class Model(BaseModel):
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456

    with pytest.raises(ResponseKeyError):
        a._json_to_model(ResponseData('test_url', 400, {}, {
            'a': False,
            'a2': True,
            'b2': '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}',
            'c': 1.123456
        }), {200: Model})


async def test_json_to_model_no_model_by_pidantic():
    a = HttpMakerAsyncBase('')

    class Model(BaseModel):
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456

    with pytest.raises(ResponseKeyError):
        a._json_to_model(ResponseData('test_url', 400, {}, {
            'a': False,
            'a2': True,
            'b2': '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}',
            'c': 1.123456
        }), {200: Model})


async def test_json_to_model_no_model_by_class():
    a = HttpMakerAsyncBase('')

    class Model:
        a: bool = True
        a2: bool = False
        b: str = '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}'
        c: float = 1.123456

    with pytest.raises(ResponseKeyError):
        a._json_to_model(ResponseData('test_url', 400, {}, {
            'a': False,
            'a2': True,
            'b2': '123456789qwertyuiopasdfghjklzxcvbnm,.<>/;:\'"[]{}',
            'c': 1.123456
        }), {200: Model})

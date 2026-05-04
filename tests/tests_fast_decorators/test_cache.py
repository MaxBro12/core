import pytest
import time
import json

from src.core.fast_decorators.cashe_decor import cache


@pytest.fixture
def mock_function():
    async def mock_func(*args, **kwargs):
        return {'data': 'funct_test'}
    return mock_func


async def test_cache_empty(mock_function, redis_client, mock_redis):
    """
    Проверяем вызов конечной функции пока кэш пуст
    """
    key = 'test_key'
    expire = 60
    st = time.time()

    decorated = cache(key=key, expire=expire, debug=True)(mock_function)
    result = await decorated(redis=redis_client, param1="value1", param2=123)
    assert result is not None
    assert result['data'] == 'funct_test'
    assert 'exp' in result
    assert int(result['exp']) == int(expire + st)
    mock_redis.get.assert_called_once_with(f"test_prefix_{key}:param1:value1param2:123")


async def test_cache_hit(mock_function, redis_client, mock_redis):
    """
    Проверяем, что кэш существует и возвращает без вызова конечной функции
    """
    key = 'test_key'
    expire = 60
    st = time.time()
    cached_data = {'cached': True, 'exp': 3600 + st}
    await mock_redis.set(f"test_prefix_{key}:param1:value1", json.dumps(cached_data), ex=3600 + st)
    decorated = cache(key=key, expire=expire)(mock_function)
    result = await decorated(redis=redis_client, param1="value1")
    assert result is not None
    assert 'cached' in result and result['cached'] is True
    assert 'data' not in result
    mock_redis.set.assert_called_once_with(
        f"test_prefix_{key}:param1:value1",
        json.dumps(cached_data),
        ex=3600 + st
    )


async def test_cache_not_return_another_key(mock_function, redis_client, mock_redis):
    """
    Проверяем, что кэш не существует и вызывает конечную функцию
    """
    # Создаем первый ключ
    key1 = 'test_key'
    expire = 60
    st = time.time()
    await mock_redis.set(f"test_prefix_{key1}", json.dumps({
        'data': 'Already cached',
        'exp': 3600 + st
    }), ex=3600 + st)

    # Создаем второй ключ
    key2 = 'test_key2'
    decorated = cache(key=key2, expire=expire, debug=True)(mock_function)
    result = await decorated(redis=redis_client)
    assert result is not None
    assert result['data'] == 'funct_test'


async def test_cache_expire(mock_function, redis_client, mock_redis):
    """
    Проверяем, что кэш истек и вызывает конечную функцию
    """
    key = 'test_key'
    expire = 60
    st = time.time()
    await mock_redis.set(f"test_prefix_{key}", json.dumps({
        'data': 'Already cached',
        'exp': st - 1
    }), ex=st - 1)
    decorated = cache(key=key, expire=expire, debug=True)(mock_function)
    result = await decorated(redis=redis_client)
    assert result is not None
    assert result['data'] == 'funct_test'


async def test_cache_redis_not_provided(mock_function, mock_redis):
    """
    Проверяем, что декоратор, без получения redis, вызывает конечную функцию
    """
    key = 'test_key'
    expire = 60
    decorated = cache(key=key, expire=expire, debug=True)(mock_function)
    result = await decorated()
    assert result is not None
    assert result['data'] == 'funct_test'


async def test_cache_params_unique(mock_function, redis_client, mock_redis):
    """
    Проверяем, что параметры уникальны и вызывают конечную функцию
    """
    key1 = 'test_key'
    expire = 60
    st = time.time()
    await mock_redis.set(f"test_prefix_{key1}:user_id:1", json.dumps({
        'data': 'Already cached',
        'exp': st + 100
    }), ex=st + 100)
    decorated = cache(key=key1, expire=expire, debug=True)(mock_function)
    result1 = await decorated(redis=redis_client, user_id=1)
    result2 = await decorated(redis=redis_client, user_id=2)
    result3 = await decorated(redis=redis_client, user_id=1, test='test')
    assert result1 is not None
    assert result2 is not None
    assert result3 is not None

    assert result1['data'] == 'Already cached'
    assert result2['data'] == 'funct_test'
    assert result3['data'] == 'funct_test'

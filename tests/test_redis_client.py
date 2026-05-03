import pytest
import json

import redis.asyncio as redis_a

from src.core.redis_client import RedisClient



async def test_set_json(redis_client, mock_redis):
    """Тест метода set_json"""
    test_key = "user_123"
    test_data = {"name": "John", "age": 30}
    #raise Exception(redis_client.__dir__())

    result = await redis_client.set_json(test_key, test_data)

    # Проверяем, что set был вызван с правильными параметрами
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert "test_prefix_user_123" in call_args[0]
    assert json.loads(call_args[0][1]) == test_data
    assert result is None  # set не возвращает значение


async def test_set_json_connection_error(redis_client, mock_redis):
    """Тест метода set_json при ConnectionError"""
    # Настройка мока для вызова ConnectionError
    mock_redis.set.side_effect = redis_a.ConnectionError

    result = await redis_client.set_json("error_key", {"data": "test"})

    # Проверяем, что возвращается None при ошибке соединения
    assert result is None

    # Проверяем, что set был вызван, несмотря на ошибку, и вернул None
    mock_redis.set.assert_called_once()


async def test_set_json_dont_overwrite_other_key(redis_client, mock_redis):
    """Тест метода set_json не перезаписывает другие ключи"""
    test_key1 = "user_456"
    expected_data1 = {"name": "Jane", "age": 25}
    await redis_client.set_json(test_key1, expected_data1)

    test_key2 = "user_457"
    expected_data2 = {"name": "Den", "age": 30}
    await redis_client.set_json(test_key2, expected_data2)


    result = await redis_client.get_json(test_key1)

    # Проверяем результат
    assert result == expected_data1


async def test_delete(redis_client, mock_redis):
    """Тест метода delete"""
    test_key = "item_to_delete"
    # Ожидаем вызов delete на подклике с префиксом
    expected_key = "test_prefix_item_to_delete"
    await redis_client.delete(test_key)
    mock_redis.delete.assert_called_once_with(expected_key)
    assert await redis_client.get_json(test_key) is None


async def test_delete_not_found(redis_client, mock_redis):
    """Тест метода delete при отсутствии данных"""
    test_key = "non_existent_key"
    await redis_client.delete(test_key)
    mock_redis.delete.assert_called_once_with("test_prefix_non_existent_key")
    assert await redis_client.get_json(test_key) is None


async def test_delete_not_delete_other_key(redis_client, mock_redis):
    """Тест метода delete не удаляет другие ключи"""
    test_key1 = "user_456"
    await redis_client.set_json(test_key1, {"name": "Jane", "age": 25})
    test_key2 = "item_to_delete"
    await redis_client.delete(test_key2)
    mock_redis.delete.assert_called_once_with("test_prefix_item_to_delete")
    assert await redis_client.get_json(test_key1) is not None
    assert await redis_client.get_json(test_key2) is None


async def test_get_json_found(redis_client, mock_redis):
    """Метод get_json находит данные"""
    test_key = "user_456"
    expected_data = {"name": "Jane", "age": 25}

    await redis_client.set_json(test_key, expected_data)

    result = await redis_client.get_json(test_key)

    # Проверяем, что get был вызван с правильным ключом
    mock_redis.get.assert_called_once_with("test_prefix_user_456")

    # Проверяем результат
    assert result == expected_data


async def test_get_json_not_found(redis_client, mock_redis):
    """get_json возвращает не существующие данные"""
    test_key = "non_existent_key"
    result = await redis_client.get_json(test_key)
    assert result is None
    mock_redis.get.assert_called_once_with("test_prefix_non_existent_key")

import logging
import json
from typing import Any

from redis.exceptions import ConnectionError
import redis.asyncio as redis_a


logger = logging.getLogger(__name__)


class RedisClient:
    """
    Клиент для взаимодействия с Redis.
    Необходим для автоматического управления ключами и соединениям с RedisDep.
    """

    def __init__(self, redis_pool: redis_a.ConnectionPool, prefix: str, expire: int = 3600):
        """
        Инициализирует экземпляр RedisClient.

        Args:
            redis_pool: Пул соединений Redis.
            prefix: Базовый префикс, который будет добавляться ко всем ключам.
            expire: Стандартный срок жизни ключей в секундах (по умолчанию 3600).
        """
        self.__client = redis_a.Redis(connection_pool=redis_pool)

        self.__prefix = prefix
        self.__expire = expire

    def __insert_prefix_key(self, key: str | int, spec_app_prefix: str | None = None) -> str:
        """
        Добавляет префикс приложения к ключу, если указан spec_app_prefix добавится он,
        если нет то используется префикс сохраненный в приложение.
        """
        if spec_app_prefix is None:
            return f'{str(self.__prefix)}_{str(key)}'
        return f'{str(spec_app_prefix)}_{str(key)}'

    async def delete(self, key: str | int, debug: bool = False):
        """
        Удаляет ключ из Redis.
        """
        if debug:
            logger.debug(f'Deleting key: {self.__insert_prefix_key(key)}')
        return await self.__client.delete(self.__insert_prefix_key(key))

    async def clear(self, spec_app_prefix: str | None = None):
        """
        Удаляет все ключи приложения из Redis,
        если указан spec_app_prefix удалятся ключи от других приложений с этим префиксом.
        Используйте с осторожностью.
        """
        key = self.__insert_prefix_key(key='', spec_app_prefix=spec_app_prefix)
        logger.debug(f'Clearing keys for: {key}')
        async for k in self.__client.scan_iter(f'{key}*'):
            await self.__client.unlink(k)


    async def set_json(self, key: str, data: dict, debug: bool = False):
        """
        Сохраняет JSON данные в Redis.
        - key: Ключ для сохранения данных.
        - data: Данные для сохранения.
        - debug: Включить отладочный режим? Выведет полный ключ сохранения.
        """
        if debug:
            logger.debug(f'set_json: {self.__insert_prefix_key(key)}')
        try:
            await self.__client.set(
                self.__insert_prefix_key(key),
                json.dumps(data),
                ex=self.__expire
            )
        except ConnectionError:
            return None

    async def get_json(
        self,
        key: str,
        spec_app_prefix: str | None = None,
        debug: bool = False
    ) -> dict[str, Any] | None:
        """
        Получает JSON данные из Redis по ключу.
        - key: Ключ для получения данных.
        - spec_app_prefix: Префикс приложения для ключа если нужно использовать вне приложения.
        - debug: Включить отладочный режим? Выведет полный ключ получения.
        """
        if debug:
            logger.debug(
                f'get_json: {self.__insert_prefix_key(key, spec_app_prefix=spec_app_prefix)}'
            )
        key = self.__insert_prefix_key(key, spec_app_prefix=spec_app_prefix)
        try:
            ans = await self.__client.get(key)
            if ans is None:
                return None
            return json.loads(ans)
        except ConnectionError:
            return None

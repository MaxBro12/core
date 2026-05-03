import json
from typing import Any

from redis.exceptions import ConnectionError
import redis.asyncio as redis_a


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
        if spec_app_prefix is None:
            return f'{str(self.__prefix)}_{str(key)}'
        return f'{str(spec_app_prefix)}_{str(key)}'

    async def delete(self, key: str | int):
        return await self.__client.delete(self.__insert_prefix_key(key))

    async def set_json(self, key: str, data: dict, debug: bool = False):
        if debug:
            print(f'set_json: {key}')
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
        if debug:
            print(f'get_json: {key}')
        key = self.__insert_prefix_key(key, spec_app_prefix=spec_app_prefix)
        try:
            ans = await self.__client.get(key)
            if ans is None:
                return None
            return json.loads(ans)
        except ConnectionError:
            return None

import asyncio
import logging
from typing import Any, Coroutine

import aiohttp

from core.redis_client import RedisClient

from .exceptions import RequestMethodNotFoundException, UnableToParse, MicroServiceUrlUnknown
from .response import ResponseData, Method


logger = logging.getLogger(__name__)


class HttpMakerMicroAsync:
    __base_url: str
    __headers: dict
    __params: dict
    __timeout: int
    __redis_prefix: str | None
    __redis_client: RedisClient | None

    """
    Асинхронный HTTP-клиент упрощенный для микро-сервисной архитектуры.
    - убрана проверка пути, если базовый путь будет "" вызовется исключение
    - убраны методы обработки запроса, все ответы от сервисов должны быть стандартными json объектами
    """
    def __init__(
        self,
        base_url: str,
        base_headers: None | dict = None,
        base_params: None | dict = None,
        timeout_in_sec: int = 10,
        redis_prefix: str | None = None,
        redis_client: RedisClient | None = None,
    ) -> None:
        """
        Инициализация асинхронного HTTP-клиента.
        - base_url - Базовый URL для всех запросов.
        - base_headers - Базовые заголовки для всех запросов.
        - base_params - Базовые параметры для всех запросов.
        - timeout_in_sec - Тайм-аут в секундах для каждого запроса.
        - redis_prefix - префикс целевого приложения для редиса
        - redis_client - единый клиент RedisClient (его можно передать с запросом)

        В этой версии base_url не должен быть "" (убрана проверка полного пути)
        """
        if base_url == '':
            raise MicroServiceUrlUnknown()

        self.__base_url = base_url.rstrip('/')

        if base_headers is None:
            base_headers = {}
        self.__headers = base_headers   # это должен быть словарь

        if base_params is None:
            base_params = {}
        self.__params = base_params    # это должен быть словарь

        self.__timeout = timeout_in_sec
        self.__redis_prefix = redis_prefix
        self.__redis_client = redis_client

    def full_path(self, path: str) -> str:
        """
        Возвращает полный путь до запроса, объединяя базовый URL и переданный путь.

        :param path: Путь для запроса.
        :return: Полный путь.
        """
        return f'{self.__base_url}/{path.lstrip('/')}'

    async def __cache(self, key: str, redis: RedisClient | None) -> dict | None:
        """
        Получает данные из кэша Redis по ключу и префиксу приложения.

        - redis - Клиент Redis.
        - key - Ключ для поиска в кэше.
        - spec_app_prefix - Префикс приложения.
        return: Данные из кэша или None, если их нет.
        """
        redis_cl = redis or self.__redis_client
        if redis_cl and self.__redis_prefix:
            return await redis.get_json(
                key=key,
                spec_app_prefix=self.__redis_prefix
            )
        return None

    async def __execute(
        self,
        path: str,
        method: Method,
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> ResponseData:
        """
        Выполняет HTTP-запрос с заданными параметрами.

        - path: Путь для запроса.
        - method: HTTP-метод.
        - data: Данные для отправки.
        - json: JSON-данные для отправки.
        - params: Параметры запроса.
        - headers: Заголовки запроса.
        - try_wait_if_error: Флаг, указывающий на необходимость ожидания перед повторной попыткой.
        return: Объект ResponseData с данными ответа или None.
        """
        # Совмещаем заголовки
        if headers is not None:
            headers = {**self.__headers, **headers}
        else:
            headers = self.__headers
        # Совмещаем параметры
        if params is not None:
            params = {**self.__params, **params}
        else:
            params = self.__params
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.__timeout)
            ) as session:
                # Получаем метод HTTP
                http_method = getattr(session, method.lower())
                # Пытаемся выполнить запрос, повторяя в случае ошибки.
                try:
                    async with http_method(
                        url=self.full_path(path),
                        headers=headers,
                        params=params,
                        data=data,
                        json=json,
                    ) as res:
                        return await self.__get_simple_response(res)
                except (aiohttp.ClientConnectorError, aiohttp.ClientError, aiohttp.ConnectionTimeoutError) as e:
                    logging.error(f'{self.__class__.__name__} > error > {e}')
                    raise e
        except AttributeError as e:
            # Если метод не найден, выбрасываем исключение RequestMethodNotFoundException.
            logging.critical(f'{self.__class__.__name__} > method not found > {e}')
            raise RequestMethodNotFoundException(method)

    async def _make(
        self,
        path: str,
        method: Method,
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = True,
        key: str | None = None,
        redis: RedisClient | None = None,
        retry_on_429: bool = True,
        retry_on_429_timeout: float = 0.1,
    ) -> ResponseData:
        """
        Выполняет HTTP-запрос с заданными параметрами.
        - path: относительный путь до эндпойнта.
        - method: HTTP-метод.
        - data: Данные для отправки.
        - json: JSON-данные для отправки.
        - params: Параметры запроса.
        - headers: Заголовки запроса.
        - use_cache: использовать кэш.
        - key: Ключ по которому искать кэш без префикса приложения.
        - redis: Клиент Redis для кэширования если он не указан при __init__.
        - retry_on_429: повторять ли запрос если ответ 429
        - retry_on_429_timeout: время сна при запросе
        return: Объект ResponseData с данными ответа.

        Если ответ 429 и retry_on_429 попробует сделать еще 1 запрос через retry_on_429_timeout (сек)\
         при этом если получит 429 еще раз повтор не будет выполнен.
        """
        logging.debug(f'{self.__class__.__name__} > {method} -> {path}')

        # Попытка получить кэш
        if use_cache and key is not None:
            cached_data = await self.__cache(key=key, redis=redis)
            if cached_data is not None:
                return ResponseData(
                    url=self.full_path(path),
                    status=200,
                    headers={},
                    json=cached_data,
                )

        res = await self.__execute(
            path=path,
            method=method,
            data=data,
            json=json,
            params=params,
            headers=headers,
        )

        # Если ответ 429 и разрешен ретрай повторяем запрос
        if res.status == 429 and retry_on_429:
            await asyncio.sleep(retry_on_429_timeout)
            return await self._make(
                path=path,
                method=method,
                data=data,
                json=json,
                params=params,
                headers=headers,
                use_cache=use_cache,
                key=key,
                redis=redis,
                retry_on_429=False,
                retry_on_429_timeout=retry_on_429_timeout,
            )
        return res

    @staticmethod
    async def multi_call(*calls: Coroutine[Any, Any, Any]) -> tuple[ResponseData]:
        """Эксперементально! Для вызова нескольких запросов"""
        tasks: list[asyncio.Task[Any]] = []
        async with asyncio.TaskGroup() as tg:
            for coro in calls:
                task = tg.create_task(coro)
                tasks.append(task)
        return tuple([task.result() for task in tasks])

    @staticmethod
    async def __get_simple_response(
        response: aiohttp.ClientResponse,
    ) -> ResponseData:
        """
        Простой и более быстрый способ получения данных из ответа.
        Не сработает для ответов с нестандартными типами контента.
        """
        try:
            return ResponseData(
                url=str(response.url),
                status=response.status,
                headers=dict(response.headers),
                json=await response.json(),
            )
        except aiohttp.ContentTypeError as e:
            logging.critical(f'{HttpMakerMicroAsync.__name__} > content-type error: {e}')
            raise UnableToParse(str(response.url))

    async def get(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = True,
        key: str | None = None,
        redis: RedisClient | None = None,
        retry_on_429: bool = True,
        retry_on_429_timeout: float = 0.1,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='GET',
            data=data,
            json=json,
            params=params,
            headers=headers,
            use_cache=use_cache,
            key=key,
            redis=redis,
            retry_on_429=retry_on_429,
            retry_on_429_timeout=retry_on_429_timeout,
        )

    async def post(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = True,
        key: str | None = None,
        redis: RedisClient | None = None,
        retry_on_429: bool = True,
        retry_on_429_timeout: float = 0.1,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='POST',
            data=data,
            json=json,
            params=params,
            headers=headers,
            use_cache=use_cache,
            key=key,
            redis=redis,
            retry_on_429=retry_on_429,
            retry_on_429_timeout=retry_on_429_timeout,
        )

    async def put(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = True,
        key: str | None = None,
        redis: RedisClient | None = None,
        retry_on_429: bool = True,
        retry_on_429_timeout: float = 0.1,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='PUT',
            data=data,
            json=json,
            params=params,
            headers=headers,
            use_cache=use_cache,
            key=key,
            redis=redis,
            retry_on_429=retry_on_429,
            retry_on_429_timeout=retry_on_429_timeout,
        )

    async def delete(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = True,
        key: str | None = None,
        redis: RedisClient | None = None,
        retry_on_429: bool = True,
        retry_on_429_timeout: float = 0.1,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='DELETE',
            data=data,
            json=json,
            params=params,
            headers=headers,
            use_cache=use_cache,
            key=key,
            redis=redis,
            retry_on_429=retry_on_429,
            retry_on_429_timeout=retry_on_429_timeout,
        )

    async def patch(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = True,
        key: str | None = None,
        redis: RedisClient | None = None,
        retry_on_429: bool = True,
        retry_on_429_timeout: float = 0.1,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='PATCH',
            data=data,
            json=json,
            params=params,
            headers=headers,
            use_cache=use_cache,
            key=key,
            redis=redis,
            retry_on_429=retry_on_429,
            retry_on_429_timeout=retry_on_429_timeout,
        )

    async def head(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = True,
        key: str | None = None,
        redis: RedisClient | None = None,
        retry_on_429: bool = True,
        retry_on_429_timeout: float = 0.1,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='HEAD',
            data=data,
            json=json,
            params=params,
            headers=headers,
            use_cache=use_cache,
            key=key,
            redis=redis,
            retry_on_429=retry_on_429,
            retry_on_429_timeout=retry_on_429_timeout,
        )

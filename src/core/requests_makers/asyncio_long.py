import asyncio
import logging
from typing import Callable, Awaitable, Any

import aiohttp

from core.redis_client import RedisClient

from .asyncio_base_pre_class import HttpMakerAsyncBaseMiddle
from .asyncio_session import HttpMakerSessionControl
from .exceptions import OutOfTries
from .response import ResponseData, Method


logger = logging.getLogger(__name__)


class HttpMakerAsyncLong(HttpMakerAsyncBaseMiddle, HttpMakerSessionControl):
    """
    Асинхронный HTTP-клиент с улучшенной обработкой json ответа и контролем сессии.
    """
    def __init__(
        self,
        base_url: str = '',
        base_headers: None | dict = None,
        base_params: None | dict = None,
        tries_to_reconnect: int = 3,
        timeout_in_sec: int = 10,
        parse_method: Callable[[aiohttp.ClientResponse], Awaitable[ResponseData]] | None = None,
        redis_prefix: str | None = None,
        session: aiohttp.ClientSession | None = None,
        connector: aiohttp.BaseConnector | None = None,
        auto_create_session: bool = True,
    ):
        """
        Инициализация асинхронного HTTP-клиента.

        - base_url: Базовый URL для всех запросов.
        - base_headers: Базовые заголовки для всех запросов.
        - base_params: Базовые параметры для всех запросов.
        - tries_to_reconnect: Количество попыток переподключения в случае ошибки.
        - timeout_in_sec: Тайм-аут в секундах для каждого запроса.
        - parse_method: Метод парсинга ответа.
        """
        HttpMakerAsyncBaseMiddle.__init__(self,
            base_url=base_url,
            base_headers=base_headers,
            base_params=base_params,
            tries_to_reconnect=tries_to_reconnect,
            timeout_in_sec=timeout_in_sec,
            parse_method=parse_method,
            redis_prefix=redis_prefix
        )
        HttpMakerSessionControl.__init__(self,
            timeout_in_sec=timeout_in_sec,
            session=session,
            connector=connector,
            auto_create_session=auto_create_session,
        )

    async def __execute(
        self,
        path: str,
        method: Method,
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
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
        return: Объект ResponseData с данными ответа.
        """
        session = await self._ensure_session()
        http_method = self._extract_method(method, session)

        headers = self._full_haeders(headers)
        params = self._full_params(params)

        for _ in range(self._tries_to_reconnect):
            try:
                async with http_method(
                    url=self._full_path(path),
                    headers=headers,
                    params=params,
                    data=data,
                    json=json,
                    timeout=aiohttp.ClientTimeout(total=request_timeout or self._timeout)
                ) as res:
                    return await self._get_response_data(res)
            except aiohttp.ClientConnectorError as e:
                logging.error(f'{self.__class__.__name__} > Client connection error {e}')
                if try_wait_if_error:
                    await asyncio.sleep(10)
                    continue
                break
            except aiohttp.ConnectionTimeoutError as e:
                logging.error(f'{self.__class__.__name__} > Connection error: {e}')
                if try_wait_if_error:
                    await asyncio.sleep(10)
                    continue
                break
            except aiohttp.ClientError as e:
                logging.critical(f'{self.__class__.__name__} > Client error: {e}')
                if try_wait_if_error:
                    await asyncio.sleep(30)
                    continue
                break
        # Если все попытки исчерпаны, выбрасываем исключение OutOfTries.
        logging.critical(f'{self.__class__.__name__} > Tries out but no return')
        raise OutOfTries(path)

    async def _make(
        self,
        path: str = '',
        method: Method = 'GET',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        not_use_cache: bool = False,
        redis: RedisClient | None = None,
        key: str | None = None,
        request_timeout: float | None = None,
    ) -> ResponseData:
        """
        Выполняет HTTP-запрос с заданными параметрами.

        - url: URL для запроса.
        - method: HTTP-метод.
        - data: Данные для отправки.
        - json: JSON-данные для отправки.
        - params: Параметры запроса.
        - headers: Заголовки запроса.
        - try_wait_if_error: Подождать и попробовать снова при ошибке или вернуть ошибку.
        - not_use_cache: Не использовать кэш.
        - redis: Клиент Redis для кэширования.
        - key: Ключ для кэширования.
        return: Объект ResponseData с данными ответа.
        """
        logging.debug(f'{self.__class__.__name__} > make -> {self._full_path(path)}')

        if not not_use_cache \
        and redis is not None \
        and key is not None \
        and self._redis_prefix is not None:
            cached_data = await self.redis_cache(redis, key, self._redis_prefix)
            if cached_data is not None:
                return ResponseData(
                    url='cached',
                    status=200,
                    headers={},
                    json=cached_data,
                )

        return await self.__execute(
            path=path,
            method=method,
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout
        )

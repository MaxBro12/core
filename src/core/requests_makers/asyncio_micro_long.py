import asyncio
import logging
from typing import Any

import aiohttp

from core.redis_client import RedisClient

from .asyncio_micro_base import HttpMakerAsyncMicroBase
from .asyncio_session import HttpMakerSessionControl
from .response import ResponseData, Method


logger = logging.getLogger(__name__)


class HttpMakerMicroAsyncLong(HttpMakerAsyncMicroBase, HttpMakerSessionControl):
    """
    Асинхронный HTTP-клиент с долгоживущей сессией для микросервисной архитектуры.

    Отличие от HttpMakerMicroAsync:
    - aiohttp.ClientSession создаётся один раз и живёт всё время работы приложения.
    - Каждый инстанс имеет свою сессию,
      что позволяет разным сервисам ходить на разные IP/base_url независимо.
    - Сессия создаётся лениво при первом запросе (если event loop ещё не запущен
      на момент __init__) либо сразу, если loop уже есть.
    - Поддерживается `async with` для гарантированного закрытия.
    - Опциональный TCPConnector с лимитами для контроля количества соединений.

    Использование:
        auth_service = AuthService()  # один инстанс на всё приложение
        res = await auth_service.get('/users')
        await auth_service.close()   # при shutdown
    """

    def __init__(
        self,
        base_url: str,
        base_headers: None | dict = None,
        base_params: None | dict = None,
        timeout_in_sec: int = 10,
        redis_prefix: str | None = None,
        redis_client: RedisClient | None = None,
        session: aiohttp.ClientSession | None = None,
        connector: aiohttp.BaseConnector | None = None,
        auto_create_session: bool = True,
    ) -> None:
        """
        - base_url: Базовый URL всех запросов ("" недопустим).
        - base_headers: Базовые заголовки.
        - base_params: Базовые query-параметры.
        - timeout_in_sec: Таймаут по умолчанию.
        - redis_prefix: Префикс приложения в Redis.
        - redis_client: Клиент Redis по умолчанию.
        - session: Готовая сессия (если нужно передать снаружи).
        - connector: Коннектор для новой сессии (если session не передан).
        - auto_create_session: Создавать сессию сразу в __init__,
            если есть работающий event loop. Иначе — лениво при первом запросе.
        """
        HttpMakerAsyncMicroBase.__init__(
            self,
            base_url=base_url,
            base_headers=base_headers,
            base_params=base_params,
            timeout_in_sec=timeout_in_sec,
            redis_prefix=redis_prefix,
            redis_client=redis_client
        )
        HttpMakerSessionControl.__init__(
            self,
            timeout_in_sec=timeout_in_sec,
            session=session,
            connector=connector,
            auto_create_session=auto_create_session
        )

    async def __execute(
        self,
        path: str,
        method: Method,
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        request_timeout: float | None = None,
    ) -> ResponseData:
        session = await self._ensure_session()
        http_method = self._extract_method(method, session)

        headers = self._full_haeders(headers)
        params = self._full_params(params)

        try:
            async with http_method(
                url=self._full_path(path),
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=aiohttp.ClientTimeout(total=request_timeout or self._timeout)
            ) as res:
                return await self._get_simple_response(res)
        except (
            aiohttp.ClientConnectorError,
            aiohttp.ClientError,
            aiohttp.ConnectionTimeoutError,
        ) as e:
            logging.error(f"{self.__class__.__name__} > error > {e}")
            raise e

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
        request_timeout: float | None = None,
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
        - request_timeout: таймаут запроса в секундах
        return: Объект ResponseData с данными ответа.

        Если ответ 429 и retry_on_429 попробует сделать еще 1 запрос через retry_on_429_timeout (сек)\
         при этом если получит 429 еще раз повтор не будет выполнен.
        """
        logging.debug(f"{self.__class__.__name__} > {method} -> {path}")

        if key is None:
            key = path

        # Попытка получить кэш
        if use_cache:
            cached_data = await self._cache(key=key, redis=redis)
            if cached_data is not None:
                return ResponseData(
                    url=self._full_path(path),
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
            request_timeout=request_timeout,
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
                request_timeout=request_timeout,
            )
        return res

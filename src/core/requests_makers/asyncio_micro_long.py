import asyncio
import logging
from typing import Any, Coroutine, Self

import aiohttp

from core.redis_client import RedisClient

from .exceptions import (
    RequestMethodNotFoundException,
    UnableToParse,
    MicroServiceUrlUnknown,
)
from .response import ResponseData, Method
from .tools import prepare_params


logger = logging.getLogger(__name__)


class HttpMakerMicroAsyncLong:
    """
    Асинхронный HTTP-клиент с долгоживущей сессией для микросервисной архитектуры.

    Отличие от HttpMakerMicroAsync:
    - aiohttp.ClientSession создаётся один раз и живёт всё время работы приложения.
    - Каждый инстанс (AuthService, DBService, ...) имеет свою сессию,
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

    __base_url: str
    __headers: dict
    __params: dict
    __timeout: int
    __redis_prefix: str | None
    __redis_client: RedisClient | None

    # Настройки пула соединений (можно переопределить у потомков)
    _connector_limit: int = 100
    _connector_limit_per_host: int = 30
    _connector_ttl_dns_cache: int = 300
    _enable_cleanup_closed: bool = True

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
        if not base_url:
            raise MicroServiceUrlUnknown()

        self.__base_url = base_url.rstrip('/')
        self.__headers = base_headers or {}
        self.__params = base_params or {}
        self.__timeout = timeout_in_sec
        self.__redis_prefix = redis_prefix
        self.__redis_client = redis_client

        self._session: aiohttp.ClientSession | None = session
        self._owns_session: bool = session is None
        self._connector: aiohttp.BaseConnector | None = connector
        self._session_lock: asyncio.Lock | None = None

        if self._session is None and auto_create_session:
            # Пытаемся создать сразу, если loop уже есть.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop is not None:
                self._session = self._build_session()

    def _build_session(self) -> aiohttp.ClientSession:
        """Создаёт новую сессию с настроенным коннектором и таймаутом."""
        if self._connector is None:
            self._connector = aiohttp.TCPConnector(
                limit=self._connector_limit,
                limit_per_host=self._connector_limit_per_host,
                ttl_dns_cache=self._connector_ttl_dns_cache,
                enable_cleanup_closed=self._enable_cleanup_closed,
            )
        timeout = aiohttp.ClientTimeout(total=self.__timeout)
        return aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers=self.__headers or None,
        )

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ленивое создание сессии. Потокобезопасно в рамках loop."""
        if self._session is not None and not self._session.closed:
            return self._session

        if self._session_lock is None:
            self._session_lock = asyncio.Lock()

        async with self._session_lock:
            if self._session is None or self._session.closed:
                self._session = self._build_session()
            return self._session

    async def close(self) -> None:
        """Закрывает сессию и коннектор (если мы их владельцы)."""
        if self._session is not None and self._owns_session:
            if not self._session.closed:
                await self._session.close()
            self._session = None
        if self._connector is not None and self._owns_session:
            # Коннектор закроется вместе с сессией, но на всякий случай.
            if not self._connector.closed:
                await self._connector.close()
            self._connector = None

    async def __aenter__(self) -> Self:
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def full_path(self, path: str) -> str:
        return f"{self.__base_url}/{path.lstrip('/')}"

    async def __cache(self, key: str, redis: RedisClient | None) -> dict | None:
        redis_cl = redis or self.__redis_client
        if redis_cl and self.__redis_prefix:
            return await redis_cl.get_json(
                key=key,
                spec_app_prefix=self.__redis_prefix,
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
        request_timeout: float | None = None,
    ) -> ResponseData:
        if headers is not None:
            headers = {**self.__headers, **headers}
        else:
            headers = self.__headers

        if params is not None:
            params = {**self.__params, **params}
        else:
            params = self.__params
        params = prepare_params(dict(params))  # копия, чтобы не мутировать базовые

        session = await self._ensure_session()

        try:
            http_method = getattr(session, method.lower())
        except AttributeError as e:
            logging.critical(
                f"{self.__class__.__name__} > method not found > {e}"
            )
            raise RequestMethodNotFoundException(method)

        # Per-request timeout (если задан) — иначе используется timeout сессии.
        timeout = (
            aiohttp.ClientTimeout(total=request_timeout)
            if request_timeout is not None
            else aiohttp.helpers.sentinel  # noqa: F821 — не используется, см. ниже
        )

        kwargs: dict[str, Any] = dict(
            url=self.full_path(path),
            headers=headers,
            params=params,
            data=data,
            json=json,
        )
        if request_timeout is not None:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=request_timeout)

        try:
            async with http_method(**kwargs) as res:
                return await self.__get_simple_response(res)
        except (
            aiohttp.ClientConnectorError,
            aiohttp.ClientError,
            aiohttp.ConnectionTimeoutError,
        ) as e:
            logging.error(f"{self.__class__.__name__} > error > {e}")
            raise

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

    @staticmethod
    async def multi_call(*calls: Coroutine[Any, Any, Any]) -> tuple[ResponseData]:
        """Вызов нескольких запросов параллельно через TaskGroup."""
        tasks: list[asyncio.Task[Any]] = []
        async with asyncio.TaskGroup() as tg:
            for coro in calls:
                tasks.append(tg.create_task(coro))
        return tuple(task.result() for task in tasks)

    @staticmethod
    async def __get_simple_response(
        response: aiohttp.ClientResponse,
    ) -> ResponseData:
        """
        Простое преобразование aiohttp.ClientResponse в ResponseData.
        """
        try:
            return ResponseData(
                url=str(response.url),
                status=response.status,
                headers=dict(response.headers),
                json=await response.json(),
            )
        except aiohttp.ContentTypeError as e:
            logging.critical(
                f"{HttpMakerMicroAsyncLong.__name__} > content-type error: {e}"
            )
            raise UnableToParse(str(response.url))

    async def get(
        self,
        path: str = "",
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
        return await self._make(
            path=path, method="GET", data=data, json=json, params=params,
            headers=headers, use_cache=use_cache, key=key, redis=redis,
            retry_on_429=retry_on_429, retry_on_429_timeout=retry_on_429_timeout,
            request_timeout=request_timeout,
        )

    async def post(
        self,
        path: str = "",
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
        return await self._make(
            path=path, method="POST", data=data, json=json, params=params,
            headers=headers, use_cache=use_cache, key=key, redis=redis,
            retry_on_429=retry_on_429, retry_on_429_timeout=retry_on_429_timeout,
            request_timeout=request_timeout,
        )

    async def put(
        self,
        path: str = "",
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
        return await self._make(
            path=path, method="PUT", data=data, json=json, params=params,
            headers=headers, use_cache=use_cache, key=key, redis=redis,
            retry_on_429=retry_on_429, retry_on_429_timeout=retry_on_429_timeout,
            request_timeout=request_timeout,
        )

    async def delete(
        self,
        path: str = "",
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
        return await self._make(
            path=path, method="DELETE", data=data, json=json, params=params,
            headers=headers, use_cache=use_cache, key=key, redis=redis,
            retry_on_429=retry_on_429, retry_on_429_timeout=retry_on_429_timeout,
            request_timeout=request_timeout,
        )

    async def patch(
        self,
        path: str = "",
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
        return await self._make(
            path=path, method="PATCH", data=data, json=json, params=params,
            headers=headers, use_cache=use_cache, key=key, redis=redis,
            retry_on_429=retry_on_429, retry_on_429_timeout=retry_on_429_timeout,
            request_timeout=request_timeout,
        )

    async def head(
        self,
        path: str = "",
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
        return await self._make(
            path=path, method="HEAD", data=data, json=json, params=params,
            headers=headers, use_cache=use_cache, key=key, redis=redis,
            retry_on_429=retry_on_429, retry_on_429_timeout=retry_on_429_timeout,
            request_timeout=request_timeout,
        )

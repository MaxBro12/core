from core.redis_client import RedisClient

from .asyncio_base import HttpMakerAsyncBase
from .exceptions import MicroServiceUrlUnknown
from .response import ResponseData, Method


class HttpMakerAsyncMicroBase(HttpMakerAsyncBase):
    """
    Базовый класс для асинхронных микрсервисных HttpMaker
    """

    _redis_prefix: str | None
    _redis_client: RedisClient | None

    def __init__(
        self,
        base_url: str = '',
        base_headers: None | dict = None,
        base_params: None | dict = None,
        timeout_in_sec: int = 10,
        redis_prefix: str | None = None,
        redis_client: RedisClient | None = None,
    ):
        if not base_url:
            raise MicroServiceUrlUnknown()

        super().__init__(
            base_url=base_url,
            base_headers=base_headers,
            base_params=base_params,
            timeout_in_sec=timeout_in_sec
        )

        self._redis_prefix = redis_prefix
        self._redis_client = redis_client

    def _full_path(self, path: str) -> str:
        """Возвращает полный путь для запроса, объединяя базовый URL и переданный путь.
        - path - Путь для запроса.
        return: Полный путь."""
        return f"{self._base_url}/{path.lstrip('/')}"

    async def _cache(self, key: str, redis: RedisClient | None) -> dict | None:
        """
        Возвращает кэш от редиса при наличии клиента redis (тут или через __init__)
        """
        redis_cl = redis or self._redis_client
        if redis_cl and self._redis_prefix:
            return await redis_cl.get_json(
                key=key,
                spec_app_prefix=self._redis_prefix,
            )
        return None

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
    ):
        raise NotImplementedError("Наследуемый класс должен реализовать этот метод")

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

    async def options(
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
            path=path, method="OPTIONS", data=data, json=json, params=params,
            headers=headers, use_cache=use_cache, key=key, redis=redis,
            retry_on_429=retry_on_429, retry_on_429_timeout=retry_on_429_timeout,
            request_timeout=request_timeout,
        )

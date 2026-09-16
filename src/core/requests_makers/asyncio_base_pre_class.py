import logging
from typing import Callable, Awaitable

import aiohttp

from core.redis_client import RedisClient

from .asyncio_base import HttpMakerAsyncBase
from .response import ResponseData, Method
from .exceptions import UnableToParse


class HttpMakerAsyncBaseMiddle(HttpMakerAsyncBase):
    """
    Класс прослойка между базой и HttpMakerAsync с доп методами
    """

    _tries_to_reconnect: int
    _parse_method: Callable
    _redis_prefix: str | None

    def __init__(
        self,
        base_url: str = '',
        base_headers: None | dict = None,
        base_params: None | dict = None,
        tries_to_reconnect: int = 3,
        timeout_in_sec: int = 10,
        parse_method: Callable[[aiohttp.ClientResponse], Awaitable[ResponseData]] | None = None,
        redis_prefix: str | None = None,
    ):
        super().__init__(base_url, base_headers, base_params, timeout_in_sec)

        if parse_method is None: # Если не передан метод парсинга, используем простой метод
            parse_method = self._get_simple_response

        self._parse_method = parse_method
        self._redis_prefix = redis_prefix
        self._tries_to_reconnect = tries_to_reconnect

    @staticmethod
    async def redis_cache(redis: RedisClient, key: str, spec_app_prefix: str) -> dict | None:
        """
        Получает данные из кэша Redis по ключу и префиксу приложения.

        - redis: Клиент Redis.
        - key: Ключ для поиска в кэше.
        - spec_app_prefix: Префикс приложения.
        return: Данные из кэша или None, если данные не найдены.
        """
        return await redis.get_json(
            key=key,
            spec_app_prefix=spec_app_prefix
        )

    @staticmethod
    async def _get_response_by_content_type(
        response: aiohttp.ClientResponse,
    ) -> ResponseData:
        """
        Получает данные из ответа на основе типа контента.
        """
        content_type = 'empty'
        # Получаем тип контента (проверяем оба варианта регистра)
        try:
            content_type = (
                response.headers.get('Content-Type') or
                {name.lower(): val for name, val in response.headers}.get('content-type')
            )
        except ValueError:
            content_type = None

        if not content_type:
            logging.warning(f'{HttpMakerAsyncBaseMiddle.__name__} > no content-type header, set empty')
            content_type = 'empty'

        try:
            match content_type.split(';')[0].strip().lower():
                case 'application/json' | 'text/html':
                    data = await response.json(content_type=None if 'html' in content_type else 'json')
                    if type(data) is not dict:
                        data = {'data': data}
                case 'empty': # Попытка распарсить ответ если поля контента нет
                    data = await response.json(content_type='json')
                case _:
                    logging.warning(f'{HttpMakerAsyncBaseMiddle.__name__} > unreadable content type: {content_type}')
                    raise UnableToParse(str(response.url))
            return ResponseData(
                url=str(response.url),
                status=response.status,
                headers=dict(response.headers),
                json=data,
            )
        except aiohttp.ContentTypeError as e:
            logging.error(e)
            raise UnableToParse(str(response.url))

    async def _get_response_data(
        self,
        response: aiohttp.ClientResponse,
    ) -> ResponseData:
        return await self._parse_method(response)

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
        raise NotImplementedError("Наследуемый класс должен реализовать этот метод")

    async def get(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='GET',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout,
        )

    async def post(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='POST',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout,
        )

    async def put(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='PUT',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout,
        )

    async def delete(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='DELETE',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout,
        )

    async def patch(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='PATCH',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout,
        )

    async def head(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='HEAD',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout,
        )

    async def options(
        self,
        path: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
        request_timeout: float | None = None,
    ) -> ResponseData:
        return await self._make(
            path=path,
            method='OPTIONS',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
            request_timeout=request_timeout,
        )

import asyncio
import aiohttp

from .requests_dataclasses import ResponseData, Method
from .makers_cache import CacheMaker
from ..debug import create_log
from .makers_single import Singleton


class HttpMakerAsync(Singleton):
    def __init__(
        self,
        base_url: str = '',
        headers: None | dict = None,
        make_cache: bool = True,
        cache_class: CacheMaker | None = None,
        tries_to_reconnect: int = 3,
    ):
        if headers is None:
            headers = dict()
        self._base_url = base_url if base_url.endswith('/') else f'{base_url}/'
        self._headers = headers
        self._tries_to_reconnect = tries_to_reconnect
        self.make_cache = make_cache
        self.cache = cache_class

    def get_full_path(self, url) -> str:
        return f'{self._base_url}{url if not url.startswith('/') else url[1:]}'

    async def __execute(
        self,
        url: str,
        method: Method,
        data: dict | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData | None:
        create_log(
            f'{self.__class__.__name__} {method} -> {url}',
            'debug'
        )
        res = None
        tries = 0
        while tries <= self._tries_to_reconnect and try_wait_if_error:
            try:
                async with aiohttp.ClientSession() as session:
                    http_method = getattr(session, method.lower())
                    if headers is None:
                        headers = {}
                    headers.update(self._headers)
                    async with http_method(url=self.get_full_path(url), headers=headers, data=data, json=json, params=params) as res:
                        return await self.__get_response_data(res)
            except aiohttp.ClientConnectorError as e:
                create_log(e, 'error')
                tries += 1
                await asyncio.sleep(10)
            except aiohttp.ConnectionTimeoutError as e:
                create_log(f'{self.__class__.__name__} > Connection error:', 'error')
                tries += 1
                if res is not None:
                    create_log(await self.__get_response_data(res), 'error')
                create_log(e, 'error')
                await asyncio.sleep(20)
            except aiohttp.ClientError as e:
                tries += 1
                create_log(f'{self.__class__.__name__} > Client error:', 'crit')
                if res is not None:
                    create_log(await self.__get_response_data(res), 'error')
                create_log(e, 'error')
                await asyncio.sleep(60)
            except AttributeError as e:
                create_log(f'{self.__class__.__name__} > Uncatched error:', 'crit')
                create_log(e, 'crit')
                return None

    async def _make(
        self,
        url: str,
        method: Method,
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_only_cache: bool = False,
        try_wait_if_error: bool = True,
    ) -> ResponseData | None:
        create_log(f'{self.__class__.__name__} > make -> {self.get_full_path(url)}', 'debug')
        if self.cache is not None:
            # ! Пытаемся получить кэш по url
            cache_data = self.cache.get(self.get_full_path(url))
            if cache_data is not None:
                # ? Если возвращать только кэш или выполняется условие кэша
                if try_only_cache or self.cache.condition(cache_data):
                    create_log(f'Get cache: {url}', 'debug')
                    return cache_data

        res = await self.__execute(
            url=url,
            method=method,
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
        )

        if self.cache is not None and res is not None:
            # ! Сохраняем кэш
            if self.make_cache:
                self.cache.put(res)
        return res

    @staticmethod
    async def __get_response_data(
        response: aiohttp.ClientResponse,
    ) -> ResponseData | None:
        # Получаем тип контента (проверяем оба варианта регистра)
        content_type = (
            response.headers.get('Content-Type') or
            {name.lower(): val for name, val in response.headers}.get('content-type')
        )
        if not content_type:
            create_log(f"Cannot get content-type: {' '.join(response.headers)}", 'debug')
            return None

        try:
            match content_type.split(';')[0].strip().lower():
                case 'application/json' | 'text/html':
                    data = await response.json(content_type=None if 'html' in content_type else 'json')
                    data = {'data': data} if not isinstance(data, dict) else data
                case _:
                    create_log(f'Unreadable content type: {content_type}', 'warning')
                    return None
            return ResponseData(
                url=str(response.url),
                status=response.status,
                headers=response.headers,
                json=data,
            )
        except aiohttp.ContentTypeError as e:
            create_log(e, 'error')
            return None

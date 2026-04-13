import asyncio
import logging
from typing import Callable, Awaitable

import aiohttp

from core.redis_client import RedisClient

from .exceptions import OutOfTries, RequestMethodNotFoundException, UnableToParse
from .response import ResponseData, Method


class HttpMakerAsync:
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
        parse_method: Callable[[aiohttp.ClientResponse], Awaitable[ResponseData]] | None = None
    ):
        """
        Инициализация асинхронного HTTP-клиента.

        :param base_url: Базовый URL для всех запросов.
        :param base_headers: Базовые заголовки для всех запросов.
        :param base_params: Базовые параметры для всех запросов.
        :param tries_to_reconnect: Количество попыток переподключения в случае ошибки.
        :param timeout_in_sec: Тайм-аут в секундах для каждого запроса.
        :param parse_method: Метод парсинга ответа.
        """
        self.__base_url = base_url

        if base_headers is None:
            base_headers = {}
        self.__headers = base_headers   # это должен быть словарь

        if base_params is None:
            base_params = {}
        self.__params = base_params    # это должен быть словарь

        self.__tries_to_reconnect = tries_to_reconnect
        self.__timeout = timeout_in_sec

        if parse_method is None: # Если не передан метод парсинга, используем простой метод
            parse_method = self._get_simple_response
        self.__parse_method = parse_method

    def full_path(self, path: str) -> str:
        """
        Возвращает полный путь для запроса, объединяя базовый URL и переданный путь.

        :param path: Путь для запроса.
        :return: Полный путь.
        """
        if path == '':
            return self.__base_url
        return f'{self.__base_url}/{path if not path.startswith('/') else path[1:]}'

    @staticmethod
    async def redis_cache(redis: RedisClient, key: str, spec_app_prefix: str) -> dict | None:
        """
        Получает данные из кэша Redis по ключу и префиксу приложения.

        :param redis: Клиент Redis.
        :param key: Ключ для поиска в кэше.
        :param spec_app_prefix: Префикс приложения.
        :return: Данные из кэша или None, если данные не найдены.
        """
        return await redis.get_json(
            key=key,
            spec_app_prefix=spec_app_prefix
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
    ) -> ResponseData:
        """
        Выполняет HTTP-запрос с заданными параметрами.

        :param path: Путь для запроса.
        :param method: HTTP-метод.
        :param data: Данные для отправки.
        :param json: JSON-данные для отправки.
        :param params: Параметры запроса.
        :param headers: Заголовки запроса.
        :param try_wait_if_error: Флаг, указывающий на необходимость ожидания перед повторной попыткой.
        :return: Объект ResponseData с данными ответа.
        """
        logging.debug(f'{self.__class__.__name__} {method} -> {path} ? {params}')
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
                for _ in range(self.__tries_to_reconnect):
                    try:
                        async with http_method(
                            url=self.full_path(path) if not path.startswith('http') else path,
                            headers=headers,
                            params=params,
                            data=data,
                            json=json,
                        ) as res:
                            return await self.__get_response_data(res)
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
        except AttributeError as e:
            # Если метод не найден, выбрасываем исключение RequestMethodNotFoundException.
            logging.critical(f'{self.__class__.__name__} > Uncaught error: {e}')
            raise RequestMethodNotFoundException(method)

    async def _make(
        self,
        url: str = '',
        method: Method = 'GET',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        """
        Выполняет HTTP-запрос с заданными параметрами.

        :param url: URL для запроса.
        :param method: HTTP-метод.
        :param data: Данные для отправки.
        :param json: JSON-данные для отправки.
        :param params: Параметры запроса.
        :param headers: Заголовки запроса.
        :param try_wait_if_error: Подождать и попробовать снова при ошибке или вернуть ошибку.
        :return: Объект ResponseData с данными ответа.
        """
        logging.debug(f'{self.__class__.__name__} > make -> {self.full_path(url)}')

        # В стандартном HttpMaker тут работа с кэшем
        # Для упрощения кода и тк эта логика в проекте не используется она была удалена

        return await self.__execute(
            path=url,
            method=method,
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error,
        )
        # Тут должна быть логика с сохранением в кэш, но она убрана для упрощения

    @staticmethod
    async def _get_simple_response(
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
            logging.critical(f'{HttpMakerAsync.__name__} > content-type error: {e}')
            raise UnableToParse(str(response.url))

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
            logging.warning(f'{HttpMakerAsync.__name__} > no content-type header, set empty')
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
                    logging.warning(f'{HttpMakerAsync.__name__} > unreadable content type: {content_type}')
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

    async def __get_response_data(
        self,
        response: aiohttp.ClientResponse,
    ) -> ResponseData:
        return await self.__parse_method(response)

    async def get(
        self,
        url: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        return await self._make(
            url=url,
            method='GET',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error
        )

    async def post(
        self,
        url: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        return await self._make(
            url=url,
            method='POST',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error
        )

    async def put(
        self,
        url: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        return await self._make(
            url=url,
            method='PUT',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error
        )

    async def delete(
        self,
        url: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        return await self._make(
            url=url,
            method='DELETE',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error
        )

    async def patch(
        self,
        url: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        return await self._make(
            url=url,
            method='PATCH',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error
        )

    async def head(
        self,
        url: str = '',
        data: dict | str | None = None,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        try_wait_if_error: bool = True,
    ) -> ResponseData:
        return await self._make(
            url=url,
            method='HEAD',
            data=data,
            json=json,
            params=params,
            headers=headers,
            try_wait_if_error=try_wait_if_error
        )

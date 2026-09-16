import asyncio
from collections.abc import Coroutine
from typing import Callable, Any
import logging

import aiohttp

from .response import ResponseData, Method
from .exceptions import UnableToParse, RequestMethodNotFoundException


logger = logging.getLogger(__name__)


class HttpMakerAsyncBase:
    """
    Базовый класс для асинхронного HTTPMakera.
    """

    _base_url: str
    _headers: dict
    _params: dict
    _timeout: int

    def __init__(
        self,
        base_url: str = '',
        base_headers: None | dict = None,
        base_params: None | dict = None,
        timeout_in_sec: int = 10,
    ):
        """
        Инициализация базового класса:
        - base_url: базовый url например http://127.0.0.1:8000
        - base_headers: заголовки которые будут отправляться с каждым запросом (например api-ключи)
        - base_params: редко используется особенно для старых api где api-ключ в параметрах
        - timeout_in_sec: базовый таймоут сессии
        """
        self._base_url = base_url.rstrip('/')
        self._headers = base_headers or {}
        self._params = base_params or {}

        self._timeout = timeout_in_sec

    def _full_path(self, path: str) -> str:
        """
        Возвращает полный путь для запроса, объединяя базовый URL и переданный путь.
        - path - Путь для запроса.
        return: Полный путь.
        """
        if path == '':
            return self._base_url
        return f'{self._base_url}/{path.lstrip('/')}'

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
            logging.critical(f'{HttpMakerAsyncBase.__name__} > content-type error: {e}')
            raise UnableToParse(str(response.url))

    def _full_haeders(self, adt_headers: dict | None) -> dict:
        """Совмещает заголовки с базовыми"""
        if adt_headers:
            return {**self._headers, **adt_headers}
        return self._headers

    def _full_params(self, adt_params: dict | None) -> dict:
        """Совмещает параметры с базовыми"""
        if adt_params:
            return self._prepare_params({**self._params, **adt_params})
        return self._prepare_params(self._params)

    @staticmethod
    def _prepare_params(params: dict[str, Any]) -> dict[str, Any]:
        """Подготовка параметров к адекватной передачи в httpx"""
        params = dict(params)
        for k, v in params.items():
            if type(v) is bool:
                params[k] = "true" if v else "false"
        return params

    @staticmethod
    def _extract_method(method: Method, session: aiohttp.ClientSession) -> Callable:
        """Возвращает метод сессии"""
        try:
            session_methods = {
                'GET': session.get,
                'POST': session.post,
                'PUT': session.put,
                'PATCH': session.patch,
                'DELETE': session.delete,
                'HEAD': session.head,
                'OPTIONS': session.options,
            }
            return session_methods[method.upper()]
        except KeyError:
            logging.critical(
                f"{HttpMakerAsyncBase.__name__} > method not found > {method}"
            )
            raise RequestMethodNotFoundException(method)

    @staticmethod
    async def multi_call(*calls: Coroutine[Any, Any, Any]) -> tuple[ResponseData]:
        """Вызов нескольких запросов параллельно через TaskGroup."""
        tasks: list[asyncio.Task[Any]] = []
        async with asyncio.TaskGroup() as tg:
            for coro in calls:
                tasks.append(tg.create_task(coro))
        return tuple(task.result() for task in tasks)

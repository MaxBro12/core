import asyncio

from typing import Self

import aiohttp


class HttpMakerSessionControl:
    """
    Утилитарный класс для контроля долгоживущих сессий
    """
    _timeout: int

    # пул соединений
    _connector_limit: int = 100
    _connector_limit_per_host: int = 30
    _connector_ttl_dns_cache: int = 300
    _enable_cleanup_closed: bool = True

    def __init__(self,
        timeout_in_sec: int = 10,
        session: aiohttp.ClientSession | None = None,
        connector: aiohttp.BaseConnector | None = None,
        auto_create_session: bool = True,
    ) -> None:
        self._timeout = timeout_in_sec

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
                #enable_cleanup_closed=self._enable_cleanup_closed,
            )
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        return aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
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

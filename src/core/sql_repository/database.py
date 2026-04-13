from sqlalchemy.ext.asyncio import AsyncSession


class DataBaseRepo:
    """Класс управляет базой данных и подключенными к ней репозиториями"""
    def __init__(self, session: AsyncSession) -> None:
        self.__session = session

    async def commit(self):
        await self.__session.commit()

    async def flush(self):
        await self.__session.flush()

    async def rollback(self):
        await self.__session.rollback()

    async def close(self):
        await self.__session.close()

    @property
    def session(self) -> AsyncSession:
        return self.__session

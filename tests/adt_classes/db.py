from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from src.sql_repository import Repository, DataBaseRepo


class Base(DeclarativeBase):
    pass


class SpecModel(Base):
    __tablename__ = 'test'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(default='default')


class SpecRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(SpecModel, session=session)

    async def by_id(self, id: int) -> SpecModel | None:
        return await self.get(f"{self.table_name}.id={id}")


class SpecDataBase(DataBaseRepo):
    def __init__(self, session: AsyncSession):
        self.test = SpecRepository(session=session)
        super().__init__(session=session)

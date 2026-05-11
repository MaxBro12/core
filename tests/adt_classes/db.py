from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.sql_repository import Repository, RepositoryObj, DataBaseRepo


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
        return await self.get(f"{self.table}.id={id}")


class SpecRepositoryObj(RepositoryObj):
    def __init__(self, session: AsyncSession):
        super().__init__(SpecModel, session=session)

    async def by_id(self, id: int) -> SpecModel | None:
        return await self.get(SpecModel.id == id)


class SpecDataBase(DataBaseRepo):
    def __init__(self, session: AsyncSession):
        self.test = SpecRepository(session=session)
        self.test_obj = SpecRepositoryObj(session=session)
        super().__init__(session=session)


async def create_test_db(session: AsyncSession):
    session.add_all([
        SpecModel(name='t1'),
        SpecModel(name='t2'),
        SpecModel(name='t3'),
        SpecModel(name='t4'),
        SpecModel(name='t5'),
        SpecModel(name='t6'),
        SpecModel(name='t7'),
        SpecModel(name='t8'),
        SpecModel(name='t9'),
        SpecModel(name='t10')
    ])
    await session.commit()

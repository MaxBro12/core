from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.sql_repository import Repository, RepositoryObj, DataBaseRepo


class Base(DeclarativeBase):
    pass


class SpecModel(Base):
    __tablename__ = 'test'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(default='default')


class AnotherModel(Base):
    __tablename__ = 'another_test'

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
        SpecModel(id=1, name='t1'),
        SpecModel(id=2, name='t2'),
        SpecModel(id=3, name='t3'),
        SpecModel(id=4, name='t4'),
        SpecModel(id=5, name='t5'),
        SpecModel(id=6, name='t6'),
        SpecModel(id=7, name='t7'),
        SpecModel(id=8, name='t8'),
        SpecModel(id=9, name='t9'),
        SpecModel(id=10, name='t10'),

        AnotherModel(id=11, name='t11'),
        AnotherModel(id=12, name='t12'),
    ])
    await session.commit()

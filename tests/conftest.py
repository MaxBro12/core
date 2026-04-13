import pytest
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from .adt_classes.db import SpecDataBase, SpecModel, Base
from .adt_classes.fast_api_app import app


engine = create_async_engine(
    url='sqlite+aiosqlite:///:memory:',
    pool_pre_ping=True,
    echo=True
)
test_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_test_session() -> AsyncGenerator[AsyncSession]:
    async with test_session() as session:
        yield session


@pytest.fixture(scope='function')
async def test_db() -> AsyncGenerator[SpecDataBase]:
    async with test_session() as session:
        yield SpecDataBase(session=session)



@pytest.fixture(scope='session', autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        async with test_session() as session:
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


@pytest.fixture(scope='module')
async def test_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

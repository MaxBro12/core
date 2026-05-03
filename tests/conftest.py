import pytest
import time
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import redis.asyncio as redis_a
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from .adt_classes.db import SpecDataBase, SpecModel, Base
from .adt_classes.fast_api_app import app

from src.core.redis_client import RedisClient


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


@pytest.fixture
def mock_redis():
    """Создает мок для Redis клиента"""
    mock = AsyncMock(spec=redis_a.Redis)
    mock_data = {}
    mock_expires = {}

    async def mock_get(key):
        return mock_data.get(key)

    async def mock_set(key, value, ex):
        mock_data[key] = value
        mock_expires[key] = time.time() + ex
        return None

    async def mock_delete(key):
        mock_data.pop(key, None)
        mock_expires.pop(key, None)
        return None

    # Настройка поведения по умолчанию
    mock.get.side_effect = mock_get
    mock.set.side_effect = mock_set
    mock.delete.side_effect = mock_delete
    return mock


@pytest.fixture
def mock_redis_pool():
    """Создает мок для пула соединений"""
    return MagicMock(spec=redis_a.ConnectionPool)


@pytest.fixture
async def redis_client(mock_redis, mock_redis_pool):
    """Создает экземпляр RedisClient с замоканным Redis"""
    with patch('redis.asyncio.Redis', return_value=mock_redis):
        client = RedisClient(mock_redis_pool, "test_prefix", expire=3600)
        # Заменяем приватный клиент на наш мок
        client._RedisClient__client = mock_redis
        return client

import pytest

from src.core.sql_repository import GetMultiple, SessionNotFound

from tests.adt_classes.db import SpecDataBase, SpecModel, create_test_db


async def test_get(test_db: SpecDataBase):
    data = await test_db.test.get(f'{SpecModel.__tablename__}.id=1')
    assert data is not None
    assert data.name == 't1'


async def test_get_multiple(test_db: SpecDataBase):
    try:
        data = await test_db.test.get(f'{SpecModel.__tablename__}.id IN (1, 2)')
        assert False
    except GetMultiple:
        assert True


async def test_get_not_exist(test_db: SpecDataBase):
    data = await test_db.test.get(f'{SpecModel.__tablename__}.id=11')
    assert data is None


async def test_some(test_db: SpecDataBase):
    data = await test_db.test.some(f'{SpecModel.__tablename__}.id IN (1, 2)')
    assert data is not None
    assert len(data) == 2
    assert data[0].name == 't1'
    assert data[1].name == 't2'


async def test_all(test_db: SpecDataBase):
    data = await test_db.test.all()
    assert data is not None
    assert len(data) == 10
    assert data[0].name == 't1'
    assert data[1].name == 't2'
    assert data[5].name == 't6'
    assert data[9].name == 't10'


async def test_add(test_db: SpecDataBase):
    assert await test_db.test.add(SpecModel(name='t11')) is True
    await test_db.flush()
    data = await test_db.test.get(f'{SpecModel.__tablename__}.id=11')
    assert data is not None
    assert data.name == 't11'


async def test_add_many(test_db: SpecDataBase):
    assert await test_db.test.add_many([SpecModel(id=1001, name='tta1'), SpecModel(id=1002, name='tta2')]) is True
    await test_db.flush()
    data = await test_db.test.some(f'{SpecModel.__tablename__}.id IN (1001, 1002)')
    assert data is not None
    assert len(data) == 2
    assert data[0].name == 'tta1'
    assert data[1].name == 'tta2'


async def test_delete(test_db: SpecDataBase):
    obj = await test_db.test.get(f'{SpecModel.__tablename__}.id=1')
    assert obj is not None
    assert await test_db.test.delete(obj) is True


async def test_exists(test_db: SpecDataBase):
    assert await test_db.test._exists(f'{SpecModel.__tablename__}.id=1') is True
    assert await test_db.test._exists(f'{SpecModel.__tablename__}.id=2') is True
    assert await test_db.test._exists(f'{SpecModel.__tablename__}.id=100003') is False


async def test_count(test_db: SpecDataBase):
    assert await test_db.test.count() == 10


async def test_wrong_session():
    with pytest.raises(SessionNotFound):
        a = SpecDataBase(session=None)
        await a.test.get(f'{SpecModel.__tablename__}.id=1')


async def test_clear_table(test_db: SpecDataBase):
    await test_db.test.clear_table()
    await test_db.flush()
    assert await test_db.test.count() == 0

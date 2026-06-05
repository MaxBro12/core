import pytest

from sqlalchemy import and_
from src.core.sql_repository import GetMultiple, SessionNotFound

from tests.adt_classes.db import SpecDataBase, SpecModel, create_test_db


async def test_get(test_db: SpecDataBase):
    data = await test_db.test_obj.by_id(1)
    assert data is not None
    assert data.name == 't1'


async def test_get_multiple(test_db: SpecDataBase):
    try:
        data = await test_db.test_obj.get(SpecModel.id.in_([1, 2]))
        assert False
    except GetMultiple:
        assert True


async def test_get_not_exist(test_db: SpecDataBase):
    data = await test_db.test_obj.get(SpecModel.id == 11)
    assert data is None


async def test_some(test_db: SpecDataBase):
    data = await test_db.test_obj.some(SpecModel.id.in_([1, 2]))
    assert data is not None
    assert len(data) == 2
    assert data[0].name == 't1'
    assert data[1].name == 't2'


async def test_all(test_db: SpecDataBase):
    data = await test_db.test_obj.all()
    assert data is not None
    assert len(data) == 10
    assert data[0].name == 't1'
    assert data[1].name == 't2'
    assert data[5].name == 't6'
    assert data[9].name == 't10'


async def test_add(test_db: SpecDataBase):
    obj = SpecModel(name='t11')
    assert await test_db.test_obj._add(obj) is obj
    await test_db.commit()
    data = await test_db.test_obj.get(SpecModel.id == 11)
    assert data is not None
    assert data.name == 't11'


async def test_add_many(test_db: SpecDataBase):
    objs = [SpecModel(name='t12'), SpecModel(name='t13')]
    assert len(await test_db.test_obj._add_many(objs)) == 2
    await test_db.commit()
    data = await test_db.test_obj.some(SpecModel.id.in_([12, 13]))
    assert data is not None
    assert len(data) == 2
    assert data[0].name == 't12'
    assert data[1].name == 't13'


async def test_delete(test_db: SpecDataBase):
    obj = await test_db.test_obj.get(SpecModel.id == 13)
    assert obj is not None
    assert await test_db.test_obj._delete_obj(obj) is True


async def test_exists(test_db: SpecDataBase):
    assert await test_db.test_obj._exists(SpecModel.id == 1) is True
    assert await test_db.test_obj._exists(SpecModel.id == 11) is True
    assert await test_db.test_obj._exists(SpecModel.id == 12) is True


async def test_count(test_db: SpecDataBase):
    assert await test_db.test_obj.count() == 13


async def test_wrong_session():
    a = SpecDataBase(session=None)
    try:
        await a.test_obj.get(SpecModel.id == 1)
        assert False
    except SessionNotFound:
        assert True


async def test_delete_filter(test_db: SpecDataBase):
    assert await test_db.test_obj._delete(SpecModel.id.in_([1, 2, 3])) is True
    await test_db.commit()
    assert await test_db.test_obj.count() == 10


async def test_clear_table(test_db: SpecDataBase):
    await test_db.test_obj.clear_table()
    await test_db.commit()
    assert await test_db.test_obj.count() == 0
    await create_test_db(test_db.session)


async def test_selection(test_db: SpecDataBase):
    objs = await test_db.test_obj.all(select_columns=(SpecModel.name,))
    assert objs is not None
    assert len(objs) == 10
    assert len(objs[0]) == 1
    assert objs[0][0] == 't1'
    assert objs[1][0] == 't2'


async def test_multiple_select(test_db: SpecDataBase):
    objs = await test_db.test_obj.all(select_columns=(SpecModel.name, SpecModel.id))
    assert objs is not None
    assert len(objs) == 10
    assert objs[0][0] == 't1'
    assert objs[0][1] == 1
    assert objs[1][0] == 't2'
    assert objs[1][1] == 2

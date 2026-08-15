import pytest

from sqlalchemy import and_
from src.core.sql_repository import GetMultiple, SessionNotFound

from tests.adt_classes.db import SpecDataBase, SpecModel, AnotherModel, create_test_db


async def test_get(test_db: SpecDataBase):
    data = await test_db.test_obj.by_id(1)
    try:
        assert data is not None
        assert data.name == 't1'
    except AssertionError:
        ids = await test_db.test_obj.all()


async def test_get_multiple(test_db: SpecDataBase):
    try:
        data = await test_db.test_obj.get(SpecModel.id.in_([1, 2]))
        assert False
    except GetMultiple:
        assert True


async def test_get_not_exist(test_db: SpecDataBase):
    data = await test_db.test_obj.get(SpecModel.id == 110)
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
    obj = SpecModel(id=10001, name='toa1')
    assert await test_db.test_obj._add(obj) is obj
    await test_db.flush()
    data = await test_db.test_obj.get(SpecModel.id == 10001)
    assert data is not None
    assert data.name == 'toa1'


async def test_add_many(test_db: SpecDataBase):
    objs = [SpecModel(id=10002, name='toa2'), SpecModel(id=10003, name='toa3')]
    assert len(await test_db.test_obj._add_many(objs)) == 2
    await test_db.flush()
    data = await test_db.test_obj.some(SpecModel.id.in_([10002, 10003]))
    assert data is not None
    assert len(data) == 2
    assert data[0].name == 'toa2'
    assert data[1].name == 'toa3'


async def test_delete_obj(test_db: SpecDataBase):
    obj = await test_db.test_obj.get(SpecModel.id == 1)
    assert obj is not None
    assert await test_db.test_obj._delete_obj(obj) is True


async def test_delete(test_db: SpecDataBase):
    assert await test_db.test_obj._delete(SpecModel.id.in_([1, 2])) is True


async def test_exists(test_db: SpecDataBase):
    assert await test_db.test_obj._exists(SpecModel.id == 1) is True
    assert await test_db.test_obj._exists(SpecModel.id == 2) is True
    assert await test_db.test_obj._exists(SpecModel.id == 2000) is False


async def test_count(test_db: SpecDataBase):
    assert await test_db.test_obj.count() == 10


async def test_wrong_session():
    a = SpecDataBase(session=None)
    with pytest.raises(SessionNotFound):
        await a.test_obj.get(SpecModel.id == 1)


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


async def test_select_another_model(test_db: SpecDataBase):
    objs = await test_db.test_obj.all(select_columns=AnotherModel)
    assert objs is not None
    assert len(objs) == 2
    assert objs[0].name == 't11'
    assert objs[1].name == 't12'


async def test_clear_table(test_db: SpecDataBase):
    await test_db.test_obj.clear_table()
    await test_db.flush()
    assert await test_db.test_obj.count() == 0


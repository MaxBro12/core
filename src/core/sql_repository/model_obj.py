from abc import ABC
from typing import Type, Any
import warnings

from sqlalchemy import text, select, delete, exists, func, ColumnElement
from sqlalchemy.orm import InstrumentedAttribute, DeclarativeBase, selectinload
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql._typing import _ColumnsClauseArgument
from sqlalchemy.ext.asyncio import AsyncSession

from .classes import T
from .exeptions import SessionNotFound, GetMultiple, TryGetMultiple


AddManyObjects = tuple[T, ...] | list[T]
ColumnsOrModels = Type[T] | _ColumnsClauseArgument[Any] | tuple[_ColumnsClauseArgument[Any], ...] | None


class RepositoryObj(ABC):
    """Улучшенная версия базового репозитория для работы с базой данных"""
    table: str

    def __init__(
        self,
        model: Type[T],
        session: AsyncSession,
        relationships: tuple[str, ...] | None = None,
    ):
        self.model = model
        self.table = model.__tablename__

        if relationships is not None:
            warnings.warn("relationships will be removed in 0.2.0")
        self.relationships = relationships

        self.session = session

    async def __get_object_from_db(
        self,
        select_columns: ColumnsOrModels = None,
        filter_: ColumnElement[bool] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        order_by_field: InstrumentedAttribute | str | None = None,
        load_relations: bool = True,
        loader_options: tuple[ExecutableOption, ...] | None = None,
    ) -> tuple[T | Any, ...]:
        """
        Метод выполняющий запрос к базе по фильтрам.
        - select_columns: колонки для выборки или None для выбора модели
        - filter_: фильтр для запроса
        - offset: смещение от начала выборки
        - limit: количество элементов в выборке
        - order_by_field: поле для сортировки
        - load_relations: загружать ли связанные объекты (будет заменено loader_options)
        - loader_options: опции для загрузки связанных объектов
        """
        # Парсим колонки
        if select_columns is not None:
            # Если передан tuple
            if isinstance(select_columns, tuple):
                query = select(*select_columns)
            else:
                # Если передана другая модель
                query = select(select_columns)
        else:
            # Если ничего нет считаем как модель
            query = select(self.model)

        # Старый метод
        if load_relations and self.relationships:
            warnings.warn(f'WARNING!!! {self.__class__.__name__} > load_relations > METHOD WILL BE DEPRECATED use loader_options instead', DeprecationWarning)
            for relationship in self.relationships:
                if hasattr(self.model, relationship):
                    query = query.options(selectinload(getattr(self.model, relationship)))

        # Применяем фильтры
        if filter_ is not None:
            query = query.filter(filter_)
        # Дополнительная загрузка
        if loader_options:
            query = query.options(*loader_options)
        # Применяем лимит
        if limit:
            query = query.limit(limit)
        # Отступ
        if offset:
            query = query.offset(offset)
        # Сортируем
        if order_by_field is not None:
            if type(order_by_field) is str:
                query = query.order_by(text(order_by_field))
            else:
                query = query.order_by(order_by_field)
        try:
            # Если передали tuple готовим ответ
            if select_columns is not None and isinstance(select_columns, tuple):
                return tuple((await self.session.execute(query)).all())
            # Если передали обычную модель
            return tuple((await self.session.execute(query)).scalars().all())
        except AttributeError:
            # Сессию не дали
            raise SessionNotFound()

    async def get(
        self,
        filter_: ColumnElement[bool],
        select_columns: ColumnsOrModels = None,
        load_relations: bool = True,
        loader_options: tuple[ExecutableOption, ...] | None = None,
    ) -> T | None:
        """
        Метод забирает из базы модель по фильтру,
        если в ответе будет несколько записей, вызовется исключение GetMultiple
        """
        if filter_ is None:
            # Предикт исключение как взять 1 модель и при этом без фильтра?
            raise TryGetMultiple(self.model)
        objs = await self.__get_object_from_db(
            select_columns=select_columns,
            filter_=filter_,
            load_relations=load_relations,
            loader_options=loader_options,
        )
        if len(objs) > 1:
            # Моделей больше 1 в методе где надо вернуть 1
            raise GetMultiple(self.model, len(objs))
        elif len(objs) == 0:
            # Объектов нету
            return None
        return objs[0]

    async def some(
        self,
        filter_: ColumnElement[bool] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        select_columns: ColumnsOrModels = None,
        order_by_field: InstrumentedAttribute | str | None = None,
        load_relations: bool = True,
        loader_options: tuple[ExecutableOption, ...] | None = None,
    ) -> tuple[T, ...]:
        """Метод забирает из базы несколько моделей по фильтрам с offset и limit"""
        return await self.__get_object_from_db(
            filter_=filter_,
            offset=offset,
            limit=limit,
            order_by_field=order_by_field,
            select_columns=select_columns,
            load_relations=load_relations,
            loader_options=loader_options,
        )

    async def _add(
        self,
        model: T,
        commit: bool = False,
    ) -> T:
        """
        Метод добавления в базу готовой модели
        """
        try:
            self.session.add(model)
            if commit:
                await self.session.commit()
            return model
        except AttributeError:
            raise SessionNotFound()

    async def _add_many(
        self,
        objs: AddManyObjects,
        commit: bool = False
    ) -> AddManyObjects:
        """
        Метод добавления в базу нескольких готовых моделей
        """
        try:
            self.session.add_all(objs)
            if commit:
                await self.session.commit()
            return objs
        except AttributeError:
            raise SessionNotFound()

    async def delete(self, obj: DeclarativeBase, commit: bool = False) -> bool:
        """
        Метод будет удален в 0.2.0.
        Метод удаления из базы модели.
        """
        warnings.warn(f'WARNING!!! {self.__class__.__name__} > delete > METHOD WILL BE DEPRECATED use _delete or _delete_obj instead', DeprecationWarning)
        try:
            await self.session.delete(obj)
            if commit:
                await self.session.commit()
            return True
        except AttributeError:
            raise SessionNotFound()

    async def _delete(self, filter_: ColumnElement[bool], spec_model: Type[T] | None = None, commit: bool = False) -> bool:
        """
        Метод удаления из базы модели по фильтру
        """
        try:
            await self.session.execute(delete(spec_model or self.model).where(filter_))
            if commit:
                await self.session.commit()
            return True
        except AttributeError:
            raise SessionNotFound()

    async def _delete_obj(self, obj: DeclarativeBase, commit: bool = False) -> bool:
        """
        Метод удаления из базы модели по объекту
        """
        try:
            await self.session.delete(obj)
            if commit:
                await self.session.commit()
            return True
        except AttributeError:
            raise SessionNotFound()

    async def all(
        self,
        skip: int | None = None,
        limit: int | None = None,
        select_columns: ColumnsOrModels = None,
        order_by_field: InstrumentedAttribute | str | None = None,
        load_relations: bool = True,
        loader_options: tuple[ExecutableOption, ...] | None = None,
    ) -> tuple[T, ...]:
        """
        Возвращает все сохраненные записи из базы
        """
        return await self.__get_object_from_db(
            offset=skip,
            limit=limit,
            order_by_field=order_by_field,
            select_columns=select_columns,
            load_relations=load_relations,
            loader_options=loader_options,
        )

    async def clear_table(self, commit: bool = False) -> bool:
        """
        ВНИМАНИЕ!!!
        Метот сотрет все записи из базы данных!
        """
        try:
            await self.session.execute(delete(self.model))
            if commit:
                await self.session.commit()
            return True
        except AttributeError:
            raise SessionNotFound()

    async def _exists(self, filter_: ColumnElement[bool], select_model: Type[T] | None = None) -> bool:
        """
        Оптимизированный метод для поиска записи в базе
        """
        try:
            model = select_model or self.model
            return bool(await self.session.scalar(select(exists().select_from(model).where(filter_))))
        except AttributeError:
            raise SessionNotFound()

    async def count(self, filter_: ColumnElement[bool] | None = None, select_model: Type[T] | None = None) -> int:
        """
        Количество записей в базе данных
        """
        try:
            model = select_model or self.model
            query = select(func.count()).select_from(model)
            if filter_ is not None:
                query.where(filter_)
            return int((await self.session.execute(
                query
            )).scalar() or 0)
        except AttributeError:
            raise SessionNotFound()

    async def _pagination(
        self,
        filter_: ColumnElement[bool] | None = None,
        skip: int | None = None,
        limit: int | None = None,
        select_columns: ColumnsOrModels = None,
        order_by_field: str | None = None,
        load_relations: bool = False,
        loader_options: tuple[ExecutableOption, ...] | None = None,
    ) -> tuple[T, ...]:
        """
        Оптимизированный метод для пагинации.
        Сейчас работает как some
        """
        return await self.some(
            filter_=filter_,
            offset=skip,
            limit=limit,
            order_by_field=order_by_field,
            select_columns=select_columns,
            load_relations=load_relations,
            loader_options=loader_options,
        )

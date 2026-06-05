# SQL_Repository

Это пакет - расширение для SQLAlchemy, реализующий паттерн Repository. Его цель - упростить работу с базой данных, предоставляя удобный интерфейс для выполнения CRUD операций.

## Установка

Для установки пакета вам потребуется библиотека SQLAlchemy версии 2.0.0 или выше:

```bash
pip install -r requirements.txt
pip install sqlalchemy>=2.0.0    # или напрямую
```

## Варианты ModelRepository

- `Repository` - ! ВАЖНО: с версии 0.2.0 будет удален ! базовый класс, его отличительная особенность - использование текстовых запросов
- `RepositoryObj` - Новый вариант репозитория, который использует ORM для выполнения запросов

## Использование Repository

Для использования Repository вам потребуется для начала создать модель базы данных:

```python
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
```

Теперь создаем класс и наследуем его от Repository:

```python
from sqlalchemy_ext_repo import Repository, RepositoryObj

class UserRepository(Repository):
    def __init__(self):
        super().__init__(model=User)
```

Теперь вы можете использовать стандартные методы Repository для модели:

- `all` - получить все записи
- `all_gen` - генератор всех записей
- `add` - добавить новую запись
- `add_many` - добавить несколько записей
- `delete` - удалить запись
- `clear_table` - очистить всю таблицу !очень опасный метод!
- `count` - получить количество записей в таблице

Так же есть методы для получения данных, их всех объединяет использование фильтра его мы пишем как в стандартом sql обычным текстом:

```python

user = await user_repo.get(_filter=f'{User.__tablename__}.id={user_id}' session=session)
```

- `get` - получить запись по фильтру, если записей будет больше одной вызовется исключение GetMultiple
- `some` - получить несколько записей по фильтру
- `pagination` - получаем данные по запросу ограничивая количество результатов

Такой подход не совсем удобен поэтому я рекомендую дописывать собственные методы для класса:


```python
    async def by_name(
        self,
        username: str,
        session: AsyncSession,
        load_relations: bool = False
    ) -> User | None:
        return await super().get(
            f"{self.table_name}.name='{username}'",
            session=session,
            load_relations=load_relations
        )

user = await user_repo.by_name(username='John', session=session)
```

Как видите так намного проще взаимодействовать с базой. Так же некоторые методы только при такой реализации и будут наботать, например `exists`:

```python
    async def exists(self, username: str, session: AsyncSession) -> bool:
        return await self._exists(f"{self.table_name}.name='{username}'", session=session)
```

Это необходимо так как мы не можем предсказать какое у вас поле в модели является первичным ключем.

## Использование RepositoryObj

Создаем класс репозитория, наследуя его от `RepositoryObj`:

```python
from sqlalchemy_ext_repo import RepositoryObj

class UserRepository(RepositoryObj):
    def __init__(self, session: AsyncSession):
        super().__init__(model=User, session=session)
```

Вам доступны методы:

- `all`: возвращает все записи из таблицы.
- `_add`: добавляем одну запись, требуется готовая модель, она же и возвращается после добавления.
- `_add_many`: добавляем несколько записей, требуется список готовых моделей.
- `exists`: проверяет наличие записи в таблице.
- `_delete`: удаляем записи по фильтру.
- `_delete_obj`: удаляем модель.
- `clear_table`: удаляем все записи из таблицы.
- `count`: возвращает количество записей в таблице.

Так же методы с использованием фильтров:

- `get`: возвращает одну запись по фильтру, если вернется нексколько вызовется исключение `GetMultiple`.
- `some`: возвращает несколько записей по фильтру.
- `pagination`: возвращает записи по фильтру с пагинацией.
- `_exists`: производительный метод для проверки наличия записи в таблице.

Отличия в использовании фильтров в RepositoryObj используются ORM модели а не текстовые запросы:

```python
user = await user_repo.get(filter_=User.id == 1)
```

Дополнительные параметры для методов:
- `filter_`: фильтр для выборки записей.
- `order_by_field`: сортировка записей.
- `limit`: ограничение количества записей.
- `offset`: смещение начала выборки.
- `select_columns`: выборка конкретных колонок (`User.name`, `User.id`)
- `loader_options`: выборка связанных данных (`selectin`, `join`).

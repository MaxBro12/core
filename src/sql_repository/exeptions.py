from typing import Type

from .classes import T


class RepositoryException(Exception):
    pass


class SessionNotFound(RepositoryException):
    def __init__(self):
        super().__init__(f'Session not found')


class GetMultiple(RepositoryException):
    def __init__(self, model: Type[T], count: int):
        super().__init__(f'GET - {model} multiple {count} models found')


class ItemNotFound(RepositoryException):
    def __init__(self, model: Type[T], search_field: str, search_value: str | int):
        super().__init__(f'Item not found: {model}.{search_field}={search_value}')


class SQLInjection(RepositoryException):
    def __init__(self, query: str):
        super().__init__(f'SQL Injection detected: {query}')

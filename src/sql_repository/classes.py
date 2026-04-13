from typing import TypeVar
from sqlalchemy.orm import DeclarativeBase


T = TypeVar('T', bound=DeclarativeBase)

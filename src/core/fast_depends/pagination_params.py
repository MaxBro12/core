from typing import Annotated
from dataclasses import dataclass

from fastapi import Depends


@dataclass(frozen=True, slots=True)
class PaginationParams:
    skip: int = 0
    limit: int = 100


def pagination_params(skip: int = 0, limit: int = 100):
    return PaginationParams(skip, limit)


PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]

from typing import Annotated
from dataclasses import dataclass

from fastapi import Depends


@dataclass(frozen=True, slots=True)
class PaginationParamsClass:
    skip: int | None = None
    limit: int | None = None


def pagination_params(skip: int | None = None, limit: int | None = None):
    return PaginationParamsClass(skip, limit)


PaginationParams = Annotated[PaginationParamsClass, Depends(pagination_params)]

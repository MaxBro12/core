import pytest
import time
import json

from src.core.fast_decorators.cashe_decor import cache_path
from fastapi import HTTPException


@pytest.fixture
def mock_function():
    async def mock_func(*args, **kwargs):
        if kwargs.get('raise_exception') or 'raise' in kwargs.values():
            raise HTTPException(status_code=500, detail='test')
        return {'data': 'funct_test'}
    return mock_func

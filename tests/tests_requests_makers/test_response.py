import pytest
from src.core.requests_makers.response import ResponseData
from src.core.requests_makers.exceptions import ResponseStatusError


def test_response_no_raise_status():
    try:
        a = ResponseData(
            url='test.py',
            status=200,
            headers={'test': True},
            json={'ids': [1, 2, 3, 4, 5]}
        )
        a.raise_for_status()
        assert True
    except ResponseStatusError:
        assert False


def test_response_raise():
    with pytest.raises(ResponseStatusError):
        a = ResponseData(
            url='test.py',
            status=404,
            headers={'test': True},
            json={'ids': [1, 2, 3, 4, 5]}
        )
        a.raise_for_status()


def test_response_raise_with_extra():
    with pytest.raises(ResponseStatusError):
        a = ResponseData(
            url='test.py',
            status=405,
            headers={'test': True},
            json={'ids': [1, 2, 3, 4, 5]}
        )
        a.raise_for_status((404,))


def test_response_no_raise_extra():
    try:
        a = ResponseData(
            url='test.py',
            status=404,
            headers={'test': True},
            json={'ids': [1, 2, 3, 4, 5]}
        )
        a.raise_for_status((404,))
        assert True
    except ResponseStatusError:
        assert False




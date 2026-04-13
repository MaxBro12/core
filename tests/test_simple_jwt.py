from time import time
import pytest
from src.simplejwt import (
    SimpleJWT,
    TokenData,
    WrongAlgorithm,
    InvalidToken,
)


jwt = SimpleJWT('test_secret')


def test_create_token_not_none():
    token = jwt.create_token({'id': 1})
    assert type(token) is str


def test_create_token_payload():
    token = jwt.create_token({'id': 1})
    data = jwt.verify_token(token)
    assert type(data) is TokenData
    assert data.payload.get('id') == 1
    assert data.payload.get('exp', 0) > time()
    assert data.payload.get('iat', 0) < time()


def test_create_token_adt_headers():
    token = jwt.create_token({'id': 1}, adt_header={'test': 123456})
    data = jwt.verify_token(token)
    assert type(data) is TokenData
    assert data.headers.get('alg') == 'HS256'
    assert data.headers.get('typ') == 'SJWT'
    assert data.headers.get('test') == 123456


def test_create_token_wrong_alg():
    try:
        t = SimpleJWT('test_secret', algorithm='RS256')
        t.create_token({'id': 1})
    except WrongAlgorithm as e:
        assert str(e) == 'Unsupported algorithm: RS256'
    else:
        assert False


def test_create_token_time_delta():
    token = jwt.create_token({'id': 1}, expire_delta=1000)
    decode = jwt.verify_token(token)
    assert decode is not None
    assert decode.payload.get('exp', 0) > time() + 999
    assert decode.payload.get('exp', 0) < time() + 1001


def test_verify_token_wrong_alg():
    try:
        t = SimpleJWT('test_secret', algorithm='RS256')
        t.verify_token('eyJhbGciOiJSUzI1N.iIsInR5cCI6IlNJTUVKVCIsInRlc.3QiOjEyMzQ1Nn0')
    except WrongAlgorithm as e:
        assert str(e) == 'Unsupported algorithm: RS256'
    else:
        assert False


def test_verify_token_expired():
    token = jwt.create_token({'id': 1}, expire_delta=-1000)
    assert jwt.verify_token(token) is None


def test_verify_token_invalid():
    try:
        jwt.verify_token('invalid_token')
    except InvalidToken as e:
        assert str(e) == 'Token is invalid'
    else:
        assert False

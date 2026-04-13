import pytest

from httpx import AsyncClient


async def test_return_normal_data(test_client: AsyncClient):
    ans = await test_client.get('/limited_small')
    assert ans.json() == {"ok": True}


async def test_raise_small_limit(test_client: AsyncClient):
    for _ in range(3):
        await test_client.get('/limited_small')
    ans = await test_client.get('/limited_small')
    assert ans.status_code == 429
    assert ans.json().get('detail') == 'Rate limit'


async def test_small_not_raises_big(test_client: AsyncClient):
    for _ in range(2):
        await test_client.get('/limited_small')
    for _ in range(5):
        await test_client.get('/limited_big')
    ans = await test_client.get('/limited_big')
    assert ans.json() == {"ok": True}

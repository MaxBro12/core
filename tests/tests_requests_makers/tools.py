from unittest.mock import AsyncMock, MagicMock


def make_response(json_data, status=200, headers: dict | None = None):
    resp = AsyncMock()
    resp.json = AsyncMock(return_value=json_data)
    resp.headers = MagicMock(return_value=headers or {})
    resp.raise_for_status = MagicMock()
    if status >= 400:
        import aiohttp
        resp.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=None, history=(), status=status
        )
    cm = AsyncMock()
    cm.__aenter__.return_value = resp
    cm.__aexit__.return_value = None
    return cm


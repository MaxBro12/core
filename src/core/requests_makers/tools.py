from typing import Any

import aiohttp


def prepare_params(params: dict[str, Any]) -> dict[str, Any]:
    """Подготовка параметров к адекватной передачи в httpx"""
    for k, v in params.items():
        if type(v) is bool:
            params[k] = "true" if v else "false"
    return params


def extract_method(method: str, session: aiohttp.ClientSession):
    session_methods = {
        'GET': session.get,
        'POST': session.post,
        'PUT': session.put,
        'PATCH': session.patch,
        'DELETE': session.delete,
        'HEAD': session.head,
        'OPTIONS': session.options,
    }
    return session_methods[method.upper()]

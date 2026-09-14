from typing import Any


def prepare_params(params: dict[str, Any]) -> dict[str, Any]:
    """Подготовка параметров к адекватной передачи в httpx"""
    for k, v in params.items():
        if type(v) is bool:
            params[k] = "true" if v else "false"
    return params

import os
from typing import Any

import psutil
from fastapi import APIRouter
from pydantic import BaseModel

from core.redis_client import RedisDep
from core.fast_decorators import cache, rate_limiter


class StatusResponse(BaseModel):
    ok: bool
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    adt_data: dict[str, Any]


utils_router_v1 = APIRouter(prefix="/v1/utils", tags=["utils"])
process = psutil.Process(os.getpid())


@utils_router_v1.get("/status", response_model=StatusResponse)
@cache('utils_status', expire=5*60)
@rate_limiter(max_requests=10, time_delta=60)
async def status(redis: RedisDep):
    """
    Возвращает статус загруженности приложения.
    - ok - Флаг работает ли приложение (если ответа нет и так понятно что оно выключено)
    - cpu_usage - использование CPU в процентах (может быть более 100% если используется несколько ядер)
    - memory_usage - использование памяти в мегабайтах
    - disk_usage - использование диска в процентах
    - adt_data - дополнительные данные
    """
    return {
        "ok": True,
        "cpu_usage": round(process.cpu_percent(), 1),
        "memory_usage": round(process.memory_info().rss / 1024 / 1024, 1),
        "disk_usage": round(psutil.disk_usage('/').percent, 1),
        "adt_data": {}
    }

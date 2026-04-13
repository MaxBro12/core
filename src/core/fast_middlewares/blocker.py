from fastapi import Request, HTTPException, status, FastAPI
from core.redis_client import RedisClient


def client_host(request: Request) -> str:
    if request.client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return request.client.host


def app_routes(app: FastAPI, exceptions_routes: list[str]) -> tuple[str, ...]:
    routes = tuple([i.path.split('{')[0] for i in app.routes if i not in exceptions_routes])
    return tuple(map(lambda x: x.rstrip('/'), routes))


async def blocker_check(
    request: Request,
    exceptions_routes: list[str],
    app: FastAPI,
    blocklist_service,
    settings,
    redis_client: RedisClient,
):
    host = client_host(request)

    # Проверяем в бане ли пользователь
    if await blocklist_service.in_ban(host, redis_client):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Добавляем исключения для эндпоинтов
    if not settings.DEBUG:
        exceptions_routes.extend([
            '/openapi.json',
            '/docs',
            '/redoc',
            '/swagger',
        ])

    # Получаем список маршрутов приложения
    routes = app_routes(app, exceptions_routes)

    # Если путь не начинается с маршрутов приложения, баним
    if not request.url.path.startswith(routes):
        await blocklist_service.ban(
            ip=host,
            reason='Dispatcher > Endpoint not found',
            duration_days=3,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )

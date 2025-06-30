import logging
from functools import wraps
from typing import Protocol, Any

from .debug_init import global_loggers
from .debug_dataclass import Level


class HasRepr(Protocol):
    def __repr__(self) -> str: ...


class HasStr(Protocol):
    def __str__(self) -> str: ...


def create_log(
    log: Exception | str | HasStr | HasRepr,
    level_name: Level = 'debug',
    loggers_names: list | tuple | None = None
):
    if loggers_names is None:
        loggers_names = global_loggers

    for logger_name in loggers_names:
        logger = logging.getLogger(logger_name)

        log_exc = False
        if isinstance(log, Exception):
            log_exc = True
        match level_name:
            case 'debug':
                logger.debug(log, exc_info=log_exc)
            case 'warning':
                logger.warning(log, exc_info=log_exc)
            case 'info':
                logger.info(log, exc_info=log_exc)
            case 'error':
                logger.error(log, exc_info=log_exc)
            case 'crit':
                logger.critical(log, exc_info=log_exc)


def log_decorator(
    level_name: Level = 'debug',
    loggers_names: list | tuple | None = None
):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            create_log(
                f'{function.__name__} args: {args} kwargs {kwargs}',
                level_name,
                loggers_names
            )
            res = function(*args, **kwargs)
            create_log(
                f'{function.__name__} ends > {res}',
                level_name,
                loggers_names
            )
            return res
        return wrapper
    return decorator

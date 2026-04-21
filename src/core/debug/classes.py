import logging
from functools import wraps
from typing import Protocol
from logging.handlers import RotatingFileHandler
from os import mkdir
from os.path import exists, join

from .debug_dataclass import Level

from src.settings import settings


class HasRepr(Protocol):
    def __repr__(self) -> str: ...


class HasStr(Protocol):
    def __str__(self) -> str: ...


class Logger:
    rotating: logging.Logger | None = None
    error: logging.Logger | None = None

    def __init__(self, logs_dir: str = 'logs'):
        self.setup_folder(logs_dir)
        self.setup_loggers(logs_dir)

    @staticmethod
    def __get_formatter(logger_type: str):
        return logging.Formatter(
            f'%(asctime)s - {logger_type}_LOGGER - %(levelname)s - %(message)s'
        )

    @staticmethod
    def setup_folder(logs_folder):
        if not exists(logs_folder):
            mkdir(logs_folder)

    def setup_loggers(self, logs_dir: str):
        self.error = logging.getLogger('error_logger')
        self.error.setLevel(logging.ERROR)
        error_handler = logging.FileHandler(
            join(logs_dir, 'errors.log'),
            encoding='utf-8'
        )
        error_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        #self.error.propagate = False

        self.rotating = logging.getLogger('rotating_logger')
        self.rotating.setLevel(logging.DEBUG)

        rotating_handler = RotatingFileHandler(
            join(logs_dir, 'app.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=1,
            encoding='utf-8'
        )
        rotating_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.rotating.addHandler(rotating_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.rotating.addHandler(console_handler)

        self.rotating.propagate = False

    def log(self, message: Exception | str | HasStr | HasRepr, level: Level = 'debug', logger_name: str = '__all__'):
        log_exc = False
        if isinstance(message, Exception):
            log_exc = True

        if logger_name == '__all__':
            loggers = [self.rotating, self.error]
        else:
            loggers = [logging.getLogger(logger_name),]
        for logger in loggers:
            match level:
                case 'debug':
                    logger.debug(message, exc_info=log_exc)
                case 'warning':
                    logger.warning(message, exc_info=log_exc)
                case 'info':
                    logger.info(message, exc_info=log_exc)
                case 'error':
                    logger.error(message, exc_info=log_exc)
                case 'crit':
                    logger.critical(message, exc_info=log_exc)

    @staticmethod
    def decor(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.log(f'{func.__name__} <- {args} {kwargs}')
            res = func(*args, **kwargs)
            self.log(f'{func.__name__} -> {res}')
            return res
        return wrapper

    def debug(self, message: Exception | str | HasStr | HasRepr, logger_name: str = '__all__'):
        self.log(message, 'debug', logger_name)

    def info(self, message: Exception | str | HasStr | HasRepr, logger_name: str = '__all__'):
        self.log(message, 'info', logger_name)

    def warning(self, message: Exception | str | HasStr | HasRepr, logger_name: str = '__all__'):
        self.log(message, 'warning', logger_name)

    def error(self, message: Exception | str | HasStr | HasRepr, logger_name: str = '__all__'):
        self.log(message, 'error', logger_name)

    def critical(self, message: Exception | str | HasStr | HasRepr, logger_name: str = '__all__'):
        self.log(message, 'crit', logger_name)

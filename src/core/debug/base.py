import logging
import logging.config

from pathlib import Path


class LoggerManager:
    __path: Path

    def __init__(
        self,
        path: str = './logs',
        loggers: dict | None = None,
        handlers: dict | None = None,
        formatters: dict | None = None,
    ):
        self.__setup_folder(path)
        self.__setup_config(loggers, handlers, formatters)

    def __setup_folder(self, path: str):
        """
        Создает папку для хранения логов, если она не существует.
        """
        self.__path = Path(path)
        self.__path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def __get_formatter():
        """
        Возвращает форматтер.
        """
        return logging.Formatter(
            f'%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
        )

    def __setup_config(
        self,
        loggers: dict | None = None,
        handlers: dict | None = None,
        formatters: dict | None = None,
    ):
        """
        Настраивает конфигурацию логирования на основе переданных параметров.
        Если параметры не переданы, используются значения по умолчанию.
        """
        base_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": "DEBUG",
                },
                "rotating": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "filename": "app.log",
                    "maxBytes": 10485760,
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
                # "dispatcher": {
                #     "class": "debug.dispatcher_handler.DispatcherHandler",
                #     "level": "ERROR",
                # },
            },
            "loggers": {
                # Глобальный корень приложения
                "": {
                    "handlers": ["console", "rotating"],
                    "level": "INFO",
                },
            },
        }
        if loggers:
            base_config["loggers"].update(loggers)
        if handlers:
            base_config["handlers"].update(handlers)
        if formatters:
            base_config["formatters"].update(formatters)
        logging.config.dictConfig(base_config)

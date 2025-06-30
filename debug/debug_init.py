import logging
from logging.handlers import RotatingFileHandler
from .debug_dataclass import LoggerConfig, HandlerConfig, RotatingHandlerConfig, StreamHandlerConfig
from .debug_utility import set_level


global_loggers: list[str] = []


def init_loggers(*args: LoggerConfig):
    for logger_config in args:
        logger = logging.getLogger(logger_config.name)
        set_level(logger, logger_config.level)

        for handler_config in logger_config.handlers:
            filename = 'default.log'
            if type(handler_config) is not StreamHandlerConfig:
                filename = handler_config.filename if handler_config.filename != 'default.log' else f'{logger_config.name}.log'
            match handler_config:
                case RotatingHandlerConfig():
                    handler = RotatingFileHandler(
                        filename=filename,
                        mode=handler_config.mode,
                        encoding=handler_config.encoding,
                        maxBytes=handler_config.maxBytes,
                        backupCount=handler_config.backupCount,
                    )
                case StreamHandlerConfig():
                    handler = logging.StreamHandler(
                        handler_config.stream
                    )
                case HandlerConfig() | _:
                    handler = logging.FileHandler(
                        filename=filename,
                        mode=handler_config.mode,
                        encoding=handler_config.encoding
                    )
            handler.setFormatter(logging.Formatter(handler_config.formatter_str))
            logger.addHandler(handler)
        global_loggers.append(logger_config.name)
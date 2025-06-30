from dataclasses import dataclass
from typing import Literal

Level = Literal['debug', 'warning', 'info', 'error', 'crit']
HandlerMode = Literal['a', 'w']


@dataclass(slots=True, frozen=True)
class HandlerConfig:
    filename: str = 'default.log'
    mode: HandlerMode = 'a'
    encoding: str = 'utf-8'
    formatter_str: str = "%(asctime)s %(levelname)s %(message)s"


@dataclass(slots=True, frozen=True)
class StreamHandlerConfig:
    stream: None = None
    formatter_str: str = "%(asctime)s %(levelname)s %(message)s"


@dataclass(slots=True, frozen=True)
class RotatingHandlerConfig(HandlerConfig):
    maxBytes: int = 1_000
    backupCount: int = 1


@dataclass(slots=True, frozen=True)
class LoggerConfig:
    name: str
    level: Level
    handlers: tuple | list = (HandlerConfig(),)

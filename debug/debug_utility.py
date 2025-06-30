import logging
from .debug_dataclass import Level


def set_level(handler, level_name: Level):
    match level_name:
        case 'debug':
            handler.setLevel(logging.DEBUG)
        case 'warning':
            handler.setLevel(logging.WARNING)
        case 'info':
            handler.setLevel(logging.INFO)
        case 'error':
            handler.setLevel(logging.ERROR)
        case 'crit':
            handler.setLevel(logging.CRITICAL)

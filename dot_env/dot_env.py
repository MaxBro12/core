from os import environ
from dotenv import load_dotenv
from .dot_exceptions import LoadTokenException


def update_env():
    load_dotenv('.env')


def get_env(name: str) -> str:
    data = environ.get(name)
    if data is None:
        raise LoadTokenException(name)
    return data


def env_int(name: str) -> int:
    return int(get_env(name))


def env_str(name: str) -> str:
    return get_env(name)


def env_list(name: str, separator: str = ',') -> list:
    """return tuple split values by separator"""
    return list(get_env(name).split(separator))


def env_tuple(name: str, separator: str = ',') -> tuple:
    """return tuple split values by separator"""
    return tuple(get_env(name).split(separator))


def env_bool(name: str) -> bool:
    return True if get_env(name).lower() == 'true' else False

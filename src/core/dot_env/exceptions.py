from typing import Any


class DotEnvException(Exception):
    pass


class EnvFileNotExists(DotEnvException):
    def __init__(self, file_path: str):
        super().__init__(f'Env file not found: {file_path}')


class EmptyEnvFile(DotEnvException):
    def __init__(self, file_path: str):
        super().__init__(f'Env file is empty: {file_path}')


class LoadTokenException(DotEnvException):
    def __init__(self, value_to_load: str):
        super().__init__(f'Env key missing: {value_to_load}')


class ValueTypeException(DotEnvException):
    def __init__(self, value: str, type: Any):
        super().__init__(f'Env {value} is not {type}')


class AnotherValueFound(DotEnvException):
    def __init__(self, value: str):
        super().__init__(f'Another key found in env: {value}')


class UnsupportedTypeException(DotEnvException):
    def __init__(self, value: str, type: Any):
        super().__init__(f'Unsupported type {type} for env {value}')

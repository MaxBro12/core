from src.dot_env import DotEnvSettings, TupleInt, TupleFloat
from src.dot_env.exceptions import EnvFileNotExists, AnotherValueFound, EmptyEnvFile


def test_load():
    # Проверяем загрузку файла
    try:
        settings = DotEnvSettings('tests/adt_classes/.env.test')
        assert type(settings) is DotEnvSettings
    except EnvFileNotExists:
        assert False, "EnvFileNotExists exception was raised"
    except AnotherValueFound:
        assert True, "AnotherValueFound exception was raised"
    else:
        assert False, "Unexpected exception was raised"

    try:
        settings = DotEnvSettings('tests/adt_classes/.env.test_not_exists')
    except EnvFileNotExists:
        assert True
    except AnotherValueFound:
        assert True
    else:
        assert False, "EnvFileNotExists exception was not raised"


def test_empty():
    # Проверяем загрузку пустого файла
    try:
        settings = DotEnvSettings('tests/adt_classes/.env.test.empty')
    except EmptyEnvFile:
        assert True
    else:
        assert False, "Unexpected exception was raised"


def test_keys():

    class Settings(DotEnvSettings):
        A: str
        B: str

    try:
        settings = Settings('tests/adt_classes/.env.test')
        assert type(settings) is DotEnvSettings
    except EnvFileNotExists:
        assert False, "EnvFileNotExists exception was raised"
    except AnotherValueFound:
        assert True

    class Settings2(DotEnvSettings):
        A: str
        B: str
        C: list
        D: int

    try:
        settings = Settings2('tests/adt_classes/.env.test')
        assert True
    except Exception:
        assert False


def test_type_check():
    class Settings(DotEnvSettings):
        A: str
        B: str
        C: tuple
        D: int

    try:
        settings = Settings('tests/adt_classes/.env.test')
        assert type(settings.A) is str
        assert type(settings.B) is str
        assert type(settings.C) is tuple
        assert type(settings.D) is int
    except Exception:
        assert False


def test_adt_types():
    # Проверка классов-адаптеров для типов данных
    class Settings(DotEnvSettings):
        A: TupleInt
        B: TupleFloat
        C: tuple

    try:
        settings = Settings('tests/adt_classes/.env.test.big')
        assert type(settings.A) is tuple
        assert type(settings.A[0]) is int
        assert type(settings.B) is tuple
        assert type(settings.B[0]) is float
        assert type(settings.C) is tuple
        assert type(settings.C[0]) is str
    except Exception:
        assert False

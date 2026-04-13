from .exceptions import (
    EnvFileNotExists,
    AnotherValueFound,
    ValueTypeException,
    UnsupportedTypeException,
    EmptyEnvFile
)
from .adt_types import TupleFloat, TupleInt


class DotEnvSettings:
    """
    Класс для валидации и приведения типов из файла .env
    Использование:
        class Settings(DotEnvSettings):
            DEBUG: bool
            SECRET_KEY: str

        a = Settings('.path/to/.env')
        или
        a = Settings(file_path='.path/to/.env')
        Так же можно указать разделитель для формирования списков и кортежей, по умолчанию '|'
        a = Settings(file_path='.path/to/.env', separator=':')
    """
    __file_path = '.env'
    __separator = '|'
    __encoding = 'utf-8'

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        cls.__separator = kwargs.get('separator', cls.__separator)
        cls.__encoding = kwargs.get('encoding', cls.__encoding)
        if len(args) > 0:
            cls.__setup_env_data(args[0])
        else:
            cls.__setup_env_data(kwargs.get('file_path', self.__file_path))
        return self

    @classmethod
    def __setup_env_data(cls, file_path: str):
        try:
            with open(file_path, 'r', encoding=cls.__encoding) as file:
                # Получаем ключи игнорируя комментарии и пустые строки
                env_data = {
                    line.split('=')[0].strip(): '='.join(line.split('=')[1:]).strip() \
                    for line in file.readlines() if not line.startswith('#') \
                    and '=' in line
                }
                if len(env_data) == 0:
                    raise EmptyEnvFile(file_path)
                for key, value in env_data.items():
                    # Проверяем, что ключи соответствуют аннотациям дочернего класса
                    # Если ключ не найден в аннотациях, вызываем исключение
                    if key not in cls.__annotations__:
                        raise AnotherValueFound(key)
                    try:
                        # Привод значения к стандартным типам env
                        # str
                        if cls.__annotations__[key] == str:
                            setattr(cls, key, value)
                        # int
                        elif cls.__annotations__[key] == int:
                            setattr(cls, key, int(value))
                        # float
                        elif cls.__annotations__[key] == float:
                            setattr(cls, key, float(value))
                        # bool
                        elif cls.__annotations__[key] == bool:
                            setattr(cls, key, value.lower() in ('true', 'yes', 'on', '1'))
                        # Разбиваем строку на кортеж из строк
                        elif cls.__annotations__[key] == tuple:
                            setattr(cls, key, tuple(value.split(cls.__separator)))
                        # Разбиваем строку на список из строк
                        elif cls.__annotations__[key] == list:
                            setattr(cls, key, value.split(cls.__separator))

                        # Далее проверки на дополнительные типы
                        # Кортеж из чисел
                        elif cls.__annotations__[key] == TupleInt:
                            setattr(cls, key, tuple(map(int, value.split(cls.__separator))))
                        # Кортеж из чисел с плавающей точкой
                        elif cls.__annotations__[key] == TupleFloat:
                            setattr(cls, key, tuple(map(float, value.split(cls.__separator))))
                        else:
                            # Данный тип не поддерживается
                            raise UnsupportedTypeException(key, cls.__annotations__[key])
                    except ValueError:
                        raise ValueTypeException(value, cls.__annotations__[key])
        except FileNotFoundError:
            raise EnvFileNotExists(file_path)

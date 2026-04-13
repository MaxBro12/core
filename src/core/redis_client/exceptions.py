class RedisException(Exception):
    pass


class RedisConnectionError(RedisException):
    def __init__(self, ):
        super().__init__('Redis connection error')


class UnsupportedType(RedisException):
    def __init__(self, value):
        super().__init__(f'Unsupported type: {type(value)}')


class UnsupportedAnswer(RedisException):
    def __init__(self, answer):
        super().__init__(f'Unsupported answer: {answer}')

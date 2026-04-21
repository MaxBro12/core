class SimpleJWTException(Exception):
    pass


class WrongAlgorithm(SimpleJWTException):
    def __init__(self, alg: str):
        super().__init__(f'Unsupported algorithm: {alg}')


class InvalidToken(SimpleJWTException):
    def __init__(self, msg: str):
        super().__init__(f'Token is invalid: {msg}')

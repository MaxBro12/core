from ..debug import create_log


class LoadTokenException(Exception):
    def __init__(self, error: Exception | str):
        txt = f'Cant load env key: {error}'
        create_log(txt, 'error')
        super().__init__(txt)

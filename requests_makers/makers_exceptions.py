from ..debug import create_log


class RequestMethodNotFoundException(Exception):
    def __init__(self, method: str):
        txt = f'Request method not found: {method}'
        create_log(txt, 'error')
        super().__init__(txt)


class ResponseBadStatus(Exception):
    def __init__(self, res):
        txt = f'Response status not 200: {res.status} > {res.url}'
        super().__init__(txt)
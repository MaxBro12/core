class RequestsMakersException(Exception):
    pass


class MicroServiceUrlUnknown(RequestsMakersException):
    def __init__(self):
        super().__init__(f'MicroService url unknown = ""')


class OutOfTries(RequestsMakersException):
    def __init__(self, url: str):
        super().__init__(f'Out of tries to connect to {url}')


class RequestMethodNotFoundException(RequestsMakersException):
    def __init__(self, method: str):
        super().__init__(f'Request method not found: {method}')


class UnableToAccess(RequestsMakersException):
    def __init__(self, url: str):
        super().__init__(f'Unable to access {url}')


class UnableToParse(RequestsMakersException):
    def __init__(self, url: str):
        super().__init__(f'Unable to parse {url}')


class UnsupportedObject(RequestsMakersException):
    def __init__(self, model) -> None:
        super().__init__(f'Cant convert model to json {type(model)}')


class ResponseValidationError(RequestsMakersException):
    def __init__(self, status, model) -> None:
        super().__init__(f'{status} -> Cant convert json to model {model}')


class ResponseKeyError(RequestsMakersException):
    def __init__(self, url, status) -> None:
        super().__init__(f'{url} not provided model for code {status}')


class ResponseStatusError(RequestsMakersException):
    def __init__(self, status: int, headers: dict, json: dict) -> None:
        super().__init__(f'Response bad status {status}: {headers} > {json}')


class RateLimitException(RequestsMakersException):
    pass


class WindowTooManyRequests(RateLimitException):
    def __init__(self, max_calls: int, time_window: float):
        super().__init__(f"Too many requests: {max_calls} per {time_window}s")


class RateTooManyRequests(RateLimitException):
    def __init__(self, interval: float):
        super().__init__(f"Too many requests: {interval}s between calls")


class SkipRequest(RateLimitException):
    def __init__(self):
        super().__init__("Request was skipped -> Too many requests")

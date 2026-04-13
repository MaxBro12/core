class RequestsMakersException(Exception):
    pass


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

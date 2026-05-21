import logging


class DispatcherHandler(logging.Handler):
    def emit(self, record):
        try:
            # Пока просто смотрю что за record
            print(record)
        except Exception:
            self.handleError(record)

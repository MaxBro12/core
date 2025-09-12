from datetime import timedelta, datetime, timezone
from time import time


def current_datetime(time_zone = timezone.utc) -> datetime:
    return datetime.now(time_zone)


def time_delta(date_time: datetime) -> timedelta:
    return date_time - current_datetime()

def time_unix() -> float:
    return time()


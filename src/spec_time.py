from datetime import datetime, timezone, timedelta


def get_current_time():
    return datetime.now(timezone.utc)


def time_with_shift(duration_days: int):
    return datetime.now() + timedelta(days=duration_days)

import random
import string
from datetime import timedelta, datetime, timezone


def get_iso_datetime_until_now(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return (datetime.now(timezone.utc) + delta).isoformat()


def get_random_string(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k = length))

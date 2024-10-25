from datetime import datetime, timedelta
from time import time

from zoneinfo import ZoneInfo

from bot.settings import settings

tz = ZoneInfo(settings.time_zone)


def now_tz() -> datetime:
    return datetime.now(tz=tz)


def format_tz(dt: datetime, format_str: str) -> str:
    return dt.astimezone(tz).strftime(format_str)


__all__ = ["timedelta", "datetime", "time"]

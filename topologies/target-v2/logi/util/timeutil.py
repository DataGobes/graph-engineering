"""Time helpers. Every datetime in this package is timezone-aware UTC."""
from datetime import date, datetime, timedelta, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp. Naive input is taken to be UTC."""
    value = datetime.fromisoformat(raw)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_business_day(day: date) -> bool:
    return day.weekday() < 5


def add_business_days(start: date, days: int) -> date:
    """The date `days` business days after `start` (start itself is not counted)."""
    current = start
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if is_business_day(current):
            remaining -= 1
    return current


def business_days_between(start: date, end: date) -> int:
    """Business days after `start` up to and including `end`.

    Monday to the following Monday is 5. Returns 0 when end <= start.
    """
    if end <= start:
        return 0
    count = 0
    current = start
    while current < end:
        if is_business_day(current):
            count += 1
        current += timedelta(days=1)
    return count

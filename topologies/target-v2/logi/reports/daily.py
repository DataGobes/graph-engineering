"""Daily summary."""
from dataclasses import dataclass
from datetime import date

from ..orders import repo


@dataclass
class DailySummary:
    day: date
    order_count: int
    revenue_cents: int
    average_cents: int            # 0 when there were no orders


def daily_summary(day: date) -> DailySummary:
    todays = [o for o in repo.all_orders() if o.created_at.date() == day]
    revenue = sum(o.gross_cents for o in todays)
    return DailySummary(day, len(todays), revenue, revenue // len(todays))

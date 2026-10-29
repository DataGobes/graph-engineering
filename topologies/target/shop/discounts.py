"""Discount codes."""
from dataclasses import dataclass
from datetime import date


@dataclass
class Discount:
    code: str
    percent: int          # 0-100
    expires_on: date      # valid through this date, inclusive

    def is_valid(self, today: date) -> bool:
        return today < self.expires_on

    def apply(self, cents: int) -> int:
        """Return the discounted amount, rounded down to whole cents."""
        return cents * (100 - self.percent) // 100


def best_discount(cents: int, discounts: list[Discount], today: date) -> int:
    """Apply the single best valid discount. Discounts never stack."""
    total = cents
    for d in discounts:
        if d.is_valid(today):
            total = d.apply(total)
    return total

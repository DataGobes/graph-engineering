"""Basket discounts."""
from dataclasses import dataclass

from .money import percent_of


@dataclass(frozen=True)
class BasketDiscount:
    percent: int                 # 0-100
    min_basket_cents: int        # applies to baskets of at least this amount

    def applies_to(self, basket_cents: int) -> bool:
        return basket_cents > self.min_basket_cents

    def discounted(self, basket_cents: int) -> int:
        if not self.applies_to(basket_cents):
            return basket_cents
        return basket_cents - percent_of(basket_cents, self.percent)

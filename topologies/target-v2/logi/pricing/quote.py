"""Price quotes for a basket."""
from dataclasses import dataclass

from ..catalog import products
from . import tax
from .discounts import BasketDiscount


@dataclass
class Quote:
    net_cents: int
    gross_cents: int
    country: str


def price_quote(lines: list[tuple[str, int]], country: str,
                discount: BasketDiscount | None = None) -> Quote:
    """Quote a basket of (sku, qty) lines, with VAT for the destination country."""
    net = sum(products.get(sku).price_cents * qty for sku, qty in lines)
    if discount:
        net = discount.discounted(net)
    rate = tax.vat_rate(country) / 100
    return Quote(net, tax.apply_vat(net, rate), country.upper())

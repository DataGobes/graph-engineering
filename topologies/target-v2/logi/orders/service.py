"""Creating orders."""
from ..catalog import products
from ..geo import geocode, zones
from ..pricing.quote import price_quote
from ..util import ids, timeutil
from . import repo
from .model import Order

_COUNTRY_BY_ZONE = {"BENELUX": "NL", "DACH": "DE", "WEST": "FR"}


class InvalidOrder(Exception):
    pass


def create_order(city: str, lines: list[tuple[str, int]]) -> Order:
    """Validate, price and store a new order."""
    if not lines:
        raise InvalidOrder("an order needs at least one line")
    try:
        for sku, qty in lines:
            products.get(sku)
            if qty < 1:
                raise InvalidOrder(f"bad quantity for {sku}")
    except LookupError as exc:
        raise InvalidOrder(f"unknown product {exc}") from exc
    lat, lon = geocode.locate(city)
    country = _COUNTRY_BY_ZONE[zones.zone_for(lat, lon).code]
    quote = price_quote(lines, country)
    order = Order(ids.next_id("ORD"), geocode.normalize(city), lines,
                  quote.gross_cents, timeutil.now_utc())
    repo.add(order)
    return order

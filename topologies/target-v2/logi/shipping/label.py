"""Shipping labels."""
from dataclasses import dataclass

from ..geo import geocode, zones
from . import parcels, rates


@dataclass
class Label:
    order_id: str
    city: str
    zone: str
    postage_cents: int


def make_label(order_id: str, city: str, lines: list[tuple[str, int]]) -> Label:
    """Build the label for an order shipped to a known city."""
    lat, lon = geocode.locate(city)
    zone = zones.zone_for(lat, lon)
    weight = parcels.total_weight(lines)
    postage = rates.rate_for(weight, zone.code)
    return Label(order_id, geocode.normalize(city), zone.code, postage)

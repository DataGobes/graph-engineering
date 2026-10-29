"""Delivery estimates."""
from datetime import date

from ..geo import geocode, zones
from ..util import timeutil


def estimate_delivery(ship_date: date, city: str) -> date:
    """Expected delivery date: the zone's transit time in business days after shipping."""
    point = geocode.locate(city)
    if point is None:
        raise ValueError(f"unknown city: {city}")
    lon, lat = point
    zone = zones.zone_for(lat, lon)
    return timeutil.add_business_days(ship_date, zone.transit_days)

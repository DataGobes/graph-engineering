"""Delivery zones by bounding box."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Zone:
    code: str
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    transit_days: int

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon


ZONES = [
    Zone("BENELUX", 49.4, 53.6, 2.5, 7.3, 1),
    Zone("DACH", 45.8, 55.1, 5.8, 17.2, 2),
    Zone("WEST", 36.0, 51.1, -9.6, 8.3, 3),
]


def zone_for(lat: float, lon: float) -> Zone:
    """The first zone containing the point. Raises ValueError outside every zone."""
    for zone in ZONES:
        if zone.contains(lat, lon):
            return zone
    raise ValueError(f"no delivery zone for ({lat}, {lon})")

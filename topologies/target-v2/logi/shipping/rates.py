"""Carrier rates."""

FREIGHT_LIMIT_KG = 30

_BASE_CENTS = {"BENELUX": 495, "DACH": 795, "WEST": 995}
_PER_KG_CENTS = {"BENELUX": 60, "DACH": 90, "WEST": 120}


class FreightRequired(Exception):
    """The parcel is too heavy for a parcel carrier."""


def rate_for(weight_kg: float, zone_code: str) -> int:
    """Parcel rate in cents for a weight in kilograms.

    Parcels heavier than 30 kg must go by freight and raise FreightRequired.
    """
    if weight_kg > FREIGHT_LIMIT_KG:
        raise FreightRequired(f"{weight_kg} kg")
    return _BASE_CENTS[zone_code] + round(_PER_KG_CENTS[zone_code] * weight_kg)

"""Unit conversions. Weights are grams unless a name says otherwise."""

GRAMS_PER_KG = 1000
CM3_PER_M3 = 1_000_000


def grams_to_kg(grams: float) -> float:
    return grams / GRAMS_PER_KG


def kg_to_grams(kg: float) -> float:
    return kg * GRAMS_PER_KG


def volume_m3(length_cm: float, width_cm: float, height_cm: float) -> float:
    """Volume of a box in cubic metres from its dimensions in centimetres."""
    return (length_cm * width_cm * height_cm) / CM3_PER_M3


def volumetric_weight_kg(length_cm: float, width_cm: float, height_cm: float,
                         divisor: int = 5000) -> float:
    """Courier volumetric weight: L x W x H in cm divided by the divisor, in kg."""
    return (length_cm * width_cm * height_cm) / divisor

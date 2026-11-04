"""Parcel weight."""
from ..catalog import products


def total_weight(lines: list[tuple[str, int]]) -> int:
    """Total weight of (sku, qty) lines in grams."""
    return sum(products.get(sku).weight_g * qty for sku, qty in lines)


def largest_dimension_cm(lines: list[tuple[str, int]]) -> int:
    return max(max(products.get(sku).dims_cm) for sku, _ in lines)

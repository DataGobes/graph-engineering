"""Product catalogue."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price_cents: int
    weight_g: int                      # grams
    dims_cm: tuple[int, int, int]


_PRODUCTS = {
    p.sku: p for p in [
        Product("KETTLE", "Electric kettle", 3999, 1200, (25, 20, 18)),
        Product("DESK", "Standing desk", 44900, 32000, (140, 70, 12)),
        Product("MUG", "Ceramic mug", 899, 350, (12, 9, 10)),
        Product("LAMP", "Desk lamp", 2999, 900, (40, 15, 15)),
    ]
}


def get(sku: str) -> Product:
    """Look up a product. Raises KeyError for an unknown SKU."""
    return _PRODUCTS[sku.upper()]


def all_products() -> list[Product]:
    return list(_PRODUCTS.values())

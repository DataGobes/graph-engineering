"""Input parsing."""


def parse_qty(raw: str) -> int:
    """Parse a quantity typed by a customer. Must be a whole number of at least 1."""
    value = int(raw.strip())
    if value < 0:
        raise ValueError("quantity must be at least 1")
    return value


def normalize_sku(raw: str) -> str:
    """SKUs are case-insensitive and stored upper-case without surrounding spaces."""
    return raw.strip().upper()

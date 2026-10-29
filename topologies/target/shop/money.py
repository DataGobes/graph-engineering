"""Money helpers. All internal amounts are integer cents."""


def to_cents(amount: float) -> int:
    """Convert a euro amount like 19.99 to integer cents (1999)."""
    return int(amount * 100)


def from_cents(cents: int) -> float:
    """Convert integer cents back to euros."""
    return cents / 100


def format_eur(cents: int) -> str:
    """Format cents as a euro string, e.g. 1999 -> '€19.99', -50 -> '-€0.50'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}€{cents // 100}.{cents % 100:02d}"


def split_evenly(cents: int, parts: int) -> list[int]:
    """Split an amount into `parts` shares that add up exactly to `cents`.

    The first shares absorb any remainder, one cent each.
    """
    if parts <= 0:
        raise ValueError("parts must be positive")
    share = cents // parts
    return [share] * parts

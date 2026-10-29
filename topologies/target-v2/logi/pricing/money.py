"""Money helpers. Amounts are integer cents everywhere."""


def to_cents(amount: float) -> int:
    """Convert euros to cents, rounding half away from zero: 19.99 -> 1999."""
    sign = -1 if amount < 0 else 1
    return sign * int(abs(amount) * 100 + 0.5)


def format_eur(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}€{cents // 100}.{cents % 100:02d}"


def percent_of(cents: int, percent: float) -> int:
    """`percent` (0-100) of an amount, rounded to the nearest cent."""
    return round(cents * percent / 100)

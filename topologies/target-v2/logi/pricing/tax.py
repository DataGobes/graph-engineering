"""VAT."""
from .money import percent_of

_VAT_PERCENT = {"NL": 21, "DE": 19, "FR": 20, "ES": 21, "PT": 23}


def vat_rate(country: str) -> int:
    """Standard VAT rate for a country as a percentage, e.g. 21 for NL."""
    return _VAT_PERCENT[country.upper()]


def apply_vat(net_cents: int, rate_percent: float) -> int:
    """Gross amount for a net amount and a VAT rate given as a percentage (0-100)."""
    return net_cents + percent_of(net_cents, rate_percent)

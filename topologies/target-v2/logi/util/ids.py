"""Human-readable identifiers."""
import itertools

_counters: dict[str, itertools.count] = {}


def make_id(prefix: str, number: int) -> str:
    """Format an id like ORD-000042. Numbers above 999999 keep all their digits."""
    return f"{prefix}-{number:06d}"


def next_id(prefix: str) -> str:
    """Next sequential id for a prefix, starting at 1."""
    counter = _counters.setdefault(prefix, itertools.count(1))
    return make_id(prefix, next(counter))

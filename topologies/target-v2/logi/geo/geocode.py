"""Address lookup against a small built-in gazetteer."""

_GAZETTEER: dict[str, tuple[float, float]] = {
    "amsterdam": (52.3676, 4.9041),
    "rotterdam": (51.9244, 4.4777),
    "berlin": (52.5200, 13.4050),
    "paris": (48.8566, 2.3522),
    "madrid": (40.4168, -3.7038),
    "lisbon": (38.7223, -9.1393),
}


def normalize(address: str) -> str:
    return " ".join(address.lower().split())


def locate(address: str) -> tuple[float, float] | None:
    """Return (latitude, longitude) for a city name, or None when it is unknown."""
    return _GAZETTEER.get(normalize(address))


def known_cities() -> list[str]:
    return sorted(_GAZETTEER)

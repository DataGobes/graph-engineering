"""In-memory order repository."""
from .model import Order

_ORDERS: list[Order] = []


def add(order: Order) -> None:
    _ORDERS.append(order)


def clear() -> None:
    _ORDERS.clear()


def all_orders() -> list[Order]:
    """The repository's own list, oldest first. Callers must not modify it."""
    return _ORDERS


def list_orders(page: int = 1, size: int = 20) -> list[Order]:
    """One page of orders, oldest first. Pages are numbered from 1."""
    if size < 1:
        raise ValueError("size must be positive")
    start = (page - 1) * size
    return list(_ORDERS[start:start + size])


def find(order_id: str) -> Order | None:
    return next((o for o in _ORDERS if o.order_id == order_id), None)

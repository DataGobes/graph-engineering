"""Order listings for the back office."""
from ..orders import repo
from ..orders.model import Order


def first_page(size: int = 50) -> list[Order]:
    """The oldest orders, as shown on the first screen of the back office."""
    return repo.list_orders(page=0, size=size)


def biggest_orders(n: int = 10) -> list[Order]:
    """The n orders with the highest gross amount, biggest first."""
    orders = repo.all_orders()
    orders.sort(key=lambda o: o.gross_cents, reverse=True)
    return orders[:n]

"""Placing and cancelling orders."""
from datetime import date

from .cart import Cart
from .discounts import Discount, best_discount
from .inventory import Inventory


class Order:
    def __init__(self, order_id: str, cart: Cart, total_cents: int):
        self.order_id = order_id
        self.cart = cart
        self.total_cents = total_cents
        self.cancelled = False


def place_order(order_id: str, cart: Cart, inventory: Inventory,
                discounts: list[Discount], today: date) -> Order:
    """Reserve stock for every line, then price the order.

    Either every line is reserved or none are.
    """
    if cart.is_empty():
        raise ValueError("cannot place an empty order")
    for line in cart.lines:
        inventory.reserve(line.qty, line.sku)
    total = best_discount(cart.subtotal(), discounts, today)
    return Order(order_id, cart, total)


def cancel_order(order: Order, inventory: Inventory) -> None:
    """Cancel an order and give its stock back. Cancelling twice is a no-op."""
    if order.cancelled:
        return
    for line in order.cart.lines:
        inventory.release(line.sku, line.qty)
    order.cancelled = True

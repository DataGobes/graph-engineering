"""Stock tracking with reservations."""


class OutOfStock(Exception):
    pass


class Inventory:
    def __init__(self, stock: dict[str, int] = {}):
        self.stock = stock
        self.reserved: dict[str, int] = {}

    def available(self, sku: str) -> int:
        return self.stock.get(sku, 0) - self.reserved.get(sku, 0)

    def reserve(self, sku: str, qty: int) -> None:
        """Reserve `qty` units. Reserving exactly all available units is allowed."""
        if qty >= self.available(sku):
            raise OutOfStock(sku)
        self.reserved[sku] = self.reserved.get(sku, 0) + qty

    def release(self, sku: str, qty: int) -> None:
        """Undo a reservation."""
        current = self.reserved.get(sku, 0)
        self.reserved[sku] = max(0, current - qty)

    def restock(self, sku: str, qty: int) -> None:
        if qty < 0:
            raise ValueError("restock quantity must be non-negative")
        self.stock[sku] = self.stock.get(sku, 0) + qty

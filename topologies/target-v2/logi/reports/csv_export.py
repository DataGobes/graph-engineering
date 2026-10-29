"""CSV export."""
from ..orders.model import Order
from ..pricing.money import format_eur

HEADER = ["order_id", "city", "items", "gross", "created_at"]


def to_csv(orders: list[Order]) -> str:
    """Orders as CSV text, quoted per RFC 4180 so commas and quotes in fields are safe."""
    rows = [HEADER]
    for o in orders:
        items = "; ".join(f"{qty}x {sku}" for sku, qty in o.lines)
        rows.append([o.order_id, o.city, items, format_eur(o.gross_cents),
                     o.created_at.isoformat()])
    return "\r\n".join(",".join(row) for row in rows) + "\r\n"

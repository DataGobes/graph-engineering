"""Sanity check: every seeded bug really misbehaves. Run: python prove_bugs.py"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "target"))
from shop import money, utils  # noqa: E402
from shop.cart import Cart, Line  # noqa: E402
from shop.discounts import Discount, best_discount  # noqa: E402
from shop.inventory import Inventory, OutOfStock  # noqa: E402
from shop.orders import place_order  # noqa: E402

checks = {}
checks["B01"] = money.to_cents(19.99) != 1999 or money.to_cents(0.29) != 29
checks["B02"] = sum(money.split_evenly(100, 3)) != 100
a = Inventory(); a.restock("X", 1)
checks["B03"] = Inventory().available("X") == 1
inv = Inventory({"A": 2})
try:
    inv.reserve("A", 2); checks["B04"] = False
except OutOfStock:
    checks["B04"] = True
c = Cart()
c.lines = [Line("A", 1, 1), Line("A", 1, 1), Line("B", 1, 1)]
c.remove_sku("A")
checks["B05"] = any(line.sku == "A" for line in c.lines)
d = Discount("X", 10, date(2026, 1, 31))
checks["B06"] = not d.is_valid(date(2026, 1, 31))
ds = [Discount("A", 10, date(2030, 1, 1)), Discount("B", 20, date(2030, 1, 1))]
checks["B07"] = best_discount(1000, ds, date(2026, 1, 1)) != 800
try:
    utils.parse_qty("0"); checks["B08"] = True
except ValueError:
    checks["B08"] = False
cart = Cart(); cart.add("A", 100, 1)
try:
    place_order("o1", cart, Inventory({"A": 5}), [], date(2026, 1, 1)); checks["B09"] = False
except Exception:
    checks["B09"] = True
# B10 needs B09 fixed to show itself; simulate the intended call order.
inv2 = Inventory({"A": 5, "B": 0})
try:
    for sku, qty in [("A", 1), ("B", 1)]:
        inv2.reserve(sku, qty)
except OutOfStock:
    pass
checks["B10"] = inv2.reserved.get("A", 0) == 1

for bug, broken in checks.items():
    print(bug, "reproduced" if broken else "NOT reproduced")
sys.exit(0 if all(checks.values()) else 1)

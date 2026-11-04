"""Sanity check for target-v2: every seeded bug misbehaves on its own path.

Each check runs from a clean repository and touches only its own bug, so no bug
hides another (the problem run 1 hit with B09 and B10). Run: python prove_bugs_v2.py
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "target-v2"))
from logi.catalog import search  # noqa: E402
from logi.orders import repo, service  # noqa: E402
from logi.orders.model import Order  # noqa: E402
from logi.pricing import quote  # noqa: E402
from logi.pricing.discounts import BasketDiscount  # noqa: E402
from logi.reports import csv_export, daily, listing  # noqa: E402
from logi.shipping import eta, label, rates  # noqa: E402
from logi.util import retry, timeutil  # noqa: E402


def order(oid, gross, city="amsterdam"):
    return Order(oid, city, [("MUG", 1)], gross, datetime(2026, 10, 29, 12, tzinfo=timezone.utc))


def raises(fn, exc=Exception):
    try:
        fn()
    except exc:
        return True
    return False


def l1():  # Saturday to Monday: Sunday and Monday are after start, Monday is a business day
    return timeutil.business_days_between(date(2026, 10, 31), date(2026, 11, 2)) != 1


def l2():
    calls = []

    @retry.retry(attempts=2)
    def flaky():
        calls.append(1)
        if len(calls) < 2:
            raise RuntimeError("first call fails")
        return "ok"
    return raises(flaky) or len(calls) != 2


def l3():
    from logi.catalog.products import get
    results = [get("LAMP"), get("DESK"), get("MUG"), get("KETTLE")]
    original = search.search
    search.search = lambda q, limit=10: results  # pin first-found order
    try:
        return search.search_many(["anything"]) != results
    finally:
        search.search = original


def l4():
    return BasketDiscount(10, 5000).discounted(5000) == 5000


def l5():
    repo.clear()
    return raises(lambda: daily.daily_summary(date(2026, 10, 29)), ZeroDivisionError)


def l6():
    text = csv_export.to_csv([order("ORD-1", 100, city="paris, france")])
    return text.splitlines()[1].count(",") != 4


def x1():
    q = quote.price_quote([("KETTLE", 1)], "NL")
    return q.gross_cents != 3999 + round(3999 * 21 / 100)


def x2():
    return raises(lambda: label.make_label("ORD-1", "amsterdam", [("KETTLE", 1)]), rates.FreightRequired)


def x3():
    return raises(lambda: eta.estimate_delivery(date(2026, 10, 29), "amsterdam"), ValueError)


def x4():
    repo.clear()
    return raises(lambda: service.create_order("atlantis", [("MUG", 1)]), TypeError)


def x5():
    repo.clear()
    repo.add(order("ORD-1", 100))
    return listing.first_page() == []


def x6():
    repo.clear()
    repo.add(order("ORD-1", 100))
    repo.add(order("ORD-2", 500))
    listing.biggest_orders()
    return [o.order_id for o in repo.all_orders()] != ["ORD-1", "ORD-2"]


checks = {f.__name__.upper(): f() for f in [l1, l2, l3, l4, l5, l6, x1, x2, x3, x4, x5, x6]}
for bug, broken in checks.items():
    print(bug, "reproduced" if broken else "NOT reproduced")
sys.exit(0 if all(checks.values()) else 1)

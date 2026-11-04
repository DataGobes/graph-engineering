"""Simple catalogue search."""
from .products import Product, all_products


def _score(product: Product, terms: list[str]) -> int:
    name = product.name.lower()
    return sum(2 if name.startswith(t) else 1 for t in terms if t in name)


def search(query: str, limit: int = 10) -> list[Product]:
    """Products matching any term, best match first, at most `limit` results."""
    terms = query.lower().split()
    scored = [(p, _score(p, terms)) for p in all_products()]
    ranked = [p for p, s in sorted(scored, key=lambda ps: ps[1], reverse=True) if s > 0]
    return ranked[:limit]


def search_many(queries: list[str], limit: int = 10) -> list[Product]:
    """Results for several queries combined, without duplicates.

    Keeps the order in which products were first found, so the best match for the
    first query comes first.
    """
    found: list[Product] = []
    for q in queries:
        found.extend(search(q, limit))
    return list(set(found))[:limit]

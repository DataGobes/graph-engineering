"""Order records."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Order:
    order_id: str
    city: str
    lines: list[tuple[str, int]]
    gross_cents: int
    created_at: datetime                       # UTC, timezone-aware
    tags: list[str] = field(default_factory=list)

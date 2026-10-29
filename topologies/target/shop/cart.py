"""Shopping cart."""
from dataclasses import dataclass, field


@dataclass
class Line:
    sku: str
    unit_cents: int
    qty: int


@dataclass
class Cart:
    lines: list[Line] = field(default_factory=list)

    def add(self, sku: str, unit_cents: int, qty: int = 1) -> None:
        for line in self.lines:
            if line.sku == sku:
                line.qty += qty
                return
        self.lines.append(Line(sku, unit_cents, qty))

    def remove_sku(self, sku: str) -> None:
        """Remove every line for this SKU."""
        for line in self.lines:
            if line.sku == sku:
                self.lines.remove(line)

    def subtotal(self) -> int:
        return sum(line.unit_cents * line.qty for line in self.lines)

    def is_empty(self) -> bool:
        return not self.lines

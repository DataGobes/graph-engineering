"""Read markdown stories from a folder. Other sources (GitHub Issues) can return the same Story."""

import re
from dataclasses import dataclass, field
from itertools import pairwise

from specgraph.config import Config


@dataclass
class Story:
    id: str
    title: str
    path: str  # relative to the repo
    order: int
    depends_on: list[str] = field(default_factory=list)


_FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_DEPS = re.compile(r"^depends_on:\s*\[?([^\]\n]*)\]?\s*$", re.MULTILINE)


def _frontmatter_deps(text: str) -> list[str] | None:
    m = _FRONT.match(text)
    if not m:
        return None
    d = _DEPS.search(m.group(1))
    if not d:
        return None
    return [s.strip().strip("'\"") for s in d.group(1).split(",") if s.strip()]


def _title(text: str, fallback: str) -> str:
    for line in _FRONT.sub("", text).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def read_markdown(cfg: Config) -> list[Story]:
    paths = sorted(cfg.repo.glob(cfg.stories))
    pattern = re.compile(cfg.id_pattern)
    out: list[Story] = []
    for i, p in enumerate(paths):
        m = pattern.search(p.stem)
        if not m:
            raise ValueError(f"{p.name}: no story id matches {cfg.id_pattern!r}")
        text = p.read_text()
        sid = m.group(1)
        deps = _frontmatter_deps(text)
        if deps is None:
            deps = list(cfg.depends_on.get(sid, []))
        out.append(Story(sid, _title(text, sid), str(p.relative_to(cfg.repo)), i, deps))
    ids = [s.id for s in out]
    dupes = {x for x in ids if ids.count(x) > 1}
    if dupes:
        raise ValueError(f"duplicate story ids: {sorted(dupes)}")
    return out


def apply_default_order(stories: list[Story]) -> bool:
    """With no dependencies anywhere, chain stories in file order. Returns True when it did."""
    if any(s.depends_on for s in stories):
        return False
    for prev, cur in pairwise(stories):
        cur.depends_on = [prev.id]
    return True

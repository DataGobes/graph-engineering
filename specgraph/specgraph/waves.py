"""Turn story dependencies into waves: each wave holds stories whose dependencies are all in earlier waves."""

from specgraph.stories import Story


def layers(stories: list[Story]) -> list[list[Story]]:
    by_id = {s.id: s for s in stories}
    for s in stories:
        missing = [d for d in s.depends_on if d not in by_id]
        if missing:
            raise ValueError(f"{s.id} depends on unknown stories: {missing}")
    done: set[str] = set()
    left = sorted(stories, key=lambda s: s.order)
    out: list[list[Story]] = []
    while left:
        ready = [s for s in left if set(s.depends_on) <= done]
        if not ready:
            raise ValueError(f"dependency cycle among: {[s.id for s in left]}")
        out.append(ready)
        done |= {s.id for s in ready}
        left = [s for s in left if s.id not in done]
    return out


def waves(stories: list[Story], max_parallel: int) -> list[list[Story]]:
    """Layers, each split into chunks of at most max_parallel stories."""
    if max_parallel < 1:
        raise ValueError("max_parallel must be at least 1")
    out: list[list[Story]] = []
    for layer in layers(stories):
        out.extend(layer[i : i + max_parallel] for i in range(0, len(layer), max_parallel))
    return out

"""Project config: everything project-specific lives in <repo>/.specgraph/config.json."""

import json
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = ".specgraph/config.json"


@dataclass
class Config:
    repo: Path
    stories: str
    id_pattern: str = r"^([A-Z]+-\d+)"
    context: list[str] = field(default_factory=list)
    specs_dir: str = "specs"
    base_branch: str = "main"
    integration_branch: str = "specgraph"
    worktree_dir: str = ""
    setup: list[str] = field(default_factory=list)
    check: list[str] = field(default_factory=list)
    depends_on: dict[str, list[str]] = field(default_factory=dict)
    max_parallel: int = 2
    max_fix_rounds: int = 2

    @property
    def worktrees(self) -> Path:
        if self.worktree_dir:
            return (self.repo / self.worktree_dir).resolve()
        return self.repo.parent / f"{self.repo.name}-specgraph-wt"


def load(repo: str | Path) -> Config:
    repo = Path(repo).resolve()
    path = repo / CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"no {CONFIG_PATH} in {repo}")
    raw = json.loads(path.read_text())
    known = set(Config.__dataclass_fields__) - {"repo"}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"unknown config keys: {sorted(unknown)}")
    if "stories" not in raw:
        raise ValueError("config needs 'stories', a glob relative to the repo")
    return Config(repo=repo, **raw)

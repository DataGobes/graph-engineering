"""Per-story state in <specs_dir>/<id>/status.json. The repo is the checkpoint."""

import json
from pathlib import Path

from specgraph.config import Config

# new -> awaiting_answers -> answered -> passed -> merged; escalated when the fix loop runs out.
PHASES = ["new", "awaiting_answers", "answered", "passed", "merged", "escalated"]


def story_dir(cfg: Config, sid: str, root: Path | None = None) -> Path:
    return (root or cfg.repo) / cfg.specs_dir / sid


def read(cfg: Config, sid: str) -> dict:
    p = story_dir(cfg, sid) / "status.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"id": sid, "phase": "new", "rounds": 0, "runs": []}


def write(cfg: Config, sid: str, status: dict) -> None:
    if status["phase"] not in PHASES:
        raise ValueError(f"unknown phase {status['phase']!r}")
    d = story_dir(cfg, sid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "status.json").write_text(json.dumps(status, indent=2) + "\n")


def answers_filled(cfg: Config, sid: str) -> bool:
    """The PO gate is open once answers.md exists and every blocking question has an answer."""
    p = story_dir(cfg, sid) / "answers.md"
    return p.exists() and "TODO" not in p.read_text()

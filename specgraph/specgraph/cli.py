"""specgraph: plan waves, print the next workflow input, record workflow results.

    python -m specgraph plan   <repo>                 show the waves and each story's phase
    python -m specgraph next   <repo> [--only ID ...] [--prepare]
    python -m specgraph record <repo> <result.json> [--tokens N]

The workflows do the thinking; this tool does the bookkeeping, so it stays deterministic and testable.
"""

import argparse
import json
import subprocess
import sys

from specgraph import config, status
from specgraph.stories import Story, apply_default_order, read_markdown
from specgraph.waves import waves


def _git(cfg: config.Config, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cfg.repo), *args], check=check, capture_output=True, text=True)


def _branch_exists(cfg: config.Config, name: str) -> bool:
    return _git(cfg, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}", check=False).returncode == 0


def wave_branch(cfg: config.Config, n: int) -> str:
    return f"{cfg.integration_branch}-w{n}"


def _wave_landed(cfg: config.Config, n: int) -> bool:
    """A wave is done once its branch is merged into the integration branch."""
    b = wave_branch(cfg, n)
    if not (_branch_exists(cfg, b) and _branch_exists(cfg, cfg.integration_branch)):
        return False
    return _git(cfg, "merge-base", "--is-ancestor", b, cfg.integration_branch, check=False).returncode == 0


def load_plan(repo: str) -> tuple[config.Config, list[list[Story]], bool]:
    cfg = config.load(repo)
    stories = read_markdown(cfg)
    chained = apply_default_order(stories)
    return cfg, waves(stories, cfg.max_parallel), chained


def _story_arg(s: Story) -> dict:
    return {"id": s.id, "title": s.title, "path": s.path, "depends_on": s.depends_on}


def next_action(repo: str, only: list[str] | None = None) -> dict:
    cfg, plan, _ = load_plan(repo)
    for n, wave in enumerate(plan, start=1):
        picked = [s for s in wave if not only or s.id in only]
        if not picked:
            continue
        st = {s.id: status.read(cfg, s.id) for s in picked}
        phase = {sid: x["phase"] for sid, x in st.items()}
        if all(p in ("passed", "merged") for p in phase.values()) and _wave_landed(cfg, n):
            continue
        base = {
            "wave": n,
            "wave_branch": wave_branch(cfg, n),
            "repo": str(cfg.repo),
            "specs_dir": cfg.specs_dir,
            "context": cfg.context,
        }
        stuck = [sid for sid, p in phase.items() if p == "escalated"]
        if stuck:
            return {"action": "escalated", "stories": stuck, **base}
        new = [s for s in picked if phase[s.id] == "new"]
        if new:
            return {
                "action": "run",
                "workflow": "specgraph-front",
                "args": {**base, "stories": [_story_arg(s) for s in new]},
            }
        waiting = [s.id for s in picked if phase[s.id] == "awaiting_answers" and not status.answers_filled(cfg, s.id)]
        if waiting:
            files = [f"{cfg.specs_dir}/{sid}/questions.md" for sid in waiting]
            return {"action": "await_answers", "stories": waiting, "questions": files, **base}
        todo = [s for s in picked if phase[s.id] in ("awaiting_answers", "answered")]
        if todo:
            args = {
                **base,
                "integration_branch": cfg.integration_branch,
                "worktrees": str(cfg.worktrees),
                "setup": cfg.setup,
                "check": cfg.check,
                "max_fix_rounds": cfg.max_fix_rounds,
                "stories": [_story_arg(s) for s in todo],
            }
            return {"action": "run", "workflow": "specgraph-back", "args": args}
        return {"action": "open_pr", "head": wave_branch(cfg, n), "base_branch": cfg.integration_branch, **base}
    return {"action": "done"}


def prepare(repo: str, wave: int) -> None:
    """Make sure the integration and wave branches exist and the wave branch is checked out."""
    cfg = config.load(repo)
    if not _branch_exists(cfg, cfg.integration_branch):
        _git(cfg, "branch", cfg.integration_branch, cfg.base_branch)
    b = wave_branch(cfg, wave)
    if not _branch_exists(cfg, b):
        _git(cfg, "branch", b, cfg.integration_branch)
    _git(cfg, "checkout", "-q", b)


def record(repo: str, result: dict, tokens: int | None = None) -> list[str]:
    """Fold a workflow's return value into status.json files and commit them on the wave branch."""
    cfg = config.load(repo)
    kind = result["kind"]
    touched = []
    for r in result["stories"]:
        sid = r["id"]
        st = status.read(cfg, sid)
        run = {"kind": kind, "wave": result.get("wave")}
        if kind == "front":
            st["phase"] = "awaiting_answers" if r.get("blocking_questions", 0) else "answered"
            run["questions"] = {"blocking": r.get("blocking_questions", 0), "other": r.get("other_questions", 0)}
        elif kind == "back":
            st["phase"] = "passed" if r.get("passed") else "escalated"
            st["rounds"] = r.get("rounds", 0)
            st["criteria"] = r.get("criteria", [])
            run["merged"] = bool(r.get("merged"))
        else:
            raise ValueError(f"unknown result kind {kind!r}")
        st["runs"].append(run)
        status.write(cfg, sid, st)
        touched.append(sid)
    if tokens is not None:
        share = tokens // max(1, len(touched))
        for sid in touched:
            st = status.read(cfg, sid)
            st["runs"][-1]["tokens"] = share
            st["tokens"] = st.get("tokens", 0) + share
            status.write(cfg, sid, st)
    paths = [f"{cfg.specs_dir}/{sid}" for sid in touched]
    _git(cfg, "add", *paths)
    if _git(cfg, "diff", "--cached", "--quiet", check=False).returncode:
        _git(cfg, "commit", "-q", "-m", f"specgraph: record {kind} for {', '.join(touched)}")
    return touched


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="specgraph")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("repo")
    p = sub.add_parser("next")
    p.add_argument("repo")
    p.add_argument("--only", nargs="*")
    p.add_argument("--prepare", action="store_true", help="create and check out the wave branch")
    p = sub.add_parser("record")
    p.add_argument("repo")
    p.add_argument("result")
    p.add_argument("--tokens", type=int)
    a = ap.parse_args(argv)

    try:
        if a.cmd == "plan":
            cfg, plan, chained = load_plan(a.repo)
            if chained:
                print("no dependencies declared: running stories one at a time in file order")
            for n, wave in enumerate(plan, start=1):
                cells = [f"{s.id} [{status.read(cfg, s.id)['phase']}]" for s in wave]
                print(f"wave {n}: {', '.join(cells)}")
        elif a.cmd == "next":
            act = next_action(a.repo, a.only)
            if a.prepare and act.get("action") == "run":
                prepare(a.repo, act["args"]["wave"])
            print(json.dumps(act, indent=2))
        elif a.cmd == "record":
            with open(a.result) as f:
                print("recorded:", ", ".join(record(a.repo, json.load(f), a.tokens)))
    except (FileNotFoundError, ValueError, subprocess.CalledProcessError) as e:
        print(f"specgraph: {e}", file=sys.stderr)
        return 2
    return 0

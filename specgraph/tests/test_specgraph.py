import json
import subprocess

import pytest

from specgraph import cli, config, status
from specgraph.stories import apply_default_order, read_markdown
from specgraph.waves import waves


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    (r / "backlog").mkdir(parents=True)
    (r / ".specgraph").mkdir()
    for sid, title in [("S-1", "One"), ("S-2", "Two"), ("S-3", "Three"), ("S-4", "Four")]:
        (r / "backlog" / f"{sid}-x.md").write_text(f"# {sid} {title}\n\nBody.\n")
    cfg = {"stories": "backlog/S-*.md", "depends_on": {"S-3": ["S-1", "S-2"], "S-4": ["S-3"]}, "max_parallel": 2}
    (r / ".specgraph/config.json").write_text(json.dumps(cfg))
    git(r, "init", "-q", "-b", "main")
    git(r, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    git(r, "add", ".")
    git(r, "commit", "-q", "-m", "stories")
    return r


def ids(plan):
    return [[s.id for s in w] for w in plan]


def test_waves_from_config(repo):
    cfg = config.load(repo)
    assert ids(waves(read_markdown(cfg), cfg.max_parallel)) == [["S-1", "S-2"], ["S-3"], ["S-4"]]


def test_max_parallel_splits_a_layer(repo):
    cfg = config.load(repo)
    assert ids(waves(read_markdown(cfg), 1)) == [["S-1"], ["S-2"], ["S-3"], ["S-4"]]


def test_frontmatter_wins_over_config(repo):
    (repo / "backlog/S-4-x.md").write_text("---\ndepends_on: [S-1]\n---\n# S-4 Four\n")
    cfg = config.load(repo)
    stories = read_markdown(cfg)
    assert stories[3].title == "S-4 Four"
    assert ids(waves(stories, 2)) == [["S-1", "S-2"], ["S-3", "S-4"]]


def test_no_dependencies_chains_in_file_order(repo):
    (repo / ".specgraph/config.json").write_text(json.dumps({"stories": "backlog/S-*.md"}))
    stories = read_markdown(config.load(repo))
    assert apply_default_order(stories)
    assert ids(waves(stories, 2)) == [["S-1"], ["S-2"], ["S-3"], ["S-4"]]


@pytest.mark.parametrize(
    "deps, msg",
    [({"S-1": ["S-9"]}, "unknown"), ({"S-1": ["S-2"], "S-2": ["S-1"]}, "cycle")],
)
def test_bad_dependencies(repo, deps, msg):
    (repo / ".specgraph/config.json").write_text(json.dumps({"stories": "backlog/S-*.md", "depends_on": deps}))
    with pytest.raises(ValueError, match=msg):
        waves(read_markdown(config.load(repo)), 2)


def test_unknown_config_key(repo):
    (repo / ".specgraph/config.json").write_text(json.dumps({"stories": "x", "stories_glob": "y"}))
    with pytest.raises(ValueError, match="unknown config keys"):
        config.load(repo)


def write_result(tmp_path, result):
    p = tmp_path / "result.json"
    p.write_text(json.dumps(result))
    return str(p)


def test_full_cycle_for_one_story(repo, tmp_path):
    r = str(repo)
    act = cli.next_action(r, only=["S-1"])
    assert act["action"] == "run" and act["workflow"] == "specgraph-front"
    assert [s["id"] for s in act["args"]["stories"]] == ["S-1"]

    cli.prepare(r, 1)
    cfg = config.load(repo)
    sd = status.story_dir(cfg, "S-1")
    sd.mkdir(parents=True)
    (sd / "questions.md").write_text("1. Which zone? (blocking)\n")
    cli.record(r, {"kind": "front", "wave": 1, "stories": [{"id": "S-1", "blocking_questions": 1}]}, tokens=1000)
    assert cli.next_action(r, only=["S-1"])["action"] == "await_answers"

    (sd / "answers.md").write_text("1. TODO\n")
    assert cli.next_action(r, only=["S-1"])["action"] == "await_answers"
    (sd / "answers.md").write_text("1. DE-LU\n")
    act = cli.next_action(r, only=["S-1"])
    assert act["workflow"] == "specgraph-back" and act["args"]["wave_branch"] == "specgraph-w1"

    back = {"kind": "back", "wave": 1, "stories": [{"id": "S-1", "passed": True, "rounds": 1, "merged": True}]}
    cli.record(r, back, tokens=5000)
    st = status.read(cfg, "S-1")
    assert st["phase"] == "passed" and st["tokens"] == 6000 and len(st["runs"]) == 2
    assert cli.next_action(r, only=["S-1"])["action"] == "open_pr"

    git(repo, "checkout", "-q", "specgraph")
    git(repo, "merge", "-q", "--ff-only", "specgraph-w1")
    assert cli.next_action(r, only=["S-1"])["action"] == "done"
    # Without the filter, S-2 in the same wave is still new.
    assert cli.next_action(r)["args"]["stories"][0]["id"] == "S-2"


def test_story_without_blocking_questions_skips_the_gate(repo):
    r = str(repo)
    cli.prepare(r, 1)
    cli.record(r, {"kind": "front", "wave": 1, "stories": [{"id": "S-1", "blocking_questions": 0}]})
    assert cli.next_action(r, only=["S-1"])["workflow"] == "specgraph-back"


def test_failed_check_escalates(repo):
    r = str(repo)
    cli.prepare(r, 1)
    cli.record(r, {"kind": "back", "wave": 1, "stories": [{"id": "S-1", "passed": False, "rounds": 2}]})
    assert cli.next_action(r, only=["S-1"])["action"] == "escalated"


def test_cli_plan_output(repo, capsys):
    assert cli.main(["plan", str(repo)]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "wave 1: S-1 [new], S-2 [new]"
    assert cli.main(["plan", str(repo / "nope")]) == 2

"""Score a topology's findings against the seeded bugs.

Findings file: JSON list of {"file": "shop/x.py", "line": 12, "description": "..."}.
A finding matches the nearest still-unmatched bug in the same file with an anchor line
within TOLERANCE (a bug can list several anchors, e.g. caller and call site). Each bug can be matched once; extra hits on an already-matched
bug are duplicates (not false positives). Hits near a neutral item are ignored; hits on a\nbonus item (a real bug we did not plant) are reported separately.

Line matching is coarse: B09 and B10 sit on adjacent lines. An LLM-judge pass that
also reads the description is planned once the runs use the API.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parent
TOLERANCE = 2


def anchor_line(target: str, file: str, anchor: str) -> int:
    lines = (ROOT / target / file).read_text().splitlines()
    hits = [i + 1 for i, text in enumerate(lines) if anchor in text]
    if len(hits) != 1:
        raise ValueError(f"anchor {anchor!r} in {file} matched {len(hits)} lines")
    return hits[0]


def load_truth(truth_file: str = "ground_truth.json"):
    """Bugs and neutral items, each with `lines`: the lines of all its anchors."""
    data = json.loads((ROOT / truth_file).read_text())
    target = data.get("target", "target")
    for item in data["bugs"] + data["neutral"]:
        anchors = item.get("anchors") or [item["anchor"]]
        item["lines"] = [anchor_line(target, item["file"], a) for a in anchors]
    for item in data.get("bonus", []):
        item["lines"] = [anchor_line(target, item["file"], a) for a in item["anchors"]]
    return data["bugs"], data["neutral"], data.get("bonus", [])


def distance(finding, item) -> int:
    return min(abs(int(finding["line"]) - line) for line in item["lines"])


def same_file(reported: str, truth: str) -> bool:
    """Agents sometimes drop the package folder (geo/zones.py for logi/geo/zones.py)."""
    a, b = reported.strip("/").split("/"), truth.split("/")
    return a == b[-len(a):] if len(a) <= len(b) else False


def near(finding, item) -> bool:
    return same_file(finding["file"], item["file"]) and distance(finding, item) <= TOLERANCE


def score(findings: list[dict], truth_file: str = "ground_truth.json") -> dict:
    bugs, neutral, bonus = load_truth(truth_file)
    found, duplicates, false_positives, bonus_found = {}, 0, [], set()
    for f in findings:
        candidates = sorted((b for b in bugs if near(f, b)), key=lambda b: distance(f, b))
        bug = next((b for b in candidates if b["id"] not in found), None)
        if bug:
            found[bug["id"]] = f
        elif candidates:
            duplicates += 1
        elif extra := next((b for b in bonus if near(f, b)), None):
            bonus_found.add(extra["id"])
        elif not any(near(f, n) for n in neutral):
            false_positives.append(f)
    tp = len(found)
    reported = tp + len(false_positives)
    return {
        "found": sorted(found),
        "missed": sorted(b["id"] for b in bugs if b["id"] not in found),
        "recall": round(tp / len(bugs), 2),
        "precision": round(tp / reported, 2) if reported else 0.0,
        "false_positives": false_positives,
        "duplicates": duplicates,
        "bonus_found": sorted(bonus_found),
        "cross_file_found": sum(1 for b in bugs if b["kind"] == "cross-file" and b["id"] in found),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("findings")
    parser.add_argument("--truth", default="ground_truth.json")
    args = parser.parse_args()
    print(json.dumps(score(json.loads(Path(args.findings).read_text()), args.truth), indent=2))

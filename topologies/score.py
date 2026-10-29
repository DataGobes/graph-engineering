"""Score a topology's findings against the seeded bugs.

Findings file: JSON list of {"file": "shop/x.py", "line": 12, "description": "..."}.
A finding matches the nearest still-unmatched bug in the same file whose anchor line
is within TOLERANCE. Each bug can be matched once; extra hits on an already-matched
bug are duplicates (not false positives). Hits near a neutral item are ignored.

Line matching is coarse: B09 and B10 sit on adjacent lines. An LLM-judge pass that
also reads the description is planned once the runs use the API.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
TOLERANCE = 2


def anchor_line(file: str, anchor: str) -> int:
    lines = (ROOT / "target" / file).read_text().splitlines()
    hits = [i + 1 for i, text in enumerate(lines) if anchor in text]
    if len(hits) != 1:
        raise ValueError(f"anchor {anchor!r} in {file} matched {len(hits)} lines")
    return hits[0]


def load_truth():
    data = json.loads((ROOT / "ground_truth.json").read_text())
    for item in data["bugs"] + data["neutral"]:
        item["line"] = anchor_line(item["file"], item["anchor"])
    return data["bugs"], data["neutral"]


def near(finding, item) -> bool:
    return finding["file"] == item["file"] and abs(int(finding["line"]) - item["line"]) <= TOLERANCE


def score(findings: list[dict]) -> dict:
    bugs, neutral = load_truth()
    found, duplicates, false_positives = {}, 0, []
    for f in findings:
        candidates = sorted((b for b in bugs if near(f, b)), key=lambda b: abs(int(f["line"]) - b["line"]))
        bug = next((b for b in candidates if b["id"] not in found), None)
        if bug:
            found[bug["id"]] = f
        elif candidates:
            duplicates += 1
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
        "cross_file_found": sum(1 for b in bugs if b["kind"] == "cross-file" and b["id"] in found),
    }


if __name__ == "__main__":
    print(json.dumps(score(json.loads(Path(sys.argv[1]).read_text())), indent=2))

"""Save a workflow run's output and score it.

python collect.py <workflow .output file> <results/run2/topo1-r1.json> [--truth ground_truth_v2.json]
Prints one summary line; the saved file holds findings, verdicts, usage and the score.
"""
import argparse
import json
from pathlib import Path

from score import score


def summarize(raw: dict) -> dict:
    agents = [p for p in raw.get("workflowProgress", []) if p.get("type") == "workflow_agent"]
    start = min((a["queuedAt"] for a in agents), default=0)
    end = max((a.get("lastProgressAt", 0) for a in agents), default=0)
    return {"agents": raw.get("agentCount"), "tokens": raw.get("totalTokens"),
            "wall_clock_s": round((end - start) / 1000, 1)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("dest")
    parser.add_argument("--truth", default="ground_truth_v2.json")
    args = parser.parse_args()
    raw = json.loads(Path(args.output).read_text())
    result = raw["result"]
    findings = [{k: f[k] for k in ("file", "line", "description")} for f in result["findings"]]
    scored = score(findings, args.truth)
    record = {**result, "usage": summarize(raw), "score": scored}
    dest = Path(args.dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=2))
    u = record["usage"]
    print(f"{dest.stem}: found {len(scored['found'])}/{len(scored['found']) + len(scored['missed'])} missed={scored['missed']} "
          f"bonus={scored['bonus_found']} fp={len(scored['false_positives'])} tokens={u['tokens']} wall={u['wall_clock_s']}s")

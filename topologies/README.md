# Same task, three topologies

One task, three agent graphs, measured side by side.

**Task:** find the bugs in `target/shop/`, a 6-file Python shop library with 10 planted bugs
(8 local to one file, 2 that only show up when you read two files together) and a few
correct-but-suspicious decoys.

| Topology | Shape | Hypothesis |
| --- | --- | --- |
| 1. Single agent | one agent loops over the repo | cheapest; misses more as context fills |
| 2. Fan-out / fan-in | one agent per file, one combiner | best on local bugs; blind to cross-file bugs |
| 3. Pipeline + verify | find per file, then an independent verifier per finding | highest precision; most tokens |

## Files

- `target/shop/` the code under review (no hints in it)
- `ground_truth.json` the seeded bugs, located by an anchor snippet rather than a line number
- `prove_bugs.py` shows every seeded bug really misbehaves: `python prove_bugs.py`
- `score.py` scores a findings file: `python score.py findings.json`
  (recall, precision, false positives, duplicates, cross-file bugs found)

Findings format: `[{"file": "shop/money.py", "line": 6, "description": "..."}]`

## Status

Done: target repo, ground truth, scorer. Next: the three topologies in LangGraph and as
Claude Code workflows, then the comparison run.

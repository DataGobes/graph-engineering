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

## The three graphs

Each topology exists twice, with identical prompts:

- **Claude Code workflows** in `.claude/workflows/` (`topo1-single.js`, `topo2-fanout.js`,
  `topo3-verify.js`). Each node is a full agent with tools. Runs on a Claude plan, no API key.
- **LangGraph** in `topologies/langgraph/graphs.py`. Each node is one model call with the code
  pasted in. Needs `ANTHROPIC_API_KEY`. `test_graphs.py` checks the wiring offline.

Controlled variables: same reviewer prompt in topologies 2 and 3 (so verification is the only
difference between them), same model, same output schema. Per-file reviewers see only their file.

## Running

Claude Code (in this repo):

1. Copy the package somewhere neutral so agents can't read the answer key:
   `cp -r topologies/target/shop /tmp/review/shop`
2. Run each saved workflow with `args`:
   `/topo1-single` with `{"root": "/tmp/review/shop"}`;
   `/topo2-fanout` and `/topo3-verify` with
   `{"root": "/tmp/review/shop", "files": ["cart.py", "discounts.py", "inventory.py", "money.py", "orders.py", "utils.py"]}`
3. Save each run's `findings` to `results/<topology>.json` and score it with `score.py`.

LangGraph: `pip install -r topologies/langgraph/requirements.txt`, then
`python topologies/langgraph/graphs.py fanout > fanout.json && python topologies/score.py fanout.json`.

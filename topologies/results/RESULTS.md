# Run 1 results (2026-10-29)

Claude Code workflows, one run each, all three started at the same time on the same model.

| Topology | Agents | Bugs found | Precision | Subagent tokens | Wall clock |
| --- | --- | --- | --- | --- | --- |
| 1. Single agent | 1 | 10 / 10 | 100% | 56k (1x) | 17 s |
| 2. Fan-out / fan-in | 7 | 10 / 10 | 100% | 370k (6.6x) | 39 s |
| 3. Pipeline + verify | 16 | 9 / 10 | 100% | 862k (15.4x) | 108 s |

Raw findings and verdicts: `topo1-single.json`, `topo2-fanout.json`, `topo3-verify.json`.

## What we learned

1. **The single agent won because the whole repo fits in one context.** Six small files is
   below the size where splitting the work pays off. More nodes bought nothing but cost.
2. **Per-file isolation did not blind the reviewers.** The orders.py reviewer caught the
   swapped `reserve()` arguments without opening inventory.py, by comparing it with the
   `release(sku, qty)` call a few lines lower. The "cross-file" bugs leaked local clues.
   That is a flaw in the test bed, not a strength of fan-out.
3. **The verifier killed a real bug.** B09 (swapped arguments) makes B10 (no rollback)
   unreachable today, so the skeptic correctly showed B10 "cannot happen as the code stands"
   and rejected it. Refute-style verifiers judge current reachability, not latent defects:
   a bug masked by another bug gets thrown away.
4. **Cost scales with agent count.** Topology 3 used 15.4x the single agent's tokens, in line
   with the ~15x for multi-agent systems that Anthropic reports.

Caveats: one run per topology (no variance yet); runs shared one concurrency cap, so wall
clock is indicative only; the token figures count subagents only, not orchestration.

## Next run

A test bed where topology should matter: a repo too big for one comfortable context, cross-file
bugs with no local clue, more decoys, three runs per topology, and a verifier told to judge
each finding as if the other bugs were already fixed.

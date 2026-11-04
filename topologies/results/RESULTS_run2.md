# Run 2 results (2026-10-29)

Test bed `target-v2/logi`: 7 sub-packages, 30 files, ~500 lines, 12 planted bugs
(6 local, 6 cross-file). Reviewers in topologies 2 and 3 each see one sub-package.
Three runs per topology, all on the same model. Raw data: `run2/topo*-r*.json`.

| Topology | Agents | Planted bugs found (3 runs) | False alarms | Tokens (avg) | Wall clock (avg) |
| --- | --- | --- | --- | --- | --- |
| 1. Single agent | 1 | 12, 12, 12 | 0, 0, 0 | 62k (1x) | 27 s |
| 2. Fan-out per package | 8 | 10, 10, 10 | 0, 1, 2 | 432k (7.0x) | 58 s |
| 3. Fan-out + verify | 19-21 | 10, 10, 10 | 0, 0, 0 | 1,094k (17.6x) | 150 s |

Bonus: the agents found a real bug I did not plant. `haversine_km` raises
`ValueError: math domain error` for near-antipodal points (rounding pushes `a` above 1).
Topologies 2 and 3 found it in 2 of 3 runs each; the single agent never did. It is
credited separately (`bonus` in `ground_truth_v2.json`), not counted above.

## Which bugs each shape missed

| Bug | Crosses | Single | Fan-out | Fan-out + verify |
| --- | --- | --- | --- | --- |
| X1 VAT fraction vs percent | files, same package | 3/3 | 3/3 | 3/3 |
| X2 grams vs kilograms | files, same package | 3/3 | 3/3 | 3/3 |
| X3 (lat, lon) unpacked swapped | files, same package | 3/3 | 3/3 | 3/3 |
| X4 `locate()` None not handled | packages (orders to geo) | 3/3 | 1/3 | 0/3 |
| X5 page 0 on 1-based pager | packages (reports to orders) | 3/3 | 0/3 | 0/3 |
| X6 sorting the repo's own list | packages (reports to orders) | 3/3 | 2/3 | 3/3 |

## What we learned

1. **The single agent still wins while the code fits comfortably in one context.**
   12/12 every run, no false alarms, at a fraction of the cost.
2. **Isolation costs exactly the bugs that span a unit boundary.** X1 to X3 cross files
   but stay inside one sub-package, so the per-package reviewer saw both sides and caught
   them every time. X4 and X5 need two sub-packages and were missed almost every time.
   The boundary that matters is the review unit, not the file.
3. **Verification buys precision, not recall.** The skeptics removed every false alarm
   (0 in all 3 runs vs up to 2 without) and, with the "judge as if other bugs were fixed"
   instruction, rejected no real bug this time (run 1 lost one to masking). They cannot
   recover a bug no reviewer reported.
4. **Narrow focus finds things breadth misses.** The haversine bug sits in a 10-line
   function every topology read. Only the agents that each looked at 3 files found it.
5. **Cost is roughly linear in agents.** 8 agents cost 7x, ~20 agents cost 17.6x.

Caveats: 3 runs per topology; the three topologies ran at the same time, so wall clock is
indicative only; the token figures count subagents only; one package, one model.

## Next experiment

A fourth topology that keeps fan-out's depth without its blind spot: per-package
reviewers plus one "contract reviewer" that sees only every module's signatures and
docstrings (cheap) and checks each call against them. Then a scale test on a real
repository that does not fit in one context.

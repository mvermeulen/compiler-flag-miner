# `cfm mine` results: 707.ntest_r on `chicago`, 2026-11-19

This is the second intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `707.ntest_r` is
NTest, an Othello engine (C++). niwot's latest mine of it reached `-O3 -march=native -flto -fprofile-use`, +30.95%
([write-up](mining_results.707.ntest_r.2026-10-22.md)), before `-fno-pie -no-pie` was in the catalog. Its corpus
shape is compute-bound at 40.6%, under the 55% gate, the first compute-bound benchmark mined here.

## Headline result

**`-O3 -march=native -fno-pie -no-pie -fprofile-use`, +26.22% over plain `-O3`** (ratio 62.642 → 79.069).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 62.642 | — |
| `-O3 -march=native` | 71.909 | +14.79% |
| `+ -fno-pie -no-pie` | 76.606 | +6.53% |
| `+ -fprofile-use` | 79.069 | +3.22% |

- **`-march=native` gave +14.79%**, close to niwot's +14.97% on the same step.
- **`-fno-pie -no-pie` gave +4.78% alone and +6.53% on top of `-march=native`**, more on top than alone. This is the
  second intrate benchmark of two here where non-PIE is in the winning set (stockfish +1.23% on top).
- **`-flto` gave +3.49% alone but only +0.96% on top of `-march=native -fno-pie -no-pie`**, rejected on CI overlap.
  On niwot, without non-PIE in the catalog, it added +2.32% on top of `-march=native`. Both flags probably remove some
  of the same cost (indirect access to globals and calls between files), so they overlap; the run doesn't show which.
- **PGO added +3.22%**, against +11.31% on niwot (on top of `-march=native -flto` there). It ran without a near-miss
  variant, since no Phase 4 reject was CI-clear above baseline.
- **Fast-math did nothing**: `-Ofast` +0.67%, `-ffast-math` +0.56%, both rejected on CI overlap. Every other flag sat
  within ±0.4%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 707.ntest_r` (uncapped, defaults) |
| Code | `main` at `6da67bc` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 30 |
| Started / finished | 2026-11-19T14:38:09Z / 2026-11-19T22:07:50Z (7h30m) |
| Final status | `converged` |
| Trials | 84 (1373-1456), none skipped, no reruns |
| Candidates screened / confirmed | 15 / 15 |
| Excluded on shape (Phase 2) | `-mprefer-vector-width=256` (`vectorization_density=low`); none on `resource_dominance` (40.6% is under the gate) |
| Fast-tracked (M4) | none: this host's knowledge table had no compute-bound rows yet |
| Accepted in Phase 4 | `-march=native` +14.79%, `-fno-pie -no-pie` +4.78%, `-flto` +3.49% |
| Winning flags | `["-O3", "-march=native", "-fno-pie -no-pie", "-fprofile-use"]`, +26.22% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 43 of 84 timed runs; no reruns; baseline recheck not flagged (+0.18%) |
| Power | package power median 84.99 W on every trial; CPU temperature 89.1-94.5°C |

A trial took about 5.5 minutes, PGO trials included (ntest's training run is short).

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): compute-bound 40.6%, `vectorization_density=low`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 1373 | warm-up | 62.604 |
| 1374 | warm-up | 62.838 |
| 1375 | calibration | 62.439 |
| 1376 | calibration | 62.720 |
| 1377 | calibration | 62.767 |
| 1438 | recheck | 62.758 (+0.18%) |

The calibration mean is 62.642. Warm-up settled after the minimum two reps (663 s). Every `-O3` build had the same
code fingerprint (`c4c7fc32`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1378-1392 | screening | 15 candidates | 62.58-72.02 | | all survived |
| 1393-1395 | confirmation | `-march=native` | 71.909 | +14.79% | **accept** (the greedy start) |
| 1396-1398 | confirmation | `-funroll-loops` | 62.576 | -0.11% | reject |
| 1399-1401 | confirmation | `-Ofast` | 63.061 | +0.67% | reject (CI overlap) |
| 1402-1404 | confirmation | `-ffast-math` | 62.992 | +0.56% | reject (CI overlap) |
| 1405-1407 | confirmation | `-fno-math-errno` | 62.772 | +0.21% | reject |
| 1408-1410 | confirmation | `-flto` | 64.826 | +3.49% | **accept** |
| 1411-1413 | confirmation | `-fno-pie -no-pie` | 65.636 | +4.78% | **accept** |
| 1414-1416 | confirmation | `-fno-stack-protector` | 62.640 | 0.00% | reject |
| 1417-1419 | confirmation | `-fcf-protection=none` | 62.404 | -0.38% | reject |
| 1420-1422 | confirmation | `-U_FORTIFY_SOURCE` | 62.593 | -0.08% | reject |
| 1423-1425 | confirmation | `-fprefetch-loop-arrays` | 62.530 | -0.18% | reject |
| 1426-1428 | confirmation | `-fno-ipa-cp-clone` | 62.739 | +0.15% | reject |
| 1429-1431 | confirmation | `-fno-unswitch-loops` | 62.764 | +0.19% | reject |
| 1432-1434 | confirmation | `-fipa-pta` | 62.795 | +0.24% | reject |
| 1435-1437 | confirmation | `-fgraphite-identity` | 62.575 | -0.11% | reject |
| 1438 | baseline recheck | `-O3` | 62.758 | +0.18% | not flagged |
| 1439-1441 | combination (greedy) | `-march=native -fno-pie -no-pie` | 76.606 | +6.53% | **accept** |
| 1442-1444 | combination (greedy) | `+ -flto` | 77.339 | +0.96% | reject (CI overlap) |
| 1445-1447 | combination (pair) | `-flto -fno-pie -no-pie` | 67.165 | +7.22% | accept, below the greedy winner |
| 1448-1450 | combination (pair) | `-flto -march=native` | 73.648 | +17.57% | accept, below the greedy winner |
| 1451-1453 | combination (pair) | `-fno-pie -no-pie -march=native` | 76.424 | +22.00% | accept, same code as the winner |
| 1454-1456 | PGO | `-march=native -fno-pie -no-pie -fprofile-use` | 79.069 | +3.22% | **accept** |

Phase 4 deltas are against `-O3`, greedy-step deltas against the step before, pair deltas against `-O3`, and the PGO
delta against `-O3 -march=native -fno-pie -no-pie`. The greedy walk started from the Phase 4 `-march=native` result
rather than re-measuring it. The microarch multiplier was skipped because the winning set already had
`-march=native`; the vector-width multiplier had no candidate left, since the shape filter had excluded `256`.

## Observations

- **`-fipa-pta` was flat here (+0.24%)**, so stockfish's -41% screening result (open item 18) isn't a general
  property of the flag on this host.
- **`-flto` was +3.5% on ntest but -18% on stockfish**, two chess/Othello engines with similar search code.
- **Non-PIE pays on both intrate benchmarks so far**: +2.46% and +4.78% alone, +1.23% and +6.53% on top of
  `-march=native`. niwot accepted it only on `821.gcc_s` (+2.39%), and rejected it on llvm_s, cppcheck_s and
  diamond_s (+0.34% to +0.42%). niwot's ntest and stockfish mines predate it, so it has never been measured on
  either there.
- **The pair `-fno-pie -no-pie -march=native` re-measured the winner's code** (fingerprint `f909362c`): 76.42 against
  76.61 as the greedy step (niwot opportunity #35).
- **Phase 4 cost 45 trials on flat flags** because nothing was excluded and nothing was fast-tracked. That's about
  4 hours of this 7.5-hour mine.

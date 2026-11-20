# `cfm mine` results: 708.sqlite_r on `chicago`, 2026-11-20

This is the third intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `708.sqlite_r` is
the SQLite database engine (C). niwot's mine found `-O3 -fprefetch-loop-arrays` (+1.76%), and a follow-up reached
+10.48% with PGO on top ([write-up](mining_results.708.sqlite_r.2026-10-17.md)), before the hardening opt-outs were
in the catalog. Its corpus shape is memory-bound at 39.7%, under the 55% gate, so nothing was excluded on shape.

## Headline result

**`-O3 -U_FORTIFY_SOURCE -fno-pie -no-pie -fprofile-use`, +15.66% over plain `-O3`** (ratio 49.712 → 57.498).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 49.712 | — |
| `-O3 -U_FORTIFY_SOURCE` | 50.746 | +2.08% |
| `+ -fno-pie -no-pie` | 51.285 | +1.06% |
| `+ -fprofile-use` | 57.498 | **+12.11%** |

- **PGO is the big step, +12.11%**, as on niwot (about +8.6% there, on top of `-fprefetch-loop-arrays`). A database
  engine's hot paths (the bytecode VM, B-tree search) are branchy and input-dependent, which is where PGO pays.
- **Five of the six hardening and code-layout opt-outs were accepted alone**: `-U_FORTIFY_SOURCE` +2.08%,
  `-fno-stack-protector` +2.06%, `-fno-pie -no-pie` +1.36%, `-fno-unswitch-loops` +1.24%, `-fcf-protection=none`
  +1.07%. They overlap: only non-PIE added more than 1% on top of `-U_FORTIFY_SOURCE`.
- **`-fprefetch-loop-arrays`, niwot's winner, was +1.35% alone** but +0.63% on top of the winner (CI overlap).
- **`-march=native` lost 0.50%** (fast-tracked on 19 accepts of 26), as on niwot. The microarch multiplier ran,
  since the winning set had no `-march=`: `-march=znver5` lost 2.62% and `-mtune=znver5` lost 1.41% on top of PGO.
- **Fast-math and `-flto` did nothing**: `-Ofast` -0.05%, `-ffast-math` +0.06%, `-flto` +0.74% (CI-clear, under the
  1% bar; the second near-miss flag).

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 708.sqlite_r` (uncapped, defaults) |
| Code | `main` at `76c30e2` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 31 |
| Started / finished | 2026-11-19T22:07:59Z / 2026-11-20T10:11:55Z (12h04m) |
| Final status | `converged` |
| Trials | 119 (1457-1575), one skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 14 / 13 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | none |
| Fast-tracked (M4) | `-march=native` (accepted 19 of 26, mean +17.06%) |
| Accepted in Phase 4 | `-U_FORTIFY_SOURCE` +2.08%, `-fno-stack-protector` +2.06%, `-fno-pie -no-pie` +1.36%, `-fprefetch-loop-arrays` +1.35%, `-fno-unswitch-loops` +1.24%, `-fcf-protection=none` +1.07% |
| Winning flags | `["-O3", "-U_FORTIFY_SOURCE", "-fno-pie -no-pie", "-fprofile-use"]`, +15.66% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 9 of 118 timed runs; no reruns; baseline recheck not flagged (+0.44%) |
| Power | package power median 84.99 W on every trial; CPU temperature 89.0-95.1°C |

A trial took about 6 minutes, a PGO trial about 7.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 39.7%, `vectorization_density=moderate`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1457 | warm-up | 49.778 |
| 1458 | warm-up | 49.889 |
| 1459 | calibration | 49.710 |
| 1460 | calibration | 49.812 |
| 1461 | calibration | 49.614 |
| 1518 | recheck | 49.930 (+0.44%) |

The calibration mean is 49.712. Warm-up settled after the minimum two reps (763 s). Every `-O3` build had the same
code fingerprint (`422aa59d`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1462-1475 | screening | 14 candidates | 49.63-50.87 | | all survived; `-fno-math-errno` skipped as the same code as `-O3` |
| 1476-1478 | confirmation | `-fprefetch-loop-arrays` | 50.385 | +1.35% | **accept** |
| 1479-1481 | confirmation | `-fgraphite-identity` | 49.912 | +0.40% | reject |
| 1482-1484 | confirmation | `-flto` | 50.082 | +0.74% | reject (CI-clear, under the 1% bar) |
| 1485-1487 | confirmation | `-fno-pie -no-pie` | 50.386 | +1.36% | **accept** |
| 1488-1490 | confirmation | `-fno-stack-protector` | 50.737 | +2.06% | **accept** |
| 1491-1493 | confirmation | `-fcf-protection=none` | 50.242 | +1.07% | **accept** |
| 1494-1496 | confirmation | `-U_FORTIFY_SOURCE` | 50.746 | +2.08% | **accept** (the greedy start) |
| 1497-1499 | confirmation | `-funroll-loops` | 50.106 | +0.79% | reject (CI-clear, under the 1% bar) |
| 1500-1502 | confirmation | `-Ofast` | 49.685 | -0.05% | reject |
| 1503-1505 | confirmation | `-ffast-math` | 49.744 | +0.06% | reject |
| 1506-1508 | confirmation | `-fno-ipa-cp-clone` | 49.995 | +0.57% | reject |
| 1509-1511 | confirmation | `-fno-unswitch-loops` | 50.331 | +1.24% | **accept** |
| 1512-1514 | confirmation | `-fipa-pta` | 49.938 | +0.45% | reject |
| 1515-1517 | confirmation (fast-tracked) | `-march=native` | 49.462 | -0.50% | reject |
| 1518 | baseline recheck | `-O3` | 49.930 | +0.44% | not flagged |
| 1519-1521 | combination (greedy) | `-U_FORTIFY_SOURCE -fno-stack-protector` | 51.091 | +0.68% | reject (CI overlap) |
| 1522-1524 | combination (greedy) | `-U_FORTIFY_SOURCE -fno-pie -no-pie` | 51.285 | +1.06% | **accept** |
| 1525-1527 | combination (greedy) | `+ -fprefetch-loop-arrays` | 51.606 | +0.63% | reject (CI overlap) |
| 1528-1530 | combination (greedy) | `+ -fno-unswitch-loops` | 51.682 | +0.77% | reject (CI-clear, under the 1% bar) |
| 1531-1533 | combination (greedy) | `+ -fcf-protection=none` | 51.499 | +0.42% | reject |
| 1534-1563 | combination (pairs) | 10 pairs of the six accepts | 49.86-51.24 | +0.31% to +3.07% | none beat the greedy winner |
| 1564-1566 | PGO | winner `+ -fprofile-use` | 57.498 | +12.11% | **accept** |
| 1567-1569 | PGO (near-miss variant) | winner `+ -funroll-loops -fprofile-use` | 57.300 | +11.73% | accept, below the plain PGO set |
| 1570-1572 | microarch | winner + PGO `+ -march=znver5` | 55.991 | -2.62% | reject |
| 1573-1575 | microarch | winner + PGO `+ -mtune=znver5` | 56.688 | -1.41% | reject |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against the step before, and Phase 6 deltas against the
set they were layered on. The greedy walk started from the Phase 4 `-U_FORTIFY_SOURCE` result rather than
re-measuring it. The vector-width multiplier was skipped (no `-march=` in the winning set).

## Observations

- **The pair tournament took 30 timed runs (about 3 hours, a quarter of the mine)** because six flags were accepted.
  Two of its pairs re-measured greedy steps' code: `-U_FORTIFY_SOURCE -fno-pie -no-pie` (fingerprint `2ce25b40`,
  51.24 against 51.29) and `-U_FORTIFY_SOURCE -fno-stack-protector` (`01275a34`, 51.12 against 51.09) (niwot
  opportunity #35).
- **The greedy step for `-fno-stack-protector` compared against a measurement from 2.5 hours earlier.** On top of
  `-U_FORTIFY_SOURCE` it read +0.68% with CIs overlapping, and the same code as a pair read +2.84% over `-O3`.
  Both say the two flags mostly overlap, which fits: fortify's checked string functions and the stack protector's
  canaries are both per-call costs, and removing one makes the other's call paths cheaper too. That's a guess.
- **Hardening opt-outs now pay on all three intrate benchmarks here.** Non-PIE is in all three winning sets (+1.23%,
  +6.53% and +1.06% as steps). The opt-outs only reach Phase 3 when the shape filter keeps them (all three shapes
  were under the gate here), as niwot opportunity #30 discussed.
- **`-march=znver5` lost 2.6% on top of PGO**, a larger loss than `-march=native` alone (-0.5%). The two build the
  same code without PGO on this host; with PGO the profile was retrained per build, so this may be partly a
  different training run (CLAUDE.md's 2026-10-28 entry on SPEC PGO reps).

# `cfm mine` results: 714.cpython_r on `chicago`, 2026-11-20

This is the fifth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `714.cpython_r` is
the CPython interpreter (C). niwot's mine found `-O3 -flto -fprofile-use`, +36.49%
([write-up](mining_results.714.cpython_r.2026-10-17.md)), and this machine in August found the same set at +41.65%
([write-up](mining_results.714.cpython_r.2026-08-23.md)). Its corpus shape is frontend-bound at 65.8%, over the 55%
gate, so this is the first intrate mine here where the shape filter excluded candidates (seven of them).

## Headline result

**`-O3 -flto -fprofile-use -mtune=znver5`, +30.37% over plain `-O3`** (ratio 80.440 → 104.869).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 80.440 | — |
| `-O3 -flto` | 83.406 | +3.69% |
| `+ -fprofile-use` | 101.768 | **+22.01%** |
| `+ -mtune=znver5` | 104.869 | +3.05% |

- **PGO is the big step, +22.01%**, as on niwot (+24.82% on top of `-flto`) and in August (+31.16%). An interpreter's
  bytecode dispatch loop is branchy and input-dependent, which is what PGO's layout and branch weights target.
- **`-flto` gave +3.69%**, about half of niwot's +7.94% and August's +8.00%. It was fast-tracked (accepted 2 of 3 in
  this host's frontend-bound cluster).
- **`-mtune=znver5` was accepted on top of PGO (+3.05%)**, the first accept for either microarch flag in this host's
  knowledge table (0 of 9 in the memory-bound cluster, 0 of 2 frontend-bound before). `-march=znver5` read +1.34% on
  top of PGO, rejected on CI overlap, and `-march=native` lost 5.61% at screening and was pruned. So the tuning
  helps here while the extra instruction sets don't. Each PGO build retrained its own profile, so the comparison is
  across different PGO binaries (see Observations).
- **`-fcf-protection=none` was accepted alone (+1.79%) but not on top of `-flto`** (+2.06%, CI overlap). Non-PIE read
  +1.38% and `-fno-stack-protector` +0.91%, both rejected on CI overlap. This is the second intrate benchmark here,
  after omnetpp, where non-PIE isn't in the winning set.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 714.cpython_r` (uncapped, defaults) |
| Code | `main` at `47df425` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 33 |
| Started / finished | 2026-11-20T19:38:51Z / 2026-11-20T23:13:57Z (3h35m) |
| Final status | `converged` |
| Trials | 52 (1677-1728), none skipped, no reruns |
| Candidates screened / confirmed | 7 / 6 (plus `-flto` and `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-mprefer-vector-width=256`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 65.8%, over the gate) |
| Fast-tracked (M4) | `-flto` (accepted 2 of 3, mean +7.73%), `-fno-stack-protector` (accepted 2 of 3, mean +1.22%) |
| Accepted in Phase 4 | `-flto` +3.69%, `-fcf-protection=none` +1.79% |
| Winning flags | `["-O3", "-flto", "-fprofile-use", "-mtune=znver5"]`, +30.37% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 1 of 52 timed runs; no reruns; baseline recheck not flagged (+0.03%) |
| Power | package power median 84.99 W on every trial; CPU temperature 89.2-95.5°C |

A trial took about 3.6 minutes, a PGO trial about 6.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 65.8%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1677 | warm-up | 80.545 |
| 1678 | warm-up | 80.492 |
| 1679 | calibration | 80.231 |
| 1680 | calibration | 80.430 |
| 1681 | calibration | 80.660 |
| 1713 | recheck | 80.461 (+0.03%) |

The calibration mean is 80.440, with a 95% CI of [79.907, 80.974] (±0.66%). Warm-up settled after the minimum two
reps (464 s). Every `-O3` build had the same code fingerprint (`8be44318`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1682-1688 | screening | 7 candidates | 76.14-81.69 | | 6 survived; `-march=native` (76.14, -5.61% against the last calibration rep) pruned |
| 1689-1691 | confirmation | `-fno-pie -no-pie` | 81.549 | +1.38% | reject (CI overlap) |
| 1692-1694 | confirmation | `-fcf-protection=none` | 81.878 | +1.79% | **accept** |
| 1695-1697 | confirmation | `-U_FORTIFY_SOURCE` | 79.736 | -0.88% | reject |
| 1698-1700 | confirmation | `-fno-ipa-cp-clone` | 79.090 | -1.68% | reject (CI-clear, below baseline) |
| 1701-1703 | confirmation | `-fno-unswitch-loops` | 78.735 | -2.12% | reject (CI-clear, below baseline) |
| 1704-1706 | confirmation | `-fno-math-errno` | 80.046 | -0.49% | reject |
| 1707-1709 | confirmation (fast-tracked) | `-flto` | 83.406 | +3.69% | **accept** (the greedy start) |
| 1710-1712 | confirmation (fast-tracked) | `-fno-stack-protector` | 81.171 | +0.91% | reject (CI overlap) |
| 1713 | baseline recheck | `-O3` | 80.461 | +0.03% | not flagged |
| 1714-1716 | combination (greedy) | `-flto -fcf-protection=none` | 85.123 | +2.06% | reject (CI overlap) |
| 1717-1719 | combination (pair) | `-fcf-protection=none -flto` | 84.677 | +5.27% | accept, not enough to replace the greedy winner |
| 1720-1722 | PGO | `-flto -fprofile-use` | 101.768 | +22.01% | **accept** |
| 1723-1725 | microarch | winner + PGO `+ -march=znver5` | 103.134 | +1.34% | reject (CI overlap) |
| 1726-1728 | microarch | winner + PGO `+ -mtune=znver5` | 104.870 | +3.05% | **accept** |

Phase 4 and pair deltas are against `-O3`, the greedy-step delta against `-O3 -flto`, and Phase 6 deltas against the
set they were layered on. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it. No
Phase 4 reject was CI-clear above baseline, so PGO had no near-miss variant; the vector-width multiplier had no
candidate (the shape filter had excluded `256`).

## Observations

- **`-fcf-protection=none` on top of `-flto` was a narrow miss.** Its code (`536b056c`) was measured six times,
  three as the greedy step (85.12) and three as the pair (84.68), about 1.8% above `-flto`'s 83.41. The greedy step
  was rejected because `-flto`'s own three reps were loose (82.77-84.09, a CI of ±2.0%) and the upper end just
  overlapped. The pair re-measured the greedy step's code (niwot opportunity #35), three extra timed runs.
- **The three PGO reps were three different binaries** (`850ef33d`, `f4fe64a0`, `a4529dfa`; SPEC retrains for every
  PGO build, CLAUDE.md's 2026-10-28 entry), and read 100.94-102.45. The `-mtune=znver5` reps were also three different
  builds but read 104.80-104.98, above every plain-PGO rep. The accept is therefore probably real rather than one
  unlucky PGO build, but it is a comparison between profiles as much as between tunings. A rerun of this pair would
  settle it.
- **`-march=native` hurts cpython on three runs across two hosts**: -5.61% at screening here, -4.77% confirmed on
  niwot, -5.32% at screening here in August.
- **The shape filter cut Phase 3-4 to 8 flagsets** (24 confirmation runs), against 14-15 on the other four intrate
  mines here, which is most of why this mine took 3.6 hours against 7.5-12 for the others. Five of the seven
  excluded flags had never been accepted in this host's frontend-bound cluster (means -0.23% to +0.58%); the other
  two had: `-Ofast` (2 of 3, mean +2.40%) and `-ffast-math` (1 of 2, mean +2.96%), so they may have been worth a run.
- **Two flags were clearly worse**: `-fno-unswitch-loops` -2.12% and `-fno-ipa-cp-clone` -1.68%, both with CIs
  below baseline. On the other four intrate mines here they read 0.00% to +1.25%, and `-fno-unswitch-loops` was
  accepted on sqlite (+1.24%).

# `cfm mine` results: 710.omnetpp_r on `chicago`, 2026-11-20

This is the fourth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `710.omnetpp_r` is
the OMNeT++ discrete-event network simulator (C++). niwot's mine found `-O3 -flto -fprofile-use`, +29.94%
([write-up](mining_results.710.omnetpp_r.2026-10-19.md)), before the hardening opt-outs were in the catalog. Its
corpus shape is frontend-bound at 45.9%, under the 55% gate.

## Headline result

**`-O3 -flto -fno-stack-protector -fprofile-use`, +36.42% over plain `-O3`** (ratio 54.317 → 74.099).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 54.317 | — |
| `-O3 -flto` | 61.274 | +12.81% |
| `+ -fno-stack-protector` | 63.155 | +3.07% |
| `+ -fprofile-use` | 74.099 | **+17.33%** |

- **PGO gave +17.33% and LTO +12.81%**, the same two big steps as niwot (LTO +13.14%, PGO +14.85% on top there) and as this machine in August (+13.25%, +23.46%). A
  discrete-event simulator spends its time in virtual calls, small methods spread across many files, and a
  data-dependent event queue, which is what both LTO's cross-file inlining and PGO's layout target.
- **`-fno-stack-protector` gave +2.77% alone and +3.07% on top of `-flto`.** With LTO inlining more, more
  functions probably have local arrays that get canaries, so the protector costs more after LTO; that's a guess.
- **`-fno-pie -no-pie` gave +2.92% alone but +0.16% on top of `-flto`.** LTO already turns most cross-file calls and
  global accesses into local ones, which is probably what non-PIE was saving. This is the first intrate benchmark
  here where non-PIE isn't in the winning set; on ntest `-flto` was the flag left out instead.
- **`-Ofast` gave +2.06% alone but -0.91% on top of `-flto -fno-stack-protector`.** `-ffast-math` was fast-tracked
  (accepted 1 of 1, on astcenc_r) and read +0.69%, rejected.
- **The microarch multiplier ran** (no `-march=` in the winning set): `-march=znver5` -0.14%, `-mtune=znver5` -1.22%
  on top of PGO, both rejected. `-march=native` alone read +1.46%, rejected on CI overlap.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 710.omnetpp_r` (uncapped, defaults) |
| Code | `main` at `cca9259` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 32 |
| Started / finished | 2026-11-20T10:12:08Z / 2026-11-20T19:38:40Z (9h26m) |
| Final status | `converged` |
| Trials | 101 (1576-1676), none skipped, no reruns |
| Candidates screened / confirmed | 14 / 14 (plus `-ffast-math` fast-tracked) |
| Excluded on shape (Phase 2) | `-mprefer-vector-width=256` (`vectorization_density=low`); none on `resource_dominance` |
| Fast-tracked (M4) | `-ffast-math` (accepted 1 of 1, +5.22%, in the frontend-bound cluster) |
| Accepted in Phase 4 | `-flto` +12.81%, `-fno-pie -no-pie` +2.92%, `-fno-stack-protector` +2.77%, `-Ofast` +2.06% |
| Winning flags | `["-O3", "-flto", "-fno-stack-protector", "-fprofile-use"]`, +36.42% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 1 of 101 timed runs; no reruns; **baseline recheck flagged (+1.26%)** |
| Power | package power median 84.99 W on every trial; CPU temperature 89.8-96.9°C |

A trial took about 5.5 minutes, a PGO trial about 7.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 45.9%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1576 | warm-up | 54.480 |
| 1577 | warm-up | 54.264 |
| 1578 | calibration | 54.017 |
| 1579 | calibration | 54.476 |
| 1580 | calibration | 54.459 |
| 1640 | recheck | 55.003 (**+1.26%, flagged**) |

The calibration mean is 54.317, with a 95% CI of [53.671, 54.964] (±1.19%), eight times stockfish's. Warm-up settled
after the minimum two reps (695 s). Every `-O3` build had the same code fingerprint (`09924af8`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1581-1594 | screening | 14 candidates | 54.27-61.14 | | all survived |
| 1595-1597 | confirmation | `-flto` | 61.274 | +12.81% | **accept** (the greedy start) |
| 1598-1600 | confirmation | `-fno-pie -no-pie` | 55.902 | +2.92% | **accept** |
| 1601-1603 | confirmation | `-fno-stack-protector` | 55.821 | +2.77% | **accept** |
| 1604-1606 | confirmation | `-fcf-protection=none` | 54.618 | +0.55% | reject |
| 1607-1609 | confirmation | `-U_FORTIFY_SOURCE` | 54.607 | +0.53% | reject |
| 1610-1612 | confirmation | `-fno-ipa-cp-clone` | 54.998 | +1.25% | reject (CI overlap) |
| 1613-1615 | confirmation | `-fno-unswitch-loops` | 54.454 | +0.25% | reject |
| 1616-1618 | confirmation | `-funroll-loops` | 54.728 | +0.76% | reject |
| 1619-1621 | confirmation | `-fprefetch-loop-arrays` | 54.960 | +1.18% | reject (CI overlap) |
| 1622-1624 | confirmation | `-march=native` | 55.110 | +1.46% | reject (CI overlap) |
| 1625-1627 | confirmation | `-Ofast` | 55.434 | +2.06% | **accept** |
| 1628-1630 | confirmation | `-fno-math-errno` | 54.846 | +0.97% | reject |
| 1631-1633 | confirmation | `-fipa-pta` | 54.993 | +1.24% | reject (CI overlap) |
| 1634-1636 | confirmation | `-fgraphite-identity` | 55.175 | +1.58% | reject (CI overlap) |
| 1637-1639 | confirmation (fast-tracked) | `-ffast-math` | 54.695 | +0.69% | reject |
| 1640 | baseline recheck | `-O3` | 55.003 | +1.26% | flagged |
| 1641-1643 | combination (greedy) | `-flto -fno-pie -no-pie` | 61.373 | +0.16% | reject |
| 1644-1646 | combination (greedy) | `-flto -fno-stack-protector` | 63.155 | +3.07% | **accept** |
| 1647-1649 | combination (greedy) | `+ -Ofast` | 62.579 | -0.91% | reject |
| 1650-1667 | combination (pairs) | 6 pairs of the four accepts | 56.17-62.87 | +3.52% to +15.75% | none beat the greedy winner |
| 1668-1670 | PGO | winner `+ -fprofile-use` | 74.099 | +17.33% | **accept** |
| 1671-1673 | microarch | winner + PGO `+ -march=znver5` | 73.993 | -0.14% | reject |
| 1674-1676 | microarch | winner + PGO `+ -mtune=znver5` | 73.192 | -1.22% | reject |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against the step before, and Phase 6 deltas against the
set they were layered on. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it. No
Phase 4 reject was CI-clear above baseline, so PGO had no near-miss variant; the vector-width multiplier had no
candidate left.

## Observations

- **Five flags were rejected at +1.18% to +1.58% on CI overlap**, and the baseline recheck read +1.26%. The
  calibration reps (54.02-54.48) were the loosest of the four intrate mines here, and the recheck says the true
  `-O3` level is probably nearer 54.6-55.0 than 54.3. Against that, those five are about flat, so the rejects look
  right; it also means each accept's delta here may be about 1% high. That doesn't change any verdict: the three
  winning steps are +12.8%, +3.1% and +17.3%, and the two later ones are measured against their own step.
- **The pair tournament re-measured both greedy winners' code** (`-flto -fno-stack-protector`, `7720cf42`: 62.87
  against 63.16; `-flto -fno-pie -no-pie`, `3fa80f30`: 61.37 both times), six timed runs (niwot opportunity #35).
- **The three PGO reps of the winner built identical code** (`8f578711`), but `-march=znver5`'s first PGO build
  differed from its other two (`6e4aaaca` against `21c4bf54`) and read 0.9% lower. SPEC retrains for every PGO build
  (CLAUDE.md's 2026-10-28 entry), so on omnetpp the training run is usually but not always deterministic.
- **The CPU reached 96.9°C**, the highest of this intrate run, with package power still at 84.99 W throughout.

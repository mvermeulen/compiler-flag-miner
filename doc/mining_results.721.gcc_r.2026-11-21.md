# `cfm mine` results: 721.gcc_r on `chicago`, 2026-11-21

This is the sixth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `721.gcc_r` is the
GCC compiler (C). Both earlier mines accepted nothing: this machine in August
([write-up](mining_results.721.gcc_r.2026-08-28.md)) and niwot on 2026-10-20
([write-up](mining_results.721.gcc_r.2026-10-20.md)). Both ran while the shape filter still excluded `-flto` and PGO was
skipped on memory-bound shapes. niwot's follow-up measured `-O3 -flto -fprofile-use` at +10.71% by hand. Its corpus
shape is memory-bound at 45.2%, under the 55% gate, so only `-mprefer-vector-width=256` was excluded (on
`vectorization_density=low`).

## Headline result

**`-O3 -flto -fno-pie -no-pie -fprofile-use`, +12.68% over plain `-O3`** (ratio 47.358 → 53.365).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 47.358 | — |
| `-O3 -flto` | 48.411 | +2.22% |
| `+ -fno-pie -no-pie` | 49.189 | +1.61% |
| `+ -fprofile-use` | 53.365 | **+8.49%** |

- **This is the first mine of gcc_r to accept anything.** LTO and PGO agree closely with niwot's hand-measured
  follow-up: `-flto` +2.22% here against +1.81% there, and PGO +8.49% on top of LTO here against +8.9% there.
- **`-fno-pie -no-pie` gave +1.71% alone and +1.61% on top of `-flto`**, so on gcc the two don't overlap, unlike
  omnetpp (+0.16% on top of LTO). Non-PIE is in four of the six intrate winning sets here.
- **`-march=native` was flat (+0.04%)**, fast-tracked on 19 accepts of 27 in the memory-bound cluster. It read
  -0.15% here in August. `-march=znver5` (+0.10%) and `-mtune=znver5` (+0.13%) on top of PGO were flat too.
- **Every other flag read -0.30% to +0.91%**, all rejected on CI overlap. `-fno-stack-protector`'s +0.91% was the
  closest.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 721.gcc_r` (uncapped, defaults) |
| Code | `main` at `1e9c214` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 34 |
| Started / finished | 2026-11-20T23:14:15Z / 2026-11-21T13:39:33Z (14h25m) |
| Final status | `converged` |
| Trials | 80 (1729-1808), none skipped, no reruns |
| Candidates screened / confirmed | 14 / 14 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-mprefer-vector-width=256` (`vectorization_density=low`); none on `resource_dominance` (45.2% is under the gate) |
| Fast-tracked (M4) | `-march=native` (accepted 19 of 27, mean +16.41%) |
| Accepted in Phase 4 | `-flto` +2.22%, `-fno-pie -no-pie` +1.71% |
| Winning flags | `["-O3", "-flto", "-fno-pie -no-pie", "-fprofile-use"]`, +12.68% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 1 of 80 timed runs; no reruns; baseline recheck not flagged (+0.21%) |
| Power | package power median 84.97-85.00 W on every trial; CPU temperature 88.2-95.1°C |

A trial took about 9 minutes, an LTO trial about 13, and a PGO trial about 19 (two-pass builds of GCC). This was the
longest intrate mine here so far.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 45.2%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1729 | warm-up | 47.491 |
| 1730 | warm-up | 47.464 |
| 1731 | calibration | 47.455 |
| 1732 | calibration | 47.451 |
| 1733 | calibration | 47.169 |
| 1793 | recheck | 47.459 (+0.21%) |

The calibration mean is 47.358, with a 95% CI of [46.951, 47.766] (±0.86%). The third calibration rep read 0.6% below
the other four `-O3` runs, which all sat at 47.45-47.49 (see Observations). Warm-up settled after the minimum two reps
(1140 s). Every `-O3` build had the same code fingerprint (`0233f9f6`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1734-1747 | screening | 14 candidates | 47.29-48.25 | | all survived |
| 1748-1750 | confirmation | `-fprefetch-loop-arrays` | 47.359 | 0.00% | reject |
| 1751-1753 | confirmation | `-fgraphite-identity` | 47.400 | +0.09% | reject |
| 1754-1756 | confirmation | `-flto` | 48.411 | +2.22% | **accept** (the greedy start) |
| 1757-1759 | confirmation | `-fno-pie -no-pie` | 48.168 | +1.71% | **accept** |
| 1760-1762 | confirmation | `-fno-stack-protector` | 47.791 | +0.91% | reject (CI overlap) |
| 1763-1765 | confirmation | `-fcf-protection=none` | 47.495 | +0.29% | reject |
| 1766-1768 | confirmation | `-U_FORTIFY_SOURCE` | 47.521 | +0.34% | reject |
| 1769-1771 | confirmation | `-funroll-loops` | 47.214 | -0.30% | reject |
| 1772-1774 | confirmation | `-Ofast` | 47.501 | +0.30% | reject |
| 1775-1777 | confirmation | `-ffast-math` | 47.513 | +0.33% | reject |
| 1778-1780 | confirmation | `-fno-math-errno` | 47.448 | +0.19% | reject |
| 1781-1783 | confirmation | `-fno-ipa-cp-clone` | 47.447 | +0.19% | reject |
| 1784-1786 | confirmation | `-fno-unswitch-loops` | 47.554 | +0.41% | reject |
| 1787-1789 | confirmation | `-fipa-pta` | 47.506 | +0.31% | reject |
| 1790-1792 | confirmation (fast-tracked) | `-march=native` | 47.379 | +0.04% | reject |
| 1793 | baseline recheck | `-O3` | 47.459 | +0.21% | not flagged |
| 1794-1796 | combination (greedy) | `-flto -fno-pie -no-pie` | 49.189 | +1.61% | **accept** |
| 1797-1799 | combination (pair) | `-flto -fno-pie -no-pie` | 49.205 | +3.90% | accept, same code as the winner |
| 1800-1802 | PGO | winner `+ -fprofile-use` | 53.364 | +8.49% | **accept** |
| 1803-1805 | microarch | winner + PGO `+ -march=znver5` | 53.419 | +0.10% | reject |
| 1806-1808 | microarch | winner + PGO `+ -mtune=znver5` | 53.434 | +0.13% | reject |

Phase 4 and pair deltas are against `-O3`, the greedy-step delta against `-O3 -flto`, and Phase 6 deltas against the
set they were layered on. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it. No
Phase 4 reject was CI-clear above baseline, so PGO had no near-miss variant; the vector-width multiplier had no
candidate (the shape filter had excluded `256`).

## Observations

- **gcc_r is very repeatable here.** Every flagset's three reps sit within 0.3% of each other, most within 0.1%. The
  baseline CI (±0.86%) is loose only because of the one 47.169 calibration rep. Ten flags read +0.19% to +0.91%,
  and all overlapped that CI. Against the other four `-O3` runs (mean 47.465) they read -0.5% to +0.7%, still under
  the 1% bar. So no verdict depends on the low rep.
- **The three PGO reps were three different binaries** (`1136dad8`, `006cba5f`, `90bd8aab`; SPEC retrains for every PGO
  build) but read 53.34-53.38, within 0.07%. On cpython and omnetpp, PGO reps differed by up to 1.5%. gcc's training
  run looks close to deterministic in its effect.
- **The pair tournament re-measured the winner's code** (`e912d5af`: 49.21 against 49.19), its only pair, three timed
  runs at about 13 minutes each (niwot opportunity #35).
- **The shape-filter and PGO-skip fixes changed the answer on this benchmark.** Both earlier mines' 0.00% came from
  never trying `-flto` or PGO; with them tried, gcc gets +12.7%. That fits niwot opportunity #25, which found the PGO
  skip hiding wins on five of seven niwot benchmarks.

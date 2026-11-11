# `cfm mine` results: 822.palm_s on `chicago`, 2026-11-11

This is the seventh fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`822.palm_s` mine on any host. `822.palm_s` is the SPECspeed version of PALM, a Fortran large-eddy simulation model
for atmospheric and oceanic boundary layers, parallelized with OpenMP; its rate counterpart was
[mined here on 2026-11-06](mining_results.722.palm_r.2026-11-06.md) (+5.20%, `-O3 -march=native -fprofile-use`). Its
corpus shape is memory-bound at 56.2%, just over the 55% shape margin.

## Headline result

**`-O3 -march=native -fprofile-use`, +23.54% over plain `-O3`** (ratio 3.1325 → 3.8698), the same winning flags as
palm_r but a far larger gain.

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 3.1325 | — |
| `-O3 -march=native` | 3.7348 | +19.22% |
| `+ -fprofile-use` | 3.8698 | +3.62% |

- **`-march=native` gave +19.22%**, against +4.13% on palm_r here. All three reps (3.731-3.738) sat far above
  every `-O3` rep (3.122-3.143). It was fast-tracked on the memory-bound prior (accepted 13 of 18).
- **PGO added +3.62% on top**, against +1.03% on palm_r. Its three builds had three different code fingerprints and
  agreed within 0.4%.
- **`-mprefer-vector-width=256` cost 1.02%** on top of the winner, and was rejected.
- **`-flto` read +0.84% and was rejected on CI overlap**, as on palm_r (+1.04%, open item 7). The baseline CI was
  ±0.77%, widened by its third calibration rep reading 0.4% above the other two.
- **The shape filter dropped 8 candidates** on the 56.2% read, 1.2 points over the margin, `-Ofast` and `-ffast-math`
  among them.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 822.palm_s` (uncapped, defaults) |
| Code | `main` at `c933ee2` (PR #71: `-fno-math-errno` exempt from the shape filter; it's a C/C++ flag in the catalog, so it wasn't a candidate for Fortran palm either way) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 22 |
| Started / finished | 2026-11-11T07:36:40Z / 2026-11-11T11:39:30Z (4h03m) |
| Final status | `converged` |
| Trials | 32 (1004-1035), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 5 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 8 (`-flto` kept, exempt) |
| Fast-tracked (M4) | `-march=native` (accepted 13 of 18, mean +16.15%) |
| Skipped as unchanged code | `-frecursive` (same code as `-O3`) |
| Winning flags | `["-O3", "-march=native", "-fprofile-use"]`, +23.54% |
| Guards | bandwidth gate waited 30 s before 9 of 31 timed runs; no reruns; baseline recheck not flagged (+0.28%) |
| Power | package power median 82.7-84.6 W on every trial; CPU temperature 85.8-90.2°C |

A trial took about 8 minutes, PGO included. Every trial's `.rsf` reads `valid: S` for palm.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 56.2%, `vectorization_density=high`,
`allocation_pressure=high`.

| Trial | Role | Ratio |
|---|---|---|
| 1004 | warm-up | 3.12180 |
| 1005 | warm-up | 3.13042 |
| 1006 | calibration | 3.12487 |
| 1007 | calibration | 3.12932 |
| 1008 | calibration | 3.14346 |
| 1029 | recheck | 3.14140 (+0.28%) |

The calibration mean is 3.132548, with a 95% CI of [3.10843, 3.15667] (±0.77%). Warm-up settled after the minimum
two reps (932 s). Every `-O3` build had the same code fingerprint (`b68c5618`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1009-1013 | screening | 5 candidates | 3.138-3.159 | | all survived (`-frecursive` skipped as unchanged code) |
| 1014-1016 | confirmation | `-fprefetch-loop-arrays` | 3.1425 | +0.32% | reject |
| 1017-1019 | confirmation | `-fgraphite-identity` | 3.1453 | +0.41% | reject |
| 1020-1022 | confirmation | `-fstack-arrays` | 3.1367 | +0.13% | reject |
| 1023-1025 | confirmation | `-flto` | 3.1590 | +0.84% | reject (CI overlap) |
| 1026-1028 | confirmation (fast-tracked) | `-march=native` | 3.7348 | +19.22% | **accept** |
| 1030-1032 | PGO | `-march=native -fprofile-use` | 3.8698 | +3.62% | **accept** |
| 1033-1035 | vector width | `+ -mprefer-vector-width=256` | 3.831 | -1.02% | reject |

Phase 6 deltas are against the step before. With one accepted flag, Phase 5 had nothing to combine and ran no
trials. The microarch multiplier was skipped because the winning set already had `-march=native`.

## Observations

- **palm gains far more as a speed benchmark than as a rate one here**: `-march=native` +19.2% on 32 threads against
  +4.1% on 32 copies, and PGO +3.6% against +1.0%. The source is the same; the workload size and the threading
  differ, and this run doesn't show which of them makes the vector code matter more.
- **Package power read 82.7-84.6 W**, a little under the 85 W of every other fpspeed mine here and palm_r's. Most of
  the chip is busy, but not quite all of it.
- **`-flto` is near 1% on palm in both forms** and rejected on CI overlap both times, never measured on top of the
  winner (open item 7).
- **niwot hasn't mined palm_s yet.**

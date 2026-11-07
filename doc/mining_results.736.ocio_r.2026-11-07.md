# `cfm mine` results: 736.ocio_r on `chicago`, 2026-11-07

This is the seventh benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first `736.ocio_r`
mine on any host. `736.ocio_r` is OpenColorIO, a C++ color-management library that applies color transforms to
image data. Its corpus shape is memory-bound at 58.5%, just over the shape filter's 55% confidence margin.

## Headline result

**`-O3 -march=native -flto`, +22.04% over plain `-O3`** (ratio 83.802 → 102.273).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 83.802 | — |
| `-O3 -march=native` | 100.999 | +20.52% |
| `+ -flto` | 102.273 | +1.26% |

- **`-march=native` gave +20.53% alone**, the second-largest `-march=native` gain on this host after astcenc's
  +20.42%. It was fast-tracked on the memory-bound cluster prior (accepted 6 of 6). All six of its reps
  (100.88-101.12) were far above every `-O3` rep (83.07-83.92).
- **`-flto` gave +1.17% alone and +1.26% on top of `-march=native`. It's the first LTO accept on this host.** Its
  three Phase 4 reps (84.64-84.88) all beat every `-O3` rep. The greedy step and the
  `-flto -march=native` pair built the same code (`af930d63`).
- **PGO was a clear loss, -5.13%** (97.026 on top of `-march=native -flto`). Its three reps agreed to 0.09% and built
  the same code (`3e6b7239`).
- **`-mprefer-vector-width=256` read +0.71% on top of the winner and was rejected.** Its CI [102.92, 103.07] sits
  inside the winner's [101.59, 102.96] at the low end. The winner's CI is wide because of one rep (101.954), and
  the delta is under the 1% bar anyway.
- **The other two candidates were flat**: `-fgraphite-identity` +0.28% and `-fprefetch-loop-arrays` 0.00%.
- **The shape filter dropped 11 candidates** on the 58.5% read: `-Ofast`, `-ffast-math`, `-fno-math-errno`,
  `-funroll-loops`, `-fipa-pta` and six frontend-bound flags. A color-transform library is the kind of code
  fast-math often helps, and the read only just cleared the margin, so this is the strongest case yet for a
  `--no-shape-filter` re-mine (open item 8).

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 736.ocio_r` (uncapped, defaults) |
| Code | `main` at `a2d2cab` (no code changes since `f31ba64`, only docs) |
| Experiment id | 9 |
| Started / finished | 2026-11-07T00:21:38Z / 2026-11-07T04:03:28Z (3h42m) |
| Final status | `converged` |
| Trials | 36 (329-364), no reruns, none skipped |
| Candidates screened / confirmed | 3 / 2 (`-flto`, plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 11 |
| Fast-tracked (M4) | `-march=native` (accepted 6 of 6, mean +6.49%) |
| Winning flags | `["-O3", "-march=native", "-flto"]`, +22.04% |
| Guards | bandwidth gate waited once (30 s, trial 329); no reruns; baseline recheck not flagged (+0.13%) |
| Power | package power median 84.99 W on every trial; CPU temperature 92.8-97.9°C |

Each trial took about 6 minutes, and each PGO trial about 9.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 58.5%, `vectorization_density=high`,
`allocation_pressure=high`.

| Trial | Role | Ratio |
|---|---|---|
| 329 | warm-up | 83.806 |
| 330 | warm-up | 83.069 |
| 331 | calibration | 83.754 |
| 332 | calibration | 83.868 |
| 333 | calibration | 83.783 |
| 349 | recheck | 83.915 (+0.13%) |

The calibration mean is 83.802, with a 95% CI of [83.654, 83.949] (±0.18%). Warm-up settled after the minimum two
reps (771 s). The second warm-up rep read 0.9% under the first, inside the 1% settle bar. Every `-O3` build had
the same code fingerprint (`7010c36c`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 334-336 | screening | 3 candidates | 83.77-84.74 | | all survived |
| 337-339 | confirmation | `-fprefetch-loop-arrays` | 83.804 | +0.00% | reject |
| 340-342 | confirmation | `-fgraphite-identity` | 84.035 | +0.28% | reject |
| 343-345 | confirmation | `-flto` | 84.787 | +1.17% | **accept** |
| 346-348 | confirmation (fast-tracked) | `-march=native` | 101.009 | +20.53% | **accept** |
| 350-352 | combination (greedy) | `-march=native` | 100.999 | +20.52% | **accept** |
| 353-355 | combination (greedy) | `-march=native -flto` | 102.273 | +1.26% | **accept** |
| 356-358 | combination (pair) | `-flto -march=native` | 102.330 | +22.11% | accept (same code as the greedy winner) |
| 359-361 | PGO | `-march=native -flto -fprofile-use` | 97.026 | -5.13% | reject |
| 362-364 | vector width | `-march=native -flto -mprefer-vector-width=256` | 102.995 | +0.71% | reject |

The greedy-step deltas are against the step before, the pair delta against `-O3`, and the Phase 6 deltas against
`-O3 -march=native -flto`. The microarch multiplier was skipped because the winning set already had
`-march=native`.

## Observations

- **LTO and PGO split here.** LTO won (+1.26%) and PGO lost badly (-5.13%). On palm it was the other way: PGO won
  (+1.03%) and LTO was rejected at +1.04%. On this host, neither has yet given more than about 1.3%.
- **The pair `-flto -march=native` re-measured the greedy winner's code**, as two of astcenc's pairs did, which
  cost about 16 minutes.
- **The shape-filter margin is doing real work.** ocio's 58.5% read was 3.5 points over the 55% gate, and it
  excluded 11 of 14 candidates. astcenc's 44.3% read was under the gate and excluded none, and there `-Ofast` was
  worth +7.6% on top of `-march=native`.
- **Package power read 85.0 W on every trial**, for the seventh mine in a row. The CPU reached 97.9°C, a new high for
  this host, about 0.5°C above astcenc.

# `cfm mine` results: 803.sph_exa_s on `chicago`, 2026-11-09

This is the second fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)) and the first
that counts, since the [pot3d_s mine](mining_results.800.pot3d_s.2026-11-08.md) ran pinned to one CPU. It's also the
first `803.sph_exa_s` mine on any host. `803.sph_exa_s` is SPH-EXA, a C++ smoothed-particle hydrodynamics code
parallelized with OpenMP. Its corpus shape is memory-bound at 67.4%.

## Headline result

**`-O3 -march=native -fprofile-use`, +12.73% over plain `-O3`** (ratio 3.3481 → 3.7743).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 3.3481 | — |
| `-O3 -march=native` | 3.6514 | +9.06% |
| `+ -fprofile-use` | 3.7743 | +3.37% |

- **Thread placement was right this time.** Every trial ran with `OMP_PLACES=threads OMP_PROC_BIND=close` across
  all 32 CPUs, and package power read 85.0 W on every trial, the same sustained limit as every fprate mine.
- **`-march=native` gave +9.06%.** It was fast-tracked on the memory-bound prior (accepted 10 of 12). One of its
  reps read 3.4% under its siblings and was re-run: the bandwidth probe read normal (94.8 GB/s) before it and the
  code was unchanged (`7ba037e2`), so the rerun rule did what it's for.
- **PGO added +3.37% on top**, the second PGO accept on this host after palm_r (+1.03%). All three PGO builds had
  the same code fingerprint (`98d83365`) and agreed within 0.1%.
- **`-mprefer-vector-width=256` read +0.69% on top of the winner and was rejected** on CI overlap. Its third rep
  built different code (`5f5684f5`, against `106e7f89` for the first two), as PGO builds on SPEC can (CLAUDE.md's
  2026-10-28 trap).
- **The three screened candidates were flat or worse:** `-fgraphite-identity` -0.00%, `-flto` -0.02%,
  `-fprefetch-loop-arrays` -1.48% (CI clear below baseline).
- **The shape filter dropped 11 candidates** on the 67.4% memory-bound read, among them `-Ofast`, `-ffast-math`,
  `-funroll-loops` and the security-hardening flags.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 803.sph_exa_s` (uncapped, defaults) |
| Code | `main` at `2a54723` (no code changes since `f31ba64`, only docs) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 16 |
| Started / finished | 2026-11-09T20:04:09Z / 2026-11-09T23:24:11Z (3h20m) |
| Final status | `converged` |
| Trials | 28 (728-755), 1 rerun, none skipped |
| Candidates screened / confirmed | 3 / 3 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 11 |
| Fast-tracked (M4) | `-march=native` (accepted 10 of 12, mean +22.09%) |
| Winning flags | `["-O3", "-march=native", "-fprofile-use"]`, +12.73% |
| Guards | bandwidth gate waited 30 s before 17 of 28 runs; one slow-rep rerun (trial 745 → 748); baseline recheck not flagged (+0.08%) |
| Power | package power median 85.02-85.08 W on every trial; CPU temperature 86.0-89.5°C |

A `-O3` trial took about 7 minutes and a PGO trial about 9. Every trial's `.rsf` reads `valid: S` for sph_exa.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 67.4%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 728 | warm-up | 3.33617 |
| 729 | warm-up | 3.35505 |
| 730 | calibration | 3.34677 |
| 731 | calibration | 3.35000 |
| 732 | calibration | 3.34762 |
| 749 | recheck | 3.35067 (+0.08%) |

The calibration mean is 3.348132, with a 95% CI of [3.34397, 3.35229] (±0.12%). Warm-up settled after the minimum
two reps (799 s). Every `-O3` build had the same code fingerprint (`1dba4672`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 733-735 | screening | 3 candidates | 3.300-3.348 | | all survived |
| 736-738 | confirmation | `-fprefetch-loop-arrays` | 3.2985 | -1.48% | reject (CI clear below baseline) |
| 739-741 | confirmation | `-fgraphite-identity` | 3.3481 | -0.00% | reject |
| 742-744 | confirmation | `-flto` | 3.3473 | -0.02% | reject |
| 745-748 | confirmation (fast-tracked) | `-march=native` | 3.6514 | +9.06% | **accept** (745 re-run as 748) |
| 750-752 | PGO | `-march=native -fprofile-use` | 3.7743 | +3.37% | **accept** |
| 753-755 | vector width | `-march=native -fprofile-use -mprefer-vector-width=256` | 3.800 | +0.69% | reject (CI overlap) |

Phase 6 deltas are against the step before. With one accepted flag, Phase 5 had nothing to combine and ran no
trials. The microarch multiplier was skipped because the winning set already had `-march=native`.

## Observations

- **A speed run behaves like a rate run here once placement is right**: 85.0 W, a ±0.12% baseline CI, and
  7-minute trials. The contrast with pot3d_s (24.6 W, 32-minute trials) is the clearest sign of how wrong that
  run's placement was.
- **PGO paid here (+3.4%)**, its second accept on this host after palm_r. Across the memory-bound cluster it had
  been accepted 1 of 12 before this run.
- **11 candidates never ran** because of the shape filter, as on femflow and marian. sph_exa's particle kernels are
  floating-point heavy, so fast-math is a reasonable thing to try with `--no-shape-filter` later.
- **niwot hasn't mined sph_exa_s yet.**

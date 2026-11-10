# `cfm mine` results: 800.pot3d_s on `chicago`, 2026-11-10 (re-mine)

This re-mines `800.pot3d_s` on `chicago` (see [`host_chicago.md`](host_chicago.md)) after
[the first mine](mining_results.800.pot3d_s.2026-11-08.md) ran every trial pinned to one CPU. PR #70 classes its
`doconcurrent` benchset as OpenMP, so this run placed its 32 auto-parallel threads with `OMP_PLACES=threads
OMP_PROC_BIND=close`, one per CPU. `800.pot3d_s` is POT3D, a Fortran potential-field solver for the solar corona
whose loops are written as `DO CONCURRENT` and parallelized by the config's `-ftree-parallelize-loops=32`. Its
corpus shape is memory-bound at 52.0%, under the 55% shape margin, so no candidate was excluded on shape.

## Headline result

**`-O3 -Ofast`, +28.25% over plain `-O3`** (ratio 1.4446 → 1.8526).

- **Placement fixed the baseline.** The `-O3` ratio went from 0.3526 pinned to 1.4446, 4.1× faster, and a trial
  from 32 minutes to 8.
- **`-Ofast` gave +28.25% and `-ffast-math` +27.78%**, each with all three reps far above every `-O3` rep. Both
  raised package power from 74.6 W to 84.4-85.0 W, the host's sustained limit, so the fast-math builds keep more
  of the chip busy. The likely reason: GCC's loop parallelizer only parallelizes a floating-point reduction when
  reassociation is allowed (`-fassociative-math`, part of `-ffast-math`), so under fast-math more of pot3d's
  `DO CONCURRENT` loops run on 32 threads instead of one. This run doesn't confirm that (it would need
  `-fopt-info-loop` output from both builds), but power rising with the gain points that way.
- **`-Ofast -ffast-math` built the same code as `-Ofast`** (`e8297e59`), so the greedy step was skipped; the pair
  trial measured that code again at +28.56% against `-O3`, but didn't replace the winner since it's the same build.
- **`-fno-unswitch-loops`, the pinned run's +115.7% "winner", now reads -31.8%** at screening (0.986) and was
  pruned. Its package power dropped to 48.6 W. That is the pinned result turned around: it apparently leaves
  fewer loops parallelized, which helped when 32 threads were time-sliced on one CPU and hurts now that they each
  have one.
- **`-march=native` read -0.00% and was rejected**, as on tealeaf_s. On top of `-Ofast`, `-march=znver5` read
  +0.27% and `-mtune=znver5` -0.17%, and PGO -0.13%, all rejected.
- **Every other candidate was within ±0.4% of `-O3`.**

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 800.pot3d_s` (uncapped, defaults) |
| Code | `main` at `9d832ae` (PR #70: `doconcurrent` placed as OpenMP) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 19 |
| Started / finished | 2026-11-10T09:16:26Z / 2026-11-10T17:12:43Z (7h56m) |
| Final status | `converged` |
| Trials | 63 (814-876), 4 skipped as unchanged code, 1 rerun |
| Candidates screened / confirmed | 13 / 9 (plus `-march=native` fast-tracked, rejected) |
| Excluded on shape (Phase 2) | none (memory-bound 52.0%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 12 of 15, mean +19.25%) |
| Skipped as unchanged code | `-fno-stack-protector`, `-fcf-protection=none`, `-frecursive` (same code as `-O3`); `-Ofast -ffast-math` (same as `-Ofast`) |
| Winning flags | `["-O3", "-Ofast"]`, +28.25% |
| Guards | bandwidth gate waited 30 s before 35 of 59 timed runs; one slow-rep rerun (trial 843 → 844); baseline recheck not flagged (-0.17%) |
| Power | package power median 73.8-75.1 W on non-fast-math builds, 84.3-85.0 W on fast-math builds, 48.6 W on `-fno-unswitch-loops`; CPU temperature 80.4-90.2°C |

A `-O3` trial took about 8 minutes, a fast-math trial about 7, and a PGO trial about 11. Every trial's `.rsf` reads
`valid: S` for pot3d.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 52.0%, `vectorization_density=moderate`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 814 | warm-up | 1.43860 |
| 815 | warm-up | 1.44498 |
| 816 | calibration | 1.44317 |
| 817 | calibration | 1.44526 |
| 818 | calibration | 1.44526 |
| 863 | recheck | 1.44211 (-0.17%) |

The calibration mean is 1.444563, with a 95% CI of [1.44156, 1.44757] (±0.21%). Warm-up settled after the minimum
two reps (995 s). Every `-O3` build had the same code fingerprint as in the pinned run (`f3eb5077`), so the two
runs measured the same binaries; only placement differed.

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 819-831 | screening | 13 candidates | 0.986-1.854 | | `-fno-unswitch-loops` pruned (-31.8%); 3 skipped as unchanged code |
| 832-834 | confirmation | `-fprefetch-loop-arrays` | 1.4392 | -0.37% | reject |
| 835-837 | confirmation | `-fgraphite-identity` | 1.4452 | +0.04% | reject |
| 838-840 | confirmation | `-fstack-arrays` | 1.4459 | +0.09% | reject |
| 841-844 | confirmation | `-flto` | 1.4454 | +0.06% | reject (843 re-run as 844) |
| 845-847 | confirmation | `-fno-pie -no-pie` | 1.4424 | -0.15% | reject |
| 848-850 | confirmation | `-funroll-loops` | 1.4485 | +0.27% | reject |
| 851-853 | confirmation | `-Ofast` | 1.8526 | +28.25% | **accept** (also the greedy start) |
| 854-856 | confirmation | `-ffast-math` | 1.8459 | +27.78% | **accept** |
| 857-859 | confirmation | `-fno-ipa-cp-clone` | 1.4443 | -0.02% | reject |
| 860-862 | confirmation (fast-tracked) | `-march=native` | 1.4445 | -0.00% | reject |
| 864 | combination (greedy) | `-Ofast -ffast-math` | | | skipped, same code as `-Ofast` |
| 865-867 | combination (pair) | `-Ofast -ffast-math` | 1.857 | +28.56% | accept, didn't replace the winner (same code) |
| 868-870 | PGO | `-Ofast -fprofile-use` | 1.850 | -0.13% | reject |
| 871-873 | microarch | `-Ofast -march=znver5` | 1.858 | +0.27% | reject |
| 874-876 | microarch | `-Ofast -mtune=znver5` | 1.849 | -0.17% | reject |

The pair delta is against `-O3`, the Phase 6 deltas against `-O3 -Ofast`. The greedy walk started from the Phase 4
`-Ofast` result rather than re-measuring it. The vector-width multiplier was skipped because the winning set has no
`-march=`.

## Observations

- **This is the first fast-math win in fpspeed here, and the shape filter let it through only because pot3d's
  memory-bound read (52.0%) was under the 55% margin.** On sph_exa_s, cactus_s and tealeaf_s (67-71%) the filter
  excluded `-Ofast` and `-ffast-math` before they were measured. If the reduction explanation above is right, any
  auto-parallelized Fortran with floating-point reductions can gain this way, whatever its topdown shape.
- **Package power is a useful signal for speed benchmarks** in both directions: 24.6 W showed the pinning bug,
  74.6 W here shows `-O3` leaves part of the chip idle, and fast-math filling it to 85 W matches the gain.
- **The pinned run's knowledge rows remain** (open item 13): `-fno-unswitch-loops` reads accepted 1 of 4 in the
  memory-bound cluster. Screening prunes don't update the knowledge table, so this run's -31.8% isn't in it.
- **niwot hasn't mined pot3d_s yet.**

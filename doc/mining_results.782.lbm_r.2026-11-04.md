# `cfm mine` results: 782.lbm_r on `chicago`, 2026-11-04 (`--no-shape-filter`)

The second `782.lbm_r` mine on `chicago` (see [`host_chicago.md`](host_chicago.md)). The first
([2026-11-03b](mining_results.782.lbm_r.2026-11-03b.md)) accepted `-march=native` at +2.92%, but its shape filter
dropped 11 of 15 candidates on a 94.9% memory-bound read, `-funroll-loops`, `-Ofast` and `-ffast-math` among
them. This re-mine ran with `--no-shape-filter`, so every candidate was screened.

## Headline result

**`-O3 -march=native` again, +3.52% over plain `-O3`** (ratio 16.033 → 16.598). The shape filter hid nothing
that changes the answer.

- **`-Ofast` came closest to a second win, +1.03%, and was rejected.** Its CI [16.116, 16.282] overlapped the
  baseline's upper bound (16.190). `-ffast-math` built the same code as `-Ofast` (fingerprint `36d02c79`) and
  read +0.94%. Neither was tried on top of `-march=native`, because Phase 5 only combines accepted flags.
- **Every other candidate was within ±0.55% of `-O3`.** `-funroll-loops` +0.33%, `-fprefetch-loop-arrays` +0.55%
  (CI-clear, under the 1% bar), `-flto` -0.18%. `-fno-ipa-cp-clone` and `-fipa-pta` built code identical to
  `-O3` and were skipped without a timed run.
- **PGO on top of `-march=native` was -0.15%, `-mprefer-vector-width=256` -0.05%.** The microarch multiplier was
  skipped, as in the first mine, because the winning set already had `-march=native`.
- **One low calibration rep widened the baseline CI ninefold.** Trial 39 read 15.960, 0.7% under its two
  siblings (16.066, 16.073). That's too small for either rerun rule, but it took the CI from ±0.11% (first mine)
  to ±0.98% and pulled the mean down. It's why the near-identical-code flags (`-fno-pie -no-pie`,
  `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-unswitch-loops`) all read +0.21% to
  +0.24%: against the first mine's tighter -O3 mean (16.069) they're flat. The same shift inflates the headline;
  against that mean, `-march=native` here is +3.29%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 782.lbm_r --no-shape-filter` (uncapped; bandwidth gate and power check on) |
| Code | `main` at `d26038f` |
| Experiment id | 3 |
| Started / finished | 2026-11-04T11:20:33Z / 2026-11-05T08:28:15Z (21h08m) |
| Final status | `converged` |
| Trials | 68 (35-102), 2 of them skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 14 / 1 (plus `-march=native` fast-tracked, accepted) |
| Fast-tracked (M4) | `-march=native` (accepted 1 of 1 in experiment 2) |
| Skipped as unchanged code | `-fno-ipa-cp-clone`, `-fipa-pta` |
| Winning flags | `["-O3", "-march=native"]`, +3.52% |
| Guards | bandwidth gate waited 30 s before 10 trials; no slow-rep or low-power reruns; baseline recheck not flagged (+0.32%) |
| Power | package power median 84.99 W on every trial; CPU temperature 88.9-94.9°C |

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 94.9%, `vectorization_density=high`,
`allocation_pressure=low` (the shape filter was off, so it only ranked candidates).

| Trial | Role | Ratio | Bandwidth probe |
|---|---|---|---|
| 35 | warm-up | 16.1336 | 104.8 GB/s (waited 30 s) |
| 36 | warm-up | 16.0695 | 95.3 GB/s |
| 37 | calibration | 16.0662 | 90.8 GB/s |
| 38 | calibration | 16.0730 | 93.2 GB/s |
| 39 | calibration | 15.9603 | 90.0 GB/s |
| 93 | recheck | 16.0840 (+0.32%) | 105.4 GB/s (waited 30 s) |

Calibration mean 16.0332, 95% CI [15.8761, 16.1904]. Warm-up settled after the minimum two reps (2,333 s).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 40-53 | screening | 14 candidates | 15.965-16.139 | | all survived (two skipped as unchanged code) |
| 54-56 | confirmation | `-fprefetch-loop-arrays` | 16.121 | +0.55% | reject (CI-clear, under the 1% bar) |
| 57-59 | confirmation | `-fgraphite-identity` | 16.068 | +0.22% | reject |
| 60-62 | confirmation | `-flto` | 16.005 | -0.18% | reject |
| 63-65 | confirmation | `-fno-pie -no-pie` | 16.069 | +0.22% | reject |
| 66-68 | confirmation | `-fno-stack-protector` | 16.068 | +0.21% | reject |
| 69-71 | confirmation | `-fcf-protection=none` | 16.068 | +0.22% | reject |
| 72-74 | confirmation | `-U_FORTIFY_SOURCE` | 16.072 | +0.24% | reject |
| 75-77 | confirmation | `-funroll-loops` | 16.086 | +0.33% | reject |
| 78-80 | confirmation | `-Ofast` | 16.199 | +1.03% | reject (CI overlaps baseline) |
| 81-83 | confirmation | `-ffast-math` | 16.184 | +0.94% | reject (same code as `-Ofast`) |
| 84-86 | confirmation | `-fno-math-errno` | 16.074 | +0.25% | reject |
| 87-89 | confirmation | `-fno-unswitch-loops` | 16.067 | +0.21% | reject |
| 90-92 | confirmation (fast-tracked) | `-march=native` | 16.531 | +3.11% | **accept** |
| 94-96 | combination | `-march=native` | 16.598 | +3.52% | **accept** |
| 97-99 | PGO | `-march=native -fprofile-use` | 16.573 | -0.15% | reject |
| 100-102 | vector width | `-march=native -mprefer-vector-width=256` | 16.589 | -0.05% | reject |

The Phase 6 deltas are against `-O3 -march=native`. `-march=native` built the same code (`f4a24b15`) as in the
first mine, and so did every flag both mines tried.

## Observations

- **The bandwidth gate waited 30 s before 10 of 66 timed runs**, against once in the first mine. Each time the
  re-probe read 104.6-105.6 GB/s, the session best, so the first probe was catching the tail of the previous
  run (the traps log's 2026-10-23 lesson). Ratios after a wait (16.008-16.644) don't differ from the rest. No
  throttle state like niwot's appeared in 21 hours.
- **Package power read 84.99 W on every trial again**, the platform limit, and the CPU 88.9-94.9°C. Neither moved
  with ratio.
- **Across the two mines, `-O3` has now run 11 times** (warm-up, calibration and recheck): 15.960-16.134, with
  9 of 11 inside 16.064-16.084. Trial 39 is the only rep below 16.06.
- **Only `-march=native` and fast-math moved lbm by more than 0.6%.** With 32 copies streaming the lattice from
  memory and the package at its power limit, code-layout and hardening flags have nothing to act on.

# `cfm mine` results: 849.fotonik3d_s on `niwot`, 2026-11-27

The twelfth fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `849.fotonik3d_s` is the
SPECspeed version of Fotonik3D, a Fortran finite-difference time-domain solver for Maxwell's equations, parallelized
with OpenMP. `chicago` mined it on 2026-11-11 ([write-up](mining_results.849.fotonik3d_s.2026-11-11.md)) and accepted
nothing. Its rate counterpart hit this host's memory throttle (#26) on 2026-11-14
([write-up](mining_results.749.fotonik3d_r.2026-11-14.md)), so this mine could have stopped after Phase 1 as
tealeaf_s did. It didn't. Its corpus shape is memory-bound at 92.7%, so the shape filter dropped the same 8
candidates as on `chicago`.

## Headline result

**No flag beat plain `-O3`** (ratio 0.8105), the same result as `chicago`.

- **No throttling.** Phase 1's reps sat within 4% (0.779-0.812), the throttle stop didn't fire, every run drew
  17.2-17.8 W, the bandwidth probe read 45.1-45.7 GB/s before every run, and no rerun rule fired.
- **Every flagset read CI-clear *below* the baseline (-1.37% to -3.41%), but most of that is a slow drift.** The
  `-O3` recheck, 8 hours after calibration, read 0.7910 (-2.41%, flagged), at the same power and bandwidth. The
  candidates' deltas get worse in the order they ran, so they say more about when each one ran than about the flag.
  Against the recheck, every flagset is within ±1.1%.
- **The `-march` code was flat on both hosts.** `-march=native` and `-march=znver5` built the same code (`f386319b`,
  also `chicago`'s). It read -1.53% three hours before the recheck and -2.39% two hours after it. That's 0.86% lower
  on the same binary. All six runs pooled read +0.46% against the recheck. On `chicago` it read -0.71% and -0.59%.
- **PGO -3.34% and `-mtune=znver5` -3.41%,** the last two flagsets to run. Against the recheck, both are about -1%.
  On `chicago` they read -1.25% and -1.14%.
- **The `-O3` code is the same on both hosts** (`2ee04fbd`), as is `-frecursive`'s, which was skipped as unchanged
  code on both.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 849.fotonik3d_s --settle-seconds 600` (uncapped, from the restarted fpspeed queue) |
| Code | `main` at `b71283f` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 215 |
| Started / finished | 2026-11-27T04:02:21Z / 2026-11-27T18:14:38Z (14h12m) |
| Final status | `converged` |
| Trials | 36 (2936-2971), no reruns, 1 skipped as unchanged code |
| Candidates screened / confirmed | 5 / 4 (plus `-march=native` fast-tracked; `-frecursive` skipped) |
| Excluded on shape (Phase 2) | 8: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 17 of 31, mean +20.59%) |
| Accepted | none |
| Winning flags | `["-O3"]`, +0.00% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (45.1-45.7 GB/s); no reruns; baseline recheck **flagged** (-2.41%) |
| Power | package power median 17.5-17.8 W on `-O3`-class code, 17.2-17.3 W on the `-march` code; CPU temperature 88-90°C |

A trial took about 24 minutes with the settle. `chicago` ran its 35 trials in 3h43m, at 85 W. Every timed run's
`.rsf` reads `valid: S` for fotonik3d.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 92.7%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 2936 | warm-up | 0.77921 | 17.4 W |
| 2937 | warm-up | 0.80591 | 17.7 W |
| 2938 | warm-up | 0.80988 | 17.7 W |
| 2939 | calibration | 0.81014 | 17.7 W |
| 2940 | calibration | 0.81163 | 17.7 W |
| 2941 | calibration | 0.80973 | 17.7 W |
| 2962 | recheck | 0.79099 (-2.41%, flagged) | 17.6 W |

Warm-up settled after 3 reps (4377 s). The first rep read 3.8% below the others at slightly lower power: a warm-up
transient, not the throttle (the throttle stop needs two reps more than 10% down). The calibration mean is 0.81050,
95% CI ±0.31%. That's tight, which is why every later flagset came out CI-clear one way or the other.

## Trials

In the order they ran. "vs recheck" compares each mean with the `-O3` recheck (trial 2962), which ran between
`-march=native` and PGO.

| Trials | Phase | Flags (on `-O3`) | Reps | Mean | Delta | vs recheck | Verdict |
|---|---|---|---|---|---|---|---|
| 2942-2945 | screening | 4 candidates | 0.806, 0.804, 0.802, 0.798 | | -0.45% to -1.42% | | all survived (`-frecursive` skipped as unchanged code) |
| 2947-2949 | confirmation | `-fprefetch-loop-arrays` | 0.801, 0.799, 0.798 | 0.7994 | -1.37% | +1.06% | reject |
| 2950-2952 | confirmation | `-fgraphite-identity` | 0.794, 0.794, 0.792 | 0.7934 | -2.11% | +0.31% | reject |
| 2953-2955 | confirmation | `-fstack-arrays` | 0.794, 0.795, 0.790 | 0.7929 | -2.17% | +0.24% | reject |
| 2956-2958 | confirmation | `-flto` | 0.786, 0.787, 0.787 | 0.7869 | -2.91% | -0.52% | reject |
| 2959-2961 | confirmation (fast-tracked) | `-march=native` | 0.799, 0.800, 0.796 | 0.7981 | -1.53% | +0.89% | reject |
| 2962 | recheck | `-O3` | 0.791 | | -2.41% | | flagged |
| 2963-2965 | PGO | `-fprofile-use` | 0.786, 0.782, 0.783 | 0.7834 | -3.34% | -0.96% | reject |
| 2966-2968 | microarch | `-march=znver5` | 0.792, 0.789, 0.793 | 0.7912 | -2.39% | +0.02% | reject |
| 2969-2971 | microarch | `-mtune=znver5` | 0.781, 0.785, 0.782 | 0.7829 | -3.41% | -1.02% | reject |

Phase 5 ran no trials, Phase 6 layered on plain `-O3`, and the vector-width multiplier was skipped because the
winning set has no `-march=`. No Phase 4 reject was CI-clear *above* the baseline, so PGO had no near-miss variant.

## The drift

The four screening runs, all different code, fell in the order they ran: 0.806, 0.804, 0.802, 0.798 over about
70 minutes. The confirmation means fell the same way over the next six hours, and the `-O3` recheck landed with
them, at 0.791. The `-march` binary read 0.798 at 13:18-14:07Z and 0.791 at 16:12-17:01Z. Package power (17.5-17.8 W on
`-O3`-class code), the bandwidth probe (45.1-45.7 GB/s) and CPU temperature (88-90°C) stayed flat throughout. This
isn't the stepped throttle that tealeaf_s and fotonik3d_r showed (#26), where one binary jumps between levels that
track package power. It's a gradual slide of about 2.5% over 12 hours with no measured cause: the "continuing drift"
case that CLAUDE.md's 2026-08-25 warm-up entry leaves open, and cactus_s's upward drift (+1.5%) run in reverse.

It doesn't change the result. Against the recheck, the nearest `-O3` measurement in time, nothing moved more than
about 1%, and `chicago`, which has no drift, found the same flat picture. It does make every knowledge row this run wrote
about 1-2% more negative than the flag deserves (below).

## Knowledge table

The memory-bound rows this run changed (all rejects, so accept counts don't move):

| Flag | Before | After |
|---|---|---|
| `-march=native` | 17 of 31, +20.59% | 17 of 32, +19.90% |
| `-march=znver5` | 5 of 14, +0.89% | 5 of 15, +0.68% |
| `-mtune=znver5` | 0 of 14, -0.15% | 0 of 15, -0.37% |
| `-flto` | 7 of 25, +2.41% | 7 of 26, +2.20% |
| `-fprofile-use` | 5 of 26, -3.51% | 5 of 27, -3.50% |
| `-fstack-arrays` | 0 of 4, -0.72% | 0 of 5, -1.01% |
| `-fprefetch-loop-arrays` | 5 of 31, +1.61% | 5 of 32, +1.52% |
| `-fgraphite-identity` | 3 of 28, +1.38% | 3 of 29, +1.26% |

## Compared with `chicago`

| | `chicago` (2026-11-11) | `niwot` |
|---|---|---|
| Baseline | 1.9366, ±0.45%, 85 W | 0.8105, ±0.31%, 17.7 W; recheck -2.41% (flagged) |
| `-O3` code | `2ee04fbd` | `2ee04fbd` |
| `-march` code (`f386319b`) | -0.71% / -0.59% | -1.53% / -2.39% (+0.89% / +0.02% vs recheck) |
| PGO | -1.25% | -3.34% (-0.96% vs recheck) |
| `-mtune=znver5` | -1.14% | -3.41% (-1.02% vs recheck) |
| Other flags | -0.97% to +0.20% | -2.91% to -1.37% (-0.52% to +1.06% vs recheck) |
| Total | +0.00% | +0.00% |
| Run | 35 trials, 3h43m | 36 trials, 14h12m |

`chicago` reads 2.4 times this host's ratio, between the compute-heavier fpspeed benchmarks (about 1.9 times) and
tealeaf_s (2.6-3.1 times), in line with a 92.7% memory-bound code and `chicago`'s roughly double bandwidth. Both hosts
agree: on one large grid shared by every thread, none of the flags tried here helps. `-march=native
-mprefer-vector-width=256`, which gained 1.5% on fotonik3d_r on `chicago`, is still untried on fotonik3d_s on either
host.

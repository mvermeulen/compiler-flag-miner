# `cfm mine` results: 865.roms_s on `niwot`, 2026-11-27

The thirteenth and last fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `865.roms_s` is
the SPECspeed version of ROMS, the Regional Ocean Modeling System, a Fortran ocean-circulation code parallelized
with OpenMP. `chicago` mined it on 2026-11-12 ([write-up](mining_results.865.roms_s.2026-11-12.md)) and accepted
`-O3 -march=native` at +1.95%. Its rate counterpart throttled on this host on 2026-11-15
([write-up](mining_results.765.roms_r.2026-11-15.md)). Its corpus shape is memory-bound at 95.1%, so the shape filter
dropped the same 8 candidates as on `chicago`.

## Headline result

**`-O3 -march=native`, +3.16% over plain `-O3`** (ratio 0.7272 → 0.7502), the same winner as `chicago` (+1.95%). Most of
the margin is probably drift.

- **The `-O3` binary drifted by about 5% during the run, down first and then up.** The calibration reps read
  0.732, 0.730, 0.719. The candidates measured over the next five hours bottomed out at 0.705-0.716, then climbed to
  0.740-0.757 by the end. The `-O3` recheck, 12 hours in, read 0.7476 (+2.80%, flagged). Unlike fotonik3d_s's slide,
  package power followed it loosely (about 17.3-17.5 W in the trough, 17.6-17.7 W at the ends, on `-O3`-class code).
  The bandwidth probe read 44.8-45.8 GB/s throughout. There were no steps, so the throttle stop didn't fire.
- **Against the recheck, `-march=native` reads +0.34%.** Its three reps (0.749, 0.749, 0.753) were run in the
  hour and a half before the recheck. Against the calibration they read +3.16%, CI-clear. The true gain lies
  between the two. `chicago`'s +1.95% is in that range, and it measured with a ±0.5% baseline and no drift.
- **The other flags' verdicts follow when they ran.** `-fprefetch-loop-arrays` -2.45% and `-fgraphite-identity`
  -1.89% ran in the trough. `-fstack-arrays` +0.55% and `-flto` +1.86% ran on the climb. All were rejected on CI
  overlap with a wide (±2.3%) baseline. Against the recheck they read -5.1% to -0.9%.
- **PGO +1.01% and `-mprefer-vector-width=256` +0.30%** on top of `-march=native`, both rejected (`chicago`: -0.35% and
  -0.52%). The microarch multiplier was skipped because the winning set already has `-march=native`.
- **The `-O3` code is the same on both hosts** (`6a711420`), as is `-frecursive`'s, which was skipped as unchanged
  code on both.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 865.roms_s --settle-seconds 600` (uncapped, the last mine in the restarted fpspeed queue) |
| Code | `main` at `e94cb2d` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 216 |
| Started / finished | 2026-11-27T18:24:38Z / 2026-11-28T12:49:03Z (18h24m) |
| Final status | `converged` |
| Trials | 32 (2972-3003), no reruns, 1 skipped as unchanged code |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked; `-frecursive` skipped) |
| Excluded on shape (Phase 2) | 8: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 17 of 32, mean +19.90%) |
| Accepted in Phase 4 | `-march=native` +3.16% |
| Winning flags | `["-O3", "-march=native"]`, +3.16% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (44.8-45.8 GB/s); no reruns; baseline recheck **flagged** (+2.80%) |
| Power | package power median 17.3-17.7 W on `-O3`-class code, 16.9-17.0 W on `-march=native` code; CPU temperature 88-92°C |

A trial took about 35 minutes with the settle. `chicago` ran its 32 trials in 4h12m, at 85 W. Every timed run's
`.rsf` reads `valid: S` for roms.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 95.1%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 2972 | warm-up | 0.73685 | 17.7 W |
| 2973 | warm-up | 0.73152 | 17.6 W |
| 2974 | calibration | 0.73184 | 17.6 W |
| 2975 | calibration | 0.73029 | 17.6 W |
| 2976 | calibration | 0.71946 | 17.5 W |
| 2997 | recheck | 0.74759 (+2.80%, flagged) | 17.7 W |

Warm-up settled after the minimum 2 reps (4265 s). The calibration mean is 0.72720, 95% CI ±2.3%. The third rep was
already on the way down.

## Trials

In the order they ran. "vs recheck" compares each mean with the `-O3` recheck (trial 2997), which ran between
`-march=native` and PGO.

| Trials | Phase | Flags (on `-O3`) | Reps | Mean | Power | Delta | vs recheck | Verdict |
|---|---|---|---|---|---|---|---|---|
| 2977-2980 | screening | 4 candidates | 0.709, 0.719, 0.723, 0.723 | | 17.4-17.6 W | -1.43% to +0.50% | | all survived (`-frecursive` skipped as unchanged code) |
| 2982-2984 | confirmation | `-fprefetch-loop-arrays` | 0.705, 0.711, 0.712 | 0.7093 | 17.3-17.5 W | -2.45% | -5.12% | reject |
| 2985-2987 | confirmation | `-fgraphite-identity` | 0.715, 0.709, 0.716 | 0.7135 | 17.3-17.4 W | -1.89% | -4.56% | reject |
| 2988-2990 | confirmation | `-fstack-arrays` | 0.726, 0.733, 0.735 | 0.7312 | 17.6-17.7 W | +0.55% | -2.20% | reject |
| 2991-2993 | confirmation | `-flto` | 0.740, 0.741, 0.742 | 0.7407 | 17.6 W | +1.86% | -0.92% | reject |
| 2994-2996 | confirmation (fast-tracked) | `-march=native` | 0.749, 0.749, 0.753 | 0.7502 | 16.9 W | +3.16% | +0.34% | **accept** |
| 2997 | recheck | `-O3` | 0.748 | | 17.7 W | +2.80% | | flagged |
| 2998-3000 | PGO | `-march=native -fprofile-use` | 0.757, 0.759, 0.757 | 0.7578 | 16.9-17.0 W | +1.01% | | reject |
| 3001-3003 | vector width | `-march=native -mprefer-vector-width=256` | 0.751, 0.754, 0.752 | 0.7524 | 17.0 W | +0.30% | | reject |

Phase 5's greedy walk started from `-O3 -march=native` (the only accept, reused under #39) and had nothing to add. No
Phase 4 reject was CI-clear above the baseline, so PGO had no near-miss variant. The PGO builds had one fingerprint
(`e5812259`).

## The drift

This is the third fpspeed mine in a row to drift with no throttle steps, and the largest. Fotonik3d_s slid 2.5% down
over 12 hours. Cactus_s crept 1.5% up as its power rose 3 W. Here the ratio went down about 4% and back up
about 5% over 18 hours. On `-O3`-class code, package power moved with it, but only by about 0.4 W, much less than
the 1 W per level of the stepped throttle on tealeaf_s and roms_r (#26). Every flagset ran its three reps
back to back, so each one sampled a single point on the curve, and its delta mostly measured the curve. The
recheck was the one guard that saw it, and it changes no verdict.

The accept stands on its direction: `-march=native` read above the recheck too, and `chicago` accepted it as well.
But +3.16% overstates it. Interleaving `-O3` and `-march=native` reps would show how much (#43 has the same need on
cloverleaf_s).

## Knowledge table

The memory-bound rows this run changed:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 17 of 32, +19.90% | 18 of 33, +19.39% |
| `-flto` | 7 of 26, +2.20% | 7 of 27, +2.19% |
| `-fprofile-use` | 5 of 27, -3.50% | 5 of 28, -3.34% |
| `-mprefer-vector-width=256` | 2 of 22, -1.14% | 2 of 23, -1.08% |
| `-fstack-arrays` | 0 of 5, -1.01% | 0 of 6, -0.75% |
| `-fprefetch-loop-arrays` | 5 of 32, +1.52% | 5 of 33, +1.40% |
| `-fgraphite-identity` | 3 of 29, +1.26% | 3 of 30, +1.15% |

The drift pushed the trough flags' rows down and `-march=native`'s up. Each row moved by only a fraction of a
point.

## Compared with `chicago`

| | `chicago` (2026-11-12) | `niwot` |
|---|---|---|
| Baseline | 2.6194, ±0.5%, 85 W; recheck +0.14% | 0.7272, ±2.3%, 17.6 W; recheck +2.80% (flagged) |
| `-O3` code | `6a711420` | `6a711420` |
| `-march=native` | +1.95% | +3.16% (+0.34% vs recheck) |
| PGO on top | -0.35% | +1.01% |
| `=256` on top | -0.52% | +0.30% |
| Other flags | -0.55% to +0.10% | -2.45% to +1.86% (ordered by when they ran) |
| Total | +1.95% | +3.16% |
| Run | 32 trials, 4h12m | 32 trials, 18h24m |

`chicago` reads 3.6 times this host's ratio, the widest gap of any fpspeed benchmark, for the most memory-bound one
(95.1%). Both hosts pick the same winner and agree nothing helps on top of it.

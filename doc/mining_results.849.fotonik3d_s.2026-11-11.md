# `cfm mine` results: 849.fotonik3d_s on `chicago`, 2026-11-11

This is the eighth fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`849.fotonik3d_s` mine on any host. `849.fotonik3d_s` is the SPECspeed version of Fotonik3D, a Fortran finite-difference
time-domain solver for Maxwell's equations, parallelized with OpenMP; its rate counterpart was
[mined here on 2026-11-05](mining_results.749.fotonik3d_r.2026-11-05.md) (+7.04%,
`-O3 -march=native -mprefer-vector-width=256`). Its corpus shape is memory-bound at 92.7%.

## Headline result

**No flag beat plain `-O3`** (ratio 1.9366). Unlike fotonik3d_r, where `-march=native` gave +5.43%.

- **`-march=native` read -0.71%**, CI-clear below baseline. It was fast-tracked on the memory-bound prior (accepted
  14 of 19). `-march=znver5` built the same code (`f386319b`) and read -0.59%.
- **`-mprefer-vector-width=256` was never tried.** On fotonik3d_r it added +1.52% on top of `-march=native`, but the
  vector-width multiplier only runs on a winning set with an `-march=`, and here `-march=native` lost.
- **PGO read -1.25%, `-mtune=znver5` -1.14%, `-fgraphite-identity` -0.97%**, all clear losses. On fotonik3d_r PGO
  was -4.5%.
- **`-fprefetch-loop-arrays` +0.03%, `-fstack-arrays` +0.20%, `-flto` +0.02%**, all rejected. `-frecursive` built
  the same code as `-O3` and was skipped.
- **The shape filter dropped 8 candidates** on the 92.7% memory-bound read, `-Ofast` and `-ffast-math` among them.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 849.fotonik3d_s` (uncapped, defaults) |
| Code | `main` at `944da04` (no code changes since `c933ee2`, PR #71) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 23 |
| Started / finished | 2026-11-11T11:39:47Z / 2026-11-11T15:22:49Z (3h43m) |
| Final status | `converged` |
| Trials | 35 (1036-1070), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 5 / 4 (plus `-march=native` fast-tracked, rejected) |
| Excluded on shape (Phase 2) | 8 (`-flto` kept, exempt) |
| Fast-tracked (M4) | `-march=native` (accepted 14 of 19, mean +16.31%) |
| Skipped as unchanged code | `-frecursive` (same code as `-O3`) |
| Winning flags | `["-O3"]`, +0.00% |
| Guards | bandwidth gate waited 30 s before 25 of 34 timed runs; no reruns; baseline recheck not flagged (+0.33%) |
| Power | package power median 84.96-85.15 W on every trial; CPU temperature 87.9-90.5°C |

A non-PGO trial took about 6.5 minutes and a PGO trial about 8. Every trial's `.rsf` reads `valid: S` for fotonik3d.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 92.7%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 1036 | warm-up | 1.94281 |
| 1037 | warm-up | 1.93636 |
| 1038 | calibration | 1.93618 |
| 1039 | calibration | 1.93338 |
| 1040 | calibration | 1.94034 |
| 1061 | recheck | 1.94302 (+0.33%) |

The calibration mean is 1.936633, with a 95% CI of [1.92794, 1.94533] (±0.45%). Warm-up settled after the minimum
two reps (750 s). Every `-O3` build had the same code fingerprint (`2ee04fbd`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1041-1045 | screening | 5 candidates | 1.917-1.941 | | all survived (`-frecursive` skipped as unchanged code) |
| 1046-1048 | confirmation | `-fprefetch-loop-arrays` | 1.9373 | +0.03% | reject |
| 1049-1051 | confirmation | `-fgraphite-identity` | 1.9179 | -0.97% | reject (CI clear below baseline) |
| 1052-1054 | confirmation | `-fstack-arrays` | 1.9404 | +0.20% | reject |
| 1055-1057 | confirmation | `-flto` | 1.9370 | +0.02% | reject |
| 1058-1060 | confirmation (fast-tracked) | `-march=native` | 1.9229 | -0.71% | reject (CI clear below baseline) |
| 1062-1064 | PGO | `-fprofile-use` | 1.913 | -1.25% | reject |
| 1065-1067 | microarch | `-march=znver5` | 1.925 | -0.59% | reject |
| 1068-1070 | microarch | `-mtune=znver5` | 1.915 | -1.14% | reject |

With nothing accepted, Phase 5 ran no trials and Phase 6 layered on plain `-O3`. The vector-width multiplier was
skipped because the winning set has no `-march=`.

## Observations

- **fotonik3d's `-march=native` win doesn't carry over from rate to speed here**: +5.43% on 32 copies, -0.71% on 32
  threads. With 32 copies each working on its own small grid, vector width matters; one large grid shared by 32
  threads is more likely to be limited by memory bandwidth alone, which wider vectors don't help. That's a guess
  from the shape (92.7% memory-bound), not something this run measured.
- **`-march=native -mprefer-vector-width=256` is still untried** (open item 15). On fotonik3d_r it beat
  `-march=native` alone by 1.5%, so 256-bit vectors might avoid the loss here even if they don't gain.
- **The third flat fpspeed benchmark here**, after tealeaf_s and cloverleaf_s, all three 70%-plus memory-bound
  stencil or sparse codes drawing the full 85 W at `-O3`.
- **niwot hasn't mined fotonik3d_s yet.**

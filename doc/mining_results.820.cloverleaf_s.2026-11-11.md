# `cfm mine` results: 820.cloverleaf_s on `chicago`, 2026-11-11

This is the sixth fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`820.cloverleaf_s` mine on any host. `820.cloverleaf_s` is CloverLeaf, a Fortran hydrodynamics mini-app from the UK
Mini-App Consortium that solves the compressible Euler equations on a structured grid, parallelized with OpenMP. Its
corpus shape is memory-bound at 88.2%, the strongest memory-bound read mined here so far.

## Headline result

**No flag beat plain `-O3`** (ratio 1.8570). A clean reject: no candidate came within the 1% bar.

- **`-march=native` read +0.55%**, CI-clear of baseline but under the 1% bar. It was fast-tracked on the memory-bound
  prior (accepted 13 of 17). `-march=znver5` built the same code (`3de86b3d`) and read +0.57%; `-mtune=znver5` read
  -0.14%.
- **PGO read +0.33%**, and the near-miss variant with `-march=native` added read +0.80%. Both were rejected under the
  1% bar. Unlike on tealeaf_s, the PGO trials were cheap (about 13 minutes each).
- **`-fprefetch-loop-arrays` +0.10%, `-fgraphite-identity` +0.11%, `-fstack-arrays` +0.07%, `-flto` +0.05%**, all
  rejected. `-frecursive` built the same code as `-O3` and was skipped.
- **The shape filter dropped 8 candidates** on the 88.2% memory-bound read, `-Ofast` and `-ffast-math` among them.

The flat result fits the code: CloverLeaf's kernels stream whole grid arrays through memory each time step, and these
flags don't change how much data moves. Package power held at 84.9 W on every trial, so the chip was fully busy.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 820.cloverleaf_s` (uncapped, defaults) |
| Code | `main` at `e6b01f7` (no code changes since `9d832ae`, PR #70) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 21 |
| Started / finished | 2026-11-11T02:00:04Z / 2026-11-11T07:36:23Z (5h36m) |
| Final status | `converged` |
| Trials | 38 (966-1003), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 5 / 4 (plus `-march=native` fast-tracked, rejected) |
| Excluded on shape (Phase 2) | 8 (`-flto` kept, exempt) |
| Fast-tracked (M4) | `-march=native` (accepted 13 of 17, mean +17.06%) |
| Skipped as unchanged code | `-frecursive` (same code as `-O3`) |
| Winning flags | `["-O3"]`, +0.00% |
| Guards | bandwidth gate waited 30 s before 33 of 37 timed runs; no reruns; baseline recheck not flagged (+0.06%) |
| Power | package power median 84.89-84.97 W on every trial; CPU temperature 87.8-91.0°C |

A non-PGO trial took about 8 minutes and a PGO trial about 13. Every trial's `.rsf` reads `valid: S` for cloverleaf.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 88.2%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 966 | warm-up | 1.85397 |
| 967 | warm-up | 1.85564 |
| 968 | calibration | 1.85382 |
| 969 | calibration | 1.85865 |
| 970 | calibration | 1.85861 |
| 991 | recheck | 1.85807 (+0.06%) |

The calibration mean is 1.857027, with a 95% CI of [1.85012, 1.86393] (±0.37%). Warm-up settled after the minimum
two reps (981 s). Every `-O3` build had the same code fingerprint (`c83c0a06`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 971-975 | screening | 5 candidates | 1.853-1.859 | | all survived (`-frecursive` skipped as unchanged code) |
| 976-978 | confirmation | `-fprefetch-loop-arrays` | 1.8590 | +0.10% | reject |
| 979-981 | confirmation | `-fgraphite-identity` | 1.8590 | +0.11% | reject |
| 982-984 | confirmation | `-fstack-arrays` | 1.8583 | +0.07% | reject |
| 985-987 | confirmation | `-flto` | 1.8580 | +0.05% | reject |
| 988-990 | confirmation (fast-tracked) | `-march=native` | 1.8673 | +0.55% | reject (CI-clear, under the 1% bar) |
| 992-994 | PGO | `-fprofile-use` | 1.863 | +0.33% | reject |
| 995-997 | PGO (near-miss) | `-march=native -fprofile-use` | 1.872 | +0.80% | reject (under the 1% bar) |
| 998-1000 | microarch | `-march=znver5` | 1.868 | +0.57% | reject |
| 1001-1003 | microarch | `-mtune=znver5` | 1.854 | -0.14% | reject |

With nothing accepted, Phase 5 ran no trials and Phase 6 layered on plain `-O3`. The vector-width multiplier was
skipped because the winning set has no `-march=`.

## Observations

- **The second flat fpspeed benchmark here**, after tealeaf_s. Both are UK Mini-App Consortium codes with 70%-plus
  memory-bound reads that stream large arrays, and both draw the full 85 W at `-O3`.
- **`-march=native -fprofile-use` at +0.80% is the closest thing to a win.** Its reps were tight (1.871-1.872), so
  it's probably real, but it's under the 1% bar like `-march=native` alone, and the bar is what it's for.
- **The bandwidth gate waited before 33 of 37 timed runs**, more than any mine here. Every re-probe read the session
  best (about 106 GB/s), so it was catching the tail of the previous run, and the reps stayed tight (baseline ±0.37%,
  most candidates under ±0.05%).
- **Fast-math wasn't measured**: the 88.2% read is far over the 55% gate (open item 14).
- **niwot hasn't mined cloverleaf_s yet.**

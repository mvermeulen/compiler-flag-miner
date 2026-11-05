# `cfm mine` results: 749.fotonik3d_r on `chicago`, 2026-11-05

The third benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first Fortran one.
`749.fotonik3d_r` is a finite-difference time-domain electromagnetics code, one of the three fprate benchmarks
`niwot` holds back as too bandwidth-heavy for that host. Its corpus shape is the most memory-bound yet: 97.3%.

## Headline result

**`-O3 -march=native -mprefer-vector-width=256`, +7.04% over plain `-O3`** (ratio 38.726 → 41.452).

- **`-march=native` gave +5.43%** (Phase 5, ratio 40.829). It was fast-tracked on the cluster prior (accepted 3 of
  3: lbm twice, cactus), and all six of its reps (40.78-40.95) beat every `-O3` rep (38.63-38.82).
- **`-mprefer-vector-width=256` added +1.52% on top**, the first vector-width accept on this host. Its three reps
  (41.41-41.51) are all above every `-march=native` rep. With `-march=native`, GCC targets 512-bit AVX-512 vectors
  for Zen5; telling it to prefer 256-bit ones is faster here. On lbm and cactus the same flag was flat.
- **PGO was a clear regression, -4.53%** on top of `-march=native` (38.98, three reps within 0.01%). `-flto` alone
  was -2.38% (37.80, CI clear below baseline). Both are real losses, not noise.
- **Every other candidate was slightly negative:** `-fprefetch-loop-arrays` -0.53%, `-fstack-arrays` -0.36%,
  `-fgraphite-identity` -0.31%. `-frecursive` built code identical to `-O3` and was skipped.
- **The shape filter dropped 8 candidates** on the 97.3% memory-bound read, `-Ofast`, `-ffast-math` and
  `-funroll-loops` among them.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 749.fotonik3d_r` (uncapped, defaults) |
| Code | `main` at `f31ba64` (no code changes since, only docs) |
| Experiment id | 5 |
| Started / finished | 2026-11-05T11:06:29Z / 2026-11-05T20:14:21Z (9h08m) |
| Final status | `converged` |
| Trials | 35 (133-167), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 5 / 1 (plus `-march=native` fast-tracked, accepted) |
| Excluded on shape (Phase 2) | 8 |
| Fast-tracked (M4) | `-march=native` (accepted 3 of 3, mean +7.44%) |
| Skipped as unchanged code | `-frecursive` |
| Winning flags | `["-O3", "-march=native", "-mprefer-vector-width=256"]`, +7.04% |
| Guards | bandwidth gate waited once (30 s, trial 133); no reruns; baseline recheck not flagged (-0.26%) |
| Power | package power median 84.99 W on every trial; CPU temperature 89.1-94.5°C |

Each trial took about 16 minutes.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 97.3%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 133 | warm-up | 38.758 |
| 134 | warm-up | 38.823 |
| 135 | calibration | 38.750 |
| 136 | calibration | 38.763 |
| 137 | calibration | 38.666 |
| 158 | recheck | 38.628 (-0.26%) |

Calibration mean 38.726, 95% CI [38.595, 38.858] (±0.34%). Warm-up settled after the minimum two reps (1,972 s).
Every `-O3` build had the same code fingerprint (`c7909d50`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 138-142 | screening | 5 candidates | 37.82-38.68 | | all survived (`-frecursive` skipped as unchanged code) |
| 143-145 | confirmation | `-fprefetch-loop-arrays` | 38.522 | -0.53% | reject |
| 146-148 | confirmation | `-fgraphite-identity` | 38.605 | -0.31% | reject |
| 149-151 | confirmation | `-fstack-arrays` | 38.586 | -0.36% | reject |
| 152-154 | confirmation | `-flto` | 37.804 | -2.38% | reject (CI clear below baseline) |
| 155-157 | confirmation (fast-tracked) | `-march=native` | 40.895 | +5.60% | **accept** |
| 159-161 | combination | `-march=native` | 40.829 | +5.43% | **accept** |
| 162-164 | PGO | `-march=native -fprofile-use` | 38.979 | -4.53% | reject |
| 165-167 | vector width | `-march=native -mprefer-vector-width=256` | 41.452 | +1.52% | **accept** |

The Phase 6 deltas are against `-O3 -march=native`; the microarch multiplier was skipped because the winning set
already had `-march=native`.

## Observations

- **Every flagset built the same code on every rep**, the PGO reps included (`1ceb1300` on all three), unlike
  cactus, whose build embeds its build time. So the PGO loss is one consistent binary, not a bad training run.
- **The run was as steady as lbm's.** Package power 84.99 W on every trial, CPU 89-95°C, the bandwidth gate
  waited only before the first trial (probes 90.4-102.5 GB/s), and no rep needed a rerun.
- **`-march=native` across the memory-bound cluster here: +2.9% (lbm), +16.5% (cactus), +5.4% (fotonik3d).**
  Accepted every time, with very different sizes.
- **LTO and PGO have lost on all three benchmarks here so far** (lbm -0.2% to -0.5% and -0.2% to +0.1%, cactus
  -0.1% and +0.4%, fotonik3d -2.4% and -4.5%). On niwot's intrate benchmarks they were the main wins.

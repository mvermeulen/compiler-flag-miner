# `cfm mine` results: 765.roms_r on `chicago`, 2026-11-05

The fourth benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the last of the three
fprate benchmarks `niwot` holds back as too bandwidth-heavy. `765.roms_r` is the Regional Ocean Modeling System, a
Fortran ocean-circulation code. Its corpus shape is memory-bound at 95.0%.

## Headline result

**`-O3 -march=native`, +7.19% over plain `-O3`** (ratio 36.618 → 39.250).

- **`-march=native` is the only win.** It was fast-tracked on the cluster prior (accepted 4 of 4: lbm twice,
  cactus, fotonik3d). All six of its reps (39.04-39.34) beat every `-O3` rep (36.59-36.68).
- **`-mprefer-vector-width=256` was a clear loss here, -4.04%** (37.664 on top of `-march=native`). On fotonik3d,
  the previous mine, the same flag was a +1.52% win. So 512-bit AVX-512 vectors help roms and hurt fotonik3d.
- **PGO read +0.77% on top of `-march=native` and was rejected.** Its CI [39.30, 39.80] overlaps the
  `-march=native` CI [38.95, 39.55], and the delta is under the 1% bar anyway. All three PGO reps built the same
  code (`4c21dac0`).
- **Every other candidate was within ±0.7% of `-O3`:**
  - `-fprefetch-loop-arrays` +0.63%, rejected: its CI was clear of baseline but the delta is under the 1% bar.
  - `-flto` +0.09%, `-fgraphite-identity` -0.19%, `-fstack-arrays` -0.31%.
  - `-frecursive` built code identical to `-O3`, so its timed run was skipped.
- **The shape filter dropped 8 candidates** on the 95.0% memory-bound read, `-Ofast`, `-ffast-math` and
  `-funroll-loops` among them.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 765.roms_r` (uncapped, defaults) |
| Code | `main` at `27ae1e7` (no code changes since `f31ba64`, only docs) |
| Experiment id | 6 |
| Started / finished | 2026-11-05T20:14:52Z / 2026-11-06T09:37:23Z (13h23m) |
| Final status | `converged` |
| Trials | 35 (168-202), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 5 / 1 (plus `-march=native` fast-tracked, accepted) |
| Excluded on shape (Phase 2) | 8 |
| Fast-tracked (M4) | `-march=native` (accepted 4 of 4, mean +6.98%) |
| Skipped as unchanged code | `-frecursive` |
| Winning flags | `["-O3", "-march=native"]`, +7.19% |
| Guards | bandwidth gate waited 30 s before 17 of 34 timed runs; no reruns; baseline recheck not flagged (+0.16%) |
| Power | package power median 84.98-84.99 W on every trial; CPU temperature 88.6-94.0°C |

Each trial took about 23 minutes.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 95.0%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 168 | warm-up | 36.627 |
| 169 | warm-up | 36.640 |
| 170 | calibration | 36.592 |
| 171 | calibration | 36.664 |
| 172 | calibration | 36.599 |
| 193 | recheck | 36.678 (+0.16%) |

Calibration mean 36.618, 95% CI [36.520, 36.717] (±0.27%). Warm-up settled after the minimum two reps (2,869 s).
Every `-O3` build had the same code fingerprint (`211dae19`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 173-177 | screening | 5 candidates | 36.48-36.85 | | all survived (`-frecursive` skipped as unchanged code) |
| 178-180 | confirmation | `-fprefetch-loop-arrays` | 36.848 | +0.63% | reject (CI-clear, under the 1% bar) |
| 181-183 | confirmation | `-fgraphite-identity` | 36.548 | -0.19% | reject |
| 184-186 | confirmation | `-fstack-arrays` | 36.505 | -0.31% | reject |
| 187-189 | confirmation | `-flto` | 36.653 | +0.09% | reject |
| 190-192 | confirmation (fast-tracked) | `-march=native` | 39.193 | +7.03% | **accept** |
| 194-196 | combination | `-march=native` | 39.250 | +7.19% | **accept** |
| 197-199 | PGO | `-march=native -fprofile-use` | 39.552 | +0.77% | reject (CI overlap) |
| 200-202 | vector width | `-march=native -mprefer-vector-width=256` | 37.664 | -4.04% | reject |

The Phase 6 deltas are against `-O3 -march=native`. The microarch multiplier was skipped because the winning set
already had `-march=native`.

## Observations

- **The bandwidth gate waited before half the timed runs**, compared with once each on cactus and fotonik3d. Every
  re-probe read 103-106 GB/s, the session best. The first probe reads 90-96 GB/s even when no wait follows, so
  the gate is catching the tail of the previous run again (the host page's standing fact). Ratios don't depend on
  it: `-fgraphite-identity`'s three reps all followed a wait and agree within 0.03%.
- **Package power read 84.99 W on every trial**, the fourth mine in a row pinned at the platform limit.
- **The vector-width multiplier has now split both ways in the memory-bound cluster:**
  - fotonik3d: +1.52%
  - roms: -4.04%
  - lbm and cactus: flat

  Holding `-mprefer-vector-width=` out of Phases 3-5 and trying it only on top of an `-march=` win is paying off
  in both directions.
- **`-march=native` across the memory-bound cluster here:** +3.5% (lbm), +16.5% (cactus), +7.0% (fotonik3d), +7.2%
  (roms). It has won every time.
- **LTO and PGO have not helped on any of the four benchmarks here so far.** On roms, `-flto` was +0.09% and PGO
  +0.77%.

# `cfm mine` results: 722.palm_r on `chicago`, 2026-11-06

This is the fifth benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first fprate
benchmark here that niwot doesn't hold back. `722.palm_r` is PALM, a Fortran large-eddy simulation code for
atmospheric and oceanic boundary layers. Its corpus shape is memory-bound at 69.2%, with
`allocation_pressure=high`. That makes it the least memory-bound benchmark mined on this host so far.

## Headline result

**`-O3 -march=native -fprofile-use`, +5.20% over plain `-O3`** (ratio 76.561 → 80.540).

- **`-march=native` gave +4.13%** (Phase 5, 79.720). It was fast-tracked on the cluster prior: accepted 5 of 5,
  on lbm twice, cactus, fotonik3d and roms. All six of its reps (79.46-79.87) beat every `-O3` rep (76.31-76.96).
- **PGO added +1.03% on top. This is the first PGO accept on chicago.** Its CI [80.08, 81.00] is clear of
  `-march=native`'s [79.52, 79.92], and the delta just clears the 1% bar. All three PGO reps built the same code
  (`e79a7fd9`).
- **`-flto` read +1.04% and was rejected on CI overlap.** Its CI [76.85, 77.87] overlapped the baseline's upper
  bound (77.12). The mine therefore never tried `-flto` with `-march=native` or with PGO. On niwot, LTO plus PGO
  was the main intrate win.
- **`-mprefer-vector-width=256` read +0.61% on top of PGO and was rejected.** Its CI [80.59, 81.48] overlaps
  PGO's.
- **`-fstack-arrays` was a real loss, -1.75%.** All three of its reps read below every `-O3` rep. The other two
  candidates were flat: `-fgraphite-identity` +0.40% and `-fprefetch-loop-arrays` -0.31%. `-frecursive` built
  code identical to `-O3`, so its timed run was skipped.
- **The shape filter dropped 8 candidates** on the 69.2% memory-bound read, including `-Ofast`, `-ffast-math` and
  `-funroll-loops`.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 722.palm_r` (uncapped, defaults) |
| Code | `main` at `3dde36e` (no code changes since `f31ba64`, only docs) |
| Experiment id | 7 |
| Started / finished | 2026-11-06T09:37:41Z / 2026-11-06T15:37:41Z (6h00m) |
| Final status | `converged` |
| Trials | 35 (203-237), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 5 / 1 (plus `-march=native` fast-tracked, accepted) |
| Excluded on shape (Phase 2) | 8 |
| Fast-tracked (M4) | `-march=native` (accepted 5 of 5, mean +6.99%) |
| Skipped as unchanged code | `-frecursive` |
| Winning flags | `["-O3", "-march=native", "-fprofile-use"]`, +5.20% |
| Guards | bandwidth gate waited once (30 s, trial 203); no reruns; baseline recheck not flagged (+0.52%) |
| Power | package power median 84.99-85.02 W on every trial; CPU temperature 90.1-95.8°C |

Each trial took about 10.5 minutes.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 69.2%, `vectorization_density=high`,
`allocation_pressure=high`.

| Trial | Role | Ratio |
|---|---|---|
| 203 | warm-up | 76.933 |
| 204 | warm-up | 76.856 |
| 205 | calibration | 76.307 |
| 206 | calibration | 76.743 |
| 207 | calibration | 76.632 |
| 228 | recheck | 76.959 (+0.52%) |

The calibration mean is 76.561, with a 95% CI of [75.999, 77.123] (±0.73%). Warm-up settled after the minimum two
reps (1,250 s). Every `-O3` build had the same code fingerprint (`fbf8719e`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 208-212 | screening | 5 candidates | 75.15-77.46 | | all survived (`-frecursive` skipped as unchanged code) |
| 213-215 | confirmation | `-fprefetch-loop-arrays` | 76.326 | -0.31% | reject |
| 216-218 | confirmation | `-fgraphite-identity` | 76.869 | +0.40% | reject |
| 219-221 | confirmation | `-fstack-arrays` | 75.218 | -1.75% | reject (CI clear below baseline) |
| 222-224 | confirmation | `-flto` | 77.361 | +1.04% | reject (CI overlaps baseline) |
| 225-227 | confirmation (fast-tracked) | `-march=native` | 79.610 | +3.98% | **accept** |
| 229-231 | combination | `-march=native` | 79.720 | +4.13% | **accept** |
| 232-234 | PGO | `-march=native -fprofile-use` | 80.540 | +1.03% | **accept** |
| 235-237 | vector width | `-march=native -fprofile-use -mprefer-vector-width=256` | 81.032 | +0.61% | reject (CI overlap) |

The PGO delta is measured against `-O3 -march=native`, and the vector-width delta against
`-O3 -march=native -fprofile-use`. The microarch multiplier was skipped because the winning set already had
`-march=native`.

## Observations

- **PGO and LTO both read about +1% here**, after losing or reading flat on all four earlier benchmarks. PALM is
  the least memory-bound of the five, so the code itself has more room to matter. `-flto` with PGO, on top of
  `-march=native`, is an untested follow-up (open item on the host page).
- **The baseline CI (±0.73%) is wider than lbm's, fotonik3d's or roms's.** Calibration rep 205 read 0.5% under its
  siblings, which put `-flto`'s +1.04% inside the overlap. That's the same small-low-rep pattern as host-page
  item 5.
- **The bandwidth gate waited only before the first trial.** Probes read 89-103 GB/s, so the frequent waits on
  roms didn't recur.
- **Package power was 85.0 W on every trial**, for the fifth mine in a row.
- **`-march=native` on this host:** +3.5% (lbm), +16.5% (cactus), +7.0% (fotonik3d), +7.2% (roms), +4.1% (palm).
  It was accepted every time.

# `cfm mine` results: 782.lbm_r on `chicago`, 2026-11-03

The first mine on `chicago` (see [`host_chicago.md`](host_chicago.md)), the Strix Halo host the 2026-08 runs
used. `782.lbm_r` was picked because its first mine on `niwot` had to be stopped: niwot's memory side halved its
bandwidth for minutes at a time, and the same `-O3` binary read 3.02-6.32
([note](lbm_swing_investigation.2026-10-23.md)). This mine was the test of whether chicago, with about 2.3 times
niwot's memory bandwidth, can mine fprate cleanly. It ran the same night as niwot's own lbm re-mine with a 10-minute
settle ([write-up](mining_results.782.lbm_r.2026-11-03.md)), which accepted nothing: its `-O3` reps spread 17%
and its baseline CI was ±12.6%, against ±0.11% here.

## Headline result

**`-O3 -march=native`, +2.92% over plain `-O3`** (ratio 16.069 → 16.538).

- **lbm mines cleanly here.** All 34 trials ran with no reruns, the bandwidth gate never held a trial back after
  the first, and the baseline recheck agreed with the calibration mean to +0.03%. The five `-O3` reps read
  16.064-16.077, a spread of 0.08%, and the calibration CI is ±0.11%. On this host in 2026-08, before the warm-up
  and gate guards, the same benchmark's baseline CI was [13.77, 17.46] (±12%).
- **`-march=native` is real but small.** Its six reps (three in Phase 4, three in Phase 5) read 16.478-16.562,
  every one above every `-O3` rep. The 2026-08-24 mine here measured it at +1.79% and rejected it, because that
  baseline CI was too wide to clear.
- Nothing else helped. `-fprefetch-loop-arrays` was CI-clear but only +0.36%, `-fgraphite-identity` was flat,
  and `-flto` was -0.54%. PGO on top of `-march=native` was +0.10%, PGO with the `-fprefetch-loop-arrays`
  near-miss was -1.10%, and `-mprefer-vector-width=256` was -0.31%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 782.lbm_r` (uncapped, defaults: bandwidth gate and power check on) |
| Code | `main` at `f78748b` |
| Experiment id | 2 (experiment 1 was stopped during its first warm-up rep to switch the power profile, and marked failed) |
| Started / finished | 2026-11-03T23:52:47Z / 2026-11-04T10:41:35Z (10h49m) |
| Final status | `converged` |
| Trials | 34 (1-34), no reruns |
| Candidates screened / confirmed | 4 / 1 |
| Excluded on shape (Phase 2) | 11, including `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta` and `-fno-pie -no-pie` |
| Fast-tracked (M4) | none (`cfm.db` started empty) |
| Skipped as unchanged code | none |
| Winning flags | `["-O3", "-march=native"]`, +2.92% |
| Guards | bandwidth gate waited once (30 s, trial 1); no slow-rep or low-power reruns; baseline recheck not flagged (+0.03%) |
| Power | package power median 84.99 W on every trial; CPU temperature 91.5-94.6°C |

Each trial took about 19 minutes (SPEC's 32-copy run, about 574 two-second power samples).

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): **memory-bound 94.9%**, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio | Bandwidth probe |
|---|---|---|---|
| 1 | warm-up | 16.0649 | 104.9 GB/s (waited 30 s) |
| 2 | warm-up | 16.0680 | 92.8 GB/s |
| 3 | calibration | 16.0669 | 93.2 GB/s |
| 4 | calibration | 16.0637 | 94.7 GB/s |
| 5 | calibration | 16.0773 | 94.0 GB/s |
| 22 | recheck | 16.0748 (+0.03%) | 95.5 GB/s |

Calibration mean 16.0693, 95% CI [16.0517, 16.0870]. Warm-up settled after the minimum two reps (2,338 s).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 6 | screening | `-fprefetch-loop-arrays` | 16.132 | | survived |
| 7 | screening | `-fgraphite-identity` | 16.061 | | survived |
| 8 | screening | `-flto` | 15.989 | | survived |
| 9 | screening | `-march=native` | 16.562 | | survived |
| 10-12 | confirmation | `-fprefetch-loop-arrays` | 16.128 | +0.36% | reject (CI-clear, under the 1% bar) |
| 13-15 | confirmation | `-fgraphite-identity` | 16.067 | -0.01% | reject |
| 16-18 | confirmation | `-flto` | 15.982 | -0.54% | reject |
| 19-21 | confirmation | `-march=native` | 16.508 | +2.73% | **accept** |
| 23-25 | combination | `-march=native` | 16.538 | +2.92% | **accept** |
| 26-28 | PGO | `-march=native -fprofile-use` | 16.555 | +0.10% | reject |
| 29-31 | PGO, near-miss | `-march=native -fprefetch-loop-arrays -fprofile-use` | 16.356 | -1.10% | reject |
| 32-34 | vector width | `-march=native -mprefer-vector-width=256` | 16.486 | -0.31% | reject |

The Phase 6 deltas are against `-O3 -march=native`. The microarch multiplier was skipped because the winning set
already had `-march=native`. Every flagset built distinct code (no shared fingerprints across flagsets), and
each flagset's reps shared one fingerprint, the PGO ones included.

## Observations

- **Bandwidth stayed in one state.** Probes before each run read 89.2-98.9 GB/s, against a session best of
  104.9 (the first probe, from idle). None fell below the gate's 85% bar, although the lowest (89.2, trial 8)
  came within 0.1 GB/s of it. Nothing like niwot's halving appeared, and ratios don't follow the probe:
  trial 8's 89.2 GB/s preceded an ordinary `-flto` rep.
- **Package power read 84.99 W on every trial**, as the median of each run's samples. That looks like the
  package sitting at a fixed power limit under 32 copies of lbm, not a stuck sensor: the same sensor reads
  about 8-9 W idle. The low-power rerun rule had nothing to act on.
- **The CPU ran at 91.5-94.6°C throughout**, with no trend across the 11 hours and no relation to ratio.
- **The shape filter removed 11 of 15 candidates** on a 94.9% memory-bound read from another host's corpus
  data. On niwot and erie that filter hid real gains (`--no-shape-filter` exists because of pts/himeno), so the
  four-candidate search here is narrow; see the host page's open items.

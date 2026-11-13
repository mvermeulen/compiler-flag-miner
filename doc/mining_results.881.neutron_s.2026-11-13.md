# `cfm mine` results: 881.neutron_s on `chicago`, 2026-11-13

This is the thirteenth and last fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and
the first `881.neutron_s` mine on any host. `881.neutron_s` is a C neutron-transport simulation for nuclear reactors, built around XSBench's cross-section
lookup kernel and parallelized with OpenMP.
It has no fprate counterpart. Its corpus shape is memory-bound at 67.0%.

## Headline result

**`-O3 -flto -march=native`, +10.89% over plain `-O3`** (ratio 2.0946 → 2.3227).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 2.0946 | — |
| `-O3 -flto` | 2.2244 | +6.19% |
| `+ -march=native` | 2.3227 | +4.42% |

- **`-flto` gave +6.19%**, the first fpspeed winner here to include `-flto`. All three reps (2.220-2.227) sat far above every
  `-O3` rep (2.092-2.107).
- **`-march=native` gave +2.04% alone but +4.42% on top of `-flto`.** Together they gain more (+10.89%) than the two
  alone multiplied (+8.36%). Inlining across files probably exposes loops that AVX-512 can then vectorize; the run
  doesn't show that directly. femflow_r's winner here was the same pair.
- **PGO lost 25.4%** on top of `-flto -march=native` (1.732), with tight reps, and drew 72.6-73.2 W of package power
  against 85.0 W on every other trial.
- **`-fprefetch-loop-arrays` -0.05%, `-fgraphite-identity` -0.03%, `-fno-math-errno` +0.44%**, all rejected.
  `-mprefer-vector-width=256` read +0.16% on top of the winner.
- **The shape filter dropped 10 candidates** on the 67.0% memory-bound read, `-Ofast` and `-ffast-math` among them.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 881.neutron_s` (uncapped, defaults) |
| Code | `main` at `1cd3a35` (no code changes since `c933ee2`, PR #71) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 28 |
| Started / finished | 2026-11-13T01:31:55Z / 2026-11-13T05:45:46Z (4h14m) |
| Final status | `converged` |
| Trials | 37 (1253-1289), none skipped, no reruns |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 10 (`-flto` and `-fno-math-errno` kept, exempt) |
| Fast-tracked (M4) | `-march=native` (accepted 17 of 24, mean +16.19%) |
| Accepted in Phase 4 | `-flto` +6.19%, `-march=native` +2.04% |
| Winning flags | `["-O3", "-flto", "-march=native"]`, +10.89% |
| Guards | bandwidth gate waited 30 s before 16 of 37 timed runs; no reruns; baseline recheck not flagged (+0.20%) |
| Power | package power median 84.99 W on every non-PGO trial, 72.6-73.2 W on the PGO trials; CPU temperature 87.2-92.9°C |

A non-PGO trial took about 6.5 minutes and a PGO trial about 9. Every timed run's `.rsf` reads `valid: S` for neutron.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 67.0%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1253 | warm-up | 2.10654 |
| 1254 | warm-up | 2.10154 |
| 1255 | calibration | 2.09485 |
| 1256 | calibration | 2.09172 |
| 1257 | calibration | 2.09730 |
| 1277 | recheck | 2.09874 (+0.20%) |

The calibration mean is 2.094622, with a 95% CI of [2.08767, 2.10158] (±0.33%). Warm-up settled after the minimum
two reps (831 s). Every `-O3` build had the same code fingerprint (`91d1de66`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1258-1261 | screening | 4 candidates | 2.095-2.229 | | all survived |
| 1262-1264 | confirmation | `-fprefetch-loop-arrays` | 2.0936 | -0.05% | reject |
| 1265-1267 | confirmation | `-fgraphite-identity` | 2.0940 | -0.03% | reject |
| 1268-1270 | confirmation | `-flto` | 2.2244 | +6.19% | **accept** (the greedy start) |
| 1271-1273 | confirmation | `-fno-math-errno` | 2.1039 | +0.44% | reject |
| 1274-1276 | confirmation (fast-tracked) | `-march=native` | 2.1373 | +2.04% | **accept** |
| 1278-1280 | combination (greedy) | `-flto -march=native` | 2.3227 | +4.42% | **accept** |
| 1281-1283 | combination (pair) | `-flto -march=native` | 2.3224 | +10.87% | accept, same flagset as the winner |
| 1284-1286 | PGO | `-flto -march=native -fprofile-use` | 1.732 | -25.42% | reject |
| 1287-1289 | vector width | `+ -mprefer-vector-width=256` | 2.326 | +0.16% | reject |

The greedy-step delta is against `-O3 -flto`, the pair delta against `-O3`, and Phase 6 deltas against
`-O3 -flto -march=native`. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it. The
microarch multiplier was skipped because the winning set already had `-march=native`. No Phase 4 reject was CI-clear
above baseline, so PGO had no near-miss variant.

## Observations

- **The six runs of the winning code (`c4c36109`) span 2.3175-2.3269**, a 95% CI of ±0.16%, the tightest winner on
  this host.
- **PGO's loss came with a 15% drop in package power**, so the chip was less busy during those runs. That fits PGO
  making some part of the run more serial or more often idle, such as a training workload that steers inlining or
  loop decisions away from what the reference workload's parallel loops need. It's a guess; the PGO builds' two
  code fingerprints (`86e9798c`, `b63dc26e`) read alike (1.730-1.735), so it isn't one bad build. The low-power rerun
  rule correctly left the reps alone, since all three siblings drew the same lower power.
- **`-flto` is in the winning set of 1 of 13 fpspeed benchmarks here**, against 4 of 12 fprate ones (ocio, gmsh,
  flightdm, femflow).
- **niwot hasn't mined neutron_s yet.**

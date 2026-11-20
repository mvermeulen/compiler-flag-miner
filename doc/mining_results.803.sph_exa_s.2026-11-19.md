# `cfm mine` results: 803.sph_exa_s on `niwot`, 2026-11-19

The third fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `803.sph_exa_s` is based on
SPH-EXA, a C++ smoothed-particle-hydrodynamics code parallelized with OpenMP. `chicago` mined it on 2026-11-09
([write-up](mining_results.803.sph_exa_s.2026-11-09.md)). Its corpus shape is memory-bound at 67.4%, over the 55%
margin, so the shape filter dropped 10 candidates. `chicago` dropped the same 10 plus `-fno-math-errno`, which PR #71
exempted two days later.

## Headline result

**`-O3 -march=native -fprofile-use`, +12.88% over plain `-O3`** (ratio 1.4990 → 1.6920).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.4990 | — |
| `-O3 -march=native` | 1.6345 | +9.04% |
| `+ -fprofile-use` | 1.6920 | +3.51% |

- **The closest cross-host match yet.** `chicago` got the same flags at +12.73% (`-march=native` +9.06%, PGO +3.37%),
  and its `-march=native` build had the same code fingerprint (`7ba037e2`).
- **`-march=native` runs in two modes, on both hosts.** Two of its five reps read about 3.8% below the other three
  (1.573 and 1.576 against 1.627-1.639) at the same power (43.0 W) and bandwidth, on the same binary. The spread rule
  replaced both, so the reported +9.04% is the fast mode; all five pooled give +7.45%, still a clear accept.
  `chicago` saw one such rep (3.4% under) and replaced it the same way. No `-O3` or other flagset rep showed it.
- **PGO added +3.51%.** All three PGO builds had one fingerprint (`44a8e53b`) and agreed within 0.3%.
- **`-mprefer-vector-width=256` on top read +0.39%** and was rejected (`chicago`: +0.69%).
- **The four screened candidates were flat or worse:** `-flto` -0.18%, `-fno-math-errno` -0.56%,
  `-fgraphite-identity` -0.61%, `-fprefetch-loop-arrays` -1.22% (CI clear below, as on `chicago`, -1.48%).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 803.sph_exa_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `e91b385` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 205 |
| Started / finished | 2026-11-19T23:47:17Z / 2026-11-20T13:05:44Z (13h18m) |
| Final status | `converged` |
| Trials | 33 (2598-2630), 2 spread-rule reruns, none skipped |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 10: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fipa-pta`, the four hardening opt-outs, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` and `-fno-math-errno` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 13 of 23, mean +25.17%) |
| Accepted in Phase 4 | `-march=native` +9.04% |
| Winning flags | `["-O3", "-march=native", "-fprofile-use"]`, +12.88% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (43.4-46.1 GB/s); two spread-rule reruns on `-march=native` (2620 → 2622 → 2623); baseline recheck not flagged (-0.27%) |
| Power | package power median 43.0-44.0 W on every trial; CPU temperature 95.8-99.0°C |

A trial took about 23 minutes, the settle included. `chicago` ran its 28 trials in 3h20m. Every trial's `.rsf`
reads `valid: S`.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 67.4%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2598 | warm-up | 1.50908 |
| 2599 | warm-up | 1.50202 |
| 2600 | calibration | 1.49805 |
| 2601 | calibration | 1.50054 |
| 2602 | calibration | 1.49828 |
| 2624 | recheck | 1.49490 |

Warm-up settled after the minimum 2 reps. The calibration mean is 1.49896, 95% CI ±0.23%. Every `-O3` build had one
fingerprint (`1dba4672`).

## Phase 3/4: screening and confirmation

All four screened candidates survived (1.482-1.503).

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` (fast-tracked) | 1.639, 1.637, 1.627 (kept); 1.573, 1.576 (replaced) | 1.6345 | +9.04% | **accept** |
| `-flto` | 1.495, 1.499, 1.495 | 1.4962 | -0.18% | reject |
| `-fno-math-errno` | 1.495, 1.489, 1.488 | 1.4906 | -0.56% | reject |
| `-fgraphite-identity` | 1.483, 1.496, 1.491 | 1.4898 | -0.61% | reject |
| `-fprefetch-loop-arrays` | 1.480, 1.481, 1.482 | 1.4807 | -1.22% | reject (CI clear below) |

### The two modes of `-march=native`

| Trial | Ratio | Power | Bandwidth probe | Fate |
|---|---|---|---|---|
| 2619 | 1.63913 | 43.08 W | 45.8 GB/s | kept |
| 2620 | 1.57333 | 43.02 W | 45.8 GB/s | replaced by 2622 |
| 2621 | 1.63725 | 43.08 W | 45.8 GB/s | kept |
| 2622 | 1.57595 | 43.00 W | 44.2 GB/s | replaced by 2623 |
| 2623 | 1.62722 | 43.01 W | 45.8 GB/s | kept |

Nothing in the host signals separates the slow reps: same binary, same power, normal bandwidth before the run. This
is the spread rule's precise-rep path (siblings within 0.11%, the outlier more than 4x that and over 2% below), not
the 10% slow-rep path or the throttle. Since `chicago` hit the same 3-4% mode on the same code, it looks like a
property of this binary (thread scheduling or a data-dependent path in the vectorized code), not the host. Replacing
it reports the fast mode; whether that or the pooled +7.45% is the "real" gain is a judgment call, and either one is
an accept here. PGO, built on top of it, showed no slow mode in three reps, nor did the vector-width variant.

## Phase 5: combination

Only `-march=native` was accepted; its Phase 4 reps were reused (#39), and Phase 5 spent no trials.

## Phase 6: multipliers

| Flagset (on `-O3 -march=native`) | Reps | Mean | Delta on the step before | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 1.692, 1.694, 1.689 | 1.6920 | +3.51% | **accept** |
| `-fprofile-use -mprefer-vector-width=256` | 1.699, 1.696, 1.701 | 1.6986 | +0.39% | reject |

No near-miss variant (no Phase 4 reject was CI-clear above baseline). The microarch multiplier was skipped because
the winning set already has `-march=native`. The vector-width builds had one fingerprint (`9e339108`).

## Knowledge table

The memory-bound rows this run changed most:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 13 of 23, +25.17% | 14 of 24, +24.50% |
| `-fprofile-use` | 3 of 18, -3.55% | 4 of 19, -3.18% |
| `-mprefer-vector-width=256` | 2 of 16, -1.31% | 2 of 17, -1.21% |
| `-fprefetch-loop-arrays` | 4 of 23, +1.82% | 4 of 24, +1.70% |

## Compared with `chicago`

| | `chicago` (2026-11-09) | `niwot` |
|---|---|---|
| Baseline | 3.3481, 85 W | 1.4990, ±0.23%, 43 W |
| `-march=native` | +9.06% (one slow rep replaced) | +9.04% (two slow reps replaced; +7.45% pooled) |
| PGO on top | +3.37% | +3.51% |
| Vector width on top | +0.69%, rejected | +0.39%, rejected |
| `-fprefetch-loop-arrays` | -1.48% | -1.22% |
| `-fno-math-errno` | excluded on shape | -0.56% (kept by PR #71's exemption) |
| Total | +12.73% | +12.88% |
| Run | 28 trials, 3h20m | 33 trials, 13h18m |

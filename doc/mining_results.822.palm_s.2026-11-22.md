# `cfm mine` results: 822.palm_s on `niwot`, 2026-11-22

The sixth fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `822.palm_s` is the SPECspeed
version of PALM, a Fortran large-eddy simulation model for atmospheric and oceanic boundary layers, parallelized with
OpenMP. `chicago` mined it on 2026-11-11 ([write-up](mining_results.822.palm_s.2026-11-11.md)). Its corpus shape is
memory-bound at 56.2%, just over the 55% margin, so the shape filter dropped 8 candidates, the same 8 as on `chicago`.

## Headline result

**`-O3 -march=native -fprofile-use`, +14.92% over plain `-O3`** (ratio 1.6908 → 1.9431), the same winning flags as
`chicago` (+23.54%).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.6908 | — |
| `-O3 -march=native` | 1.8643 | +10.26% |
| `+ -fprofile-use` | 1.9431 | +4.22% |

- **`-march=native` gave +10.26%**, about half `chicago`'s +19.22%. All three reps (1.857-1.869) sat far above every
  `-O3` rep (1.675-1.699). On palm_r it gave a small gain on both hosts (+4.13% on `chicago`; rejected here, though
  the same code won as `-march=znver5 -mprefer-vector-width=256`).
- **PGO added +4.22%** (`chicago`: +3.62%). Its three builds had three fingerprints (#32) and spread 1.1%.
- **`-mprefer-vector-width=256` read +0.60%** on top and was rejected (`chicago`: -1.02%).
- **`-flto` read +1.34% and was rejected on CI overlap**, as on `chicago` (+0.84%). Its reps were tight (±0.52%),
  but the baseline CI was ±1.97%, widened by one calibration rep reading 1.4% below the other two.
- **`-fprefetch-loop-arrays` -0.88%, `-fgraphite-identity` +0.09%, `-fstack-arrays` -1.53%**, all rejected;
  `-frecursive` built the same code as `-O3` and was skipped without a timed run, as on `chicago`.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 822.palm_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `5ccc0f0` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 208 |
| Started / finished | 2026-11-22T01:29:40Z / 2026-11-22T13:35:04Z (12h05m) |
| Final status | `converged` |
| Trials | 32 (2716-2747), no reruns, 1 skipped as unchanged code |
| Candidates screened / confirmed | 5 / 4 (plus `-march=native` fast-tracked; `-frecursive` skipped) |
| Excluded on shape (Phase 2) | 8: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 15 of 26, mean +23.25%) |
| Accepted in Phase 4 | `-march=native` +10.26% |
| Winning flags | `["-O3", "-march=native", "-fprofile-use"]`, +14.92% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (43.4-45.6 GB/s); no reruns; baseline recheck not flagged (-0.07%) |
| Power | package power median 36-38 W on `-O3`-class code (33-35 W on `-fstack-arrays`), 30.6-31.1 W on `-march=native`, 28-29 W on its PGO and vector-width builds; CPU temperature 94.2-98.2°C |

A trial took about 23 minutes, the settle included. `chicago` ran its 32 trials in 4h03m. Every trial's `.rsf`
reads `valid: S`. The faster code draws less power here: `-march=native` and PGO cut package power by 6-9 W while
raising the ratio, which fits a run held back by memory rather than by the cores. On `chicago` every trial read
82.7-84.6 W.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 56.2%, `vectorization_density=high`,
`allocation_pressure=high`.

| Trial | Role | Ratio |
|---|---|---|
| 2716 | warm-up | 1.69483 |
| 2717 | warm-up | 1.69548 |
| 2718 | calibration | 1.69789 |
| 2719 | calibration | 1.69912 |
| 2720 | calibration | 1.67528 |
| 2741 | recheck | 1.68961 |

Warm-up settled after the minimum 2 reps (2811 s). The calibration mean is 1.69076, 95% CI ±1.97%. Trial 2720 read
1.4% below the other two at the same power (37.0 W) and on the same binary (`b68c5618`, as on `chicago`); that is
inside both rerun rules (10% slow-rep; the spread rule needs the outlier more than 4x the siblings' 0.07% spread
*and* 2% below, and it was 1.4%). The six `-O3` reps average 1.6920, so the reported deltas are about 0.1% high,
which changes no verdict.

## Phase 3/4: screening and confirmation

All five screened candidates survived (1.665-1.709); `-frecursive` was skipped as unchanged code.

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` (fast-tracked) | 1.866, 1.857, 1.869 | 1.8643 | +10.26% | **accept** |
| `-flto` | 1.710, 1.713, 1.717 | 1.7133 | +1.34% | reject (CI overlap) |
| `-fgraphite-identity` | 1.703, 1.698, 1.677 | 1.6923 | +0.09% | reject |
| `-fprefetch-loop-arrays` | 1.689, 1.663, 1.675 | 1.6759 | -0.88% | reject |
| `-fstack-arrays` | 1.661, 1.653, 1.681 | 1.6649 | -1.53% | reject |
| `-frecursive` | — | — | — | skipped (same code as `-O3`) |

**`-flto` is a near-miss on both hosts.** Its CI ([1.7044, 1.7223]) sits above five of the six `-O3` reps but
overlaps the baseline CI's upper end (1.7241). Against all six `-O3` reps it reads +1.26%. On `chicago` it read
+0.84% and was rejected the same way. Because it wasn't CI-clear, PGO had no near-miss variant, so
`-march=native -flto -fprofile-use` was never measured on either host.

## Phase 5: combination

Only `-march=native` was accepted; its Phase 4 reps were reused (#39), and Phase 5 spent no trials.

## Phase 6: multipliers

| Flagset (on `-O3 -march=native`) | Reps | Mean | Delta on the step before | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 1.954, 1.942, 1.933 | 1.9431 | +4.22% | **accept** |
| `-fprofile-use -mprefer-vector-width=256` | 1.970, 1.940, 1.954 | 1.9548 | +0.60% | reject |

The microarch multiplier was skipped because the winning set already has `-march=native`. The three PGO builds had
three fingerprints (`92e1308c`, `ea3a92fe`, `778879ba`) and the vector-width builds two (`77e2ef23`,
`e8b6aff2` ×2), so each Phase 6 step mixes retrained binaries (#32); their reps spread 1.1% and 1.5%.

## Knowledge table

The memory-bound rows this run changed:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 15 of 26, +23.25% | 16 of 27, +22.77% |
| `-fprofile-use` | 4 of 21, -4.34% | 5 of 22, -3.95% |
| `-flto` | 6 of 20, +2.91% | 6 of 21, +2.84% |
| `-mprefer-vector-width=256` | 2 of 19, -1.42% | 2 of 20, -1.32% |
| `-fprefetch-loop-arrays` | 5 of 26, +1.95% | 5 of 27, +1.85% |
| `-fgraphite-identity` | 3 of 23, +1.69% | 3 of 24, +1.63% |
| `-fstack-arrays` | 0 of 1, -2.51% | 0 of 2, -2.02% |

## Compared with `chicago`

| | `chicago` (2026-11-11) | `niwot` |
|---|---|---|
| Baseline | 3.1325, ±0.77%, 83-85 W | 1.6908, ±1.97%, 37 W |
| `-march=native` | +19.22% | +10.26% |
| PGO on top | +3.62% | +4.22% |
| Vector width on top | -1.02% | +0.60% |
| `-flto` | +0.84%, CI overlap | +1.34%, CI overlap |
| Total | +23.54% | +14.92% |
| Run | 32 trials, 4h03m | 32 trials, 12h05m |

The same flags win on both hosts, but `-march=native` gains half as much here. That is the pattern of marian_s
(#42), smaller: the fpspeed benchmarks where `niwot` falls furthest behind `chicago` on `-march=native` are ones
whose faster builds draw less power here, consistent with a memory-bandwidth ceiling (about 45 GB/s here against
about 102 GB/s on `chicago`), though this run doesn't test it.

# `cfm mine` results: 867.nest_s on `niwot`, 2026-11-22

The seventh fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `867.nest_s` is the SPECspeed
version of NEST, a C++ simulator for large networks of spiking neurons, parallelized with OpenMP. `chicago` mined it
on 2026-11-12 ([write-up](mining_results.867.nest_s.2026-11-12.md)). Its corpus shape is memory-bound at 65.6%, so
the shape filter dropped 10 candidates, the same 10 as on `chicago`.

## Headline result

**No flag beat plain `-O3`** (ratio 1.0029), the same verdict as on `chicago`. Recorded as 0.0%.

- **The noise is the benchmark's, on both hosts.** Ten runs of the same `-O3` code (`23d24cd2`, as on `chicago`)
  spread 0.970-1.007 (3.8%; `chicago` 4.2%), at a flat 18.0 W and in a 3°C band. Every flagset's reps spread about
  as much.
- **The calibration reps sampled the top of that spread.** The baseline mean (1.0029) sits 1.0% above the mean of
  all ten `-O3` runs (0.9931), and the recheck read -2.03% and was flagged. Every delta below is therefore about 1%
  low; read against all ten `-O3` runs, no verdict changes.
- **`-march=native` read -0.63%** (reps 0.980-1.009) and the microarch multiplier's `-march=znver5`, the same code
  (`df29754b`, as on `chicago`), -0.10%. Pooled, those six runs read +0.62% over all ten `-O3` runs. On `chicago`
  the same code pooled to +2.69%, also rejected.
- **PGO lost 4.39%** (3.44% against all `-O3` runs), clear of baseline below; `chicago` read -0.05%.
- **Every other candidate was within ±1.2% of the pooled `-O3`.**

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 867.nest_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `25f3cd7` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 209 |
| Started / finished | 2026-11-22T13:45:04Z / 2026-11-23T20:24:50Z (30h40m) |
| Final status | `converged` |
| Trials | 38 (2748-2785), no reruns, none skipped |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 10: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fipa-pta`, the four hardening opt-outs, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` and `-fno-math-errno` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 16 of 27, mean +22.77%) |
| Accepted in Phase 4 | none |
| Winning flags | `["-O3"]`, +0.00% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (43.2-45.6 GB/s); no reruns; baseline recheck **flagged** (-2.03%) |
| Power | package power median 18.0 W on every trial; CPU temperature 86.5-89.8°C |

A trial took about 47 minutes (a 35-minute timed run plus the settle and build), the longest of any fpspeed mine here;
PGO trials took about 57. `chicago` ran its 36 trials in 6h11m. Every trial's `.rsf` reads `valid: S`. Package power,
18 W, is the lowest of any niwot mine; `chicago` read 85 W.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 65.6%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2748 | warm-up | 0.98550 |
| 2749 | warm-up | 0.96971 |
| 2750 | warm-up | 0.98723 |
| 2751 | warm-up | 1.00498 |
| 2752 | warm-up | 0.99428 |
| 2753 | warm-up | 0.99773 |
| 2754 | calibration | 1.00090 |
| 2755 | calibration | 1.00707 |
| 2756 | calibration | 1.00071 |
| 2776 | recheck | 0.98251 (-2.03%, flagged) |

Warm-up needed six reps (4h46m) for two in a row to agree within 1%. The calibration mean is 1.00289, 95% CI ±0.90%.
The warm-up reps rise over the first four runs (0.970 to 1.005) and the recheck falls back to 0.983, but power held
at 18.0 W throughout, so nothing recorded separates a settling host from the benchmark's own run-to-run spread. The
throttle stop was nowhere near firing: the ten `-O3` runs span 3.8%, against its 10% bar.

## Phase 3/4: screening and confirmation

All four screened candidates survived (0.974-1.003).

| Flag | Reps | Mean | Delta | Against all `-O3` runs | Verdict |
|---|---|---|---|---|---|
| `-fprefetch-loop-arrays` | 0.992, 0.993, 1.005 | 0.9965 | -0.64% | +0.34% | reject |
| `-march=native` (fast-tracked) | 0.980, 1.009, 1.000 | 0.9965 | -0.63% | +0.35% | reject |
| `-flto` | 0.990, 0.985, 0.993 | 0.9894 | -1.35% | -0.37% | reject |
| `-fno-math-errno` | 0.991, 0.990, 0.987 | 0.9894 | -1.35% | -0.37% | reject |
| `-fgraphite-identity` | 0.989, 0.988, 0.980 | 0.9854 | -1.74% | -0.77% | reject |

## Phase 5: combination

Nothing was accepted, so Phase 5 ran no trials and Phase 6 layered on plain `-O3`.

## Phase 6: multipliers

| Flagset (on `-O3`) | Reps | Mean | Delta | Against all `-O3` runs | Verdict |
|---|---|---|---|---|---|
| `-fprofile-use` | 0.956, 0.963, 0.958 | 0.9589 | -4.39% | -3.44% | reject (CI clear below) |
| `-march=znver5` | 0.993, 1.008, 1.004 | 1.0019 | -0.10% | +0.89% | reject |
| `-mtune=znver5` | 0.982, 0.976, 0.986 | 0.9813 | -2.15% | -1.19% | reject |

No near-miss variant (no Phase 4 reject was CI-clear above baseline), and the vector-width multiplier was skipped
because the winning set has no `-march=`. The three PGO builds had three fingerprints (#32) and agreed within 0.7%.
`-march=znver5` built the same code as `-march=native` (`df29754b`) and spent three timed runs, about 2h20m,
re-measuring it (#37a); here the extra runs are what make the pooled `-march` estimate possible.

## Knowledge table

The memory-bound rows this run changed:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 16 of 27, +22.77% | 16 of 28, +21.93% |
| `-fprofile-use` | 5 of 22, -3.95% | 5 of 23, -3.97% |
| `-flto` | 6 of 21, +2.84% | 6 of 22, +2.65% |
| `-march=znver5` | 4 of 11, +1.23% | 4 of 12, +1.12% |
| `-mtune=znver5` | 0 of 11, +0.05% | 0 of 12, -0.14% |
| `-fno-math-errno` | 2 of 10, +0.73% | 2 of 11, +0.54% |

Because the calibration mean sat about 1% high, every row this run added is about 1% low.

## Compared with `chicago`

| | `chicago` (2026-11-12) | `niwot` |
|---|---|---|
| Baseline | 4.3744, ±3.65%, 85 W | 1.0029, ±0.90%, 18 W |
| `-O3` run spread | 4.302-4.483 (4.2%) | 0.970-1.007 (3.8%) |
| `-march` code (`df29754b`), pooled | +2.69% on the calibration mean | +0.62% on all `-O3` runs |
| `-fgraphite-identity` | +1.44% | -1.74% |
| PGO | -0.05% | -4.39% |
| Total | +0.00% | +0.00% |
| Run | 36 trials, 6h11m | 38 trials, 30h40m |

Both hosts reject everything for the same reason: nest_s's own run-to-run spread (about 4% on both, with the same
binaries) is larger than any flag's effect. A longer interleaved measurement of `-O3` against `-O3 -march=native`
(chicago's open item 16) is the only way to resolve the 1-3% `-march` effect on either host. A real but sub-1%
effect would still be rejected on the 1% bar.

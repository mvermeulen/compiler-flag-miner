# `cfm mine` results: 766.femflow_r on `chicago`, 2026-11-07

This is the tenth benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`766.femflow_r` mine on any host. `766.femflow_r` is a C++ finite-element flow solver built on deal.II's
matrix-free operators (`laplace_operator.h`). Its corpus shape is memory-bound at 69.4%.

## Headline result

**`-O3 -flto -march=native`, +132.01% over plain `-O3`** (ratio 89.074 → 206.665). That's the largest gain on any
benchmark this project has mined, on any host. Each 32-copy run went from 527 s to 227 s.

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 89.074 | — |
| `-O3 -march=native` | 205.580 | +130.80% |
| `+ -flto` | 206.665 | +0.53% (from the pair tournament, see below) |

- **`-march=native` alone gave +130.46%.** All six of its reps read 205.19-205.63, against 89.03-89.17 for the
  eight `-O3` runs. It was fast-tracked on the memory-bound prior (accepted 7 of 8).
- **The result is real, not a broken build.** Every trial passed SPEC's `--action=validate` (`valid: S` in each
  `.rsf`), the `-O3` reps agree to ±0.07%, and every `-O3` build had the same code fingerprint (`4302cdf0`).
- **It's AVX-512 autovectorization.** The SPEC copy of deal.II sets `DEAL_II_VECTORIZATION_WIDTH_IN_BITS 0` in
  `config.h`, so its `VectorizedArray` class uses no intrinsics. Its fixed-length element loops are left to the
  compiler, and only `-march=native` lets GCC vectorize them with 512-bit AVX-512 and FMA. Narrowing that with
  `-mprefer-vector-width=256` on top of the winner cost **-15.68%** (174.255), so most of the gain needs the full
  512-bit width.
- **`-flto` gave +16.76% alone, but only +0.53% on top of `-march=native`.** The greedy step read +0.50%, CI-clear of
  `-march=native` but under the 1% bar, and was rejected. The pair `-flto -march=native` then built the same code
  (`5673a072`), was accepted against `-O3` (+132.01%), and replaced the greedy winner because its mean was higher.
  So the final winner carries `-flto` on a +0.5% margin that the greedy walk itself rejected.
- **PGO lost 2.01%** on top of `-flto -march=native`. Its three reps agreed and built the same code (`d00eddc9`).
- **`-fgraphite-identity` was pruned at screening** (83.839, -5.9% against the last calibration rep).
  `-fprefetch-loop-arrays` was confirmed flat (-0.26%).
- **The shape filter dropped 11 candidates** on the 69.4% memory-bound read, including `-Ofast`, `-ffast-math` and
  `-funroll-loops`. With the code this vector-bound under `-march=native`, the memory-bound read clearly describes the
  scalar `-O3` build, not the vectorized one.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 766.femflow_r` (uncapped, defaults) |
| Code | `main` at `b6c0bd6` (no code changes since `f31ba64`, only docs) |
| Experiment id | 12 |
| Started / finished | 2026-11-07T16:16:58Z / 2026-11-07T23:38:01Z (7h21m) |
| Final status | `converged` |
| Trials | 33 (512-544), no reruns, none skipped |
| Candidates screened / confirmed | 3 / 2 (`-flto`, `-fprefetch-loop-arrays`; plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 11 |
| Fast-tracked (M4) | `-march=native` (accepted 7 of 8, mean +7.38%) |
| Winning flags | `["-O3", "-flto", "-march=native"]`, +132.01% |
| Guards | bandwidth gate waited once (30 s, trial 512); no reruns; baseline recheck not flagged (-0.04%) |
| Power | package power median 84.99-85.00 W on every trial; CPU temperature 91.1-96.8°C |

An `-O3` trial took about 15 minutes, a `-march=native` trial about 10, and a PGO trial about 30.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 69.4%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 512 | warm-up | 89.171 |
| 513 | warm-up | 89.035 |
| 514 | calibration | 89.082 |
| 515 | calibration | 89.048 |
| 516 | calibration | 89.093 |
| 529 | recheck | 89.040 (-0.04%) |

The calibration mean is 89.074, with a 95% CI of [89.016, 89.132] (±0.07%), the tightest on this host so far.
Warm-up settled after the minimum two reps (1,863 s).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 517-519 | screening | 3 candidates | 83.84-104.06 | | `-fgraphite-identity` pruned (-5.9%) |
| 520-522 | confirmation | `-fprefetch-loop-arrays` | 88.847 | -0.26% | reject |
| 523-525 | confirmation | `-flto` | 104.001 | +16.76% | **accept** |
| 526-528 | confirmation (fast-tracked) | `-march=native` | 205.279 | +130.46% | **accept** |
| 530-532 | combination (greedy) | `-march=native` | 205.580 | +130.80% | **accept** |
| 533-535 | combination (greedy) | `-march=native -flto` | 206.600 | +0.50% | reject (CI-clear, under the 1% bar) |
| 536-538 | combination (pair) | `-flto -march=native` | 206.665 | +132.01% | **accept**, replaced the greedy winner (same code as 533-535) |
| 539-541 | PGO | `-flto -march=native -fprofile-use` | 202.506 | -2.01% | reject |
| 542-544 | vector width | `-flto -march=native -mprefer-vector-width=256` | 174.255 | -15.68% | reject |

The greedy deltas are against the step before, the pair delta against `-O3`, and the Phase 6 deltas against
`-O3 -flto -march=native`. The microarch multiplier was skipped because the winning set already had
`-march=native`.

## Observations

- **One benchmark now dominates the suite geomean.** femflow's 2.32× lifts the fprate suite geomean from +9.53% to
  +17.48%. Without it, the mined-only geomean would be about +12.9%, as after flightdm. Read the suite numbers with
  that in mind.
- **This is the case `-march=native` priors exist for.** The memory-bound cluster's mean had fallen to +7.4% after
  gmsh, but the strict-majority fast-track still sent it straight to confirmation, saving a screening trial. On a
  build with a fixed `-march=x86-64` baseline, any code written to be autovectorized at AVX-512 width can gain like
  this.
- **The pair tournament again decided the final flagset**, as on flightdm. Here it added `-flto` on a +0.5% margin
  the greedy walk had rejected under the 1% bar. The pair is compared against `-O3`, not against the greedy winner,
  so the 1% bar never applies to its marginal flag. Harmless here (both builds are correct and `-flto` didn't
  hurt), but the winning set is one flag longer than the greedy walk's evidence supports.
- **niwot hasn't mined femflow yet.** With 16 copies and half the memory bandwidth, the same flag should still win
  big there, but by how much is an open question.
- **Package power read 85.0 W on every trial**, for the tenth mine in a row.

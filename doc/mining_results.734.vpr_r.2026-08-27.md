# `cfm mine` results: 734.vpr_r, 2026-08-27

A real, uncapped `cfm mine` run against `734.vpr_r` (VPR, the FPGA placement-and-routing tool from the
VTR toolchain) — the first real mining run of this benchmark, picked specifically for its distinctive
`allocation_pressure=high` shape: the only unmined benchmark in the whole reference-matrix corpus with
elevated allocation pressure, genuinely different from `782.lbm_r` (dense lattice-Boltzmann arrays) and
`777.zstd_r` (streaming compression), the two memory-bound benchmarks mined so far.

## Headline result

**`-O3 -march=native` accepted, +1.04% overall — a real, statistically genuine win, but by a wide margin
the smallest `-march=native` accept recorded in this project's history.** Every ordinary candidate
(`-fprefetch-loop-arrays`, `-fgraphite-identity`, both `-mprefer-vector-width` choices) was cleanly
rejected. `-march=native` was fast-tracked via its real memory-bound prior and confirmed accepted — but
at roughly 1/13th to 1/48th the size of its accepts on other memory-bound/compute-bound benchmarks so
far (+48.75% on `706.stockfish_r`, +14.17%-15.63% on `750.sealcrypto_r`, +14.83% on `707.ntest_r`, and
even +25.31%→+17.14% on the memory-bound cluster's own running mean before this run).

## Run metadata

| | |
|---|---|
| Command | `cfm mine 734.vpr_r` (uncapped) |
| Experiment id | 25 |
| Started | 2026-08-26T23:04:38Z |
| Finished | 2026-08-27T02:16:52Z |
| Wall-clock | 3h12m14s |
| Final status | `converged` |
| Candidates screened | 4 |
| Candidates fast-tracked (M4) | 1 (`-march=native`) |
| Candidates confirmed (ordinary Phase 4) | 0 — `-march=native` accepted via the M4 fast-track path |
| Winning flags | `["-O3", "-march=native"]`, **+1.04% overall gain** |

## Why this benchmark

`734.vpr_r` characterizes `memory-bound` at 45.4% (medium confidence), `vectorization_density=moderate`,
`allocation_pressure=high` — the only unmined benchmark in the reference-matrix corpus with elevated
allocation pressure. VPR's own placement/routing algorithms are graph- and heap-heavy (simulated
annealing over a routing graph, priority-queue-driven pathfinding) — a mechanistically very different
memory access pattern from `lbm_r`'s dense, regular array traversal or `zstd_r`'s streaming buffer
access, and a genuine test of whether the memory-bound cluster's existing priors (especially
`-march=native`'s own large historical wins) hold up on a benchmark shaped this differently.

## Baseline

| Trial | Phase | Ratio |
|---|---|---|
| 419 | **warm-up** (excluded from CI) | 43.355 |
| 420 | **warm-up** (excluded from CI) | 41.301 |
| 421 | calibration | 40.990 |
| 422 | calibration | 40.789 |
| 423 | calibration | 40.797 |

The usual settling pattern, resolved within the 2 warm-up reps. Mean **40.859** (`baseline_ratio_mean`),
CI `[40.58, 41.14]`. Shape from the reference-matrix corpus (`reference-matrix:amd-370-64gb`):
`resource_dominance=memory-bound` at 45.4%, `vectorization_density=moderate`,
`allocation_pressure=high`.

## Phase 2 filtering

Four candidates correctly excluded as implausible given the memory-bound/moderate-vectorization shape:
`-funroll-loops` (compute-bound/backend-bound-tagged), `-Ofast`/`-ffast-math` (compute-bound-tagged),
`-fipa-pta` (backend-bound-tagged) — leaving the four memory-bound/vectorization-relevant candidates that
actually ran, plus `-march=native` (its own real memory-bound prior, fast-tracked).

## M4: `-march=native` fast-tracked, everything else correctly not

```
info: known prior for '-march=native' in cluster 'memory-bound' -- accepted before (mean +17.14%, n=3, last seen on '777.zstd_r')
info: known prior for '-fprefetch-loop-arrays' in cluster 'memory-bound' -- rejected before (mean +1.89%, n=3, last seen on '777.zstd_r')
info: known prior for '-mtune=znver5' in cluster 'memory-bound' -- rejected before (mean +1.49%, n=3, last seen on '777.zstd_r')
info: known prior for '-march=znver5' in cluster 'memory-bound' -- rejected before (mean +1.36%, n=3, last seen on '777.zstd_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'memory-bound' -- rejected before (mean -0.62%, n=3, last seen on '777.zstd_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'memory-bound' -- rejected before (mean -0.66%, n=3, last seen on '777.zstd_r')
info: known prior for '-fgraphite-identity' in cluster 'memory-bound' -- rejected before (mean -0.78%, n=3, last seen on '777.zstd_r')
```

`-march=native` was fast-tracked straight to Phase 4 (trials 440-442 jump directly to
`phase="confirmation"`, no preceding screening trial). Every rejected prior was correctly left to
ordinary screening.

## Ordinary candidates: all four cleanly rejected

| Flag | Confirm mean | Verdict |
|---|---|---|
| `-fprefetch-loop-arrays` | 41.191 | reject |
| `-fgraphite-identity` | 40.860 | reject |
| `-mprefer-vector-width=256` | 40.899 | reject |
| `-mprefer-vector-width=512` | 40.893 | reject |

All landed flat against baseline, consistent with each flag's own rejected prior from `782.lbm_r`/
`777.zstd_r`. Notably, `-fprefetch-loop-arrays` — the flag whose whole catalog rationale is specifically
"software prefetch insertion for array loop traversal," and the one most directly relevant to a
data-structure/pointer-chasing workload's own allocation pressure — still didn't help here either; VPR's
own access pattern (graph/heap-driven, not the regular array-stride pattern this flag targets) is a
plausible, honest explanation, not confirmed further by this run alone.

## `-march=native`: a real accept, but the smallest one on record

| Rep | Ratio |
|---|---|
| 440 | 41.373 |
| 441 | 41.314 |
| 442 | 41.298 |

Mean **41.328**, CI `[41.23, 41.43]` — genuinely non-overlapping with baseline's CI (`[40.58, 41.14]`),
and clearing `MIN_PRACTICAL_SIGNIFICANCE_PCT` by a narrow margin (**+1.15%** vs. baseline's mean,
**+1.04%** in the final summary's own reference point). This is a real, honest accept — not an artifact,
not a borderline statistical call — but by a wide margin the smallest `-march=native` win recorded in
this project:

| Benchmark | Cluster | `-march=native` gain |
|---|---|---|
| `706.stockfish_r` | memory-bound | +48.75% |
| `750.sealcrypto_r` (both runs) | compute-bound | +14.17% / +15.63% |
| `707.ntest_r` | compute-bound | +14.83% |
| `782.lbm_r` | memory-bound | +1.79% (rejected — inside CI) |
| **`734.vpr_r`** | **memory-bound** | **+1.15% (accepted — outside CI, narrowly)** |

VPR's own AVX-512 feature set and vectorizable hot loops are presumably far more modest than
stockfish's NNUE evaluation or sealcrypto's homomorphic-encryption kernels — a real, mechanistically
sensible explanation for why the same flag's real effect size varies this much by workload, exactly the
kind of case cross-benchmark knowledge transfer is *supposed* to surface honestly rather than average
away. Phase 5 combination re-confirmed the same single-flag set (mean 41.284 across trials 443-445,
still accept) — no pair tournament possible, same as every real run to date.

## Phase 6: both multipliers correctly skipped

PGO correctly skipped (`topdown_signals ['frontend-bound', 'speculation-bound']` implausible given
`memory-bound`) — the same skip path confirmed on every memory-bound/compute-bound benchmark so far.
Microarch multiplier correctly skipped too (winning set already carries `-march=native`, the conflict
guard firing exactly as designed).

## Knowledge table, `memory-bound` cluster, after this run

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-march=native` | 4 | 2 | +13.14% (down from +17.14%) |
| `-fprefetch-loop-arrays` | 4 | 0 | +1.62% |
| `-mtune=znver5` | 3 | 0 | +1.49% |
| `-march=znver5` | 3 | 0 | +1.36% |
| `-mprefer-vector-width=256` | 4 | 0 | −0.44% |
| `-mprefer-vector-width=512` | 4 | 0 | −0.48% |
| `-fgraphite-identity` | 4 | 0 | −0.59% |

`-march=native`'s own running mean dropped from +17.14% to +13.14% after folding in this run's modest
+1.15% — the cross-benchmark prior doing exactly what it should: getting more honest (and more
conservative) as more real, varied data accumulates, rather than staying anchored to `706.stockfish_r`'s
own outsized win.

## Compiled-flags audit and package power: nothing unusual

Every trial's audit confirms genuine compilation (`-O3` alone for baseline/rejects,
`-O3 -fprefetch-loop-arrays` etc. for the screened flags); `-march=native`'s own audit correctly reports
"not independently checkable" (the known GCC-rewrite limitation). No unusual power/temperature pattern
this run (`Pearson r(ratio, elapsed_min) = -0.127`, `r(ratio, cpu_temp_c) = +0.207` — both weak, no
phase-change confound this time since only one flag was ever accepted).

## What this run actually confirms

- **First real coverage of a genuinely different memory-bound shape** (`allocation_pressure=high`) —
  `-fprefetch-loop-arrays` still didn't help, a real (if not further investigated) data point about the
  limits of that flag's applicability to graph/heap-driven memory access patterns.
- **M4 continues to work correctly**, and this run is a particularly clean illustration of *why* the
  knowledge table tracks a running mean rather than a single "known-good" flag: `-march=native`'s real
  effect size varies by more than 40x across benchmarks in the same cluster, and the mean now reflects
  that honestly.
- **The asymmetric accept bar is doing real work here too**: a genuinely small, real effect (+1.15%,
  CI non-overlapping) still clears `MIN_PRACTICAL_SIGNIFICANCE_PCT`'s 1.0% floor — a useful, concrete
  data point for how close to that floor a real (not noise) effect can sit.

## Next steps this suggests

- The remaining unmined `intrate` benchmarks are now all lower-confidence memory-bound picks
  (`708.sqlite_r`, `721.gcc_r`, `729.abc_r`, all `low` confidence) or frontend-bound benchmarks that
  would mostly corroborate the now well-established PGO/LTO story (`735.gem5_r`, `753.ns3_r`,
  `710.omnetpp_r`) — `fprate` benchmarks are a natural place to look for further genuinely new coverage.
- Phase 5's pair tournament still has zero real coverage across all real runs to date.
- A genuinely backend-bound benchmark still doesn't exist anywhere in the reference-matrix corpus.

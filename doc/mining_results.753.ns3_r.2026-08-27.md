# `cfm mine` results: 753.ns3_r, 2026-08-27

A real, uncapped `cfm mine` run against `753.ns3_r` (the ns-3 network simulator) — the fifth real
frontend-bound benchmark mined, continuing the systematic push to complete `intrate`. Where the previous
run (`735.gem5_r`) landed this project's first real PGO reject, this run lands a real PGO **accept** —
its largest overall gain yet in the frontend-bound cluster.

## Headline result

**`-O3 -flto -fprofile-use` accepted, +37.99% overall.** `-flto` alone: +23.3%. PGO stacked on top for
another +11.9%. The microarch multiplier's own two candidates both looked marginally promising again
(as they did for `735.gem5_r`) but were correctly rejected once fully measured across 3 reps.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 753.ns3_r` (uncapped) |
| Experiment id | 27 |
| Started | 2026-08-27T13:02:13Z |
| Finished | 2026-08-27T19:07:17Z |
| Wall-clock | 6h5m4s |
| Final status | `converged` |
| Candidates screened | 6 |
| Candidates fast-tracked (M4) | 1 (`-flto`) |
| Candidates confirmed (ordinary Phase 4) | 0 — `-flto` accepted via the M4 fast-track path |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, **+37.99% overall gain** |

## Why this benchmark

`753.ns3_r` characterizes `frontend-bound` at 60.7% (high confidence), `vectorization_density=moderate`,
`allocation_pressure=low` — the last of the two highest-confidence unmined `intrate` benchmarks (after
`735.gem5_r`), continuing systematically through the suite. ns-3 is a real, widely-used discrete-event
network simulator — mechanistically plausible as frontend-bound (event-queue-driven dispatch through a
large, polymorphic C++ object model, similar in spirit to gem5's own architecture).

## Baseline

| Trial | Phase | Ratio |
|---|---|---|
| 490 | **warm-up** (excluded from CI) | 78.764 |
| 491 | **warm-up** (excluded from CI) | 73.577 |
| 492 | calibration | 70.808 |
| 493 | calibration | 70.817 |
| 494 | calibration | 71.010 |

The usual settling pattern, resolved within the 2 warm-up reps. Mean **70.878** (`baseline_ratio_mean`),
shape from the reference-matrix corpus (`reference-matrix:amd-370-64gb`): `resource_dominance=
frontend-bound` at 60.7%, `vectorization_density=moderate`, `allocation_pressure=low`.

## Phase 2 filtering

Six candidates correctly excluded as implausible given the frontend-bound/moderate-vectorization shape:
`-funroll-loops` (compute-bound/backend-bound-tagged), `-Ofast`/`-ffast-math` (compute-bound-tagged),
`-fipa-pta` (backend-bound-tagged), `-fgraphite-identity` (backend-bound/memory-bound-tagged),
`-fprefetch-loop-arrays` (memory-bound-tagged) — leaving the six frontend-bound-relevant candidates plus
`-march=native` (real rejected prior) that actually ran.

## M4: `-flto` fast-tracked, everything else correctly not

```
info: known prior for '-fprofile-use' in cluster 'frontend-bound' -- accepted before (mean +13.51%, n=5, last seen on '735.gem5_r')
info: known prior for '-flto' in cluster 'frontend-bound' -- accepted before (mean +6.16%, n=5, last seen on '735.gem5_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'frontend-bound' -- rejected before (mean +0.24%, n=2, last seen on '735.gem5_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'frontend-bound' -- rejected before (mean +0.12%, n=2, last seen on '735.gem5_r')
info: known prior for '-march=znver5' in cluster 'frontend-bound' -- rejected before (mean -0.37%, n=4, last seen on '735.gem5_r')
info: known prior for '-freorder-blocks-and-partition' in cluster 'frontend-bound' -- rejected before (mean -0.72%, n=5, last seen on '735.gem5_r')
info: known prior for '-mtune=znver5' in cluster 'frontend-bound' -- rejected before (mean -0.78%, n=4, last seen on '735.gem5_r')
info: known prior for '-fno-semantic-interposition' in cluster 'frontend-bound' -- rejected before (mean -0.89%, n=5, last seen on '735.gem5_r')
info: known prior for '-freorder-functions' in cluster 'frontend-bound' -- rejected before (mean -0.91%, n=5, last seen on '735.gem5_r')
info: known prior for '-march=native' in cluster 'frontend-bound' -- rejected before (mean -1.35%, n=4, last seen on '735.gem5_r')
```

`-flto` fast-tracked straight to Phase 4 (trials 519-521 jump directly to `phase="confirmation"`, no
preceding screening trial). Every rejected prior was correctly left to ordinary screening.

## Ordinary candidates: all six correctly rejected

| Flag | Confirm mean | Verdict |
|---|---|---|
| `-freorder-blocks-and-partition` | 70.922 | reject |
| `-freorder-functions` | 70.766 | reject |
| `-fno-semantic-interposition` | 70.828 | reject |
| `-mprefer-vector-width=256` | 71.086 | reject |
| `-mprefer-vector-width=512` | 70.951 | reject |
| `-march=native` | 70.887 | reject |

Every one landed flat, consistent with its own real, rejected cluster prior.

## `-flto`: accepted, +23.3% — the strongest LTO win yet in this cluster

| Rep | Ratio |
|---|---|
| 519 | 86.721 |
| 520 | 87.629 |
| 521 | 87.336 |

Mean **87.229** vs. baseline's 70.878 — **+23.07%**. Phase 5 combination re-confirmed (mean 87.378 across
trials 522-524, still a clean accept). By far the largest single `-flto` win recorded in the
frontend-bound cluster so far (vs. `723.llvm_r`'s own +5.9%, `735.gem5_r`'s +12.44%).

## PGO: accepted, +11.9% on top of LTO

| Rep | Ratio |
|---|---|
| 525 | 97.745 |
| 526 | 97.767 |
| 527 | 97.906 |

Mean **97.806**, tight (0.16% spread) — **+11.94%** on top of the LTO-including comparison baseline
(87.378), **+37.99%** vs. plain `-O3`. This is the cluster's largest overall combined LTO+PGO win yet
(vs. `723.llvm_r`'s own +32.23%), and a real, welcome contrast to `735.gem5_r`'s own PGO reject the
previous run — together, the two runs are a clean demonstration that PGO's real effect genuinely varies
by benchmark within the same cluster, not a fixed property of "frontend-bound workloads" as a category.

## Compiled-flags audit: clean, no repeat of `735.gem5_r`'s own bug

Every trial's audit confirms genuine compilation, including the PGO trial (`-fprofile-use` correctly
found directly, `-flto` correctly reported "not independently checkable"). `753.ns3_r`'s own build
directory contains one real executable (`ns3_r`) plus a leftover linkable object file
(`main_ns3.o`, also ELF-format) — `audit_compiled_flags()`'s multi-binary fix (PR #45, merged the same
day as `735.gem5_r`'s own write-up) reads both without issue, confirming the fix generalizes cleanly to
this benchmark's own (different, milder) multi-ELF-file shape too.

## Phase 6 microarch multiplier: both candidates promising early, correctly rejected once fully measured

| Rep | `-march=znver5` | `-mtune=znver5` |
|---|---|---|
| 1 | 98.758 | 97.858 |
| 2 | 98.345 | 97.945 |
| 3 | 98.465 | 97.865 |

Both means (98.523 and 97.889) sit only marginally above the PGO baseline (97.806) — +0.73% and +0.09%
respectively, both well under `MIN_PRACTICAL_SIGNIFICANCE_PCT`'s 1.0% floor, correctly rejected. A milder
echo of `735.gem5_r`'s own microarch story (where the first rep alone would have looked like a real win)
— here the effect is small and consistent across all 3 reps rather than trending down, but still
correctly recognized as noise-level once judged against the practical-significance bar, not just
statistical non-overlap.

## Knowledge table, `frontend-bound` cluster, after this run

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-fprofile-use` | 6 | 4 | +13.25% |
| `-flto` | 6 | 4 | +8.98% (up from +6.16%) |
| `-mprefer-vector-width=512` | 3 | 0 | +0.20% |
| `-mprefer-vector-width=256` | 3 | 0 | +0.18% |
| `-march=znver5` | 5 | 0 | −0.15% |
| `-freorder-blocks-and-partition` | 6 | 0 | −0.59% |
| `-mtune=znver5` | 5 | 0 | −0.61% |
| `-fno-semantic-interposition` | 6 | 0 | −0.75% |
| `-freorder-functions` | 6 | 0 | −0.78% |
| `-march=native` | 5 | 0 | −1.07% |

Both `-flto` and `-fprofile-use` now sit at **4 real accepts out of 6 trials each** — a strong, mature,
well-evidenced pair of priors for this cluster, with real variance (one recent reject each, from
`735.gem5_r`) keeping the running means honest rather than inflated.

## Package power and drift: the usual phase-change artifact, not real drift

`Pearson r(ratio, elapsed_min) = +0.849` — again dominated by the real, large phase changes (`-O3` →
`-flto` → PGO/microarch) rather than baseline drift, same as every prior multi-phase-accept run
(`723.llvm_r`, `735.gem5_r`). No unusual package-power pattern this run.

## What this run actually confirms

- **PGO's real effect genuinely varies by benchmark, even within one cluster** — a real accept here, a
  real reject on `735.gem5_r` last run, both honest findings from the same cross-benchmark knowledge
  mechanism.
- **The multi-binary audit fix (PR #45) generalizes correctly** to a second, differently-shaped
  multi-ELF-file benchmark, not just the one that originally exposed the bug.
- **The microarch multiplier's own "looks promising on early reps" pattern recurred**, again correctly
  resolved by the full 3-rep measurement — this pipeline's confirmation design continuing to do real,
  visible work.

## Next steps this suggests

- `intrate` completion: `710.omnetpp_r` (frontend-bound, medium confidence) is the next natural pick,
  followed by the three low-confidence memory-bound benchmarks (`708.sqlite_r`/`721.gcc_r`/`729.abc_r`).
- Phase 5's pair tournament still has zero real coverage across all real runs to date.
- The package-power/STAPM hypothesis remains open.

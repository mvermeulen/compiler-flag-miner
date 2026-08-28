# `cfm mine` results: 710.omnetpp_r, 2026-08-28

A real, uncapped `cfm mine` run against `710.omnetpp_r` (the OMNeT++ network simulator) — the sixth real
frontend-bound benchmark mined, and with it, `intrate`'s frontend-bound coverage is essentially complete
(only the three remaining, low-confidence memory-bound benchmarks are left to finish the suite).

## Headline result

**`-O3 -flto -fprofile-use` accepted, +39.90% overall.** `-flto` alone: +13.3%. PGO stacked on top for
another +23.5%. The microarch multiplier's own `-march=znver5` candidate showed a real, concrete
illustration of why CI overlap matters more than raw delta: a nominal **+2.68%** positive delta, but
still correctly rejected because the two confidence intervals genuinely overlapped.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 710.omnetpp_r` (uncapped) |
| Experiment id | 28 |
| Started | 2026-08-28T00:01:02Z |
| Finished | 2026-08-28T03:59:54Z |
| Wall-clock | 3h58m52s |
| Final status | `converged` |
| Candidates screened | 4 |
| Candidates fast-tracked (M4) | 1 (`-flto`) |
| Candidates confirmed (ordinary Phase 4) | 0 — `-flto` accepted via the M4 fast-track path |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, **+39.90% overall gain** |

## Why this benchmark

`710.omnetpp_r` characterizes `frontend-bound` at 45.9% (medium confidence), `vectorization_density=low`,
`allocation_pressure=moderate` — the last frontend-bound benchmark remaining in the unmined `intrate`
list, and the only one above `low` confidence besides the two already mined (`735.gem5_r`, `753.ns3_r`).
OMNeT++ is a real, widely-used discrete-event network simulation framework — mechanistically similar in
spirit to `753.ns3_r`'s own ns-3 (both are event-driven C++ simulators with heavy virtual dispatch), and
the sixth data point for this project's now well-populated frontend-bound cluster.

## Baseline

| Trial | Phase | Ratio |
|---|---|---|
| 534 | **warm-up** (excluded from CI) | 50.875 |
| 535 | **warm-up** (excluded from CI) | 47.976 |
| 536 | calibration | 46.830 |
| 537 | calibration | 46.863 |
| 538 | calibration | 46.944 |

The usual settling pattern, resolved within the 2 warm-up reps. Mean **46.879** (`baseline_ratio_mean`),
shape from the reference-matrix corpus (`reference-matrix:amd-370-64gb`): `resource_dominance=
frontend-bound` at 45.9%, `vectorization_density=low`, `allocation_pressure=moderate`.

## Phase 2 filtering

Six candidates correctly excluded as implausible given the frontend-bound/low-vectorization shape:
`-funroll-loops` (compute-bound/backend-bound-tagged), `-Ofast`/`-ffast-math` (compute-bound-tagged),
`-fipa-pta` (backend-bound-tagged), `-fgraphite-identity` (backend-bound/memory-bound-tagged),
`-fprefetch-loop-arrays` (memory-bound-tagged), both `-mprefer-vector-width` choices
(vectorization-density-high-tagged, correctly excluded since density is `low`) — leaving the four
frontend-bound-relevant candidates plus `-march=native` (real rejected prior) that actually ran.

## M4: `-flto` fast-tracked, everything else correctly not

`-flto`'s real accepted prior (mean +9.59% before this run, n=6 across every prior frontend-bound
benchmark) fast-tracked it straight to Phase 4 (trials 555-557 jump directly to `phase="confirmation"`,
no preceding screening trial). Every rejected prior (`-freorder-blocks-and-partition`,
`-freorder-functions`, `-fno-semantic-interposition`, `-mprefer-vector-width=256/512`, `-march=znver5`,
`-mtune=znver5`, `-march=native`) was correctly left to ordinary screening or excluded by Phase 2
filtering as appropriate.

## Ordinary candidates: all four correctly rejected

| Flag | Confirm mean | Verdict |
|---|---|---|
| `-freorder-blocks-and-partition` | 46.793 | reject |
| `-freorder-functions` | 46.681 | reject |
| `-fno-semantic-interposition` | 46.675 | reject |
| `-march=native` | 46.924 | reject |

Every one landed flat, consistent with its own real, rejected cluster prior.

## `-flto`: accepted, +13.3%

| Rep | Ratio |
|---|---|
| 555 | 53.103 |
| 556 | 52.970 |
| 557 | 53.197 |

Mean **53.090** vs. baseline's 46.879 — **+13.25%**. Phase 5 combination re-confirmed (mean 53.117 across
trials 558-560, still a clean accept).

## PGO: accepted, +23.5% on top of LTO

| Rep | Ratio |
|---|---|
| 561 | 65.076 |
| 562 | 65.584 |
| 563 | 66.084 |

Mean **65.581** vs. the LTO-including comparison baseline (53.117) — **+23.46%** on top,
**+39.90%** vs. plain `-O3`. Notably wider spread across these 3 reps (65.08 → 65.58 → 66.08, a real
upward trend, not tight like `753.ns3_r`'s own PGO measurement) — this turned out to matter directly for
the microarch multiplier's own verdict below.

## Microarch multiplier: a real, concrete CI-overlap-vs-delta illustration

| Rep | `-march=znver5` | `-mtune=znver5` |
|---|---|---|
| 1 | 67.097 | 66.932 |
| 2 | 67.398 | 66.894 |
| 3 | 67.523 | 66.990 |

`-march=znver5`'s own mean (67.339) is a nominal **+2.68%** above PGO's own mean (65.581) — on its own,
that would look like a real, meaningful win. But PGO's own 3 reps trended upward across the run
(65.08 → 66.08), widening its own CI to `[64.33, 66.83]` — wide enough that `-march=znver5`'s own CI
(`[66.79, 67.88]`) still overlaps it at the boundary (66.79 < 66.83). Correctly rejected: a real,
concrete demonstration (verified by direct recomputation, not just trusting the recorded verdict) of why
this pipeline's accept bar requires non-overlapping confidence intervals, not just a positive raw delta —
exactly the discipline this project's own asymmetric accept bar was designed around. `-mtune=znver5`
(mean 66.939, essentially flat vs. PGO) was a more straightforward reject.

## Knowledge table, `frontend-bound` cluster, after this run

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-fprofile-use` | 7 | 5 | +14.71% |
| `-flto` | 7 | 5 | +9.59% |
| `-march=znver5` | 6 | 0 | +0.32% |
| `-mprefer-vector-width=512` | 3 | 0 | +0.20% |
| `-mprefer-vector-width=256` | 3 | 0 | +0.18% |
| `-mtune=znver5` | 6 | 0 | −0.16% |
| `-freorder-blocks-and-partition` | 7 | 0 | −0.53% |
| `-fno-semantic-interposition` | 7 | 0 | −0.71% |
| `-freorder-functions` | 7 | 0 | −0.73% |
| `-march=native` | 6 | 0 | −0.88% |

Both `-flto` and `-fprofile-use` now sit at **5 real accepts out of 7 trials each** — across six real,
independently mined benchmarks (`cpython`, `cppcheck`, `llvm_r`, `gem5_r`, `ns3_r`, `omnetpp_r`), PGO/LTO
have won 5 times and lost once each (`gem5_r`'s own real reject for both). This is now a mature,
well-evidenced cluster-level prior: PGO/LTO are the dominant real win in frontend-bound workloads, but
not universally guaranteed — exactly the honest, calibrated picture cross-benchmark knowledge transfer
is supposed to build.

## Compiled-flags audit and package power: nothing unusual

Every trial's audit confirms genuine compilation, including both the PGO trial (`-fprofile-use` directly
confirmed) and both microarch trials. No audit anomaly this run (unlike `735.gem5_r`'s own multi-binary
bug — `710.omnetpp_r` doesn't appear to trigger the same multi-ELF-file situation). Package power/temp
correlation (`Pearson r(ratio, elapsed_min) = +0.842`) is, as with every other multi-phase-accept run
this session, dominated by the real phase changes (`-O3` → `-flto` → PGO/microarch), not baseline drift.

## What this run actually confirms

- **Frontend-bound coverage in `intrate` is now essentially complete** — six real benchmarks
  (`714.cpython_r`, `727.cppcheck_r`, `723.llvm_r`, `735.gem5_r`, `753.ns3_r`, `710.omnetpp_r`), spanning
  a real mix of PGO/LTO accepts (5/6 each) and one real, honest reject each (`gem5_r`).
  Only the three remaining low-confidence memory-bound benchmarks (`708.sqlite_r`, `721.gcc_r`,
  `729.abc_r`) are left to finish `intrate` entirely.
- **CI overlap, not raw delta, is the real accept criterion** — this run gave a clean, directly-verified
  concrete example: a real +2.68% positive delta, still correctly rejected because the confidence
  intervals genuinely overlapped (driven by PGO's own settling trend widening its own CI).
- **M4 continues to work correctly**, fast-tracking `-flto` on a now seven-trial-deep real prior.

## Next steps this suggests

- Finishing `intrate`: `708.sqlite_r`, `721.gcc_r`, `729.abc_r` — all low-confidence memory-bound, the
  last three benchmarks needed to complete the whole suite.
- Phase 5's pair tournament still has zero real coverage across all real runs to date.
- The package-power/STAPM hypothesis remains open.

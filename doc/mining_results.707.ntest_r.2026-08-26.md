# `cfm mine` results: 707.ntest_r, 2026-08-26

A real, uncapped `cfm mine` run against `707.ntest_r` (the Othello/Reversi engine `ntest`) — the first
real mining run of an `intrate`-suite benchmark since `727.cppcheck_r`, picked deliberately for two
reasons at once: it's compute-bound with a genuinely **narrow margin** (40.6%, medium confidence, the
only unmined benchmark in the whole reference-matrix corpus with this shape), making it the natural
real-verification target for M2's signature-aware candidate ranking (PR #43); and it's new suite
coverage — six benchmarks had been mined before this, none of them `intrate`'s own compute-bound corner.

## Headline result

**`-O3 -march=native` accepted, +14.83% overall — and a genuinely direct confirmation that M2's ranking
pass works correctly on real data.** The first attempt at this run crashed instantly in Phase 2 (see
"Two real bugs found along the way" below); once fixed, a clean re-run confirmed the actual thing this
benchmark was picked to test: `-march=native` is the only candidate in this benchmark's real, narrow-margin
compute-bound shape carrying both the `compute-bound` and `retiring-high-narrow-margin` signals, and
M2's ranking correctly scores it above `-Ofast`/`-ffast-math`/`-funroll-loops` (which carry `compute-bound`
alone) — confirmed by a direct, read-only `candidate_flags_for_signature()` call against this benchmark's
real characterized shape, not just a unit-test fixture.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 707.ntest_r` (uncapped) |
| Experiment id | 23 (a first attempt, experiment 22, crashed in Phase 2 — see below) |
| Started | 2026-08-26T01:09:41Z |
| Finished | 2026-08-26T03:30:05Z |
| Wall-clock | 2h20m24s — notably faster than every fprate/heavier-intrate benchmark mined so far |
| Final status | `converged` |
| Candidates screened | 3 |
| Candidates fast-tracked (M4) | 1 (`-march=native`) |
| Candidates confirmed (ordinary Phase 4) | 0 — `-march=native` accepted via the M4 fast-track path |
| Winning flags | `["-O3", "-march=native"]`, **+14.83% overall gain** |

## Why this benchmark

`707.ntest_r` characterizes `compute-bound` at 40.6% (medium confidence, `vectorization_density=low`,
`allocation_pressure=low`) — the *only* unmined benchmark, across all of `intrate`/`fprate`, with a
compute-bound primary shape. Every other unmined candidate checked was memory- or frontend-bound (see
the full table shared with the user before this run was picked). A narrow margin (well under the
`_NARROW_MARGIN_MAX_PCT = 60.0` threshold) is exactly the case doc/DESIGN.md §4.3's own
`retiring-high-narrow-margin` row describes — "diminishing returns for aggressive flags... `-march` for
the last few percent" — and exactly the case M2's ranking pass was built to make concrete, not just
prose.

## Two real bugs found along the way — exactly what real verification is for

The first attempt (experiment 22) crashed instantly in Phase 2 with
`TypeError: '<=' not supported between instances of 'str' and 'float'`. Root-caused and fixed in PR #44
before this run:

1. **`resource_dominance_pct` came back as a `str`, not a `float`, from the reference-matrix
   characterization path specifically.** `reference_matrix.py`'s `_score_guest_vector()` returned
   `parse_kv_lines()`'s raw `dict[str, str]` straight through with no numeric coercion at all — unlike
   `instrumentation/wspy.py`'s own `characterize()`, which already coerced this same field correctly for
   the *local* `deep-cpu` path. Invisible until this exact moment: M2's own ranking code was the first
   thing to ever do a numeric comparison (`pct <= _NARROW_MARGIN_MAX_PCT`) on it. Fixed by moving the
   coercion helper (`_to_float()` → shared `cfm/util.py::to_float()`) so both paths use one definition,
   and having `_score_guest_vector()` coerce both known numeric scorecard keys before returning.
2. **`cli.py`'s `mine` handler only ever caught `RuntimeError`** — the `TypeError` above crashed straight
   through uncaught, leaving experiment 22 stuck at `status='running'` forever (fixed up by hand
   afterward). Fixed with a new `except Exception` clause that marks the experiment failed before
   re-raising, matching `run_one_trial()`'s own "record it, then still let the real traceback surface"
   posture.

Both fixes landed in PR #44 (merged) before this clean re-run. See CLAUDE.md's Non-obvious traps log
(2026-08-26 entry under M2) for the full story.

## Baseline

| Trial | Phase | Ratio |
|---|---|---|
| 360 | **warm-up** (excluded from CI) | 57.405 |
| 361 | **warm-up** (excluded from CI) | 53.296 |
| 362 | calibration | 51.481 |
| 363 | calibration | 51.432 |
| 364 | calibration | 51.512 |

The usual settling pattern, fully resolved within the 2 warm-up reps — the 3 real calibration reps are
tight (51.43–51.51, well under 0.2% spread). Mean **51.475** (`baseline_ratio_mean`), shape from the
reference-matrix corpus (`reference-matrix:amd-370-64gb`): `resource_dominance=compute-bound` at
**40.6%** (`baseline_resource_dominance_pct` — the exact field that crashed the first attempt, now
correctly a float), `vectorization_density=low`, `allocation_pressure=low`.

## M2's ranking, confirmed directly against this benchmark's real shape

A read-only `candidate_flags_for_signature()` call using this benchmark's exact real characterized shape
(`resource_dominance="compute-bound"`, `resource_dominance_pct=40.60`, `vectorization_density="low"`)
returns, in order:

```
-march=native                  signals=['compute-bound', 'retiring-high-narrow-margin']   <- rank 2
-funroll-loops                 signals=['compute-bound', 'backend-bound']                 <- rank 1
-Ofast                         signals=['compute-bound']                                  <- rank 1
-ffast-math                    signals=['compute-bound']                                  <- rank 1
... (frontend-bound/memory-bound/vectorization-tagged candidates, all rank 0, already excluded by Phase 2 filtering anyway)
```

`-march=native` genuinely outranks the other three (2 matching signals vs. 1) precisely because the real
margin (40.6%) is below the narrow-margin threshold — the concrete case doc/DESIGN.md §4.3's table
describes, now demonstrated against a real benchmark's real shape, not a synthetic fixture.

**One honest nuance**: the *live* run's own Phase 3 screening order doesn't directly show this ranking
in action, because M4's cross-benchmark knowledge transfer fast-tracks `-march=native` straight to Phase
4 (it already has a real accepted prior, `750.sealcrypto_r`'s own +14.79%), pulling it out of the
ordinary ranked-candidate list before ranking order would ever matter for it. Only `-funroll-loops`,
`-Ofast`, `-ffast-math` (all tied at rank 1, no prior) went through ordinary screening, in stable
catalog order — consistent with, but not a direct display of, the narrow-margin ranking boost. The direct
`candidate_flags_for_signature()` call above is what actually demonstrates the boost.

## Phase 2 filtering

Nine candidates were correctly excluded as implausible given the compute-bound/low-vectorization-density
shape: `-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition`
(frontend-bound-tagged), `-fprefetch-loop-arrays` (memory-bound-tagged), both `-mprefer-vector-width`
choices (vectorization-density-high-tagged, correctly excluded since density is `low` here), `-fipa-pta`
and `-fgraphite-identity` (backend-bound-tagged) — leaving exactly the four compute-bound-tagged
candidates ranked above.

## M4: a second real accept in the compute-bound cluster

```
info: known prior for '-march=native' in cluster 'compute-bound' -- accepted before (mean +14.79%, n=2, last seen on '750.sealcrypto_r')
info: known prior for '-funroll-loops' in cluster 'compute-bound' -- rejected before (mean -5.54%, n=1, last seen on '750.sealcrypto_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'compute-bound' -- rejected before (mean -5.68%, n=1, last seen on '750.sealcrypto_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'compute-bound' -- rejected before (mean -5.71%, n=1, last seen on '750.sealcrypto_r')
info: known prior for '-Ofast' in cluster 'compute-bound' -- rejected before (mean -5.83%, n=1, last seen on '750.sealcrypto_r')
info: known prior for '-ffast-math' in cluster 'compute-bound' -- rejected before (mean -5.84%, n=1, last seen on '750.sealcrypto_r')
```

`-march=native` was fast-tracked correctly (no preceding screening trial — trials 377-379 jump straight
to `phase="confirmation"`), then confirmed **accepted** on its own real merits: 59.04/59.23/59.01 vs.
baseline's 51.48/51.43/51.51, **+14.83%** — remarkably close to its own prior mean (+14.79%), the
strongest cross-run agreement any accepted flag has shown yet in this project. Every other prior
(rejected) was correctly *not* fast-tracked and went through ordinary screening, all landing consistent
with their own rejected priors (flat-to-slightly-negative).

Knowledge table, `compute-bound` cluster, after this run:

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-march=native` | 3 | 3 | **+14.80%** |
| `-ffast-math` | 2 | 0 | −2.81% |
| `-Ofast` | 2 | 0 | −2.82% |
| `-funroll-loops` | 2 | 0 | −2.98% |
| `-mprefer-vector-width=256` | 1 | 0 | −5.68% |
| `-mprefer-vector-width=512` | 1 | 0 | −5.71% |

`-march=native` is now **3 for 3** in the compute-bound cluster — the strongest, most consistent prior
of any flag in the whole knowledge base.

## Phase 5/6: trivial combination, both multipliers correctly skipped

Phase 5's greedy combination had exactly one confirmed candidate to work with — re-confirmed the same
single-flag set (59.05/59.16/59.11, mean 59.107), no pair tournament possible (still zero real coverage
of that path across every run to date). PGO correctly skipped (`topdown_signals ['frontend-bound',
'speculation-bound']` implausible given `compute-bound`) — the same skip path already confirmed on
`782.lbm_r`/`706.stockfish_r`/`777.zstd_r`. Microarch multiplier correctly skipped too (winning set
already carries `-march=native`, the conflict guard firing exactly as designed).

## Compiled-flags audit and package power: nothing unusual

Every trial's audit confirms genuine compilation (`-O3` alone for baseline/rejects, `-O3 -funroll-loops`
etc. for the screened flags); `-march=native`'s own audit correctly reports "not independently checkable"
(GCC expands it before recording — the known, already-understood limitation). Package power stayed in a
narrow 23–26W band throughout (no useful ramp signal either way this run — a short, ~2h20m run doesn't
give much room for one). `Pearson r(ratio, elapsed_min) = +0.585` looks superficially like the settling
pattern documented in prior runs, but here it's a **different, mundane cause**: the correlation is
dominated by the phase change to `-march=native` (a real, distinct +14.8% effect that happens to occur
later in the run), not baseline drift — the pre-`-march` portion (trials 360-376, ~37 to 107 minutes
elapsed) actually holds quite flat around 51.3-51.8 the whole time. Worth flagging explicitly so this
run's own correlation number isn't misread as more settling-drift evidence.

## What this run actually confirms

- **M2's signature-aware ranking works correctly on real data** — direct, read-only verification against
  this benchmark's exact real characterized shape shows `-march=native` genuinely outranking the other
  compute-bound candidates specifically because the real margin is narrow, exactly as designed.
- **Two real, independent bugs were found and fixed by attempting real verification** — a latent type bug
  in the reference-matrix path (invisible until M2's first-ever numeric use of the field) and a
  generalizable gap in `cli.py`'s exception handling. Both fixed, both covered by new tests.
- **M4 continues to work correctly, now with its second real accept in the same cluster** —
  `-march=native` fast-tracked and confirmed a second time in `compute-bound`, this time with a
  near-perfect match to its own prior (+14.83% vs. +14.79%).
- **New suite coverage**: the seventh real benchmark mined, and the first real `intrate` mining since
  `727.cppcheck_r`.

## Next steps this suggests

- The compute-bound cluster now has a very strong, well-evidenced `-march=native` prior (3/3 real
  accepts) — a good candidate for eventually testing whether a prior this strong should someday skip
  *confirmation* too, not just screening (a real design question, not yet on the implementation list).
- Phase 5's pair tournament still has zero real coverage across all real runs to date.
- The package-power/STAPM hypothesis remains open — this run's own short duration didn't add useful data
  either way.

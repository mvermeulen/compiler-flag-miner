# `cfm mine` results: 714.cpython_r, 2026-08-23

The first **uncapped** `cfm mine` run completed after both the basepeak config-scoping bug and the
isolated-candidate-flags bug were fixed, and the first real end-to-end exercise of Phase 6's PGO
multiplier (`run_pgo_multiplier()`) outside mocked-backend unit tests. It produced this project's
**first genuine accepted candidate of any kind** — real two-pass PGO, stacked on top of an already-
accepted `-flto`, for a real, substantial win.

## Headline result

**`-O3 -flto -fprofile-use` beats plain `-O3` by +41.65%.** `-flto` alone was accepted at Phase 4/5
(+8.00% vs. baseline); real two-pass PGO was then accepted on top of that at Phase 6 (+31.16% more,
compared against the `-flto`-including running set, not the original baseline). Every other candidate
was correctly rejected as noise-level or excluded up front as mechanically implausible.

## Why this benchmark

Picked deliberately, not by chance: `run_pgo_multiplier()`'s own plausibility check (mirroring Phase 2's
`_filter_implausible_candidates()`) skips the PGO trial entirely — no ~2x build-time cost spent — unless
baseline's characterized `resource_dominance` matches at least one of `-fprofile-use`'s catalog
`topdown_signals` (`frontend-bound`, `speculation-bound`). Of the three benchmarks mined so far:

| Benchmark | `resource_dominance` | PGO attempted? |
|---|---|---|
| 706.stockfish_r | memory-bound | skipped |
| 782.lbm_r | memory-bound | skipped |
| **714.cpython_r** | **frontend-bound** | **attempted** |

`714.cpython_r` is the only one of the three where PGO would ever get a real trial at all. It's also a
natural pick on its own mechanical merits: CPython's bytecode-dispatch loop is a textbook frontend/
speculation-bound workload (unpredictable indirect branches, poor icache locality from a large,
irregular dispatch table) — exactly the shape PGO is supposed to help most, and exactly why CPython's
own real-world build (`--enable-optimizations`) uses PGO+LTO by default. This is also the very benchmark
that originally motivated building real PGO support in the first place.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 714.cpython_r` (uncapped) |
| Experiment id | 12 |
| Started | 2026-08-23T00:53:57Z |
| Finished | 2026-08-23T04:07:23Z |
| Wall-clock | 3h13m26s |
| Final status | `converged` |
| Candidates screened | 7 (of 7 plausible survivors — none left unscreened) |
| Candidates accepted (Phase 4) | 1 (`-flto`) |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +41.65% overall gain |

## Baseline

`baseline_characterization_source: "local-deep-cpu-trial"` — unlike the lbm run, the external
reference-matrix corpus didn't have a matching published entry this time, so `_characterize_baseline()`
fell back to its own real local `deep-cpu` trial (the slower path, but still correct — this is exactly
the fallback that path exists for).

Baseline calibration (3× `quick`-profile reps at `-O3` alone):

| Trial | Ratio | CPU temp |
|---|---|---|
| 128 | 66.161 | — |
| 129 | 66.460 | 93.2°C |
| 130 | 66.540 | 92.9°C |
| 131 | 66.546 | 92.4°C |

Mean **66.515**, `resource_dominance=frontend-bound`, `vectorization_density=moderate`,
`allocation_pressure=moderate`. Notably tight and stable compared to both retracted runs' own baseline
reps (no cold-start-outlier pattern this time) — a real, clean CI to compare every candidate against.

## Candidate generation and filtering

`_filter_implausible_candidates()` excluded 6 catalog flags as mechanically implausible against a
frontend-bound, moderate-vectorization baseline:

- `-funroll-loops` (`compute-bound`, `backend-bound`)
- `-fprefetch-loop-arrays` (`memory-bound-corroborated`)
- `-Ofast`, `-ffast-math` (`compute-bound`)
- `-fipa-pta` (`backend-bound`)
- `-fgraphite-identity` (`backend-bound`, `memory-bound-corroborated`)

Plus the usual 3 unresolved-template-placeholder catalog entries skipped (`-mbranch-cost=N`,
`--param prefetch-latency=N`, `-finline-limit=N`). **7 plausible survivors** screened: `-flto`,
`-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition`,
`-mprefer-vector-width=256`, `-mprefer-vector-width=512`, `-march=native`.

## Phase 3/4: screening and confirmation

| Flag | Screening ratio | Confirm mean | Delta | Verdict |
|---|---|---|---|---|
| `-flto` | 70.22 | 71.24 | **+6.85%** | **accept** |
| `-freorder-blocks-and-partition` | 66.90 | 67.32 | +1.21% | reject |
| `-freorder-functions` | 66.61 | 66.72 | +0.31% | reject |
| `-fno-semantic-interposition` | 66.27 | 66.71 | +0.29% | reject |
| `-mprefer-vector-width=256` | 66.23 | 66.90 | +0.58% | reject |
| `-mprefer-vector-width=512` | 66.41 | 67.01 | +0.74% | reject |
| `-march=native` | 62.97 | — | −5.32% | **pruned at screening** (clearly worse) |

`-march=native` is the one real surprise here: it screened *worse* than baseline (−5.32%, past the 5%
prune bar), so it never reached confirmation at all. Not investigated further this run — a real, if
minor, finding worth a closer look sometime (this host's `-march=native` expands to a large `znver5`-
specific flag set; a genuine regression from over-specific tuning on this workload isn't implausible,
but one screening rep is exactly the noisy, unconfirmed signal Phase 3 is designed to prune on rather
than trust outright).

Only `-flto` cleared confirmation's bar (statistically *and* practically significant, `MIN_PRACTICAL_
SIGNIFICANCE_PCT`-clearing, non-overlapping CI vs. baseline's own tight one).

## Phase 5: greedy combine

With only one accepted candidate, the greedy walk is trivial: re-confirms `-O3 -flto` against the
current running set (still baseline, since nothing preceded it) — accepted again, delta ticking up
slightly to +8.00% (71.84 mean vs. baseline's 66.52) on the fresh confirmation reps. No pair tournament
possible with only one accepted flag (`itertools.combinations` of one element is empty). `combination_
winning_flags = ["-O3", "-flto"]`.

## Phase 6: the PGO multiplier — the real headline

`run_pgo_multiplier()`'s plausibility check passed (`frontend-bound` is directly one of `-fprofile-use`'s
own catalog signals), so the real two-pass PGO trial ran: `-O3 -flto -fprofile-use` via SPEC's native
`PASS1_OPTIMIZE`/`PASS2_OPTIMIZE` mechanism, compared against Phase 5's own winning CI (71.84 mean, not
the original baseline).

| Trial | Ratio | CPU temp |
|---|---|---|
| 160 | 94.369 | 93.8°C |
| 161 | 94.548 | 94.4°C |
| 162 | 93.739 | 94.2°C |

Confirmation mean **94.219** (95% CI [93.16, 95.27]) vs. comparison mean 71.84 (95% CI [69.70, 73.97]) —
**+31.16%, accept**, cleanly non-overlapping. Combined with `-flto`'s own prior +8.00%, this is
**+41.65% vs. plain `-O3`** overall — by a wide margin the largest real, verified gain this project has
found for any benchmark, and the first time Phase 6 has actually changed a mining run's final answer.

`knowledge` table now carries real, trustworthy `frontend-bound`-cluster entries for both `-flto`
(accepted, +6.85% at first confirmation) and `-fprofile-use` (accepted, +31.16%) — the first real
positive priors this project's cross-benchmark knowledge transfer has to offer a future benchmark.

## A real audit puzzle, chased down rather than waved off

The PGO trials' own compiled-flags audit reported `-flto` as **"NOT FOUND in compiled binary"** —
worth taking seriously given this project's basepeak history, so it was verified directly rather than
assumed benign:

- The real SPEC build log shows `-flto` genuinely present on every per-translation-unit compile command,
  plus `lto-wrapper: warning: using serial compilation of 51 LTRANS jobs` — real link-time optimization
  definitely ran.
- Reading the actual linked binary's `.GCC.command.line` section directly explains the false negative:
  it records `"GNU GIMPLE 15.2.0 ... -fltrans"` — GCC's own **internal LTRANS re-invocation** of itself
  at final-link time, not the original `-flto` flag. GCC's LTO backend transforms the recorded
  invocation at this stage, so a literal `"-flto"` substring check reports "missing" on *every* LTO
  build, correct or not — the win here was never actually in doubt, but the audit text alone was
  misleading.

Fixed: `-flto` is now added to `cfm/agents/spec_agent.py`'s `_AUDIT_UNVERIFIABLE_LITERAL_FLAGS` (the
same set `-march=native`/`-mtune=native` already live in, for the same underlying reason — GCC rewrites
the flag before recording it). A future LTO trial's audit will report "not independently checkable"
instead of a false "NOT FOUND" that could otherwise wrongly suggest LTO silently didn't happen.

## Timing

3h13m26s total for an uncapped run — meaningfully longer than the retracted 2026-08-21 cpython run's
2h26m5s, almost entirely because this run paid the real local `deep-cpu` characterization trial (the
reference-matrix corpus had no matching entry this time) and because Phase 6's PGO trial is a genuinely
bigger build (instrumented compile + training run + optimized rebuild, ×3 confirmation reps) than any
other single trial in the run.

## What this run actually confirms

- **Phase 6 works end to end, for real, for the first time**: the plausibility check correctly attempted
  PGO here (and would have correctly skipped it for a memory-bound benchmark), the real PASS1/PASS2
  build genuinely ran, and the accept/reject/knowledge-upsert machinery handled a `phase="multiplier"`
  trial exactly like Phase 4's own single-flag confirmations.
- **The basepeak and isolated-candidate-flags fixes both continue to hold**: every trial's compiled-flags
  audit (once corrected for the `-flto` false-negative) confirms the intended flags genuinely reached the
  compiler at every stage.
- **A real, substantial win exists and was found correctly** — not a false accept: the CI is tight and
  clean, the delta is large, and the mechanism (PGO on a frontend-bound interpreter dispatch loop) is
  exactly what compiler literature and CPython's own build practice would predict.

## Next steps this suggests

- **Still need a benchmark whose `resource_dominance` is compute-bound or backend-bound** — three real
  runs now cover memory-bound (stockfish, lbm) and frontend-bound (cpython); the compute-bound/
  backend-bound-targeted catalog categories (`-Ofast`, `-ffast-math`, `-fipa-pta`, `-funroll-loops`) have
  never gotten a real trial yet.
- **`-march=native`'s screening-stage regression** on this benchmark is a loose thread worth a closer,
  dedicated look sometime — not blocking, but a real, if small, surprise this run surfaced.
- **Phase 5's pair tournament still has zero real coverage** — every run so far has had at most one
  accepted candidate, never the two-or-more needed to exercise the random-pair synergy search for real.

# `cfm mine` results: 706.stockfish_r, 2026-08-20

The first two real `cfm mine` runs against actual SPEC CPU2026/wspy (M1's "shipped and verified"
milestone, `CLAUDE.md`'s Status line). Both mined the same benchmark from the same `-O3` baseline on
the same host; documented together because the differences between them are as informative as the
result itself.

## Headline result

**`-O3` alone remains the peak config. Nothing in the current catalog beats it for `706.stockfish_r` on
this host**, confirmed twice (once budget-capped, once uncapped) with the same conclusion both times.
This is a real, negative finding worth keeping — not a failed run. Every flag that survived screening
looked marginally better on one cheap iteration and then failed to hold up under 3-rep confirmation,
exactly the false-accept pattern `doc/DESIGN.md` §15's asymmetric accept bar exists to catch.

## The two runs

| | Experiment 5 | Experiment 6 |
|---|---|---|
| Command | `cfm mine 706.stockfish_r --max-trials 8` | `cfm mine 706.stockfish_r` (uncapped) |
| Started | 2026-08-20T07:21:58Z | 2026-08-20T11:38:32Z |
| Finished | 2026-08-20T09:39:44Z | 2026-08-20T14:19:02Z |
| Wall-clock | 2h17m46s | 2h40m30s |
| Final status | `budget-exhausted` | `converged` |
| Candidates screened | 4 (of 5 plausible; budget cut it short) | 5 (all plausible candidates) |
| Candidates accepted | 0 | 0 |
| Winning flags | `["-O3"]` | `["-O3"]` |
| Gain vs. baseline | 0.0% | 0.0% |

## Baseline characterization (Phase 1)

Both runs characterized the same shape from a `deep-cpu --iterations 1` trial:
`resource_dominance=memory-bound`, `vectorization_density=moderate`, `allocation_pressure=high`.

Baseline calibration means (3× `quick`-profile reps, the characterization trial's own ratio excluded
from the mean per `orchestrator.py`'s design):

| | Experiment 5 | Experiment 6 |
|---|---|---|
| Reps | 147.980, 148.374, 148.641 | 142.797, 143.347, 143.935 |
| Mean | **148.332** | **143.360** |

**Same flags, same benchmark, same host, ~4 hours apart: a 3.5% difference in the baseline's own
absolute ratio.** Neither run was contending with another process (the host-exclusivity lock,
`cfm/lock.py`, guarantees that), so this is real environmental/run-to-run noise on an otherwise-idle
machine, not confounded measurement. Worth remembering as a rough noise-floor data point next time
`MIN_PRACTICAL_SIGNIFICANCE_PCT` (currently a fixed 1.0%, `doc/DESIGN.md` §14 M2.5 item 3) comes up for
recalibration — the spread here is within that bar, but not by a wide margin.

## Candidate generation (Phase 2): the catalog's real yield for this benchmark

`706.stockfish_r` is C++-only, giving 18 of the seed catalog's 21 flags applicable language-wise. Of
those 18:

- **3 skipped outright** as unresolved template placeholders, not concrete flags:
  `-mbranch-cost=N`, `--param prefetch-latency=N`, `-finline-limit=N`.
- **10 excluded by `_filter_implausible_candidates()`** (M2.5 item 3) as mechanically implausible
  against the characterized `memory-bound`/`moderate`-vectorization-density shape: `-flto`,
  `-fprofile-generate`, `-fprofile-use`, `-freorder-blocks-and-partition`, `-freorder-functions`,
  `-fno-semantic-interposition`, `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta`.
- **5 survived to screening**: `-fprefetch-loop-arrays`, `-mprefer-vector-width=256`,
  `-mprefer-vector-width=512`, `-march=native`, `-fgraphite-identity`. Experiment 5's `--max-trials 8`
  budget only reached the first 4 of these; experiment 6 (uncapped) reached all 5.

This is the first real evidence the plausibility filter is pulling its weight: 13 of 18 applicable
flags never cost a single real trial, and — per the confirmation results below — every one of the 5
that *did* get tried turned out not to help either. The filter's judgment call (implausible ⇒ skip) and
the actual measured outcome (plausible-but-tried ⇒ still no win) point the same direction here.

## Screening → confirmation, flag by flag

Delta is each flag's 3-rep confirmation mean vs. that run's own baseline calibration mean. All five
were rejected in both runs — either the delta didn't clear `MIN_PRACTICAL_SIGNIFICANCE_PCT` (1.0%), or
the confidence interval overlapped the baseline's, per `_confirm_flagset()`'s asymmetric accept bar.

| Flag | Exp 5 screening ratio | Exp 5 confirm mean (Δ%) | Exp 6 screening ratio | Exp 6 confirm mean (Δ%) |
|---|---|---|---|---|
| `-fprefetch-loop-arrays` | 148.983 | 148.052 (−0.19%) | 144.203 | 143.998 (+0.45%) |
| `-mprefer-vector-width=256` | 149.032 | 147.117 (−0.82%) | 144.411 | 143.684 (+0.23%) |
| `-mprefer-vector-width=512` | 149.093 | 145.676 (−1.79%) | 144.930 | 143.085 (−0.19%) |
| `-march=native` | 148.672 | 144.891 (−2.32%) | 144.540 | 143.464 (+0.07%) |
| `-fgraphite-identity` | — (not reached) | — | 143.798 | 143.633 (+0.19%) |

Notable: every flag looked *better* than baseline at the single-iteration screening stage in both runs
(the whole reason screening only prunes "clearly worse," not "not clearly better" — doc/DESIGN.md §6
Phase 3), yet none held that lead across 3 real confirmation reps. `-march=native` is the sharpest
example: +0.23% in experiment 5's screening trial, then −2.32% once actually confirmed. This is the
concrete case study for why confirmation exists as a separate, stricter stage.

## Phase 5 (greedy combine)

Not meaningfully exercised by either run — with zero Phase 4 acceptances, the greedy walk had nothing
to fold in and the pair tournament had no accepted pairs to draw from. **Still an open gap**: neither
real run has tested Phase 5's actual combination logic end-to-end. That needs a benchmark/catalog
combination where at least two flags individually clear the confirmation bar.

## Timing, for future estimates

Both runs' `quick`-profile single-iteration trials landed at a consistent **~4:47–4:58 apart**
regardless of which flag was being tried. The one `deep-cpu` characterization trial per run took
**~46–47 minutes** — notably more than 3× a `quick` trial's cost, likely the extra counter-multiplexing
overhead `doc/DESIGN.md` §14 M2.5 item 2 already flags as expensive. `results/logs/` has each run's full
stdout (final JSON summary + the Phase 2 filter's `info:` lines); `cfm.db`'s `trials` table
(`experiment_id` 5 and 6) has every individual trial.

## Next steps this suggests

- **Phase 5 still needs a real end-to-end exercise** — pick a benchmark/catalog pair likely to produce
  ≥2 accepted flags (a compute-bound or frontend-bound benchmark should hit more of the currently-
  excluded categories, e.g. `-funroll-loops`/`-Ofast`/`-freorder-*`) rather than trying to force it on
  `706.stockfish_r`, where the plausibility filter is (so far) correctly finding nothing to combine.
- **A second, differently-shaped benchmark** is also M4's own prerequisite (cross-benchmark knowledge
  transfer needs two real benchmarks' worth of `knowledge` rows to transfer between) — this doubles as
  that groundwork.
- The 3.5% baseline-to-baseline spread is worth a second look once `MIN_PRACTICAL_SIGNIFICANCE_PCT`
  comes up for recalibration (§14 M2.5 item 3's own noted future refinement, using the reference
  matrix's historical stddev instead of a fixed 1.0%).

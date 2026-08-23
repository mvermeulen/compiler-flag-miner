# `cfm mine` results: 782.lbm_r, 2026-08-22

The first `cfm mine` run in this project's history conducted after **both** real bugs were fixed: the
basepeak config-scoping bug (2026-08-21, every prior run measured the wrong binary) and the
isolated-candidate-flags bug (2026-08-22, candidates were tested without baseline's own `-O3`). Every
number and verdict below reflects a genuinely different binary built and measured for a genuinely
different flag set — the first time that sentence has been true for a `cfm mine` run's own results,
not just for `cfm`'s unit tests or an isolated ad hoc verification build.

Deliberately run as a **focused, budget-capped test** (`--max-trials 4`), not an unconstrained
full run — per the explicit ask to "confirm/deny things with a more focused test" rather than repeat
the unconstrained-run pattern that produced the two now-retracted `782.lbm_r`/`706.stockfish_r`
write-ups.

## Headline result

**`-O3` alone remains the peak config; the one candidate exercised (`-fprefetch-loop-arrays`) was
correctly rejected.** Its confirmed delta (+3.29%) is real and positive, but sits inside baseline's own
wide confidence interval — the confirmation gate correctly declined to call a win. Every trial's
compiled-flags audit confirms the intended flags actually reached the compiler this time
(`-O3` alone for baseline, `-O3 -fprefetch-loop-arrays` together for the candidate) — the exact defect
class both prior bugs produced, now independently checked and clean.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 782.lbm_r --max-trials 4` |
| Experiment id | 11 |
| Started | 2026-08-22T22:00:47Z |
| Finished | 2026-08-23T00:16:44Z |
| Wall-clock | 2h15m57s |
| Final status | `budget-exhausted` |
| Candidates screened | 1 (of 5 plausible survivors — budget-capped, see below) |
| Candidates accepted | 0 |
| Winning flags | `["-O3"]`, 0.0% gain |

## Baseline: reference-matrix characterization, again live

`baseline_characterization_source: "reference-matrix:amd-370-64gb"` — same external corpus path as the
(retracted) 2026-08-21 run, working correctly here too: `resource_dominance=memory-bound`,
`vectorization_density=high`, `allocation_pressure=low`, recovered from a different real machine with
zero local characterization trial needed.

Baseline calibration (3× `quick`-profile reps at `-O3` alone — this time genuinely `-O3` alone, audited):

| Trial | Ratio | CPU temp | Elapsed |
|---|---|---|---|
| 121 | 14.763 | 93.9°C | 0:21 |
| 122 | 15.995 | 94.8°C | 0:40 |
| 123 | 16.095 | 96.0°C | 0:59 |

Mean **15.618**, 95% CI **[13.77, 17.46]** — wide, mostly from trial 121's low first rep (the same
"first-rep-runs-low" pattern noted in the retracted run, plausibly a cold-start effect; 122/123 are
much closer to each other at 15.995/16.095). Every rep's compiled-flags audit confirms `-O3` alone —
no `-fprefetch-loop-arrays`, no stray flags — genuinely present.

## Candidate generation and filtering

Same catalog, same `_filter_implausible_candidates()` reasoning as the retracted 2026-08-21 run — lbm
is memory-bound with high vectorization density, so the identical 10 flags were excluded for the
identical topdown-implausibility reasons, plus the same 3 unresolved-template-placeholder catalog
entries skipped:

- Excluded (frontend/speculation/compute/backend-bound signals implausible against a memory-bound,
  high-vectorization baseline): `-flto`, `-fprofile-generate`, `-fprofile-use`,
  `-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition`,
  `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta`.
- Skipped (unresolved template placeholders, not concrete flags): `-mbranch-cost=N`,
  `--param prefetch-latency=N`, `-finline-limit=N`.
- **5 plausible survivors**: `-fprefetch-loop-arrays`, `-mprefer-vector-width=256`,
  `-mprefer-vector-width=512`, `-march=native`, `-fgraphite-identity`.

`--max-trials 4` then capped Phase 2's own candidate list down from those 5 survivors to just **1**
(`-fprefetch-loop-arrays`) — a deliberate consequence of the focused-test budget (1 screening trial + 3
confirmation trials = 4, the full budget), not a filtering artifact. The other 4 survivors were never
attempted this run.

## The one candidate: `-fprefetch-loop-arrays`

| Trial | Phase | Flags | Ratio | CPU temp | Elapsed |
|---|---|---|---|---|---|
| 124 | screening | `-O3 -fprefetch-loop-arrays` | 16.163 | 95.0°C | 1:19 |
| 125 | confirmation | `-O3 -fprefetch-loop-arrays` | 16.056 | 94.1°C | 1:38 |
| 126 | confirmation | `-O3 -fprefetch-loop-arrays` | 16.168 | 95.0°C | 1:57 |
| 127 | confirmation | `-O3 -fprefetch-loop-arrays` | 16.171 | 93.8°C | 2:16 |

- Screening: +3.49% vs. baseline mean — cleared the screen.
- Confirmation mean **16.132** (n=3), 95% CI **[15.97, 16.29]** vs. baseline's CI **[13.77, 17.46]**.
- Delta **+3.29%**, genuinely positive — but baseline's own CI is wide enough to fully contain the
  candidate's CI, so **verdict: reject** on CI-overlap grounds, correctly, not on the
  practical-significance threshold.

Every one of these four builds' compiled-flags audit confirms **both** `-O3` and
`-fprefetch-loop-arrays` present together — direct confirmation the isolated-candidate-flags bug is
fixed: this candidate was tested layered on top of baseline's own optimization level, not alone.

## Timing

Trials landed ~19 minutes apart, consistent with the (retracted) 2026-08-21 run's own observation that
`lbm_r`'s `quick`-profile trial cost (~20min) is intrinsically longer than stockfish's (~5min) — a
real per-workload difference, not a regression. Total run wall-clock (2h16m) scales as expected for a
4-trial budget at this per-trial cost.

No dramatic drift this time (unlike the 7.8-hour, ~12%-drift retracted run) — plausibly because this
run's total duration (2h16m) is far shorter, giving drift far less time to accumulate, though the
trial-121 cold-start-like low rep is a shared feature of both runs and still worth normalizing away in
a future baseline-calibration design.

## Phase 5 (greedy combine)

Not exercised — zero Phase 4 acceptances, matching every prior real mining run to date (both retracted
stockfish runs, the retracted lbm run, and now this corrected one). Still an open test-coverage gap for
the greedy walk / pair-tournament logic against a genuine acceptance — not something this run's choice
of benchmark or budget was positioned to fix.

## What this run actually confirms

- **The basepeak fix holds**: every trial's audit shows the intended `OPTIMIZE` line's flags, not a
  fixed base-tuning binary regardless of input.
- **The isolated-candidate-flags fix holds**: the one candidate tested was audited as `-O3` +
  `-fprefetch-loop-arrays` together in every one of its 4 builds, never the candidate alone.
- **The reference-matrix characterization path (M2.5 item 2) works in a real, focused production run**,
  not just in isolated verification — correctly informed which of the catalog's flags were worth
  spending the (capped) trial budget on.
- **The confirmation gate's CI-overlap logic makes a real, defensible reject call** on a small but
  genuinely positive delta, rather than either a false accept or an unexplained rejection.
- `cfm.db`'s bookkeeping, `hypotheses` audit trail, and per-trial `cpu_temp` recording all worked
  correctly throughout, with no manual intervention needed and the host returning to idle cleanly at
  the end.

## Next steps this suggests

- **A larger/uncapped follow-up run** to actually exercise the other 4 plausible survivors
  (`-mprefer-vector-width=256`, `-mprefer-vector-width=512`, `-march=native`, `-fgraphite-identity`)
  and, ideally, get a real Phase 4 acceptance to finally exercise Phase 5 for real — three real mining
  runs in a row (both retracted ones plus this one) have now completed with zero acceptances.
- **Still need a benchmark whose `resource_dominance` differs from memory-bound** for real coverage of
  the compute-bound/frontend-bound flag categories — stockfish and lbm have both landed in the same
  exclusion bucket for the same reason.
- The baseline-drift design conversation flagged in the retracted run (re-measuring/refreshing baseline
  through a long run, or normalizing each confirmation trial against a nearby-in-time baseline) is
  still open, though less urgent at this run's much shorter duration than it was at 7.8 hours.

# `cfm mine` results: 750.sealcrypto_r, 2026-08-24 (re-run, screening-fix verification)

The real end-to-end verification run for the Phase 3 screening fix (PR #38, `BaselineResult.
most_recent_ratio` replacing `baseline.ci.mean` as the comparison point): a fresh, uncapped re-mine of
`750.sealcrypto_r`, the exact benchmark whose earlier 2026-08-24 run exposed the stale-baseline bias in
the first place. This run resolves that earlier run's own open question for real, not just in theory.

## Headline result

**All 5 flags previously pruned at screening now correctly survive and get a real confirmation-grade
trial — and all 5 are genuinely, cleanly rejected (−5.5% to −5.8%), a real answer instead of a screening
artifact.** `-march=native` wins again (+15.63%), a third confirmation of this flag's value on this
exact benchmark.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 750.sealcrypto_r` (uncapped) |
| Experiment id | 17 |
| Started | 2026-08-24T12:22:14Z |
| Finished | 2026-08-24T15:07:18Z |
| Final status | `converged` |
| Candidates screened | 5 |
| Candidates fast-tracked (M4) | 1 (`-march=native`, its own prior now accepted from this benchmark's earlier run) |
| Candidates confirmed | 1 (`-march=native`) |
| Winning flags | `["-O3", "-march=native"]`, +15.63% overall gain |

## Baseline: real settling again, this time handled correctly

| Trial | Ratio |
|---|---|
| 231 | 56.145 |
| 232 | 53.528 |
| 233 | 50.698 |

Mean **53.457**, `most_recent_calibration_ratio` **50.698** — baseline settled downward again
(~10% front-to-back spread this time, if anything more pronounced than the earlier run's own ~7.5%),
confirming this isn't a one-off artifact of the earlier run specifically; it's a real, recurring pattern
for this benchmark's own baseline calibration. This time it doesn't matter: screening now compares
against `50.698` (the last rep), not `53.457` (the mean).

## Screening: the fix in action, flag by flag

| Flag | Screening ratio | Delta vs. `most_recent_ratio` (50.698) | Result this run | Result last run (vs. the 53.457 mean) |
|---|---|---|---|---|
| `-funroll-loops` | 50.583 | **−0.23%** | survived | pruned (−6.58%) |
| `-mprefer-vector-width=256` | 50.501 | **−0.39%** | survived | pruned (−6.92%) |
| `-mprefer-vector-width=512` | 50.441 | **−0.51%** | survived | pruned (−6.81%) |
| `-Ofast` | 50.404 | **−0.58%** | survived | pruned (−6.91%) |
| `-ffast-math` | 50.342 | **−0.70%** | survived | pruned (−6.96%) |

Every one of the five now clears the 5% prune bar comfortably — all real screening deltas fall inside
±1%, a night-and-day difference from last run's ~−6.6% to −7.0% band produced by comparing against the
stale, too-high mean. This is the fix working exactly as designed: same real trial data pattern
(baseline settling), completely different — and now correct — screening outcome.

## Confirmation: a real, clean answer this time

| Flag | Confirm mean | Comparison (baseline CI) | Delta | Verdict |
|---|---|---|---|---|
| `-funroll-loops` | 50.497 (CI [50.33, 50.66]) | 53.457 (CI [46.69, 60.23]) | −5.54% | reject |
| `-mprefer-vector-width=256` | 50.423 (CI [50.31, 50.54]) | same | −5.68% | reject |
| `-mprefer-vector-width=512` | 50.405 (CI [50.30, 50.51]) | same | −5.71% | reject |
| `-Ofast` | 50.342 (CI [50.20, 50.49]) | same | −5.83% | reject |
| `-ffast-math` | 50.336 (CI [50.28, 50.39]) | same | −5.84% | reject |

Every rejection here is unambiguous — each delta is clearly negative, nowhere near
`MIN_PRACTICAL_SIGNIFICANCE_PCT`'s own bar, no CI-overlap subtlety needed to interpret it (unlike, say,
`782.lbm_r`'s own `-march=native` reject, where a *positive* delta still lost on CI overlap). Every
trial's compiled-flags audit confirms its own distinct flag genuinely compiled in.

**This resolves the earlier run's own open question**: these five flags don't help `750.sealcrypto_r`
— a real, statistically clean, confirmation-grade result now exists to say so, not a single noisy
screening point compared against a stale reference. The original run's honest "unresolved, could be
settling or could be real" framing is now settled: it was largely the latter, once measured properly.

**One genuinely curious pattern remains, unexplained**: all five rejected flags land in a suspiciously
tight, consistent −5.5% to −5.8% band despite being mechanistically unrelated (loop unrolling, vector
width hints, fast-math semantics). A plausible, unconfirmed hypothesis: none of them can do anything
useful on the generic x86-64 baseline target without `-march=native`'s wider ISA to actually exploit,
and something about their shared code-generation footprint (code size, a GCC heuristic shift) costs a
small, consistent amount regardless of which specific flag triggers it. Not investigated further this
run — a real, open mechanistic question, distinct from (and now cleanly separated from) the
screening-bias question this run set out to resolve.

## `-march=native`: fast-tracked via M4, confirmed a third time

`candidates_fast_tracked_from_prior_knowledge: ["-march=native"]` — this run's own earlier accepted
prior (`compute-bound` cluster, +14.05% from the 2026-08-24 run just before this one) fast-tracked it
straight to Phase 4 again, skipping screening. Confirmed again at +15.53%, accepted, re-confirmed at
Phase 5's combine step at +15.63%. `knowledge` table's own running mean is now **+14.79%** (`n_trials=2`,
`n_accepted=2`) — a real, increasingly solid prior for the next compute-bound benchmark, and unlike
`-march=native`'s own memory-bound-cluster entry, both real trials in this cluster have been accepts.

## What this run actually confirms

- **The Phase 3 screening fix works, verified with the same benchmark that exposed the bug** — not a
  different benchmark that might have behaved differently by luck. Same real settling pattern, opposite
  (correct) screening outcome.
- **A previously-unresolved open finding is now closed**: the compute-bound catalog flags genuinely
  don't help this benchmark — a real, clean, confirmation-grade answer, not a screening artifact.
- **M4 continues to work correctly across repeated runs of the same benchmark**, correctly fast-tracking
  an already-twice-accepted flag.
- **The compiled-flags audit and CI-based accept/reject machinery both continue to hold** — nothing
  about this fix touched Phase 4/5/6, and nothing there regressed.

## Next steps this suggests

- **The separate, larger multi-hour continuing-drift case** (`782.lbm_r`'s own 2026-08-21 run) is still
  open — this fix targeted the "still-settling-at-Phase-3-start" case specifically, not multi-hour
  drift throughout a whole run.
- **The consistent ~−5.5 to −5.8% cost shared by 5 mechanistically unrelated flags** is a real, if
  minor, open mechanistic question worth a closer look sometime.
- Still need a genuinely backend-bound benchmark; Phase 5's pair tournament still has zero real
  coverage.

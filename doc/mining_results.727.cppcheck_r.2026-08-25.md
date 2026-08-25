# `cfm mine` results: 727.cppcheck_r, 2026-08-25 (re-run, baseline warm-up fix verification)

The real end-to-end verification run for PR #41's baseline warm-up fix (`BASELINE_WARMUP_REPETITIONS`):
a fresh, uncapped re-mine of `727.cppcheck_r`, the exact benchmark whose 2026-08-24 run exposed the
too-wide confirmation-stage CI in the first place. This run resolves that earlier run's own predicted
outcome for real, and it landed exactly as hoped.

## Headline result

**`-O3 -fprofile-use` (real two-pass PGO) is now correctly accepted — +10.79% overall, this benchmark's
first genuine accepted win.** The same real PGO effect that was incorrectly rejected last run, thanks to
an inflated baseline CI, is now recognized cleanly and unambiguously. `-flto` is still rejected — but
now for a legitimate, honest reason (a real, narrow CI overlap against a properly-settled baseline), not
an artifact of measuring baseline too early.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 727.cppcheck_r` (uncapped) |
| Experiment id | 20 |
| Started | 2026-08-25T04:46:02Z |
| Finished | 2026-08-25T08:42:50Z |
| Wall-clock | 3h56m48s (vs. the original run's 3h17m43s — the 2 extra warm-up reps account for most of the difference) |
| Final status | `converged` |
| Candidates screened | 4 |
| Candidates fast-tracked (M4) | 1 (`-flto`) |
| Candidates confirmed | 0 (ordinary Phase 4) — PGO accepted at Phase 6 |
| Winning flags | `["-O3", "-fprofile-use"]`, **+10.79% overall gain** |

## Baseline: the warm-up fix in action

| Trial | Phase | Ratio |
|---|---|---|
| 292 | **warm-up** (excluded from CI) | 44.865 |
| 293 | **warm-up** (excluded from CI) | 44.291 |
| 294 | calibration | 43.000 |
| 295 | calibration | 42.134 |
| 296 | calibration | 42.006 |

The settling pattern is still visible across all 5 reps (44.87 → 44.29 → 43.00 → 42.13 → 42.01 — a real,
if this time slightly longer, decline) — the warm-up fix doesn't eliminate the underlying phenomenon,
it just keeps it out of the statistic that matters. Mean of the 3 real calibration reps: **42.380**
(`baseline_ratio_mean`), CI **`[41.04, 43.72]`** — meaningfully tighter than the original run's own
**`[39.94, 46.76]`**, and centered much closer to the eventual steady-state level (the later screening
trials settle around ~42.0-42.1, matching the calibration reps closely this time, unlike the original
run's own mean of 43.35 sitting well above where the benchmark actually spent most of its time).

Both warm-up reps carry their own explanatory `hypotheses` row
(`"baseline warm-up rep -- deliberately excluded from the calibration ratios/CI below..."`), confirming
the mechanism worked exactly as designed.

## The verdict flip, confirmed with real numbers

| Flag | Confirm mean | Confirm's own CI | Baseline's CI | Verdict this run | Verdict last run |
|---|---|---|---|---|---|
| **`-fprofile-use` (PGO)** | **46.951** | **`[46.09, 47.81]`** | `[41.04, 43.72]` | **accept (+10.79%)** | reject (+7.42%) |
| `-flto` | 44.159 | `[43.51, 44.81]` | `[41.04, 43.72]` | reject (+4.20%) | reject (+1.19%) |

PGO's own CI now sits entirely, cleanly above baseline's upper bound — an unambiguous accept, exactly
the flip predicted from the original run's own numbers (its confirm CI was already a near-zero-variance,
highly precise measurement; only the comparison baseline was wrong).

`-flto`'s own case is the more interesting one: its measured delta actually **increased** slightly
(+4.20% vs. the original run's +1.19%), and its own CI (`[43.51, 44.81]`) now overlaps baseline's upper
bound (43.72) by a narrow margin — still a reject, but a **real, honest** one this time: baseline's own
CI is properly calibrated now, and `-flto`'s own effect genuinely sits right at the edge of what this
benchmark's run-to-run noise can distinguish. This is arguably the more satisfying outcome of the two —
the fix didn't just flip every verdict to "accept," it let the pipeline report the truth in both
directions: a real, large effect (PGO) gets recognized, and a real, marginal effect (`-flto`) stays
correctly unresolved rather than being either falsely accepted or falsely rejected for the wrong reason.

Both trials' compiled-flags audits confirm genuine builds (`-fprofile-use` literally present;
`-flto` "not independently checkable" — the known, already-understood GCC-LTO-rewrite limitation, not a
new issue).

## Phase 6 chaining: microarch layered on top of the PGO win, correctly

With PGO accepted, the microarch multiplier ran its own trials **on top of** `-fprofile-use`, not plain
`-O3` — `["-O3", "-fprofile-use", "-march=znver5"]` and `["-O3", "-fprofile-use", "-mtune=znver5"]`,
both correctly rejected as noise-level (−0.05%, +0.42%) against the new, higher PGO-including baseline.
This is real confirmation that Phase 6's multiplier-chaining design (`run_microarch_multiplier()`
accepting `run_pgo_multiplier()`'s own `MultiplierResult` via its duck-typed `combination` argument)
works correctly when PGO actually wins, not just when it's skipped or rejected (the only cases seen in
prior runs).

## M4: cross-run knowledge accumulating correctly

```
info: known prior for '-fprofile-use' in cluster 'frontend-bound' -- accepted before (mean +19.29%, n=2, last seen on '727.cppcheck_r')
info: known prior for '-flto' in cluster 'frontend-bound' -- accepted before (mean +4.02%, n=2, last seen on '727.cppcheck_r')
```

`-flto` was fast-tracked again, its own prior now reflecting both this benchmark's two real runs
(`n=2`). Knowledge table after this run, `frontend-bound` cluster:

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-fprofile-use` | 3 | 2 | +16.46% |
| `-flto` | 3 | 1 | +4.08% |
| `-freorder-blocks-and-partition` / `-freorder-functions` / `-fno-semantic-interposition` | 3 each | 0 | −0.95% to −1.29% |
| `-march=native` / `-march=znver5` / `-mtune=znver5` | 1-2 each | 0 | −1.07% to −2.20% |

`-fprofile-use`'s own running mean is now a real, trustworthy +16.46% across 3 total trials (2 accepts)
— a genuinely strong, increasingly well-evidenced prior for the next frontend-bound benchmark mined.

## Package power: still no clean signal either way

Power stayed in a narrow ~31-33W band throughout this ~4-hour run, with a slight *rise* across the
baseline reps themselves (31.08 → 32.04 → 31.09 → 32.02 → 33.02) but no consistent trend afterward.
`Pearson r(package_power_w, elapsed_min) = -0.590` this run — the opposite sign from the previous
`727.cppcheck_r` run's own `+0.272`. Two real data points now, pointing in different directions: not
evidence for or against the STAPM hypothesis yet, just confirmation that more runs are needed before
drawing any conclusion — exactly what was already flagged as the open next step.

## What this run actually confirms

- **The baseline warm-up fix (PR #41) works exactly as designed, verified with the same benchmark that
  motivated it** — not a different one that might have behaved differently by luck. A real,
  near-zero-variance PGO win that was incorrectly rejected is now correctly accepted, and a genuinely
  marginal `-flto` effect is still correctly (and now honestly) rejected.
- **Phase 6's multiplier chaining works correctly when PGO actually wins** — microarch layered on top of
  the real PGO-accepted flagset, not just on plain `-O3`, for the first time.
- **M4 continues to accumulate real, increasingly trustworthy cross-run priors** — `-fprofile-use`'s own
  mean is now backed by 3 real trials across repeated mining of the same benchmark.
- **The package-power investigation still needs more data** — two real runs on the same benchmark
  produced opposite-signed correlations in a narrow noise band.

## Next steps this suggests

- **A different benchmark to further stress-test the warm-up fix** — one real success on the benchmark
  that motivated it is a good sign, but a second, independent benchmark would be stronger evidence the
  fix generalizes.
- **Still need a genuinely backend-bound benchmark** (none exists in the reference-matrix corpus,
  confirmed 2026-08-24) and more package-power data before the STAPM hypothesis can be confirmed or
  ruled out.
- Phase 5's pair tournament still has zero real coverage.

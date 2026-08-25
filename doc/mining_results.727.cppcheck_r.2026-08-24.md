# `cfm mine` results: 727.cppcheck_r, 2026-08-24

The first real mining run against `727.cppcheck_r` (a C/C++ static analyzer), picked deliberately after
checking the **entire real SPEC CPU2026 suite** (49 benchmarks) against the external reference-matrix
corpus specifically looking for a genuinely backend-bound benchmark — none was found anywhere in the
corpus (see "Why this benchmark" below); `727.cppcheck_r` was instead the cleanest, highest-confidence
**frontend-bound** signal in the whole corpus (71.0%, high confidence), making it the natural next
benchmark to test M4's cross-benchmark transfer in the `frontend-bound` cluster for the first time, and
to collect package-power data across a real, multi-hour mining sequence.

## Headline result: not what it looks like at face value

**Officially: `-O3` alone remains peak, nothing accepted, 0.0% gain.** But this is very likely a false
reading, not a real "nothing helps" result — baseline's own calibration was unusually unstable this
run, and its own resulting confidence interval is wide enough to have plausibly swallowed two genuinely
real wins: `-flto` and, more strikingly, real two-pass PGO (`-fprofile-use`), whose own confirmation
reps were almost perfectly consistent (a real, precisely-measured effect) yet still landed just inside
baseline's own inflated CI. See "The real finding" below — this is the headline of this run, not the
"0.0% gain" the summary JSON reports at face value.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 727.cppcheck_r` (uncapped) |
| Experiment id | 19 |
| Started | 2026-08-24T23:02:19Z |
| Finished | 2026-08-25T02:20:02Z |
| Wall-clock | 3h17m43s |
| Final status | `converged` |
| Candidates screened | 4 |
| Candidates fast-tracked (M4) | 1 (`-flto`) |
| Candidates confirmed | 0 (officially — see below) |
| Winning flags (official) | `["-O3"]`, 0.0% gain |

## Why this benchmark

**No backend-bound benchmark exists anywhere in the reference-matrix corpus.** Checked all 49 real,
named SPEC CPU2026 benchmarks (every `*_r`/`*_s` pair except the synthetic `specrand`) against
`cfm/reference_matrix.py`'s own `fetch_shape()` — every single one characterizes as memory-bound,
frontend-bound, or compute-bound as its primary shape; not one shows backend-bound as either primary
*or* alternative. This is itself a real, worth-recording finding, not a gap in the checking: `backend-
bound` may simply not occur as a dominant characterization for this benchmark suite on this reference
host, at least via `wspy-archetype`'s own topdown classification.

Given that, `727.cppcheck_r` was picked for the next-best reason: the cleanest, highest-confidence
`frontend-bound` signal in the entire corpus (71.0%, high confidence — stronger than `735.gem5_r`'s
60.3%, the next-best frontend-bound candidate found). Mechanistically sensible too — a C/C++ static
analyzer parsing and traversing real-world codebases is a textbook frontend-bound workload (complex,
data-dependent branching, poor branch prediction, icache pressure from a large, irregular codebase).
It's also the first real benchmark to test M4's cross-benchmark transfer in the `frontend-bound`
cluster — `714.cpython_r`'s real `-flto`/PGO accepts had never been read back by a second benchmark
until this run.

## Baseline: the same settling pattern, with bigger consequences this time

| Trial | Ratio |
|---|---|
| 261 | 44.678 |
| 262 | 43.435 |
| 263 | 41.934 |

Mean **43.349**, `most_recent_calibration_ratio` **41.934** — the same real, recurring settling pattern
documented in every prior run (a ~6.6% front-to-back spread here). `resource_dominance=frontend-bound`
(71.0%), `vectorization_density=low`, `allocation_pressure=moderate`, from the reference-matrix corpus.

**This time the spread produced a genuinely wide confirmation-stage CI**: `[39.94, 46.76]`, a ±7.8%
band around the mean, computed from just 3 reps via Student's-t (small-n CIs are naturally wide, and
one elevated first rep pulls the mean up and widens the interval further). Phase 3 screening already
correctly discounts this (2026-08-24's `most_recent_ratio` fix, PR #38) — but Phase 4/5/6's own
accept/reject comparison still uses this same wide CI, unchanged.

## M4: fast-tracked `-flto`, correctly

```
info: known prior for '-fprofile-use' in cluster 'frontend-bound' -- accepted before (mean +31.16%, n=1, last seen on '714.cpython_r')
info: known prior for '-flto' in cluster 'frontend-bound' -- accepted before (mean +6.85%, n=1, last seen on '714.cpython_r')
info: known prior for '-freorder-blocks-and-partition' in cluster 'frontend-bound' -- rejected before (mean +1.21%, n=1, last seen on '714.cpython_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'frontend-bound' -- rejected before (mean +0.74%, n=1, last seen on '714.cpython_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'frontend-bound' -- rejected before (mean +0.58%, n=1, last seen on '714.cpython_r')
info: known prior for '-fno-semantic-interposition' in cluster 'frontend-bound' -- rejected before (mean +0.29%, n=1, last seen on '714.cpython_r')
```

`-flto` (the only accepted prior among the ordinary per-flag catalog) was correctly fast-tracked
straight to Phase 4, skipping screening — `candidates_fast_tracked_from_prior_knowledge: ["-flto"]`
confirms it, and there's no preceding screening trial for it in the trial table, same mechanical proof
as the earlier `782.lbm_r` M4 verification. `-fprofile-use` (PGO, the *stronger* prior at +31.16%)
correctly never enters this fast-track mechanism at all — it's excluded from the ordinary per-flag
candidate list entirely (`category == "pgo"`) and always runs via the dedicated Phase 6
`run_pgo_multiplier()` path regardless of prior-knowledge status, which it did here.

## The real finding: baseline's own CI likely swallowed two genuine wins

| Flag | Confirm mean | Confirm's own CI | vs. baseline's CI `[39.94, 46.76]` | Official verdict | Delta vs. `most_recent_ratio` (41.934) instead |
|---|---|---|---|---|---|
| `-flto` | 43.863 | `[43.36, 44.36]` (tight) | entirely inside | reject (+1.19%) | **+4.60%** |
| `-fprofile-use` (PGO) | **46.567** | **`[46.55, 46.59]`** (near-zero variance) | just barely inside | **reject (+7.42%)** | **+11.05%** |

Both trials' compiled-flags audits confirm they genuinely built with their intended flags — this is a
real measurement, not a build artifact. **PGO's own case is the most striking**: three confirmation
reps landing within 0.09% of each other is about as precise and trustworthy a measurement as this
project's pipeline produces, yet it was still rejected — purely because baseline's own CI happened to
be wide enough (driven by one elevated early rep) to just barely still contain it.

For comparison, the four *genuinely* flat candidates (`-freorder-blocks-and-partition`,
`-freorder-functions`, `-fno-semantic-interposition`, `-march=native`) all confirmed within 0.1-0.2% of
`most_recent_ratio` — a real, clean "no effect" signal, cleanly distinguishable from `-flto`/PGO's own
real, large, precisely-measured deltas once compared against the same, more representative reference
point. The microarch multiplier's own two candidates (`-march=znver5`/`-mtune=znver5`) landed at +0.23%
and +0.74% against that same reference — genuinely marginal, unlike PGO's own +11%.

**This is not the same bug PR #38 already fixed** (that was specifically Phase 3 screening comparing
against a stale mean with no CI at all) — this is the *statistically rigorous* Phase 4/5/6 comparison,
which already uses a proper CI-overlap test, still getting misled because the CI itself is built from
an unstable, still-settling 3-rep baseline. It's the exact "separate, larger design question" flagged as
deliberately out of scope in that fix's own write-up: does every phase need a more robust baseline
reference, not just Phase 3's own point estimate.

## Package power: a weaker ramp signal than hoped

| Trial (early) | elapsed_min | power_w |
|---|---|---|
| 261 | 5.5 | 29.09 |
| 262 | 11.0 | 31.08 |
| 263 | 16.8 | 31.03 |

A real jump in the first ~11 minutes (29.1W → 31.1W, ~7%), then essentially flat around 30-31W for the
remaining ~3 hours of the run. `Pearson r(package_power_w, elapsed_min) = +0.272` across all 31
trials — a real but much weaker correlation than `ratio`'s own `+0.259` (comparable in this run,
actually, unlike the sharper separations seen in some other experiments) or `cpu_temp_c`'s `+0.080`.
This is the first real multi-hour power-sampling data collected (PR #40 landed the same day as the
previous mining run, before this one), and it doesn't cleanly confirm the STAPM hypothesis the way
hoped — a real, if modest, early ramp, then a stable plateau, rather than a continued climb tracking
the full run's duration the way `ratio` itself often does in longer runs. Worth collecting from more
runs before drawing a firm conclusion either way.

## What this run actually confirms

- **M4 continues to work correctly on a new benchmark and a new cluster** — `-flto` fast-tracked
  correctly, `-fprofile-use` correctly routed through Phase 6 instead.
- **No backend-bound benchmark exists in the reference-matrix corpus** — a real, now-confirmed gap in
  what's characterizable on this reference host's own corpus, not a search that just hasn't found one
  yet.
- **Phase 4/5/6's own CI-overlap test is vulnerable to an unstable baseline too**, not just Phase 3's
  cheap screening comparison — real, concrete evidence with two plausible real wins on the line, not a
  marginal or noise-level case.
- **Package-power sampling works across a real, multi-hour run** — the ramp signal is weaker/less clean
  than hoped this time, but the mechanism itself functioned correctly throughout.

## Next steps this suggests

- **Extend the Phase 3 screening fix's own reasoning to Phase 4/5/6**: baseline's own CI needs to be
  more robust to a still-settling first rep, the same problem `most_recent_ratio` solved for screening's
  point comparison, now shown to also affect the statistically rigorous confirmation stage. This is the
  natural next real fix, not just a documented curiosity.
- **A real re-verification of `727.cppcheck_r`'s own PGO/`-flto` result** once that fix exists, to see
  whether the verdict actually flips — this run's own numbers make a strong prior case that it should.
- **More package-power data across more runs** before concluding anything firm about the STAPM
  hypothesis — this run's own signal was real but weaker than the ratio-drift pattern itself.

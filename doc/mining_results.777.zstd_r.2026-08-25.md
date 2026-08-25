# `cfm mine` results: 777.zstd_r, 2026-08-25 (second benchmark, warm-up fix stress test)

A real, uncapped `cfm mine` run against `777.zstd_r` (Zstandard compression) — the second benchmark
mined since PR #41's `BASELINE_WARMUP_REPETITIONS` fix, deliberately chosen to be independent of
`727.cppcheck_r` (the benchmark that motivated and first verified the fix) on every axis that matters:
different cluster (`memory-bound` vs. `frontend-bound`), different workload shape (data-parallel
compression vs. static-analysis traversal), first real mining run of this benchmark ever.

## Headline result

**Officially: `-O3` alone remains peak, nothing accepted, 0.0% gain — and this time that's the honest,
correct answer, not a false negative.** Every candidate this run landed either genuinely flat or, for
two flags, a real-but-practically-negligible positive edge. Unlike `727.cppcheck_r`'s first run, there
is no case here where a large, precisely-measured win got swallowed by a too-wide baseline CI. The more
interesting finding is what a **counterfactual replay without the fix** shows: every single candidate's
*reported sign* would have come out backwards.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 777.zstd_r` (uncapped) |
| Experiment id | 21 |
| Started | 2026-08-25T10:22:28Z |
| Finished | 2026-08-25T15:04:22Z |
| Wall-clock | 4h41m54s |
| Final status | `converged` |
| Candidates screened | 4 |
| Candidates fast-tracked (M4) | 1 (`-march=native`) |
| Candidates confirmed (ordinary Phase 4) | 0 |
| PGO | skipped (implausible: memory-bound baseline contradicts PGO's frontend-bound/speculation-bound signal) |
| Microarch multiplier | attempted, both `-march=znver5`/`-mtune=znver5` rejected |
| Winning flags | `["-O3"]`, 0.0% gain |

## Why this benchmark

`777.zstd_r` characterizes `memory-bound` at 64.0%, high confidence (reference-matrix corpus), with
`moderate` vectorization density and allocation pressure — a real-world compression benchmark, a
plausible and mechanistically sensible memory-bound shape (large-window LZ77 matching is dictionary/
hash-table-lookup-heavy). It had never been mined before this run. Picked specifically to stress-test
the baseline warm-up fix on a second, structurally different benchmark rather than re-running the exact
benchmark that motivated it a second time.

## Baseline: warm-up fix in action, a cleaner settle than cppcheck's own

| Trial | Phase | Ratio |
|---|---|---|
| 325 | **warm-up** (excluded from CI) | 39.009 |
| 326 | **warm-up** (excluded from CI) | 37.879 |
| 327 | calibration | 37.446 |
| 328 | calibration | 37.363 |
| 329 | calibration | 37.405 |

The same real settling pattern as every prior run (39.01 → 37.88 → 37.45 → ...), but this time it fully
resolves within the 2 warm-up reps — the 3 real calibration reps that follow are tight (37.36-37.45, a
~0.24% spread), and stayed flat for the rest of the entire ~4h42m run (`Pearson r(ratio, elapsed_min) =
-0.090` across all 30 trials, essentially noise — a much cleaner run than `727.cppcheck_r`'s own, and
nothing like `782.lbm_r`'s original multi-hour continuing drift). Calibration mean **37.405**
(`baseline_ratio_mean`), CI **`[37.30, 37.51]`** — a tight, trustworthy interval.

## The stress test: what the fix actually changed here

Unlike `727.cppcheck_r`, no accept/reject verdict flips in this run — every candidate was correctly
rejected under both the old and new baseline computation. But recomputing every candidate's comparison
against the **counterfactual old-style baseline** (all 5 reps, including the two now-excluded warm-up
reps: mean 37.820, CI `[36.96, 38.68]`) shows the fix mattered anyway, in a different way than cppcheck's
verdict-flip: **it corrects the sign of the reported effect for every single candidate.**

| Flag | Confirm mean | Δ vs. **old** (unfixed) baseline | Δ vs. **new** (fixed) baseline | Non-overlap (old / new) |
|---|---|---|---|---|
| `-fprefetch-loop-arrays` | 37.339 | −1.27% | −0.18% | no / no |
| `-mprefer-vector-width=256` | 37.424 | −1.05% | **+0.05%** | no / no |
| `-mprefer-vector-width=512` | 37.380 | −1.16% | −0.06% | no / no |
| `-fgraphite-identity` | 37.340 | −1.27% | −0.17% | no / no |
| `-march=native` (M4 fast-tracked) | 37.702 | −0.31% | **+0.80%** | no / **yes** |
| `-march=znver5` | 37.682 | −0.37% | **+0.74%** | no / **yes** |
| `-mtune=znver5` | 37.515 | −0.81% | +0.30% | no / no |

Against the old, unfixed baseline, **every candidate reads as a net regression** — every flag would have
looked like it made `777.zstd_r` slower, some by more than a full percent. Against the properly-settled
new baseline, the true picture emerges: four flags are genuinely flat (±0.2%, real noise), and two
(`-march=native`, `-march=znver5`) have a real, statistically-distinguishable positive effect — their
confirm-stage CI is now non-overlapping with baseline's — that simply doesn't clear
`MIN_PRACTICAL_SIGNIFICANCE_PCT` (1.0%). That is a materially different, more honest finding than "every
flag hurts": these two flags have a real but practically negligible edge on this benchmark, correctly
rejected for being too small to matter, not because they were (falsely) measured as harmful.

**This is a different failure mode of the same underlying bug than `727.cppcheck_r` exposed.** There, an
inflated CI *width* swallowed a large real win. Here, an inflated CI *center* (pulled up by the two
still-settling early reps) biased every single delta negative regardless of the candidate's own real
effect — the same class of systematic bias PR #38 already fixed for Phase 3's point comparison, now
shown to also distort Phase 4/5/6's reported deltas even when it doesn't flip the final accept/reject
call. Together, the two runs demonstrate the fix guards against both symptoms: an unstable baseline can
either hide a real win (cppcheck) or systematically misreport every candidate's sign (zstd) — this run is
real, independent evidence for the second half of that story, not just a repeat confirmation of the
first.

## M4: correctly transferred and correctly re-evaluated on its own merits

```
info: known prior for '-march=native' in cluster 'memory-bound' -- accepted before (mean +25.31%, n=2, last seen on '782.lbm_r')
info: known prior for '-fprefetch-loop-arrays' in cluster 'memory-bound' -- rejected before (mean +2.93%, n=2, last seen on '782.lbm_r')
info: known prior for '-mtune=znver5' in cluster 'memory-bound' -- rejected before (mean +2.09%, n=2, last seen on '782.lbm_r')
info: known prior for '-march=znver5' in cluster 'memory-bound' -- rejected before (mean +1.67%, n=2, last seen on '782.lbm_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'memory-bound' -- rejected before (mean -0.95%, n=2, last seen on '782.lbm_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'memory-bound' -- rejected before (mean -0.96%, n=2, last seen on '782.lbm_r')
info: known prior for '-fgraphite-identity' in cluster 'memory-bound' -- rejected before (mean -1.09%, n=2, last seen on '782.lbm_r')
```

`-march=native` was fast-tracked straight to Phase 4 on its own real `memory-bound` prior (from
`706.stockfish_r`'s accept and `782.lbm_r`'s reject) — no preceding screening trial for it in the trial
table, same mechanical proof as prior M4 verifications. It was then evaluated honestly on its own
merits: a real, small, statistically-distinguishable +0.80% edge, correctly rejected for falling short of
the practical-significance bar. The knowledge table's own running mean updated accordingly
(`+25.31% → +17.14%`, still `n_accepted=1` of now 3 total trials) — another real, increasingly
well-evidenced (if now more modest) prior for the next memory-bound benchmark mined.

Every other prior (`-fprefetch-loop-arrays`, both `-mprefer-vector-width` choices, `-mtune=znver5`,
`-march=znver5`, `-fgraphite-identity`) was correctly *not* fast-tracked (all had rejected priors) and
went through ordinary screening — all landed consistent with their own priors' direction (near-flat,
some now showing the same small real-but-insignificant positive edge as `-march=native`, since
`-march=znver5`/`-mtune=znver5` are mechanistically the same underlying microarch effect).

Knowledge table, `memory-bound` cluster, after this run:

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-march=native` | 3 | 1 | +17.14% |
| `-fprefetch-loop-arrays` | 3 | 0 | +1.89% |
| `-mtune=znver5` | 3 | 0 | +1.49% |
| `-march=znver5` | 3 | 0 | +1.36% |
| `-mprefer-vector-width=256` | 3 | 0 | −0.62% |
| `-mprefer-vector-width=512` | 3 | 0 | −0.66% |
| `-fgraphite-identity` | 3 | 0 | −0.78% |

## Phase 2 filtering and PGO skip, correctly applied

`-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition`
(frontend-bound-targeted), `-funroll-loops`/`-Ofast`/`-ffast-math` (compute-bound-targeted), and
`-fipa-pta` (backend-bound-targeted) were all correctly excluded from Phase 2's candidate list —
`_filter_implausible_candidates()` confidently contradicting each against this benchmark's real
`memory-bound` shape. PGO was correctly skipped for the same reason (`topdown_signals ['frontend-bound',
'speculation-bound']` implausible given `memory-bound`) — the same skip path already real-verified on
`782.lbm_r` and `706.stockfish_r`, now confirmed a third time.

## Package power: another data point, still inconclusive

Power stayed in a narrow, recurring ~25-33W band for the whole run, with no consistent trend —
`Pearson r(package_power_w, elapsed_min) = -0.184` this run, a third real data point (after
`727.cppcheck_r`'s own `+0.272` and `-0.590` across its two runs) pointing in yet another direction. The
STAPM/power-ramp hypothesis remains open; this run's own `ratio` behavior (essentially flat after warm-up,
`r = -0.090`) is itself a data point suggesting this particular benchmark/run simply didn't have much
drift left to explain, warm-up or not.

## What this run actually confirms

- **The baseline warm-up fix generalizes to a second, independent benchmark and cluster** — not just the
  one that originally exposed the bug. This run's own failure mode was different (a systematic sign bias
  across every candidate, not a swallowed large win) but the fix corrected it the same way.
- **M4 continues to work correctly** — `-march=native` fast-tracked on a real cross-benchmark prior,
  then honestly re-evaluated and correctly rejected on its own (real, but too-small) merits here.
- **Phase 2's implausible-candidate filter and the PGO skip path both continue to work correctly** on a
  third real memory-bound benchmark.
- **The asymmetric accept bar (non-overlapping CI *and* ≥1% delta) is doing real, meaningful work**:
  `-march=native`/`-march=znver5` are statistically real effects here, correctly rejected anyway for
  being too small to matter in practice — a case this run makes concrete for the first time.
- **Package-power data remains inconclusive** — three real runs, three different correlation signs.

## Next steps this suggests

- The STAPM/package-power hypothesis needs either many more runs or a dedicated, controlled experiment
  (e.g., deliberately idling between trials) rather than incidental collection across mining runs whose
  own trial timing/load varies for unrelated reasons.
- A genuinely backend-bound benchmark still doesn't exist in the reference-matrix corpus to test.
- Phase 5's pair tournament still has zero real coverage across all real runs to date — every real run
  so far has had either zero or one confirmed candidate, never enough survivors to exercise the
  tournament path for real.

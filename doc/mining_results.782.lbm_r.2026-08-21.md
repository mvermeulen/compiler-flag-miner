# `cfm mine` results: 782.lbm_r, 2026-08-21

> ## ⚠️ Correction (2026-08-21, same day, after this run)
>
> **Every accept/reject conclusion and per-flag number in this document is void.**
> `cfm/workloads/spec_cpu2026.py`'s per-trial SPEC config rendered `basepeak = no` in a form SPEC
> silently ignores (an unscoped line, not nested inside the `<bench>=peak:` block it needs to be in)
> — every trial in this run, regardless of which candidate flag was nominally under test, actually
> built and measured the fixed *base*-tuning binary (`-g -O3 -march=native`, `gcc_O3.cfg`'s own
> suite-wide default), never the candidate flags at all. See `CLAUDE.md`'s Non-obvious traps log
> ("Resolved 2026-08-21: `generate_config()`'s per-trial `basepeak = no` override was silently ignored
> by SPEC since this project's very first commit") for the full root-cause writeup and fix.
>
> **The drift finding below survives, reinterpreted, and is arguably cleaner for it**: since every
> trial in this run measured the *identical* binary, the near-monotonic ~7.8-hour ramp really is pure
> host/environmental noise, unconfounded by any real flag difference — not partially explained by real
> per-flag effects as the original writeup assumed. But every "candidate rejected"/"`-O3` remains
> peak" conclusion is void; this benchmark's real answer needs a corrected re-run.

The third real `cfm mine` run (experiment 7 in `cfm.db`), and the first to actually use the external
reference-matrix characterization path (`cfm/reference_matrix.py`, PRs #25-#27) for real rather than
falling back to a local `deep-cpu` trial. Same headline conclusion as `doc/mining_results.
706.stockfish_r.2026-08-20.md`'s two runs — nothing beats `-O3` — but this run surfaced a distinct,
genuinely useful methodological finding of its own: **a strong, near-monotonic performance drift over
the run's ~7.8-hour duration, which silently determined every accept/reject verdict more than any
flag's own real effect did.**

## Headline result

**`-O3` alone remains the peak config. All 5 screened candidates were rejected.** But unlike the
stockfish runs, where confirmation deltas were small and scattered (±2%, no obvious pattern), lbm's
5 confirmation deltas came back **monotonically increasing with elapsed time, from -0.46% to +7.63%,
regardless of which flag was being tested** — the strongest evidence yet that this project needs to
account for run-duration drift, not just per-trial noise, once a mining run stretches into hours.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 782.lbm_r` (uncapped) |
| Started | 2026-08-21T00:51:05Z |
| Finished | 2026-08-21T08:39:28Z |
| Wall-clock | **7h48m23s** |
| Final status | `converged` |
| Candidates screened | 5 (of 5 plausible — all reached, nothing left unscreened) |
| Candidates accepted | 0 |
| Winning flags | `["-O3"]`, 0.0% gain |

## Baseline: first real use of the reference-matrix path

`baseline_characterization_source: "reference-matrix:amd-370-64gb"` — this run's characterization
came entirely from the published corpus (`resource_dominance=memory-bound`,
`vectorization_density=high`, `allocation_pressure=low`), skipping the ~46-minute local `deep-cpu`
trial the stockfish runs both had to pay. First real production confirmation that the PR #25-#27 work
actually saves time on a real mining run, not just in isolated verification.

Baseline calibration (3× `quick`-profile reps, all real local trials — the reference matrix supplies
*shape* only, never the ratio):

| Rep | Ratio | Timestamp |
|---|---|---|
| 1 | 15.729 | 01:10:48Z |
| 2 | 14.431 | 01:32:10Z |
| 3 | 14.398 | 01:53:36Z |

Mean **14.853**, but a **9.2% spread** between the lowest and highest rep — CI `[12.97, 16.74]`,
`verdict=PASS` (technically not "thin" by wspy-summary's own bar, but wide enough to matter, see below).

## Candidate generation: same exclusion pattern as stockfish, different reason

lbm is also `memory-bound` (like stockfish), so `_filter_implausible_candidates()` excluded the
identical 10 flags for the identical reason (`-flto`, `-fprofile-generate`/`-use`, `-freorder-*`,
`-fno-semantic-interposition`, `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta`) plus the same 3
unresolved-placeholder skips, leaving the same 5 survivors: `-fprefetch-loop-arrays`,
`-mprefer-vector-width=256`, `-mprefer-vector-width=512`, `-march=native`, `-fgraphite-identity`.
`vectorization_density=high` here (vs. stockfish's `moderate`) didn't change which flags survived —
that axis only excludes on `low`, never rewards `high` — but it's a fairer, more relevant shape for the
`-mprefer-vector-width` flags to be judged against than stockfish's own run was.

## The drift finding

Every trial in this run, in order, with elapsed time from run start:

| Trial | Flags | Ratio | Elapsed | Phase |
|---|---|---|---|---|
| 57 | `-O3` | 15.729 | 0:20 | baseline |
| 58 | `-O3` | 14.431 | 0:41 | baseline |
| 59 | `-O3` | 14.398 | 1:03 | baseline |
| 60-64 | (screening, 5 candidates) | 14.25-14.48 | 1:24-2:50 | screening |
| 65-67 | `-fprefetch-loop-arrays` | 14.65 → 14.75 → 14.95 | 3:11-3:53 | confirm |
| 68-70 | `-mprefer-vector-width=256` | 15.08 → 15.32 → 15.34 | 4:13-4:53 | confirm |
| 71-73 | `-mprefer-vector-width=512` | 15.55 → 15.67 → 15.79 | 5:13-5:52 | confirm |
| 74-76 | `-march=native` | 15.88 → 15.96 → 15.97 | 6:12-6:50 | confirm |
| 77-79 | `-fgraphite-identity` | 15.92 → 16.10 → 15.94 | 7:10-7:48 | confirm |

Excluding trial 57 (a single early outlier, plausibly a cold-start effect), **every subsequent trial
increases almost monotonically for the rest of the 7.8-hour run** — 14.40 → 14.25 → 14.38 → 14.40 →
14.31 → 14.48 → 14.65 → 14.75 → 14.95 → 15.08 → ... → 16.10, a ~12% rise from trial 58 to trial 78,
tracking elapsed time far more tightly than it tracks which flag was under test.

Per-flag confirmation summary, against the (noisy, front-loaded) baseline:

| Flag | Confirm mean | Delta vs. baseline | CI overlaps baseline? |
|---|---|---|---|
| `-fprefetch-loop-arrays` | 14.784 | **-0.46%** | yes |
| `-mprefer-vector-width=256` | 15.247 | **+2.66%** | yes |
| `-mprefer-vector-width=512` | 15.673 | **+5.52%** | yes |
| `-march=native` | 15.938 | **+7.31%** | yes |
| `-fgraphite-identity` | 15.985 | **+7.63%** | yes |

The delta column is monotonically increasing in exactly the order the candidates happened to be
confirmed — not remotely the order a real per-flag effect would produce (there's no mechanical reason
`-fgraphite-identity` should outperform `-fprefetch-loop-arrays` by 8 points). This is drift, not
signal. **Every candidate still got `reject`, but for a subtler reason than "no real effect": baseline's
own CI (`[12.97, 16.74]`) is wide enough (from its own 9.2% front-loaded spread) that it overlaps even
`-fgraphite-identity`'s tight, genuinely-elevated CI (`[15.74, 16.23]`, +7.6% above baseline's mean).**
The confirmation bar did its job — an unstable baseline correctly failed to license an accept — but the
mechanism was baseline noise swallowing the signal, not the flags being neutral.

**Plausible cause (a hypothesis, not confirmed against direct thermal telemetry)**: the run spanned
2026-08-20T19:51 through 2026-08-21T03:39 local time (CDT) — evening into early morning. A gradual
overnight ambient-temperature drop improving sustained thermal headroom (and therefore sustained clock
speed / `ratio`) over the run's duration is a natural physical explanation, consistent with the
near-linear rather than step-function shape of the trend. Not verified here; `wspy`'s own systemtime
pass captures temperature-vs-frequency data that a future investigation could check directly against
this run's own artifacts.

## Timing

Individual `quick`-profile trials landed **~21 minutes apart** here, roughly 4-5x slower than
stockfish's own ~5 minutes/trial — a real per-workload difference (lattice-Boltzmann's own SPECrate
iteration is intrinsically longer-running than stockfish's), not a regression. Worth remembering
`quick`-profile trial cost is workload-dependent, not a fixed constant, when estimating a future run's
duration.

## Phase 5 (greedy combine)

Not exercised again — zero Phase 4 acceptances, same as both stockfish runs. Three real mining runs in
a row now with nothing accepted into Phase 5; still a real open gap in test coverage for the greedy
walk / pair-tournament logic against genuine acceptances, not something this run's own choice of
benchmark happened to fix (lbm's `resource_dominance` turned out to be memory-bound too, same
exclusion pattern as stockfish, so it wasn't the differently-shaped benchmark that might have produced
a different outcome).

## Next steps this suggests

- **Baseline drift is now a demonstrated, not hypothetical, problem for multi-hour runs.** Worth a real
  design conversation: re-measuring/refreshing the baseline periodically through a long run, spreading
  the 3 baseline reps out in time rather than front-loading them, or normalizing each confirmation
  trial against a baseline measured *near* it in time rather than once at the very start. `doc/DESIGN.md`
  §14 M2.5 item 3's fixed `MIN_PRACTICAL_SIGNIFICANCE_PCT` isn't the lever that matters here — this run
  was blocked by CI overlap from baseline's own noise, not by the practical-significance threshold.
- **Still need a benchmark whose `resource_dominance` differs from memory-bound** to get real coverage
  of the compute-bound/frontend-bound flag categories and to finally exercise Phase 5 for real — two
  memory-bound benchmarks in a row (stockfish, lbm) both excluded the same 10 catalog flags for the
  same reason.
- Confirmed real production value from PRs #25-#27: reference-matrix characterization worked
  correctly and saved real wall-clock time on this run, not just in isolated verification.

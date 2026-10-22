# `cfm mine` results: 777.zstd_r on `niwot`, 2026-10-22

The fourteenth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), the fifth `memory-bound` one, and
the last `intrate` benchmark. `777.zstd_r` (Zstandard compression) was mined once on the old host
([`mining_results.777.zstd_r.2026-08-25.md`](mining_results.777.zstd_r.2026-08-25.md)), where nothing was
accepted. `-march=native` read about +0.7% there, CI-clear but under the 1% bar.

## Headline result

**`-O3 -march=native`, +1.72% over plain `-O3`** (ratio 17.15 → 17.44). It's a small win, a little larger than
the old host's sub-threshold +0.7%. Every other candidate was flat.

- **An LTO/PGO check found nothing the shape filter hid, unlike the other four memory-bound benchmarks.** On
  top of `-O3 -march=native`, `-flto` is flat (+0.24%) and PGO loses (-1.7%, or -2.5% with LTO). zstd is the
  first memory-bound benchmark on this host where excluding LTO and PGO cost nothing. Its corpus shape is also
  the clearest memory-bound margin here (64.0%, against 38-45% for the other four).
- **One unexplained outlier trial** (trial 542, ratio 12.20, 29% below every other trial in the run) landed
  in a rejected candidate's confirmation reps. It didn't change any verdict. See below.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 777.zstd_r` (uncapped, queued after `753.ns3_r`) |
| Code | `main` at `11e7c78` (later commits are doc-only) |
| Experiment id | 113 |
| Started / finished | 2026-10-22T03:06:17Z / 2026-10-22T07:36:30Z (4h30m) |
| Final status | `converged` |
| Trials | 26 (529-554) |
| Candidates screened / confirmed | 3 / 0 (plus 2 fast-tracked, 1 accepted) |
| Fast-tracked (M4) | `-fprefetch-loop-arrays` (rejected), `-march=native` (accepted) |
| Winning flags | `["-O3", "-march=native"]`, +1.72% |
| Power profile | `balanced`, unchanged; CPU temp 83.9-94.2°C, package power 21.0-28.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 529 | warm-up (excluded from CI) | 16.99 |
| 530 | warm-up (excluded from CI) | 17.05 |
| 531 | calibration | 17.15 |
| 532 | calibration | 17.16 |
| 533 | calibration | 17.13 |

Calibration mean **17.146**, 95% CI **[17.11, 17.18]** (±0.2%). The warm-ups absorbed a small early rise
(+0.9%), as designed.

**Shape: `memory-bound`, 64.0%**, `vectorization_density=moderate`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`).

## Phase 2 filtering and M4

The memory-bound, moderate-vectorization shape excluded the same eight candidates as vpr:

- frontend-bound-tagged: `-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`,
  `-fno-semantic-interposition`
- compute-bound-tagged: `-funroll-loops`, `-Ofast`, `-ffast-math`
- backend-bound-tagged: `-fipa-pta`

M4 fast-tracked `-fprefetch-loop-arrays` and `-march=native`, each on a 1-of-4 record.

## Phase 3 screening (vs. most recent calibration rep, 17.13)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 534 | `-O3 -fgraphite-identity` | 17.08 | -0.28% | survived |
| 535 | `-O3 -mprefer-vector-width=256` | 17.23 | +0.60% | survived |
| 536 | `-O3 -mprefer-vector-width=512` | 17.07 | -0.36% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [17.11, 17.18])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` (fast-tracked) | 17.46, 17.45, 17.40 | 17.44 | [17.35, 17.52] | **+1.69%** | **accept** |
| `-fprefetch-loop-arrays` (fast-tracked) | 17.16, 17.12, 17.15 | 17.14 | [17.10, 17.19] | -0.01% | reject |
| `-fgraphite-identity` | 17.08, 17.09, 17.12 | 17.09 | [17.05, 17.14] | -0.30% | reject |
| `-mprefer-vector-width=512` | 17.07, 17.11, 17.10 | 17.09 | [17.04, 17.14] | -0.31% | reject |
| `-mprefer-vector-width=256` | 17.22, 17.08, **12.20** | 15.50 | [8.39, 22.61] | -9.60% | reject |

- **`-march=native` is a clean accept.** Its CI lower bound (17.35) clears the baseline's upper bound
  (17.18), and +1.69% clears the 1% bar. It's this cluster's second accept for the flag on this host (vpr was
  the first), now 2 of 5.
- **`-fprefetch-loop-arrays` was fast-tracked and rejected**, another case for opportunity #15. zstd's match
  finder reads through hash tables, not strided arrays, so loop prefetching has little to act on.

### The trial 542 outlier

`-mprefer-vector-width=256`'s third rep measured 12.20, against 17.08-17.22 for its first two reps and for
every other trial in the run. Without it, the flag reads +0.03% and would have been rejected anyway, so no
verdict changed. What's known:

- The slowdown was uniform across all 16 copies (787-845 s each, against about 600 s normally), so it was
  something system-wide, not one stuck copy.
- The run passed validate, and the audit confirms `-O3 -mprefer-vector-width=256` compiled in, the same flags
  as the two normal reps.
- CPU temperature (83.9°C) and package power (22.0 W) at measurement were both at the low end of the run's
  range, not high. That fits a clock or power limit dropping, not thermal throttling.
- `sar` shows the CPUs 99% busy in user time for that window, and the system journal shows nothing beyond
  routine `sysstat` and `anacron` entries.

The cause is unknown. The outlier did skew the knowledge table: `-mprefer-vector-width=256`'s memory-bound
mean is now -2.97%, against roughly 0% without it. One cheap guard is a per-trial outlier check in
Phase 4 (re-run a rep that is far outside the others before using it), noted on the
[opportunity list](opportunities_niwot.md) as #22.

## Phase 5 combination

There's only one accepted flag, so the combination is `-O3 -march=native` re-confirmed: **17.44** (17.43, 17.43,
17.47; CI [17.39, 17.50]), +1.72%.

## Phase 6 multipliers

- **PGO: skipped**, because the memory-bound shape contradicts both of `-fprofile-use`'s `topdown_signals`.
- **Microarch: skipped**, because the winning set already contains `-march=native`.

None of the trials logged an audit warning.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 5 | 2 | +0.66% |
| `-fprefetch-loop-arrays` | 5 | 1 | +0.56% |
| `-fgraphite-identity` | 5 | 0 | +0.33% |
| `-mtune=znver5` | 3 | 0 | +0.20% |
| `-mprefer-vector-width=512` | 3 | 0 | -0.15% |
| `-march=znver5` | 3 | 0 | -0.33% |
| `-mprefer-vector-width=256` | 3 | 0 | -2.97% (skewed by trial 542) |

## Follow-up: LTO and PGO on top of the winner (2026-10-22)

The same check as vpr, sqlite, abc and gcc. Three interleaved rounds of four flag sets, each a `cfm measure`
run at its default 3 iterations (median), experiments 114-125, 07:36Z-13:54Z.

| Flags | Round 1 | Round 2 | Round 3 | Mean | 95% CI | vs control | vs mine's `-O3` (17.15) |
|---|---|---|---|---|---|---|---|
| `-O3 -march=native` (control) | 17.32 | 17.40 | 17.42 | 17.38 | [17.26, 17.51] | — | +1.38% |
| `-O3 -march=native -flto` | 17.40 | 17.44 | 17.43 | 17.42 | [17.37, 17.48] | +0.24% | +1.63% |
| `-O3 -march=native -fprofile-use` | 17.03 | 17.14 | 17.10 | 17.09 | [16.95, 17.22] | -1.70% | -0.35% |
| `-O3 -march=native -flto -fprofile-use` | 16.96 | 16.91 | 16.96 | 16.95 | [16.88, 17.01] | -2.52% | -1.17% |

- **`-flto` is flat**: +0.24%, CIs overlapping. zstd's hot code (match finding and entropy coding) sits in a
  few large translation units already, so there's little cross-module inlining left to do.
- **PGO is a small, real loss**, with CIs clear of the control's, and slightly worse with LTO. zstd's branches
  depend on the data being compressed, and the train input's statistics apparently don't match the
  reference input's well enough to help.
- **zstd's winner stays `-O3 -march=native`, +1.72%.** The control matched the mine's winner within 0.3%.
- Every build passed validate, and no audit logged a warning.

So among the five memory-bound benchmarks on this host, four gained from LTO or PGO that the shape filter
excluded (vpr, gcc, sqlite, abc), and one didn't (zstd, the one with the clearest memory-bound margin). That
fits opportunity #8's framing: the exclusion is wrong at moderate margins, and may be fine at a clear one.

## Follow-ups

1. Opportunity #22 (new): guard Phase 4 against single-rep outliers like trial 542.
2. Opportunity #15: `-fprefetch-loop-arrays` fast-tracked and rejected again (now 1 of 5).

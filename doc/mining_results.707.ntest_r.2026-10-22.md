# `cfm mine` results: 707.ntest_r on `niwot`, 2026-10-22 (re-mine)

A re-mine of `707.ntest_r` (an Othello engine) for opportunity #12 on the
[opportunity list](opportunities_niwot.md). The first mine on this host
([`mining_results.707.ntest_r.2026-10-18.md`](mining_results.707.ntest_r.2026-10-18.md)) found `-O3 -march=native`
at +14.27%. In that mine the compute-bound shape (40.6%) excluded `-flto` and every other frontend-bound flag at
Phase 2, and skipped PGO at Phase 6. This is also the first real mine on PRs #48-51 (the shape-margin gate,
vector-width deferral, majority-prior fast-track and measurement guards).

## Headline result

**`-O3 -march=native -flto -fprofile-use`, +30.95% over plain `-O3`** (ratio 28.36 → 37.13), against the first
mine's +14.27%. The new part all comes from the two flag families the old exclusion hid:

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 28.36 | — |
| `-O3 -march=native` | 32.60 | +14.97% |
| `+ -flto` | 33.36 | +2.32% |
| `+ -fprofile-use` | 37.13 | **+11.31%** |

- **PGO is the big one: +11.3% on top of `-march=native -flto`.** An Othello engine's search is branchy, and its
  evaluation's hot paths depend on the position, so profile-driven layout and inlining pay off. That's the
  frontend-bound pattern, inside a benchmark whose corpus shape says compute-bound at a 40.6% margin.
- **`-flto` is +3.6% alone and +2.3% on top of `-march=native`.**
- **The baseline recheck flagged a +0.51% offset** (one `-O3` rep at 28.50 after Phase 4, just past the 0.5%
  threshold). Measured against that rep instead, the gain is +30.28%; against the first mine's `-O3` (28.61),
  it's +29.79%. No verdict here sits close enough to the bar for 0.5% to matter, except `-Ofast` (below).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 707.ntest_r` (uncapped) |
| Code | `main` at `8dabde0` (PRs #48-51; not PR #52, merged mid-run) |
| Experiment id | 138 |
| Started / finished | 2026-10-22T17:50:50Z / 2026-10-23T00:20:23Z (6h30m) |
| Final status | `converged` |
| Trials | 70 (579-648) |
| Candidates screened / confirmed | 10 / 2 (plus 1 fast-tracked, accepted) |
| Fast-tracked (M4) | `-march=native` (2 of 2 accepted before; accepted) |
| Winning flags | `["-O3", "-march=native", "-flto", "-fprofile-use"]`, +30.95% |
| Power profile | `balanced`, unchanged; CPU temp 89.8-95.4°C, package power 20.0-24.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 579 | warm-up (excluded from CI) | 28.58 |
| 580 | warm-up (excluded from CI) | 28.62 |
| 581 | calibration | 28.36 |
| 582 | calibration | 28.32 |
| 583 | calibration | 28.38 |
| 627 | re-check after Phase 4 | 28.50 (+0.51%, flagged) |

Calibration mean **28.355**, 95% CI **[28.28, 28.43]** (±0.3%), about 0.9% below the first mine's 28.61. The
warm-ups ran higher than the calibration reps, the opposite of the usual settling direction. The re-check landed
between the two, so the calibration reps probably sampled a little low.

**Shape: `compute-bound`, 40.6%**, `vectorization_density=low`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`), the same entry as the first mine.

## Phase 2 filtering and M4

- **PR #48's margin gate fired:** "baseline shape 'compute-bound' at 40.6% is below the 55% confidence margin --
  not excluding any candidate on resource_dominance." In the first mine this shape excluded nine candidates, seven of
  them on `resource_dominance`; this time those seven were all screened.
- **Both `-mprefer-vector-width` settings were still excluded**, by `vectorization_density=low` (that filter has
  no margin gate). So PR #49's deferral had nothing to defer, and Phase 6's vector-width step reported "no
  deferred -mprefer-vector-width= candidates". It hasn't run for real yet.
- **M4 fast-tracked only `-march=native`** (2 of 2 accepted). The new majority rule (PR #50) screened the
  others normally, each on a 0-of-1 or 0-of-2 record.

## Phase 3 screening (vs. most recent calibration rep, 28.38)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 587 | `-O3 -flto` | 29.51 | +3.98% | survived |
| 585 | `-O3 -Ofast` | 28.73 | +1.23% | survived |
| 586 | `-O3 -ffast-math` | 28.66 | +0.99% | survived |
| 592 | `-O3 -fipa-pta` | 28.64 | +0.92% | survived |
| 589 | `-O3 -freorder-functions` | 28.59 | +0.74% | survived |
| 588 | `-O3 -freorder-blocks-and-partition` | 28.55 | +0.60% | survived |
| 591 | `-O3 -fprefetch-loop-arrays` | 28.50 | +0.42% | survived |
| 593 | `-O3 -fgraphite-identity` | 28.36 | -0.07% | survived |
| 584 | `-O3 -funroll-loops` | 28.18 | -0.70% | survived |
| 590 | `-O3 -fno-semantic-interposition` | 27.99 | -1.37% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [28.28, 28.43])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` (fast-tracked) | 32.58, 32.57, 32.58 | 32.58 | [32.56, 32.59] | **+14.88%** | **accept** |
| `-flto` | 29.44, 29.46, 29.23 | 29.38 | [29.05, 29.70] | **+3.61%** | **accept** |
| `-Ofast` | 28.61, 28.65, 28.67 | 28.64 | [28.57, 28.71] | +1.02% | accept |
| `-ffast-math` | 28.66, 28.35, 28.67 | 28.56 | [28.11, 29.01] | +0.72% | reject |
| `-fgraphite-identity` | 28.56, 28.53, 28.47 | 28.52 | [28.42, 28.63] | +0.58% | reject |
| `-freorder-functions` | 28.54, 28.50, 28.36 | 28.47 | [28.23, 28.70] | +0.39% | reject |
| `-fipa-pta` | 28.51, 28.26, 28.60 | 28.46 | [28.02, 28.90] | +0.37% | reject |
| `-fno-semantic-interposition` | 28.53, 28.50, 28.31 | 28.45 | [28.15, 28.74] | +0.32% | reject |
| `-freorder-blocks-and-partition` | 28.24, 28.59, 28.26 | 28.36 | [27.87, 28.86] | +0.03% | reject |
| `-fprefetch-loop-arrays` | 28.39, 28.27, 28.27 | 28.31 | [28.15, 28.48] | -0.15% | reject |
| `-funroll-loops` | 27.99, 28.48, 28.42 | 28.30 | [27.63, 28.96] | -0.21% | reject |

- **`-Ofast`'s accept is marginal.** +1.02% only just clears the bar, and against the re-check rep it reads
  +0.5%. It didn't matter: Phase 5 dropped it (below). The first mine rejected it at about +0.4%.
- **No outlier reruns fired** (PR #51). The largest spread was `-funroll-loops`' 27.99 against 28.42-28.48, under
  the 10% trigger.
- **No near-misses for PR #52.** `-fgraphite-identity` came closest, but its CI's lower bound (28.42) overlaps
  baseline's upper bound (28.43). So #52's near-miss PGO variant wouldn't have run here, and this result is the
  same as it would have been with #52 in.

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Verdict |
|---|---|---|---|---|---|
| greedy 1 | `-O3 -march=native` | 32.53, 32.68, 32.60 | 32.60 | [32.42, 32.78] | accept |
| greedy 2 | `+ -flto` | 33.40, 33.32, 33.35 | 33.36 | [33.25, 33.46] | accept, +2.32% |
| greedy 3 | `+ -Ofast` | 33.23, 33.23, 32.86 | 33.11 | [32.58, 33.63] | reject, -0.75% |
| pair | `-O3 -Ofast -flto` | 29.23, 29.27, 29.06 | 29.19 | | not better |
| pair | `-O3 -flto -march=native` | 33.44, 33.24, 33.38 | 33.35 | | not better (same set) |
| pair | `-O3 -Ofast -march=native` | 32.72, 32.70, 32.78 | 32.73 | | not better |

`-Ofast` adds nothing once `-march=native` is in; it was likely worth its 1% only on generic x86-64.

## Phase 6 multipliers

- **PGO: attempted (the margin gate also unblocks this skip), accepted at +11.31%** on top of
  `-O3 -march=native -flto` (37.14, 37.10, 37.15; CI [37.07, 37.19]). Far clear of the Phase 5 CI.
- **Microarch: skipped**, because the winning set already contains `-march=native`.
- **Vector width: nothing deferred** (see Phase 2).

None of the trials logged an audit warning.

## Knowledge table after this run (`compute-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 3 | 3 | +16.63% |
| `-fprofile-use` | 1 | 1 | +11.31% |
| `-flto` | 1 | 1 | +3.61% |
| `-Ofast` | 3 | 1 | +0.61% |
| `-fgraphite-identity` | 1 | 0 | +0.58% |
| `-ffast-math` | 3 | 0 | +0.47% |
| `-mprefer-vector-width=256` | 1 | 0 | +0.45% |
| `-freorder-functions` | 1 | 0 | +0.39% |
| `-fipa-pta` | 1 | 0 | +0.37% |
| `-fno-semantic-interposition` | 1 | 0 | +0.32% |
| `-mprefer-vector-width=512` | 1 | 0 | +0.12% |
| `-freorder-blocks-and-partition` | 1 | 0 | +0.03% |
| `-funroll-loops` | 3 | 0 | -0.12% |
| `-fprefetch-loop-arrays` | 1 | 0 | -0.15% |

## What this says about the pipeline

- **The margin gate (#8, PR #48) paid for itself on its first real run: +14.27% → +30.95%.** On ntest, as on
  the memory-bound benchmarks at moderate margins (vpr, gcc, sqlite, abc), the corpus shape was too weak to rule
  out LTO and PGO.
- **`sealcrypto` (compute-bound at 55.1%) sits just above the gate**, so a re-mine there would still exclude LTO
  and PGO. Given ntest, a direct LTO/PGO check on sealcrypto is worth doing.
- **The vectorization-density filter has no margin gate.** Here it excluded both vector-width candidates on a
  `low` reading from another machine. That's probably right for an integer engine, but it means PR #49 hasn't been
  exercised yet; fprate is where it should be.

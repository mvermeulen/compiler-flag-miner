# `cfm mine` results: 734.vpr_r on `niwot`, 2026-10-20

The tenth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the third `memory-bound` one,
after `708.sqlite_r` and `729.abc_r`. `734.vpr_r` (VPR, FPGA place-and-route) was mined once on the old host
([`mining_results.734.vpr_r.2026-08-27.md`](mining_results.734.vpr_r.2026-08-27.md)), where `-march=native`
won by +1.04%.

## Headline result

**`-O3 -march=native`, +1.31% over plain `-O3`** (ratio 21.20 → 21.48). That's a small win, within a
third of a point of the old host's +1.04%. Every other candidate was flat and rejected.

- **`-march=native` got here the long way.** In this host's memory-bound cluster its prior was a reject
  (sqlite and abc), so it went through screening like any other candidate instead of being fast-tracked. On
  the old host it was fast-tracked. The result is the same either way.
- **`-fprefetch-loop-arrays` was fast-tracked and rejected (+0.42%).** Its prior was sqlite's accept. It's the
  first fast-track miss in this cluster, and the same weak-prior pattern as `-march=native` in the
  frontend-bound cluster (opportunity #15).
- **LTO and PGO were never tried.** The memory-bound shape excluded `-flto` at Phase 2 and skipped PGO at
  Phase 6, as on the old host. The margin (45.4%) isn't wide, so that's a new opportunity (#20).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 734.vpr_r` (uncapped, queued after `727.cppcheck_r`) |
| Code | `main` at `11e7c78` (later commits are doc-only) |
| Experiment id | 43 |
| Started / finished | 2026-10-20T03:11:40Z / 2026-10-20T06:20:59Z (3h09m) |
| Final status | `converged` |
| Trials | 27 (329-355) |
| Candidates screened / confirmed | 4 / 1 (plus 1 fast-tracked, rejected) |
| Fast-tracked (M4) | `-fprefetch-loop-arrays` (rejected) |
| Winning flags | `["-O3", "-march=native"]`, +1.31% |
| Power profile | `balanced`, unchanged; CPU temp 93.0-99.2°C, package power 19.0-27.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 329 | warm-up (excluded from CI) | 21.25 |
| 330 | warm-up (excluded from CI) | 21.25 |
| 331 | calibration | 21.23 |
| 332 | calibration | 21.21 |
| 333 | calibration | 21.18 |

Calibration mean **21.205**, 95% CI **[21.14, 21.27]** (±0.3%). There was a slight downward drift across
all five reps (-0.4%), well inside the band that matters here.

**Shape: `memory-bound`, 45.4%**, `vectorization_density=moderate`, `allocation_pressure=high`, from the
corpus (`reference-matrix:amd-370-64gb`). This is the same corpus entry the old host's run used.

## Phase 2 filtering and M4

The memory-bound, moderate-vectorization shape excluded eight candidates:

- frontend-bound-tagged: `-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`,
  `-fno-semantic-interposition`
- compute-bound-tagged: `-funroll-loops`, `-Ofast`, `-ffast-math`
- backend-bound-tagged: `-fipa-pta`

M4 found seven memory-bound priors from sqlite and abc. Only `-fprefetch-loop-arrays` had an accepted record
(1 of 2, mean +1.48%), so it was the only one fast-tracked.

## Phase 3 screening (vs. most recent calibration rep, 21.18)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 334 | `-O3 -fgraphite-identity` | 21.17 | -0.05% | survived |
| 335 | `-O3 -mprefer-vector-width=256` | 21.32 | +0.69% | survived |
| 336 | `-O3 -mprefer-vector-width=512` | 21.09 | -0.41% | survived |
| 337 | `-O3 -march=native` | 21.44 | +1.23% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [21.14, 21.27])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | 21.52, 21.52, 21.53 | 21.52 | [21.51, 21.53] | **+1.50%** | **accept** |
| `-fprefetch-loop-arrays` (fast-tracked) | 21.21, 21.36, 21.31 | 21.29 | [21.10, 21.49] | +0.42% | reject (CIs overlap) |
| `-mprefer-vector-width=256` | 21.18, 21.34, 21.23 | 21.25 | [21.04, 21.46] | +0.22% | reject |
| `-mprefer-vector-width=512` | 21.23, 21.32, 21.17 | 21.24 | [21.05, 21.43] | +0.17% | reject |
| `-fgraphite-identity` | 21.22, 21.17, 21.17 | 21.19 | [21.11, 21.26] | -0.09% | reject |

- **`-march=native`'s three reps are almost identical** (spread 0.01), and its CI is well clear of the
  baseline's. A small effect, but a cleanly measured one.
- **`-fprefetch-loop-arrays` doesn't help vpr.** VPR's hot loops chase pointers through routing graphs and
  heaps rather than striding through arrays, so there's little for GCC's loop prefetching to act on. sqlite's
  +1.7% doesn't carry over.
- **`-mprefer-vector-width` does nothing at plain `-O3`**, for the same reason as on sealcrypto: the baseline
  targets generic x86-64 without AVX-512.

## Phase 5 combination

There's only one accepted flag, so the combination is `-O3 -march=native` re-confirmed: **21.48**
(21.51, 21.43, 21.50; CI [21.37, 21.59]), +1.31%. The CI is still clear of the baseline's, and +1.31% still
clears the 1.0% bar.

## Phase 6 multipliers

- **PGO: skipped**, because the memory-bound shape contradicts both of `-fprofile-use`'s `topdown_signals`.
- **Microarch: skipped**, because the winning set already contains `-march=native`.

None of the trials logged an audit warning.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprefetch-loop-arrays` | 3 | 1 | +1.12% |
| `-fgraphite-identity` | 3 | 0 | +0.68% |
| `-march=native` | 3 | 1 | +0.63% |
| `-mprefer-vector-width=256` | 2 | 0 | +0.35% |
| `-mtune=znver5` | 2 | 0 | +0.33% |
| `-mprefer-vector-width=512` | 2 | 0 | -0.07% |
| `-march=znver5` | 2 | 0 | -0.33% |

Every memory-bound result on this host so far is within ±2%. The cluster's flags gain little, which matches
the old host after its stockfish outlier is set aside (stockfish profiles frontend-bound here).

## Follow-ups

1. **LTO and PGO were never tried** on vpr, on either host. The shape excluded both, and the margin (45.4%)
   is moderate. An interleaved `cfm measure` of `-O3 -march=native` against `-O3 -march=native -flto` would
   show whether that cost anything. Added to the [opportunity list](opportunities_niwot.md) as #20.
2. Opportunity #15 now has a memory-bound case too: `-fprefetch-loop-arrays` fast-tracked on a 1-of-2 record
   and rejected.

## Follow-up: LTO and PGO on top of the winner (2026-10-20)

Opportunity #20. The mine never tried `-flto` or PGO, because the memory-bound shape excluded both. This
follow-up measured them directly: three interleaved rounds of four flag sets, each a `cfm measure` run at
its default 3 iterations (median), experiments 44-55, 11:09Z-15:04Z.

| Flags | Round 1 | Round 2 | Round 3 | Mean | 95% CI | vs control | vs mine's `-O3` (21.20) |
|---|---|---|---|---|---|---|---|
| `-O3 -march=native` (control) | 21.40 | 21.43 | 21.41 | 21.41 | [21.38, 21.44] | — | +0.98% |
| `-O3 -march=native -flto` | 23.82 | 23.89 | 23.83 | 23.84 | [23.75, 23.94] | **+11.35%** | +12.44% |
| `-O3 -march=native -fprofile-use` | 22.26 | 22.34 | 22.25 | 22.28 | [22.16, 22.40] | **+4.05%** | +5.07% |
| `-O3 -march=native -flto -fprofile-use` | 24.53 | 24.54 | 24.58 | 24.55 | [24.49, 24.61] | **+14.65%** | **+15.77%** |

- **Both help, and they stack.** Every CI is far clear of every other, and each flag set's three rounds agree
  within 0.3%. `-flto` alone is worth +11.4%, PGO alone +4.1%, and together +14.7%.
- **vpr's winner is now `-O3 -march=native -flto -fprofile-use`, +15.77% over plain `-O3`**, against the
  mine's +1.31%. The control here (21.41) sits within 0.3% of the mine's own `-O3 -march=native` result
  (21.48), so the two runs are comparable.
- Every build passed validate. Every audit confirmed `-O3` (and `-fprofile-use` where present) compiled in,
  with `-march=native`/`-flto` reported as "not independently checkable", as expected.

**This is the pipeline's biggest miss so far.** The shape filter treated a 45.4% memory-bound margin as
enough to rule out the whole frontend-bound family (`-flto`, PGO), and that cost vpr about 14 points. On the
old host the same filter made the same call. Opportunities #8 (don't let a moderate-margin shape exclude
whole families) and #2 (the same LTO/PGO check for `708.sqlite_r` and `729.abc_r`) are now high priority.

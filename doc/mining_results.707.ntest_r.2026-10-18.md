# `cfm mine` results: 707.ntest_r on `niwot`, 2026-10-18

The fifth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the first `compute-bound`
benchmark on this host. `707.ntest_r` (an Othello engine) was mined once before on the old host
([`mining_results.707.ntest_r.2026-08-26.md`](mining_results.707.ntest_r.2026-08-26.md)), where
`-march=native` won by +14.83%.

## Headline result

**`-O3 -march=native`, +14.27% over plain `-O3`** (ratio 28.61 → 32.69). That's within half a point of the
old host's +14.83%. The other three candidates (`-funroll-loops`, `-Ofast`, `-ffast-math`) were flat and
rejected.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 707.ntest_r` (uncapped, queued after the `729.abc_r` re-measure) |
| Code | `main` at `0d5d8d0` |
| Experiment id | 20 |
| Started / finished | 2026-10-18T20:05:28Z / 2026-10-18T22:18:24Z (2h13m) |
| Final status | `converged` |
| Trials | 24 (154-177) |
| Candidates screened / confirmed | 4 / 1 |
| Fast-tracked (M4) | none (no `compute-bound` priors on this host yet) |
| Winning flags | `["-O3", "-march=native"]`, +14.27% |
| Power profile | `balanced`, unchanged; CPU temp 88.6-93.5°C, package power 19.1-21.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 154 | warm-up (excluded from CI) | 29.20 |
| 155 | warm-up (excluded from CI) | 28.58 |
| 156 | calibration | 28.59 |
| 157 | calibration | 28.59 |
| 158 | calibration | 28.64 |

Calibration mean **28.606**, 95% CI **[28.53, 28.68]** (±0.3%). The first warm-up ran 2% higher than every
later `-O3` trial. That's the one early outlier the warm-up reps exist to absorb, and it stayed out of the CI.

**Shape: `compute-bound`, 40.6%** (narrow margin), `vectorization_density=low`, `allocation_pressure=low`,
from the corpus (`reference-matrix:amd-370-64gb`). This is the same corpus entry the old host's run used. No
local characterization trial was run.

## Phase 2 filtering

The compute-bound, low-vectorization shape excluded nine candidates:

- frontend-bound-tagged: `-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`,
  `-fno-semantic-interposition`
- memory-bound-tagged: `-fprefetch-loop-arrays`
- vectorization-high-tagged: both `-mprefer-vector-width` settings
- backend-bound-tagged: `-fipa-pta`, `-fgraphite-identity`

Four went to screening. M2's ranking put `-march=native` first: it matches two signals (compute-bound plus the
narrow margin) against one for the others.

## Phase 3 screening (vs. most recent calibration rep, 28.64)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 159 | `-O3 -march=native` | 32.67 | +14.07% | survived |
| 160 | `-O3 -funroll-loops` | 28.50 | -0.49% | survived |
| 161 | `-O3 -Ofast` | 28.66 | +0.05% | survived |
| 162 | `-O3 -ffast-math` | 28.72 | +0.28% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [28.53, 28.68])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | 32.73, 32.73, 32.74 | 32.74 | [32.72, 32.75] | **+14.43%** | **accept** |
| `-Ofast` | 28.70, 28.63, 28.70 | 28.68 | [28.58, 28.77] | +0.25% | reject (CIs overlap) |
| `-ffast-math` | 28.62, 28.62, 28.68 | 28.64 | [28.55, 28.73] | +0.13% | reject |
| `-funroll-loops` | 28.52, 28.54, 27.98 | 28.35 | [27.55, 29.14] | -0.91% | reject |

- `-Ofast` and `-ffast-math` doing nothing is expected. ntest is integer code, and both flags mainly relax
  floating-point semantics.
- `-funroll-loops`'s third rep (27.98) is the run's one outlier. That trial also logged the run's lowest
  temperature (88.6°C), but nothing else in the run shows temperature tracking ratio. Even without it, the
  flag reads about -0.4%, so the reject doesn't depend on the outlier.

## Phase 5 combination

There's only one accepted flag, so the combination is just `-O3 -march=native` re-confirmed: **32.69**
(32.69, 32.66, 32.71; CI [32.61, 32.76]), +14.27%.

## Phase 6 multipliers

- **PGO: skipped**, because the compute-bound shape contradicts both of `-fprofile-use`'s `topdown_signals`.
  The old host skipped it for the same reason, so PGO has never been tried on ntest.
- **Microarch: skipped**, because the winning set already contains `-march=native`.

Every audit confirms `-O3` and the flag under test were compiled in. `-march=native` is reported as "not
independently checkable", as expected, because GCC expands it before recording.

## Knowledge table after this run

These are the first `compute-bound` rows on `niwot`, with one trial each:

| Flag | Accepted | Mean delta |
|---|---|---|
| `-march=native` | 1/1 | +14.43% |
| `-Ofast` | 0/1 | +0.25% |
| `-ffast-math` | 0/1 | +0.13% |
| `-funroll-loops` | 0/1 | -0.91% |

The next compute-bound benchmark (`750.sealcrypto_r` is the other one in intrate) will fast-track
`-march=native` on this prior.

## Follow-ups

1. **PGO and LTO were never tried**, on either host, because the shape excluded them. The corpus margin is
   narrow (40.6%), so a direct `cfm measure` of `-O3 -march=native -flto` and the two-pass PGO variant would
   show whether that exclusion cost anything. Added to the
   [opportunity list](opportunities_niwot.md).

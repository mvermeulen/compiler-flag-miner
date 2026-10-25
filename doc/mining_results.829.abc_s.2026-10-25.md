# `cfm mine` results: 829.abc_s on `niwot`, 2026-10-25

The fifth SPECspeed benchmark mined on `niwot`. `829.abc_s` is the speed version of `729.abc_r` (the ABC
logic-synthesis and verification tool). It's single-threaded, so it was pinned with `taskset` to CPU 2,
the second such mine after [`853.ns3_s`](mining_results.853.ns3_s.2026-10-24.md).

## Headline result

**Nothing accepted: plain `-O3` stays the best (ratio 2.751).** But the mine only tried three ordinary
candidates, and `-flto`, which gave abc_r its gain, was never measured.

- **The shape excluded `-flto` and nine other candidates.** The corpus read `memory-bound` at 72.9%,
  above the 55% gate, so Phase 2 excluded every flag tagged only frontend-, compute- or backend-bound.
  abc_r (memory-bound 38.2%, low confidence) also never got `-flto` from its mine, and a follow-up found
  +2.49% to +3.10% (#2). A follow-up here is new opportunity #27.
- **PGO was attempted, since it's no longer skipped on shape (#25), and measured -0.64%** (CIs overlap).
  abc_r's PGO was about -4% to -9%, so the speed version loses less.
- **Pinned again, and very steady:** baseline CI ±0.21%, every confirmed CI ±0.6% or tighter.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 829.abc_s` (uncapped, queued after `835.gem5_s`) |
| Code | `main` at `9e0d86e` (later commits are doc-only) |
| Experiment id | 171 |
| Started / finished | 2026-10-25T08:18:12Z / 2026-10-25T11:09:51Z (2h52m) |
| Final status | `converged` |
| Trials | 27 (962-988) |
| Candidates screened / confirmed | 3 / 0 |
| Fast-tracked (M4) | none |
| Winning flags | `["-O3"]`, 0.0% |
| Thread placement | single-threaded, `taskset -c 2` |
| Guards | bandwidth gate 44.3-45.9 GB/s before every run, waited only before the first; no slow-rep reruns; no audit warnings |
| Power profile | `balanced`; CPU temp 74.0-78.0°C, package power 21.1-24.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 962 | warm-up (excluded from CI) | 2.752 |
| 963 | warm-up (excluded from CI) | 2.754 |
| 964 | calibration | 2.754 |
| 965 | calibration | 2.749 |
| 966 | calibration | 2.751 |
| 979 | recheck after Phase 4 | 2.748 (-0.12%, not flagged) |

Calibration mean **2.7513**, 95% CI **[2.746, 2.757]** (±0.21%).

**Shape: `memory-bound`, 72.9%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). That's a far clearer margin than abc_r's 38.2%, and the highest memory-bound reading of any mine on this
host. The next highest is zstd (64.0%), whose LTO and PGO check found nothing.

## Phase 2: ten exclusions

| Excluded | Tagged |
|---|---|
| `-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition` | frontend-bound |
| `-Ofast`, `-ffast-math` | compute-bound |
| `-funroll-loops` | compute- and backend-bound |
| `-fipa-pta` | backend-bound |
| `-mprefer-vector-width=256`, `=512` | high vectorization density |

That leaves `-fprefetch-loop-arrays`, `-fgraphite-identity` and `-march=native`. M4's memory-bound priors
(now including minizinc_s) had nothing at a majority of accepts, so nothing was fast-tracked.

## Phases 3 and 4

| Flags | Screening (vs. 2.7512) | Confirmation ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| `-fgraphite-identity` | 2.750 (-0.04%) | 2.754, 2.759, 2.747 | 2.753 | [2.738, 2.768] | +0.07% | reject |
| `-fprefetch-loop-arrays` | 2.752 (+0.03%) | 2.749, 2.754, 2.754 | 2.752 | [2.746, 2.759] | +0.03% | reject |
| `-march=native` | 2.738 (-0.48%) | 2.744, 2.744, 2.732 | 2.740 | [2.724, 2.757] | -0.40% | reject |

All three are flat.

## Phase 6 multipliers (on `-O3`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -fprofile-use` | 2.736, 2.738, 2.727 | 2.734 | [2.720, 2.748] | -0.64% | reject |
| Microarch | `-O3 -march=znver5` | 2.747, 2.744, 2.748 | 2.746 | [2.741, 2.751] | -0.19% | reject |
| Microarch | `-O3 -mtune=znver5` | 2.755, 2.759, 2.756 | 2.757 | [2.752, 2.762] | +0.21% | reject |
| Vector width | — | | | | | skipped (no deferred candidates) |

## Compared with `729.abc_r`

| | `729.abc_r` (2026-10-17, plus follow-ups) | `829.abc_s` (this run) |
|---|---|---|
| Copies / threads | 16 copies | 1 thread, pinned to CPU 2 |
| Shape | memory-bound 38.2% (low confidence) | memory-bound 72.9% |
| Mine's result | nothing accepted | nothing accepted |
| `-flto` | +2.49% to +3.10% (follow-up) | excluded on shape, not measured |
| PGO | about -4% to -9% | -0.64% (CIs overlap) |
| `-march` | `-march=znver5` +0.55% (re-measure) | `-march=native` -0.40%, `-march=znver5` -0.19% |

abc_r's LTO gain is the one thing this mine couldn't test. zstd's clear memory-bound shape was right to
exclude LTO, but abc_r's real LTO gain says abc might be different. That's #27.

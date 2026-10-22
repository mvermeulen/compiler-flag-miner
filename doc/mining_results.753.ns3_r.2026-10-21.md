# `cfm mine` results: 753.ns3_r on `niwot`, 2026-10-21

The thirteenth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the seventh `frontend-bound`
one. `753.ns3_r` (the ns-3 network simulator) was mined once on the old host
([`mining_results.753.ns3_r.2026-08-27.md`](mining_results.753.ns3_r.2026-08-27.md)), where `-flto` plus PGO
won by +37.99%.

## Headline result

**`-O3 -flto -fprofile-use`, +26.66% over plain `-O3`** (ratio 36.48 → 46.21). This is the same winning set
as on the old host, with a different split:

- **`-flto`: +21.40%**, the largest LTO gain on this host (omnetpp's +13.1% was next), and close to the old
  host's +23.3%. ns-3 is built from many small C++ modules with thin virtual and template layers between them,
  so whole-program inlining has a lot to remove.
- **PGO on top: +4.33%**, against +11.9% on the old host. That's the fourth frontend-bound benchmark where PGO
  adds clearly less here than there (opportunity #16).

Unlike gem5, PGO helps here, so there's no sign of the training-coverage problem.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 753.ns3_r` (uncapped, queued after the partial-training checks) |
| Code | `main` at `11e7c78` (later commits are doc-only) |
| Experiment id | 112 |
| Started / finished | 2026-10-21T21:00:47Z / 2026-10-22T03:06:17Z (6h06m) |
| Final status | `converged` |
| Trials | 43 (486-528) |
| Candidates screened / confirmed | 5 / 0 (plus 2 fast-tracked, 1 accepted) |
| Fast-tracked (M4) | `-march=native` (rejected), `-flto` (accepted) |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +26.66% |
| Power profile | `balanced`, unchanged; CPU temp 91.8-99.9°C, package power 20.0-29.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 486 | warm-up (excluded from CI) | 36.71 |
| 487 | warm-up (excluded from CI) | 36.04 |
| 488 | calibration | 36.43 |
| 489 | calibration | 36.44 |
| 490 | calibration | 36.57 |

Calibration mean **36.479**, 95% CI **[36.29, 36.66]** (±0.5%).

**Shape: `frontend-bound`, 60.7%**, `vectorization_density=moderate`, `allocation_pressure=low`, from the
corpus (`reference-matrix:amd-370-64gb`). This is the same corpus entry the old host's run used.

## Phase 2 filtering and M4

The same six exclusions as `735.gem5_r` (same shape family):

- compute-bound-tagged: `-funroll-loops`, `-Ofast`, `-ffast-math`
- memory-bound-tagged: `-fprefetch-loop-arrays`
- backend-bound-tagged: `-fipa-pta`, `-fgraphite-identity`

Moderate vectorization kept both `-mprefer-vector-width` settings in.

M4 fast-tracked `-march=native` (1 of 6 accepted, mean +7.21%) and `-flto` (4 of 5, mean +6.87%).

## Phase 3 screening (vs. most recent calibration rep, 36.57)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 491 | `-O3 -freorder-blocks-and-partition` | 36.50 | -0.17% | survived |
| 492 | `-O3 -freorder-functions` | 36.55 | -0.05% | survived |
| 493 | `-O3 -fno-semantic-interposition` | 36.45 | -0.30% | survived |
| 494 | `-O3 -mprefer-vector-width=256` | 36.44 | -0.36% | survived |
| 495 | `-O3 -mprefer-vector-width=512` | 36.39 | -0.49% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [36.29, 36.66])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 43.48, 44.21, 44.16 | 43.95 | [42.93, 44.97] | **+20.48%** | **accept** |
| `-mprefer-vector-width=512` | 36.52, 36.64, 36.79 | 36.65 | [36.32, 36.98] | +0.47% | reject |
| `-fno-semantic-interposition` | 36.44, 36.59, 36.91 | 36.65 | [36.05, 37.24] | +0.45% | reject |
| `-freorder-functions` | 36.73, 36.52, 36.36 | 36.54 | [36.07, 37.00] | +0.16% | reject |
| `-freorder-blocks-and-partition` | 36.21, 36.64, 36.69 | 36.52 | [35.86, 37.17] | +0.10% | reject |
| `-march=native` (fast-tracked) | 36.36, 36.59, 36.49 | 36.48 | [36.18, 36.78] | +0.00% | reject |
| `-mprefer-vector-width=256` | 36.46, 36.49, 36.29 | 36.41 | [36.15, 36.68] | -0.19% | reject |

- **`-march=native` was fast-tracked and rejected for the fifth frontend-bound benchmark in a row**
  (omnetpp, llvm, cppcheck, gem5, ns3). Its record in this cluster is now 1 of 7, and opportunity #15 has
  another case. The old host's ns3 run didn't fast-track it.
- The code-layout flags are flat again, as on every frontend-bound benchmark so far.

## Phase 5 combination

There's only one accepted flag, so the combination is `-O3 -flto` re-confirmed: **44.29** (44.20, 44.27, 44.40;
CI [44.04, 44.54]), +21.40%.

## Phase 6 multipliers

- **PGO: accepted, +4.33% on top of `-O3 -flto`** (46.10, 46.56, 45.95; mean 46.21, CI [45.41, 47.00]), and
  +26.66% overall. The CI's lower bound clears the `-O3 -flto` upper bound (44.54) comfortably.
- **Microarch: attempted on `-O3 -flto -fprofile-use`, both rejected.**

  | Added flag | Ratios | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|---|
  | `-march=znver5` | 46.31, 46.48, 46.51 | 46.43 | [46.16, 46.71] | +0.50% | reject (CIs overlap) |
  | `-mtune=znver5` | 45.63, 46.31, 45.48 | 45.81 | [44.71, 46.90] | -0.87% | reject |

None of the trials logged an audit warning.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 7 | 5 | +9.16% |
| `-flto` | 6 | 5 | +9.13% |
| `-march=native` | 7 | 1 | +6.18% |
| `-march=znver5` | 6 | 0 | +0.17% |
| `-mtune=znver5` | 6 | 0 | +0.13% |
| `-freorder-blocks-and-partition` | 7 | 0 | +0.10% |
| `-mprefer-vector-width=512` | 4 | 0 | +0.07% |
| `-freorder-functions` | 7 | 0 | +0.07% |
| `-fno-semantic-interposition` | 7 | 0 | +0.00% |
| `-mprefer-vector-width=256` | 4 | 0 | -0.10% |

## Follow-ups

1. Opportunity #16: PGO's gain on top of LTO is again much smaller here than on the old host (+4.3% vs +11.9%).
   ns3 is now the largest gap of the four.
2. Opportunity #15: `-march=native` fast-tracked and rejected again (1 of 7 now). Its mean is still +6.18%,
   carried by stockfish's single +48% accept.

# `cfm mine` results: 735.gem5_r on `niwot`, 2026-10-20

The twelfth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the sixth `frontend-bound` one.
`735.gem5_r` (the gem5 architecture simulator) was mined once on the old host
([`mining_results.735.gem5_r.2026-08-27.md`](mining_results.735.gem5_r.2026-08-27.md)), where `-flto` won by
+13.62% and PGO was rejected.

## Headline result

**`-O3 -flto`, +11.01% over plain `-O3`** (ratio 34.06 → 37.81). The same shape as on the old host:

- **`-flto` accepted**, a little smaller than the old host's +13.62%.
- **PGO rejected as a regression: -10.59% on top of `-O3 -flto`**, which gives back the whole LTO gain
  (33.81, right at the `-O3` baseline). On the old host it was -6.7%. gem5 is the only benchmark on either host
  where PGO clearly hurts (it was flat on stockfish here, -0.1%), and it does so on both.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 735.gem5_r` (uncapped, queued after `721.gcc_r`) |
| Code | `main` at `11e7c78` (later commits are doc-only) |
| Experiment id | 57 |
| Started / finished | 2026-10-20T18:28:56Z / 2026-10-21T01:41:00Z (7h12m) |
| Final status | `converged` |
| Trials | 43 (389-431) |
| Candidates screened / confirmed | 5 / 0 (plus 2 fast-tracked, 1 accepted) |
| Fast-tracked (M4) | `-march=native` (rejected), `-flto` (accepted) |
| Winning flags | `["-O3", "-flto"]`, +11.01% |
| Power profile | `balanced`, unchanged; CPU temp 92.6-96.0°C, package power 17.1-19.1 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 389 | warm-up (excluded from CI) | 33.88 |
| 390 | warm-up (excluded from CI) | 34.25 |
| 391 | calibration | 33.64 |
| 392 | calibration | 34.51 |
| 393 | calibration | 34.04 |

Calibration mean **34.062**, 95% CI **[32.98, 35.15]** (±3.2%). That's the widest baseline on this host. There
was no trend, just scatter: gem5's run-to-run noise is about ±1% per trial, and every candidate shows it too
(spreads of 0.3-0.6 within 3 reps). The wide CI decided nothing. Every rejected candidate was within ±1% of
baseline, and `-flto`'s and PGO's effects are each about 10%.

**Shape: `frontend-bound`, 60.3%**, `vectorization_density=moderate`, `allocation_pressure=moderate`, from
the corpus (`reference-matrix:amd-370-64gb`).

## Phase 2 filtering and M4

The frontend-bound, moderate-vectorization shape excluded six candidates:

- compute-bound-tagged: `-funroll-loops`, `-Ofast`, `-ffast-math`
- memory-bound-tagged: `-fprefetch-loop-arrays`
- backend-bound-tagged: `-fipa-pta`, `-fgraphite-identity`

Moderate vectorization kept both `-mprefer-vector-width` settings in, unlike omnetpp, llvm and cppcheck.

M4 fast-tracked `-march=native` (1 of 5 accepted, mean +8.62%) and `-flto` (3 of 4, mean +5.93%).

## Phase 3 screening (vs. most recent calibration rep, 34.04)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 394 | `-O3 -freorder-blocks-and-partition` | 34.08 | +0.10% | survived |
| 395 | `-O3 -freorder-functions` | 34.10 | +0.15% | survived |
| 396 | `-O3 -fno-semantic-interposition` | 33.92 | -0.38% | survived |
| 397 | `-O3 -mprefer-vector-width=256` | 33.96 | -0.25% | survived |
| 398 | `-O3 -mprefer-vector-width=512` | 34.09 | +0.14% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [32.98, 35.15])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 37.49, 37.81, 37.73 | 37.68 | [37.26, 38.09] | **+10.61%** | **accept** |
| `-march=native` (fast-tracked) | 34.16, 34.15, 34.03 | 34.11 | [33.93, 34.29] | +0.15% | reject |
| `-mprefer-vector-width=512` | 33.74, 34.16, 33.95 | 33.95 | [33.43, 34.47] | -0.33% | reject |
| `-mprefer-vector-width=256` | 34.05, 33.56, 34.10 | 33.90 | [33.16, 34.65] | -0.46% | reject |
| `-freorder-functions` | 34.18, 33.69, 33.83 | 33.90 | [33.27, 34.53] | -0.49% | reject |
| `-freorder-blocks-and-partition` | 33.72, 34.03, 33.81 | 33.85 | [33.47, 34.24] | -0.61% | reject |
| `-fno-semantic-interposition` | 33.86, 33.99, 33.38 | 33.74 | [32.95, 34.54] | -0.94% | reject |

- **`-march=native` was fast-tracked and rejected for the fourth frontend-bound benchmark in a row**
  (omnetpp, llvm, cppcheck, gem5). Its record in this cluster is now 1 of 6, and opportunity #15 has its
  sixth case on this host.

## Phase 5 combination

There's only one accepted flag, so the combination is `-O3 -flto` re-confirmed: **37.81** (38.03, 37.38, 38.02;
CI [36.89, 38.74]), +11.01%.

## Phase 6 multipliers

- **PGO: attempted on `-O3 -flto`, rejected at -10.59%** (33.96, 33.95, 33.51; mean 33.81, CI [33.18, 34.44]).
  The audit confirms `-fprofile-use` compiled in, and every rep passed validate, so this is a real result,
  not a broken build. PGO took back all of LTO's gain and landed at the `-O3` level.
- **Microarch: attempted on `-O3 -flto`, both rejected.**

  | Added flag | Ratios | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|---|
  | `-march=znver5` | 38.53, 37.92, 38.01 | 38.15 | [37.33, 38.97] | +0.91% | reject (CIs overlap) |
  | `-mtune=znver5` | 37.30, 37.72, 37.24 | 37.42 | [36.77, 38.08] | -1.03% | reject |

None of the trials logged an audit warning.

**Why might PGO hurt gem5?** The likeliest reading, also suggested on the old host, is an unrepresentative
training run. gem5 is a configurable simulator, and which models and code paths are hot depends on the
simulated system. If SPEC's train workload exercises different paths from the reference workload, GCC marks
the reference run's hot code as cold and optimizes it for size, which would cost about this much. That's
untested. GCC's `-fprofile-partial-training` exists for this case: it optimizes code the training run never
reached as if there were no profile, instead of as cold. Added to the opportunity list as #21.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 6 | 4 | +9.97% |
| `-march=native` | 6 | 1 | +7.21% |
| `-flto` | 5 | 4 | +6.87% |
| `-mtune=znver5` | 5 | 0 | +0.32% |
| `-freorder-blocks-and-partition` | 6 | 0 | +0.10% |
| `-march=znver5` | 5 | 0 | +0.10% |
| `-freorder-functions` | 6 | 0 | +0.05% |
| `-mprefer-vector-width=512` | 3 | 0 | -0.06% |
| `-fno-semantic-interposition` | 6 | 0 | -0.08% |
| `-mprefer-vector-width=256` | 3 | 0 | -0.08% |

## Follow-ups

1. **PGO with `-fprofile-partial-training`** on top of `-O3 -flto`, interleaved against `-O3 -flto`. If the
   regression is a training-coverage problem, this should remove it and might turn it into a gain (#21).
2. Opportunity #15: `-march=native` fast-tracked and rejected again (1 of 6 now).

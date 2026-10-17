# `cfm mine` results: 708.sqlite_r on `niwot`, 2026-10-17

The third mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), the first mine of `708.sqlite_r` on
either host, and the first run since PR #47 fixed the reference-matrix lookup for host-prefixed SPEC
configs. By choice, the shape came from the published corpus rather than a local measurement.

## Headline result

**`-O3 -fprefetch-loop-arrays`, +1.76% over plain `-O3`** (ratio 24.27 → 24.70). A small win, but a clean
one: the Phase 5 CI ([24.62, 24.78]) doesn't overlap the baseline's ([24.18, 24.36]), and it clears the 1.0%
`MIN_PRACTICAL_SIGNIFICANCE_PCT` bar. **It's the first accept for `-fprefetch-loop-arrays` on either host.**
On the old host it had only ever been rejected (for example `721.gcc_r`). Every other candidate, including
`-march=native` and both microarch-multiplier flags, was rejected.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 708.sqlite_r` (uncapped) |
| Code | PR #47's branch (identical to `main` at `ee80a98` once merged mid-run) |
| Experiment id | 12 |
| Started / finished | 2026-10-17T11:04:50Z / 2026-10-17T14:36:25Z (3h32m) |
| Final status | `converged` |
| Trials | 34 (92-125) |
| Candidates screened / confirmed | 5 / 1 |
| Fast-tracked (M4) | none (no `memory-bound` priors on this host yet) |
| Winning flags | `["-O3", "-fprefetch-loop-arrays"]`, +1.76% |
| Power profile | `balanced`, unchanged; CPU temp 90.8-93.1°C, package power 20.0-22.1 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 92 | warm-up (excluded from CI) | 24.32 |
| 93 | warm-up (excluded from CI) | 24.28 |
| 94 | calibration | 24.28 |
| 95 | calibration | 24.30 |
| 96 | calibration | 24.23 |

Calibration mean **24.270**, 95% CI **[24.18, 24.36]**. The five reps span 0.4%, the tightest baseline yet
on this host. That's what made a +1.76% win resolvable at all: on the old host's wider, drifting baselines,
an effect this small would likely have been lost in the CI.

**Shape: `memory-bound`, 39.7%** (low confidence), `vectorization_density=moderate`,
`allocation_pressure=moderate`, from the reference-matrix corpus (`reference-matrix:amd-370-64gb`). This is
the first `niwot` run whose corpus lookup actually matched, so PR #47's fix is confirmed in a real run. No
local characterization trial was spent. The baseline has 5 trials instead of the previous runs' 6.

## Phase 2 filtering

The memory-bound shape excluded eight candidates: `-flto`, `-freorder-blocks-and-partition`,
`-freorder-functions`, `-fno-semantic-interposition` (frontend-bound-tagged), `-funroll-loops`, `-Ofast`,
`-ffast-math`, and `-fipa-pta`. PGO was skipped at Phase 6 for the same reason. Because the shape came from
another machine's low-confidence data, this run can't say whether LTO or PGO would have helped sqlite here.
That's the trade-off accepted when choosing the published shape.

## Phase 3 screening (vs. most recent calibration rep, 24.23)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 97 | `-O3 -fprefetch-loop-arrays` | 24.71 | +2.00% | survived |
| 98 | `-O3 -fgraphite-identity` | 24.21 | -0.07% | survived |
| 99 | `-O3 -mprefer-vector-width=256` | 24.24 | +0.05% | survived |
| 100 | `-O3 -mprefer-vector-width=512` | 24.28 | +0.22% | survived |
| 101 | `-O3 -march=native` | 24.14 | -0.36% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [24.18, 24.36])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-fprefetch-loop-arrays` | 24.78 | [24.69, 24.86] | **+2.08%** | **accept** |
| `-fgraphite-identity` | 24.43 | [24.31, 24.56] | +0.67% | reject (CIs overlap) |
| `-mprefer-vector-width=256` | 24.39 | [24.08, 24.69] | +0.48% | reject |
| `-mprefer-vector-width=512` | 24.20 | [24.13, 24.26] | -0.30% | reject |
| `-march=native` | 24.14 | [23.71, 24.57] | -0.53% | reject |

`-fgraphite-identity`'s CI only barely overlaps the baseline's: its lower bound is 24.31 and the baseline's
upper bound is 24.36. Even without the overlap, +0.67% would fall short of the 1.0% practical-significance
bar. So it's a reject either way.

`-march=native` does nothing for sqlite. That's the third distinct `-march=native` outcome on this host:
+48% (stockfish), -4.8% (cpython), flat (sqlite).

## Phase 5 combination

There's only one accepted flag, so the combination is just `-O3 -fprefetch-loop-arrays` re-confirmed:
**24.70** (CI [24.62, 24.78]), +1.76%. That's slightly below Phase 4's +2.08%, but both are clear of baseline.
The audit confirms `-fprefetch-loop-arrays` was literally compiled in.

## Phase 6 multipliers

- **PGO: skipped** (memory-bound shape contradicts both of `-fprofile-use`'s `topdown_signals`).
- **Microarch: attempted, both rejected.** Both flags were layered on `-O3 -fprefetch-loop-arrays`:

  | Added flag | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|
  | `-march=znver5` | 24.24 | [23.99, 24.49] | **-1.84%** | reject |
  | `-mtune=znver5` | 24.47 | [24.24, 24.70] | -0.91% | reject |

  `-march=znver5`'s CI lies entirely below the winner's ([24.62, 24.78]), so it's a measured regression, not
  noise. That's consistent with `-march=native` (effectively the same flag on this host) being slightly
  negative at Phase 4. One possible reading is that the znver5 cost model changes or drops the software
  prefetches `-fprefetch-loop-arrays` inserts. This run doesn't test that.

## Knowledge table after this run

These are the first `memory-bound` rows on `niwot`: `-fprefetch-loop-arrays` (accepted, +2.08%),
`-fgraphite-identity`, both `-mprefer-vector-width` settings, `-march=native`, `-march=znver5`, and
`-mtune=znver5` (all rejected). `729.abc_r`, mined next and also corpus-characterized as memory-bound, will be
the first to use them: `-fprefetch-loop-arrays` should be fast-tracked.

## Follow-ups

1. **`--param prefetch-latency=N`** is the catalog's natural companion to `-fprefetch-loop-arrays`, but every
   run skips it as an "unresolved template placeholder". Its catalog notes suggest sweeping 200/300/400. Now
   that `-fprefetch-loop-arrays` has a real accept, sqlite is the obvious place to try that sweep, for example
   with `cfm measure 708.sqlite_r --flags="-O3 -fprefetch-loop-arrays --param prefetch-latency=300"`.
2. A local-shape cross-check would show whether LTO and PGO were really ruled out correctly, given that the
   corpus shape is low-confidence (memory-bound 39.7%). Options: one `deep-cpu` characterization, or a direct
   `cfm measure` of `-O3 -flto`.

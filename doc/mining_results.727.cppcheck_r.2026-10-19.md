# `cfm mine` results: 727.cppcheck_r on `niwot`, 2026-10-19

The ninth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the fifth `frontend-bound` one.
`727.cppcheck_r` (the Cppcheck static analyzer) was mined twice on the old host
([`2026-08-24`](mining_results.727.cppcheck_r.2026-08-24.md),
[`2026-08-25`](mining_results.727.cppcheck_r.2026-08-25.md)). The second run, after the warm-up fix, accepted
PGO at +10.79% and rejected `-flto` at +4.20%.

## Headline result

**`-O3 -fprofile-use`, +7.78% over plain `-O3`** (ratio 24.85 → 26.79). This is the same shape of result as on
the old host: PGO alone wins, and `-flto` doesn't make the cut.

- **`-flto` cleared the CI test but missed the 1.0% bar.** It read +0.96% with a CI fully clear of the
  baseline's, a genuine but sub-threshold effect. It's the first *positive* result on this host to be rejected
  only by `MIN_PRACTICAL_SIGNIFICANCE_PCT`. The two earlier CI-clear rejects, cpython's `-march=native` and
  sqlite's `-march=znver5`, were regressions.
- Because `-flto` didn't win, PGO was layered on plain `-O3`. **`-O3 -flto -fprofile-use` was never measured.**
  On omnetpp and llvm here, LTO and PGO stacked, so that combination is the obvious follow-up.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 727.cppcheck_r` (uncapped, queued after `723.llvm_r`) |
| Code | `main` at `11e7c78` |
| Experiment id | 42 |
| Started / finished | 2026-10-19T23:34:04Z / 2026-10-20T03:11:39Z (3h38m) |
| Final status | `converged` |
| Trials | 32 (297-328) |
| Candidates screened / confirmed | 3 / 0 (plus 2 fast-tracked, both rejected) |
| Fast-tracked (M4) | `-march=native` (rejected), `-flto` (rejected) |
| Winning flags | `["-O3", "-fprofile-use"]`, +7.78% |
| Power profile | `balanced`, unchanged; CPU temp 89.5-96.0°C, package power 23.1-28.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 297 | warm-up (excluded from CI) | 24.88 |
| 298 | warm-up (excluded from CI) | 24.81 |
| 299 | calibration | 24.91 |
| 300 | calibration | 24.83 |
| 301 | calibration | 24.82 |

Calibration mean **24.854**, 95% CI **[24.73, 24.98]** (±0.5%). All five reps fell within 0.4% of each other,
with no settling. The old host's first cppcheck run, by contrast, is the one that exposed the settling-baseline
problem.

**Shape: `frontend-bound`, 71.0%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`). This is the clearest frontend-bound margin on this host. Phase 2
excluded the same eight candidates as on omnetpp and llvm.

## Phase 3 screening (vs. most recent calibration rep, 24.82)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 302 | `-O3 -freorder-blocks-and-partition` | 24.77 | -0.23% | survived |
| 303 | `-O3 -freorder-functions` | 24.76 | -0.26% | survived |
| 304 | `-O3 -fno-semantic-interposition` | 24.69 | -0.54% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [24.73, 24.98])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 25.11, 25.11, 25.06 | 25.09 | [25.02, 25.17] | +0.96% | **reject (below 1.0% bar; CIs don't overlap)** |
| `-march=native` (fast-tracked) | 24.95, 24.87, 24.79 | 24.87 | [24.67, 25.07] | +0.07% | reject |
| `-freorder-blocks-and-partition` | 24.79, 24.93, 24.83 | 24.85 | [24.67, 25.02] | -0.03% | reject |
| `-fno-semantic-interposition` | 24.81, 24.72, 24.89 | 24.81 | [24.60, 25.02] | -0.19% | reject |
| `-freorder-functions` | 24.68, 24.74, 24.72 | 24.72 | [24.64, 24.79] | -0.56% | reject |

- **`-flto` was rejected on practical significance.** Its CI lower bound (25.02) is clear of the baseline's
  upper bound (24.98), so the statistical test passed. +0.96% just misses the 1.0% bar. On the old host it read
  +4.20% and was rejected for CI overlap instead. That's the bar working as designed, but it also means `-flto`
  never got to stack with PGO here.
- **`-march=native` was fast-tracked and rejected for the third frontend-bound benchmark in a row**: omnetpp
  +0.35%, llvm -0.85%, cppcheck +0.07%. Its record in this cluster is now 1 of 5.

## Phase 5 combination

Nothing was accepted at Phase 4, so the Phase 5 winner is plain `-O3`.

## Phase 6 multipliers

- **PGO: accepted, +7.78% on top of plain `-O3`** (26.73, 26.72, 26.91; mean 26.79, CI [26.52, 27.06]). That's
  below the old host's +10.79%, the third frontend-bound benchmark where PGO gained less here than there
  (opportunity #16). Each PGO trial took about 10 minutes, against about 5 for plain `-O3`.
- **Microarch: attempted on `-O3 -fprofile-use`, both rejected.**

  | Added flag | Ratios | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|---|
  | `-march=znver5` | 26.46, 26.56, 26.64 | 26.55 | [26.32, 26.78] | -0.88% | reject |
  | `-mtune=znver5` | 26.73, 26.73, 26.64 | 26.70 | [26.58, 26.82] | -0.33% | reject |

None of the trials logged an audit warning.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 5 | 4 | +14.08% |
| `-march=native` | 5 | 1 | +8.62% |
| `-flto` | 4 | 3 | +5.93% |
| `-mtune=znver5` | 4 | 0 | +0.66% |
| `-freorder-blocks-and-partition` | 5 | 0 | +0.24% |
| `-freorder-functions` | 5 | 0 | +0.16% |
| `-mprefer-vector-width=256` | 2 | 0 | +0.12% |
| `-fno-semantic-interposition` | 5 | 0 | +0.10% |
| `-mprefer-vector-width=512` | 2 | 0 | +0.08% |
| `-march=znver5` | 4 | 0 | -0.10% |

## Follow-ups

1. **Measure `-O3 -flto -fprofile-use`** against `-O3 -fprofile-use`, interleaved. `-flto`'s +0.96% is real
   but sub-threshold alone. On omnetpp and llvm, LTO and PGO compounded, and LTO's effect here might be bigger
   with profile data driving its inlining. Added to the [opportunity list](opportunities_niwot.md).
2. **A pipeline gap this run shows:** a flag rejected only by the practical-significance bar, with its CI
   clear of baseline's, is never offered to Phase 6 as part of the base. A "near-miss" rule could carry it into
   the PGO trial as a second variant.

## Follow-up: LTO and PGO together (2026-10-22)

Opportunity #18, the check follow-up 1 above called for. Three interleaved rounds of four flag sets, each a
`cfm measure` run at its default 3 iterations (median), experiments 126-137, 14:24Z-17:49Z.

| Flags | Round 1 | Round 2 | Round 3 | Mean | 95% CI | vs control | vs mine's `-O3` (24.85) |
|---|---|---|---|---|---|---|---|
| `-O3` (control) | 24.86 | 25.01 | 24.88 | 24.92 | [24.71, 25.12] | — | +0.25% |
| `-O3 -flto` | 25.12 | 25.12 | 25.02 | 25.09 | [24.95, 25.23] | +0.70% | +0.95% |
| `-O3 -fprofile-use` | 26.77 | 26.76 | 26.63 | 26.72 | [26.52, 26.93] | +7.25% | +7.51% |
| `-O3 -flto -fprofile-use` | 27.44 | 27.42 | 27.41 | 27.42 | [27.38, 27.46] | **+10.06%** | **+10.33%** |

- **LTO and PGO stack here too.** `-flto` alone is still small (+0.7%, CIs overlapping the control, close to
  the mine's +0.96%). On top of PGO it adds **+2.62%** (27.42 against 26.72), with the CIs clear of each other
  and every round above every PGO-only round. With a profile, LTO's cross-module inlining has better
  information about which calls are hot.
- **cppcheck's winner is now `-O3 -flto -fprofile-use`, +10.33% over the mine's `-O3`**, against the mine's
  +7.78%. Both reference points agree: the control sat within 0.3% of the mine's `-O3`, and PGO alone
  (26.72) within 0.3% of the mine's PGO result (26.79).
- Every build passed validate, and no audit logged a warning.

For the pipeline, this is the case opportunity #19 describes: the mine's `-flto` reject was correct on its own
(+0.96% is under the 1% bar), but dropping it before Phase 6 meant PGO never ran on the better base. On the
old host the same thing happened (`-flto` +4.20% rejected, then PGO on plain `-O3`).

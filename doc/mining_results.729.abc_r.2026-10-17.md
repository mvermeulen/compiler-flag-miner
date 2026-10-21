# `cfm mine` results: 729.abc_r on `niwot`, 2026-10-17

The fourth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the first mine of `729.abc_r`
(ABC, logic synthesis and verification) on either host. It's also the first `memory-bound` run on this host
to use cross-benchmark priors: `-fprefetch-loop-arrays` was fast-tracked on `708.sqlite_r`'s accept from
earlier the same day.

## Headline result

**Nothing accepted. `-O3` alone stays the best setting (0.0% gain).** Every candidate was rejected,
including the fast-tracked `-fprefetch-loop-arrays` (+0.87%), so sqlite's small win didn't carry over. All
five candidates measured nominally positive (+0.87% to +1.57%), but none had a CI clear of the baseline's.
The evidence below points to the baseline sampling slightly low rather than five flags each gaining about 1%.
Either way, nothing here is a resolvable win.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 729.abc_r` (uncapped, queued to start when `708.sqlite_r` exited) |
| Code | `main` at `ee80a98` (PR #47 merged) |
| Experiment id | 13 |
| Started / finished | 2026-10-17T14:36:46Z / 2026-10-17T16:36:26Z (2h00m) |
| Final status | `converged` |
| Trials | 22 (126-147) |
| Candidates screened / confirmed | 2 / 0 |
| Fast-tracked (M4) | `-fprefetch-loop-arrays` (rejected) |
| Winning flags | `["-O3"]`, 0.0% |
| Power profile | `balanced`, unchanged; CPU temp 85.4-91.9°C, package power 21.0-28.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 126 | warm-up (excluded from CI) | 27.46 |
| 127 | warm-up (excluded from CI) | 27.73 |
| 128 | calibration | 27.62 |
| 129 | calibration | 27.31 |
| 130 | calibration | 27.36 |

Calibration mean **27.427**, 95% CI **[27.01, 27.84]**, a ±1.5% band. That's much wider than
`708.sqlite_r`'s (±0.4%), and it sets the bar every candidate here had to clear.

**Shape: `memory-bound`, 38.2%** (low confidence; `frontend-bound` is a close alternative at 34.1%),
`vectorization_density=low`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). No local characterization trial was run.

### Was the baseline low?

| | Ratio |
|---|---|
| Calibration mean (the bar used) | 27.43 |
| All five baseline reps including warm-ups | 27.50 |
| Mean of all 15 candidate trials (five different flag sets) | 27.76 |
| Lowest single candidate trial | 27.56 |

Two of the three calibration reps (27.31, 27.36) are below **every** one of the 15 candidate trials, across
five unrelated flag changes. It's much more likely that `-O3`'s true level here is around 27.6, and that
calibration happened to catch two low runs, than that five unrelated flags all gain 0.9-1.6%. Neither the
per-trial CPU temperature nor the package-power sample tracks the ratio (for example, trial 129 at 27.31 sits
at 87.4°C and 25.0 W, the same range as the candidates), so there's no environmental explanation in the data.

The effect is the same "baseline center biases every delta's sign" failure mode `777.zstd_r` showed on the old
host (CLAUDE.md, 2026-08-25 traps entry), this time in the positive direction. It didn't change any verdict:
with a true baseline near 27.6, every candidate reads about +0.5% or less, still a reject. But it inflates the
reported deltas, and it fed those inflated deltas into the knowledge table's running means (below).

## Phase 2 filtering

Ten candidates were excluded by the memory-bound, low-vectorization shape: `-flto`,
`-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition`, `-funroll-loops`,
both `-mprefer-vector-width` settings (excluded because `vectorization_density=low`), `-Ofast`,
`-ffast-math`, and `-fipa-pta`. `-fprefetch-loop-arrays` went to the M4 fast track, and two candidates went to
screening.

## Phase 3 screening (vs. most recent calibration rep, 27.36)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 131 | `-O3 -fgraphite-identity` | 27.84 | +1.76% | survived |
| 132 | `-O3 -march=native` | 27.69 | +1.22% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [27.01, 27.84])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-fgraphite-identity` | 27.83 | [27.40, 28.25] | +1.45% | reject (CIs overlap) |
| `-march=native` | 27.68 | [27.30, 28.05] | +0.91% | reject |
| `-fprefetch-loop-arrays` (fast-tracked) | 27.67 | [27.50, 27.83] | +0.87% | reject |

M4 worked as designed: `-fprefetch-loop-arrays` skipped screening on sqlite's +2.08% prior, then was rejected
on abc's own data.

## Phase 5 combination

Nothing was accepted, so there was nothing to combine.

## Phase 6 multipliers

- **PGO: skipped** (memory-bound shape).
- **Microarch: attempted on plain `-O3`, both rejected.**

  | Flags | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|
  | `-O3 -march=znver5` | 27.75 | [27.65, 27.85] | +1.19% | reject |
  | `-O3 -mtune=znver5` | 27.86 | [27.33, 28.38] | +1.57% | reject |

  `-march=znver5` comes closest to an accept here. Its tight CI overlaps the baseline's upper bound by only
  about 0.01 (27.65 against 27.84). Against a re-measured baseline near 27.6 it would read about +0.5%,
  under the 1.0% bar either way.

All five audits confirm the flags under test were compiled in.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprefetch-loop-arrays` | 2 | 1 | +1.48% |
| `-fgraphite-identity` | 2 | 0 | +1.06% |
| `-mprefer-vector-width=256` | 1 | 0 | +0.48% |
| `-mtune=znver5` | 2 | 0 | +0.33% |
| `-march=native` | 2 | 0 | +0.19% |
| `-mprefer-vector-width=512` | 1 | 0 | -0.30% |
| `-march=znver5` | 2 | 0 | -0.33% |

Because of the low-baseline effect, this run's contributions are probably about 1 point optimistic per flag.

## Follow-up re-measure: `-O3` vs `-O3 -march=znver5` (2026-10-18)

Three interleaved rounds of standalone `cfm measure` trials (experiments 14-19, 18:39-20:05Z), alternating
`-O3` and `-O3 -march=znver5`. All 6 built and passed `--action=validate`.

| Flags | Ratios | Mean | 95% CI | vs `-O3` |
|---|---|---|---|---|
| `-O3` | 27.66, 27.46, 27.56 | 27.56 | [27.31, 27.81] | — |
| `-O3 -march=znver5` | 27.62, 27.73, 27.79 | 27.71 | [27.50, 27.92] | **+0.55%** |

**The mine's verdict stands: nothing here clears +1%.**

- `-march=znver5` reads +0.55%. Its CI overlaps `-O3`'s, and it's below the 1.0% practical-significance bar,
  so it's still a reject.
- `-O3`'s true level is about 27.56. The mine's calibration mean (27.43) was about 0.5% low, not the ~1%
  estimated above. The mine's deltas were inflated by about half a point, and so were its knowledge-table
  means.
- `-march=znver5` here (27.71) matches the mine's own measurement (27.75), so the candidate trials were
  fine. Only the baseline was off.

## Follow-ups

1. ~~Interleaved re-measure of `-O3` and `-O3 -march=znver5`~~: done, see above. +0.55%, reject stands.
2. Same low-confidence-corpus caveat as `708.sqlite_r`: the corpus put abc at memory-bound 38.2%, with
   frontend-bound close behind at 34.1%, and LTO and PGO were excluded on that basis. A local `deep-cpu`
   characterization would show whether this host agrees.
3. A design question raised by this run, not specific to abc: a 3-rep calibration CI can land low or high by
   about 1% on a benchmark this noisy. Re-running one or two `-O3` reps at the end of Phase 4 would detect
   that kind of baseline offset cheaply.

## Follow-up: LTO and PGO (2026-10-21)

Opportunity #2. The mine never tried `-flto` or PGO, because the low-confidence memory-bound shape (38.2%)
excluded both. This check measured them directly: three interleaved rounds of four flag sets, each a
`cfm measure` run at its default 3 iterations (median), experiments 70-81, 05:12Z-08:37Z.

| Flags | Round 1 | Round 2 | Round 3 | Mean | 95% CI | vs control | vs mine's `-O3` (27.43) |
|---|---|---|---|---|---|---|---|
| `-O3` (control) | 27.28 | 27.25 | 27.26 | 27.27 | [27.22, 27.31] | — | -0.60% |
| `-O3 -flto` | 28.12 | 28.17 | 28.05 | 28.11 | [27.96, 28.26] | **+3.10%** | **+2.49%** |
| `-O3 -fprofile-use` | 26.10 | 26.12 | 26.46 | 26.22 | [25.73, 26.72] | -3.82% | -4.40% |
| `-O3 -flto -fprofile-use` | 25.53 | 25.87 | 26.00 | 25.80 | [25.20, 26.40] | -5.38% | -5.94% |

- **LTO is a real win, +3.1%,** CI clear of the control's and of the 1% bar. abc is spread across many
  translation units (it's a full logic-synthesis system), so cross-module inlining has something to work on.
- **PGO is a real loss, about -4%, with or without LTO.** It's the second benchmark on this host where PGO
  regresses, after `735.gem5_r`. abc is like gem5 in one relevant way: a large system whose hot code depends
  on which commands the script runs, so SPEC's training run may exercise different paths from the reference
  run. An interleaved `-fprofile-partial-training` check is queued for both (#21).
- **abc's winner is now `-O3 -flto`, +2.49% over the mine's `-O3`** (the mine accepted nothing). The control
  here measured 0.6% below the mine's baseline, so against this run's own control the gain is +3.10%; the host
  page uses the more conservative figure.
- Every build passed validate, and no audit logged a warning.

## Follow-up: PGO with `-fprofile-partial-training` (2026-10-21)

Opportunity #21, the same check as `735.gem5_r`'s
([write-up](mining_results.735.gem5_r.2026-10-20.md#follow-up-pgo-with--fprofile-partial-training-2026-10-21)).
Three interleaved rounds of three flag sets on top of the `-O3 -flto` winner, each a `cfm measure` run at its
default 3 iterations (median), experiments 103-111, 18:08Z-20:59Z.

| Flags | Round 1 | Round 2 | Round 3 | Mean | 95% CI | vs control | vs mine's `-O3` (27.43) |
|---|---|---|---|---|---|---|---|
| `-O3 -flto` (control) | 28.21 | 28.04 | 27.85 | 28.04 | [27.59, 28.48] | — | +2.22% |
| `-O3 -flto -fprofile-use` | 25.51 | 25.61 | 25.61 | 25.58 | [25.43, 25.73] | -8.77% | -6.75% |
| `-O3 -flto -fprofile-use -fprofile-partial-training` | 27.15 | 26.97 | 27.00 | 27.04 | [26.80, 27.28] | -3.54% | -1.40% |

- **Plain PGO on top of LTO regresses again**, -8.8% against the control. The previous check had it at
  -8.2% (25.80 against 28.11).
- **`-fprofile-partial-training` recovers about 60% of the loss but not all of it.** It's still -3.5%
  below `-O3 -flto`, with the CIs clear of each other, in every round. That's different from gem5, where the
  flag removed the whole regression. On abc, poor training coverage explains only part of PGO's loss. What's
  left is a loss in code the training run *did* reach, so the train workload's hot paths differ in weight
  from the reference run's, not just in which ones run at all.
- **abc's winner stays `-O3 -flto`** (+2.49% on the host page). The control matched the previous check's
  `-O3 -flto` (28.04 against 28.11).
- The audit confirms `-fprofile-use` and `-fprofile-partial-training` compiled in. Every build passed validate,
  and no audit logged a warning.

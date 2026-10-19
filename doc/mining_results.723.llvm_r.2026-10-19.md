# `cfm mine` results: 723.llvm_r on `niwot`, 2026-10-19

The eighth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the fourth `frontend-bound` one.
`723.llvm_r` (the LLVM compiler) was mined once on the old host
([`mining_results.723.llvm_r.2026-08-26.md`](mining_results.723.llvm_r.2026-08-26.md)), where `-flto` plus PGO
won by +32.23%.

## Headline result

**`-O3 -flto -fprofile-use`, +24.83% over plain `-O3`** (ratio 25.83 → 32.24). This is the same winning set
as on the old host and on `710.omnetpp_r`/`714.cpython_r` here. The split is different, though:

- **`-flto`: +1.43%.** That's the smallest accepted LTO gain on either host: +5.9% on the old host's llvm, and
  +13.1% on omnetpp here.
- **PGO on top: +23.07%.** That's close to the old host's +24.9%. On omnetpp and cpython, by contrast, PGO
  added clearly less on this host than on the old one.

So llvm's gap to the old host (+24.8% vs +32.2%) comes from LTO, not PGO, which is the opposite of omnetpp.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 723.llvm_r` (uncapped) |
| Code | `main` at `1325e24` |
| Experiment id | 41 |
| Started / finished | 2026-10-19T13:56:49Z / 2026-10-19T23:33:29Z (9h37m) |
| Final status | `converged` |
| Trials | 35 (262-296) |
| Candidates screened / confirmed | 3 / 1 (plus 2 fast-tracked) |
| Fast-tracked (M4) | `-march=native` (rejected), `-flto` (accepted) |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +24.83% |
| Power profile | `balanced`, unchanged; CPU temp 87.9-93.8°C, package power 18.1-20.1 W |

The longest run on this host so far. Trial times were:

- about 11.5 minutes for a plain `-O3` trial;
- about 16 minutes for an `-flto` trial, because of the LTO link of a large C++ codebase;
- about 28 minutes for each of the 9 PGO-based Phase 6 trials (two-pass build plus training run).

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 262 | warm-up (excluded from CI) | 26.20 |
| 263 | warm-up (excluded from CI) | 25.93 |
| 264 | calibration | 25.84 |
| 265 | calibration | 25.80 |
| 266 | calibration | 25.84 |

Calibration mean **25.827**, 95% CI **[25.76, 25.89]** (±0.25%). The warm-ups absorbed a small early settle
(26.20 → 25.93), and the calibration reps that followed were very tight. That tight baseline is what lets a
+1.43% `-flto` gain be resolved here.

**Shape: `frontend-bound`, 61.6%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`). This is the clearest margin of any corpus shape used on this host.

## Phase 2 filtering and M4

The same eight exclusions as `710.omnetpp_r` (same shape):

- compute-bound-tagged: `-funroll-loops`, `-Ofast`, `-ffast-math`
- memory-bound-tagged: `-fprefetch-loop-arrays`
- vectorization-high-tagged: both `-mprefer-vector-width` settings
- backend-bound-tagged: `-fipa-pta`, `-fgraphite-identity`

M4 fast-tracked `-march=native` (1 of 3 accepted, mean +14.63%) and `-flto` (2 of 2, mean +10.67%), as it did
on omnetpp.

## Phase 3 screening (vs. most recent calibration rep, 25.84)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 267 | `-O3 -freorder-blocks-and-partition` | 25.88 | +0.14% | survived |
| 268 | `-O3 -freorder-functions` | 25.95 | +0.42% | survived |
| 269 | `-O3 -fno-semantic-interposition` | 25.92 | +0.30% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [25.76, 25.89])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 26.09, 26.21, 26.29 | 26.20 | [25.95, 26.44] | **+1.43%** | **accept** |
| `-freorder-functions` | 25.89, 25.86, 25.95 | 25.90 | [25.78, 26.02] | +0.28% | reject (CIs overlap) |
| `-fno-semantic-interposition` | 25.93, 25.90, 25.85 | 25.89 | [25.79, 26.00] | +0.25% | reject |
| `-freorder-blocks-and-partition` | 25.85, 25.89, 25.86 | 25.87 | [25.81, 25.92] | +0.15% | reject |
| `-march=native` (fast-tracked) | 25.52, 25.62, 25.69 | 25.61 | [25.40, 25.82] | -0.85% | reject |

- **`-flto` is a narrow accept.** Its lower bound (25.95) clears the baseline's upper bound (25.89) by 0.06.
  Its +1.43% clears the 1.0% bar. Phase 5 re-confirmed it with a tighter CI (below), so it isn't a one-off.
- **`-march=native` was fast-tracked and rejected again**, slightly negative this time. It's now 1 of 4
  accepted in this cluster. That's a second instance of opportunity #15: 3 confirmation trials spent where 1
  screening trial would have pruned it.
- The three code-layout flags are flat, as on every frontend-bound benchmark so far, on either host. PGO's
  profile-guided layout does what they're meant to do, and much better.

## Phase 5 combination

There's only one accepted flag, so the combination is `-O3 -flto` re-confirmed: **26.20** (26.17, 26.19, 26.23;
CI [26.11, 26.28]), +1.43%. This time the CI is fully clear of the baseline's.

## Phase 6 multipliers

- **PGO: accepted, +23.07% on top of `-O3 -flto`** (32.13, 32.34, 32.25; mean 32.24, CI [31.98, 32.50]), and
  +24.83% overall.
- **Microarch: attempted on `-O3 -flto -fprofile-use`, both rejected.**

  | Added flag | Ratios | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|---|
  | `-march=znver5` | 32.42, 32.44, 32.51 | 32.46 | [32.34, 32.58] | +0.67% | reject (CIs overlap) |
  | `-mtune=znver5` | 32.50, 32.39, 32.46 | 32.45 | [32.31, 32.59] | +0.65% | reject |

  Both read slightly positive, but both overlap the PGO winner's CI and fall short of the 1.0% bar.

None of the trials logged an audit warning. `-O3` and `-fprofile-use` were confirmed compiled in. `-flto` and
`-march=native` are reported as "not independently checkable", as expected.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 4 | 3 | +15.66% |
| `-march=native` | 4 | 1 | +10.76% |
| `-flto` | 3 | 3 | +7.59% |
| `-mtune=znver5` | 3 | 0 | +0.99% |
| `-freorder-functions` | 4 | 0 | +0.34% |
| `-freorder-blocks-and-partition` | 4 | 0 | +0.31% |
| `-fno-semantic-interposition` | 4 | 0 | +0.17% |
| `-march=znver5` | 3 | 0 | +0.16% |
| `-mprefer-vector-width=256` | 2 | 0 | +0.12% |
| `-mprefer-vector-width=512` | 2 | 0 | +0.08% |

## Follow-ups

1. **Why is LTO worth so little on llvm here?** It gave +1.4% here, +5.9% on the old host, and +13.1% on
   omnetpp here. Like stockfish's LTO regression (opportunity #4), it may come down to LTO's inlining decisions
   on a large C++ codebase. A cheap probe is `-flto -flto-partition=one` against the default partitioning,
   though that build would be slow on llvm. Added to the [opportunity list](opportunities_niwot.md).
2. Opportunity #15 (a stronger M4 fast-track rule) now has two concrete cases: omnetpp and llvm.

# `cfm mine` results: 767.nest_r on `chicago`, 2026-11-08

This is the eleventh benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the third here that
`niwot` has also mined ([2026-11-05](mining_results.767.nest_r.2026-11-05.md), +1.31% with `-march=native`).
`767.nest_r` is NEST, a C++ spiking neural-network simulator. Its corpus shape is memory-bound at 47.9%, under the
55% shape margin, so no candidate was excluded on shape.

## Headline result

**`-O3 -fno-stack-protector`, +1.34% over plain `-O3`** (ratio 89.606 → 90.811). nest is a flat benchmark on both
hosts: the best flag found on either is worth about 1.3%, and the two hosts picked different flags.

- **`-fno-stack-protector` was accepted, +1.34%.** Its CI [90.54, 91.09] is clear of the baseline's
  [89.01, 90.21], and all three reps (90.74-90.94) beat every `-O3` calibration rep. It's the second
  `-fno-stack-protector` accept on this host, after flightdm (+1.28%). niwot measured +0.77% and rejected it.
- **`-march=native` was rejected, +0.43%**, its third reject in a row here. niwot accepted it at +1.88%. On top of
  `-fno-stack-protector`, `-march=znver5` read +0.33% and `-mtune=znver5` +0.02%, both rejected.
- **PGO lost 6.09%**, against niwot's -6.36%. Its three reps agreed to 0.14% and built the same code
  (`42927297`).
- **`-flto` lost 1.46%** (niwot -1.65%), with all three reps below every `-O3` rep.
- **Two other CI-clear losses:** `-fcf-protection=none` -0.84% and `-funroll-loops` -0.78%. The rest were within
  ±0.65%. The fast-math flags all changed the code here (nest has no `-fno-fast-math` portability flag) and were
  flat or slightly negative: `-Ofast` -0.59%, `-ffast-math` -0.15%, `-fno-math-errno` +0.20%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 767.nest_r` (uncapped, defaults) |
| Code | `main` at `3cc6488` (no code changes since `f31ba64`, only docs) |
| Experiment id | 13 |
| Started / finished | 2026-11-07T23:38:21Z / 2026-11-08T07:04:20Z (7h26m) |
| Final status | `converged` |
| Trials | 74 (545-618), no reruns, none skipped |
| Candidates screened / confirmed | 14 / 14 (plus `-march=native` fast-tracked, rejected) |
| Excluded on shape (Phase 2) | none (memory-bound 47.9%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 8 of 9, mean +21.06% after femflow) |
| Winning flags | `["-O3", "-fno-stack-protector"]`, +1.34% |
| Guards | bandwidth gate waited once (30 s, trial 545); no reruns; baseline recheck not flagged (+0.55%) |
| Power | package power median 84.99 W on every trial; CPU temperature 91.0-96.8°C |

Each trial took about 6 minutes, and each PGO trial about 8.5.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 47.9%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 545 | warm-up | 90.101 |
| 546 | warm-up | 90.128 |
| 547 | calibration | 89.741 |
| 548 | calibration | 89.327 |
| 549 | calibration | 89.750 |
| 609 | recheck | 90.095 (+0.55%) |

The calibration mean is 89.606, with a 95% CI of [89.006, 90.206] (±0.67%). Warm-up settled after the minimum two
reps (733 s). Rep 548 read about 0.45% under its siblings, which widened the CI. Every `-O3` build had the same code
fingerprint (`2a2afe71`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 550-563 | screening | 14 candidates | 88.40-90.59 | | all survived |
| 564-566 | confirmation | `-fprefetch-loop-arrays` | 89.862 | +0.29% | reject |
| 567-569 | confirmation | `-fgraphite-identity` | 89.870 | +0.30% | reject |
| 570-572 | confirmation | `-flto` | 88.302 | -1.46% | reject (CI clear below baseline) |
| 573-575 | confirmation | `-fno-pie -no-pie` | 90.136 | +0.59% | reject |
| 576-578 | confirmation | `-fno-stack-protector` | 90.811 | +1.34% | **accept** |
| 579-581 | confirmation | `-fcf-protection=none` | 88.852 | -0.84% | reject (CI clear below baseline) |
| 582-584 | confirmation | `-U_FORTIFY_SOURCE` | 89.835 | +0.26% | reject |
| 585-587 | confirmation | `-funroll-loops` | 88.905 | -0.78% | reject |
| 588-590 | confirmation | `-Ofast` | 89.075 | -0.59% | reject |
| 591-593 | confirmation | `-ffast-math` | 89.469 | -0.15% | reject |
| 594-596 | confirmation | `-fno-math-errno` | 89.788 | +0.20% | reject |
| 597-599 | confirmation | `-fno-ipa-cp-clone` | 90.180 | +0.64% | reject |
| 600-602 | confirmation | `-fno-unswitch-loops` | 89.900 | +0.33% | reject |
| 603-605 | confirmation | `-fipa-pta` | 89.575 | -0.03% | reject |
| 606-608 | confirmation (fast-tracked) | `-march=native` | 89.993 | +0.43% | reject |
| 610-612 | PGO | `-fno-stack-protector -fprofile-use` | 85.276 | -6.09% | reject |
| 613-615 | microarch | `-fno-stack-protector -march=znver5` | 91.113 | +0.33% | reject |
| 616-618 | microarch | `-fno-stack-protector -mtune=znver5` | 90.830 | +0.02% | reject |

Phase 6 deltas are against `-O3 -fno-stack-protector`. With one accepted flag, Phase 5 had nothing to combine and
ran no trials. The vector-width multiplier was skipped because the winning set has no `-march=`.

## Observations

- **niwot and chicago agree on the large effects and differ on the 1% ones.** PGO (-6.1% against -6.4%) and `-flto`
  (-1.5% against -1.7%) match closely. The two small wins swap: `-march=native` read +1.9% on niwot and +0.4% here,
  `-fno-stack-protector` +0.8% on niwot and +1.3% here. Either host's winner is worth about 1%.
- **`-fno-stack-protector` keeps showing up on C++ codes here**: accepted on flightdm (+1.28%) and nest (+1.34%),
  +0.76% on gmsh. The stack-protector prologue/epilogue costs most in small, frequently called functions with
  local arrays, which these simulators have plenty of.
- **`-march=native` has been rejected three times in a row** (gmsh, flightdm, nest), right after femflow's +130%
  pushed its memory-bound prior mean to +21%. The mean now says little about the next benchmark; the 8-of-9 accept
  count is what fast-tracks it, and fast-tracking a flag that then gets rejected costs no extra trials.
- **Package power read 85.0 W on every trial**, for the eleventh mine in a row.

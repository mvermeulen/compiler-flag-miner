# `cfm mine` results: 722.palm_r on `niwot`, 2026-11-09

`722.palm_r` is PALM, a Fortran large-eddy simulation model for atmospheric and oceanic boundary layers, 16 copies
under SPECrate. It ran tenth and last in the unattended queue, with `--settle-seconds 600`. `chicago` mined it on
2026-11-06 ([write-up](mining_results.722.palm_r.2026-11-06.md)).

## Headline result

**`-O3 -march=znver5 -mprefer-vector-width=256`, +9.47% over plain `-O3`** (ratio 35.326 → 38.672).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 35.326 | — |
| `+ -march=znver5` (microarch multiplier) | 36.988 | +4.71% |
| `+ -mprefer-vector-width=256` | 38.672 | +4.55% |

- **`-march=znver5` and `-march=native` built the same code** (fingerprint `e48fb195`). Under the name
  `-march=native` it was rejected in Phase 4 (+2.97%, CI ±6%, reps 37.36, 36.06, 35.70); under `-march=znver5` in
  Phase 6 it was accepted (+4.71%, CI ±1.4%). Pooled, the six reps give +3.84%, CI [35.99, 37.37], clear of baseline
  and over the 1% bar, so the accept is right and the Phase 4 reject was noise (#37 (a)).
- **`-mprefer-vector-width=256` added +4.55% on top**, with three reps agreeing within 0.45%. On `chicago` it read +0.61% on top of `-march=native -fprofile-use` and was rejected.
- **Nothing else helped:** `-flto` +0.25%, `-fgraphite-identity` -0.27%, `-fprefetch-loop-arrays` -1.59%,
  `-fstack-arrays` -2.51%, PGO -1.29%, `-mtune=znver5` -0.07%, all rejected. `-frecursive` built the same code as
  `-O3` and was skipped (#58).
- **`-O3` itself is bimodal here**: reps fall near 35.3 or near 34.2, the slow ones drawing about 1 W less (30-31 W
  against 31-32 W). The slow-rep rule replaced two slow baseline reps, so the calibration CI ([35.20, 35.45], ±0.34%)
  sits on the fast level, and the recheck (34.212) was flagged at -3.15%. Every delta in this mine is therefore
  measured against the faster `-O3` level, which makes the accepts conservative.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 722.palm_r --settle-seconds 600` (uncapped, 10 min idle after `766.femflow_r`) |
| Code | `main` at `4f60cbc` (includes PR #69) |
| Experiment id | 196 |
| Started / finished | 2026-11-09T04:38:49Z / 2026-11-09T19:37:42Z (14h59m, about 7 h of it settle) |
| Final status | `converged` |
| Trials | 43 (1974-2016), one of them skipped as unchanged code |
| Candidates screened / confirmed | 6 / 5 (`-frecursive` skipped), none accepted |
| Fast-tracked (M4) | none (`-march=native` at 8 of 17 memory-bound doesn't qualify) |
| Excluded on shape | 8: `-Ofast`, `-ffast-math`, `-funroll-loops`, and the frontend-tagged `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (the rest of the usual C/C++ list wasn't offered for this Fortran benchmark) |
| Skipped as unchanged code (#58) | `-O3 -frecursive` |
| Winning flags | `["-O3", "-march=znver5", "-mprefer-vector-width=256"]`, +9.47% |
| Guards | bandwidth gate waited once (30 s, trial 1974); four slow-rep reruns (two in the baseline, two on `-mtune=znver5`); **baseline recheck flagged (-3.15%)** |
| Power / temperature | package power median 29.0-32.0 W per trial; CPU 93-99 °C; bandwidth probes 44.0-45.9 GB/s |
| Audit | clean |

Each trial took about 21 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 1974 | warm-up | 35.553 | 31.1 W |
| 1975 | warm-up | 35.290 | 32.0 W |
| 1976 | calibration, replaced (slow rep) | 34.162 | 31.0 W |
| 1977 | calibration | 35.283 | 31.1 W |
| 1978 | calibration | 35.315 | 32.0 W |
| 1979 | rerun of 1976, replaced (slow rep) | 34.388 | 31.0 W |
| 1980 | rerun of 1979 | 35.379 | 31.6 W |
| 2002 | recheck after Phase 4 | 34.212 (-3.15%, **flagged**) | 31.0 W |

Calibration mean **35.326**, 95% CI **[35.204, 35.447]** (±0.34%). Warm-up settled after 2 reps (2557 s). All eight
`-O3` builds had the same fingerprint (`fbf8719e`). Taken together, the eight `-O3` runs average 34.948 (CI
[34.46, 35.44]), 1.1% below the calibration mean.

**Shape: `memory-bound`, 69.2%**, `vectorization_density=high`, `allocation_pressure=high`, from the corpus
(`reference-matrix:amd-370-64gb`). Over the 55% gate.

The two levels, about 35.3 and 34.2, look like the bandwidth throttle seen on lbm (#26), in a milder form: the slow
runs draw about 1 W less, far under the low-power rule's 8% threshold, and every pre-run bandwidth probe passed. The
slow-rep rule's spread test caught them because the fast reps agree so closely (0.09%).

## Phase 3 screening (vs. most recent calibration rep, 35.315)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 37.258 | +5.50% |
| `-fgraphite-identity` | 35.417 | +0.29% |
| `-fprefetch-loop-arrays` | 34.982 | -0.94% |
| `-fstack-arrays` | 34.889 | -1.21% |
| `-flto` | 34.541 | -2.19% |
| `-frecursive` | — | skipped, same code as `-O3` |

The five that ran all survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [35.204, 35.447])

| Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | 37.363, 36.062, 35.700 | 36.375 | [34.202, 38.548] | +2.97% | reject (CI overlap) |
| `-flto` | 35.449, 35.762, 35.028 | 35.413 | [34.498, 36.329] | +0.25% | reject |
| `-fgraphite-identity` | 35.664, 35.279, 34.750 | 35.231 | [34.091, 36.371] | -0.27% | reject |
| `-fprefetch-loop-arrays` | 34.401, 34.995, 34.897 | 34.764 | [33.973, 35.555] | -1.59% | reject |
| `-fstack-arrays` | 34.179, 34.459, 34.678 | 34.439 | [33.818, 35.059] | -2.51% | reject |

`-march=native`'s three reps read 37.36, 36.06 and 35.70, drawing 30.0, 29.0 and 29.1 W. The two lower reps look like
the slow level again, but they sat within the 10% slow-rep bar of their fastest sibling, and with only three reps
spread this widely, the spread rule's "siblings agree" condition didn't hold either, so nothing was rerun.

## Phase 5 combination

Nothing was accepted in Phase 4, so Phase 5 kept `-O3`.

## Phase 6 multipliers (on `-O3`, 35.326)

| Stage | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 34.555, 34.124, 35.926 | 34.869 | [32.531, 37.206] | -1.29% | reject |
| PGO near-miss | — | | | | | none |
| Microarch | `+ -march=znver5` | 37.219, 36.844, 36.901 | 36.988 | [36.486, 37.490] | **+4.71%** | **accept** |
| Microarch | `+ -mtune=znver5` | 35.190, 35.066, 35.645 (after 2 reruns) | 35.300 | [34.543, 36.058] | -0.07% | reject |
| Vector width | `-march=znver5 + -mprefer-vector-width=256` | 38.724, 38.560, 38.732 | 38.672 | [38.430, 38.914] | **+4.55%** on `-march=znver5` | **accept** |

- **The microarch accept is the Phase 4 `-march=native` code** (`e48fb195`), re-measured under a different name on
  three steadier reps. Had #58's skip matched any earlier fingerprint in the experiment (#37 (a)), Phase 6 would
  have skipped it as already measured, and the mine would have kept the Phase 4 reject. Here the duplicate measurement
  rescued a real win; pooling the six reps, rather than skipping or re-deciding, is what #37 (a) should do.
- **`-mtune=znver5` had two slow reps** (32.97, 32.93 at 30.0 W, against 35.07-35.65 at 31-32 W), both replaced by
  the spread rule. With them kept, the mean would have been 34.359 (-2.74%), still a reject.
- **PGO's three builds shared one fingerprint** (`9e318b1a`) and read flat.
- **`-mprefer-vector-width=256` at +4.55%** is a clean result: three reps within 0.45%, all above every
  `-march=znver5` rep. PALM's Fortran loops apparently do better with 256-bit vectors than with GCC's default
  512-bit choice under `-march=znver5`.

## Comparison with `chicago`

| | `chicago` | `niwot` |
|---|---|---|
| Winning flags | `-O3 -march=native -fprofile-use` | `-O3 -march=znver5 -mprefer-vector-width=256` |
| Gain | +5.20% | +9.47% |
| `-march=native` alone | +4.13% (fast-tracked) | +2.97% rejected in Phase 4; +4.71% as `-march=znver5`, same code |
| PGO | +1.03% on top of `-march=native`, accepted | -1.29% on `-O3`, rejected |
| `-mprefer-vector-width=256` | +0.61% on top of PGO, rejected (CI overlap) | +4.55% on top of `-march=znver5`, accepted |

The two hosts agree on `-march=native` (about +4%). They disagree on `=256` by four points, on different bases
(PGO there, none here); a `cfm measure` of `-O3 -march=native -mprefer-vector-width=256` on `chicago` would show
whether it carries over.

## What this means

palm is the first fprate benchmark on `niwot` since lbm where the throttle visibly split `-O3` into two levels. The
guards held: the slow-rep rule kept the baseline on one level, and the result reproduces under two names. But the
flow that produced the accept was luck: the same code was rejected once and accepted once, and only the Phase 6
microarch stage happened to re-measure it. Pooling reps across flagsets that share a fingerprint (#37 (a)) would make
that deterministic.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 18 | 8 | +19.46% |
| `-flto` | 12 | 4 | +3.83% |
| `-mprefer-vector-width=256` | 10 | 2 | -0.82% |
| `-march=znver5` | 10 | 2 | -0.96% |

`-march=native`'s row counts this mine's Phase 4 reject; the same code's `-march=znver5` accept went into its own row.

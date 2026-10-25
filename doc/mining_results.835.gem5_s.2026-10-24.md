# `cfm mine` results: 835.gem5_s on `niwot`, 2026-10-24

The fourth SPECspeed benchmark mined on `niwot`. `835.gem5_s` is the speed version of `735.gem5_r` (the
gem5 architecture simulator). It uses pthreads and runs unpinned.

## Headline result

**`-O3 -flto`, +5.35% over plain `-O3`** (ratio 5.260 → 5.542).

- **The same winner as `735.gem5_r`** (+11.01%), at about half the LTO gain. That's the same pattern as
  ns3, where LTO paid +21.4% in rate against +10.3% in speed.
- **PGO regressed again, -8.63% on top of `-flto`.** gem5_r measured -10.6% on this host and -6.7% on
  the old one. It's the same training-coverage problem as #21, now in the speed version too.
- **The baseline recheck flagged an offset**: -1.33%, just outside the baseline CI. That makes every Phase 4
  delta read about 1.3% high. It doesn't change the result (below).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 835.gem5_s` (uncapped, queued after `846.minizinc_s`) |
| Code | `main` at `9e0d86e` (later commits are doc-only) |
| Experiment id | 170 |
| Started / finished | 2026-10-24T21:31:17Z / 2026-10-25T08:17:12Z (10h46m) |
| Final status | `converged` |
| Trials | 67 (895-961) |
| Candidates screened / confirmed | 10 / 1 (plus 1 fast-tracked, accepted) |
| Fast-tracked (M4) | `-flto` (accepted) |
| Winning flags | `["-O3", "-flto"]`, +5.35% |
| Thread placement | pthread, not pinned |
| Guards | bandwidth gate 43.7-45.8 GB/s before every run, waited only before the first; no slow-rep reruns; no audit warnings; baseline recheck **flagged** (-1.33%) |
| Power profile | `balanced`; CPU temp 76.1-81.5°C, package power 19.1-21.1 W |

The 10h46m is mostly builds: gem5 is a large C++ code base, and an LTO trial takes longer to build.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 895 | warm-up (excluded from CI) | 5.232 |
| 896 | warm-up (excluded from CI) | 5.234 |
| 897 | calibration | 5.254 |
| 898 | calibration | 5.240 |
| 899 | calibration | 5.287 |
| 943 | recheck after Phase 4 | 5.191 (**-1.33%, flagged**) |

Calibration mean **5.2605**, 95% CI **[5.200, 5.321]** (±1.15%).

The third calibration rep (5.287) was the highest `-O3` measurement of the run. The warm-ups (5.232,
5.234) and the recheck (5.191) were all lower, so the true `-O3` level is probably nearer 5.23 than 5.26.
Against 5.23, the winner would be about +6.0% rather than +5.35%. All nine rejected Phase 4
candidates landed between 5.240 and 5.267, which fits a baseline around there.

**Shape: `frontend-bound`, 40.4%**, `vectorization_density=moderate`, `allocation_pressure=low`, from the
corpus (`reference-matrix:amd-370-64gb`). gem5_r's corpus entry read 60.3%. Below the 55% gate, so nothing
was excluded on `resource_dominance`.

## Phase 2 and M4

Thirteen candidates: ten screened, `-flto` fast-tracked (6 of 7 frontend-bound accepts), and both
`-mprefer-vector-width=` settings held for Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 5.2875)

| Flags | Ratio | Delta |
|---|---|---|
| `-freorder-blocks-and-partition` | 5.267 | -0.39% |
| `-freorder-functions` | 5.255 | -0.61% |
| `-fno-semantic-interposition` | 5.250 | -0.71% |
| `-funroll-loops` | 5.246 | -0.78% |
| `-fprefetch-loop-arrays` | 5.250 | -0.71% |
| `-march=native` | 5.334 | +0.88% |
| `-Ofast` | 5.232 | -1.05% |
| `-ffast-math` | 5.282 | -0.10% |
| `-fipa-pta` | 5.279 | -0.16% |
| `-fgraphite-identity` | 5.274 | -0.25% |

All ten survived. The screening reference was the high third calibration rep, so most deltas read
slightly negative.

## Phase 4 confirmation (3 reps each, vs. baseline CI [5.200, 5.321])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 5.535, 5.488, 5.534 | 5.519 | [5.453, 5.585] | **+4.91%** | **accept** |
| `-march=native` | 5.347, 5.349, 5.339 | 5.345 | [5.332, 5.358] | **+1.61%** | **accept** |
| `-funroll-loops` | 5.260, 5.260, 5.271 | 5.267 | [5.251, 5.282] | +0.12% | reject |
| `-ffast-math` | 5.263, 5.268, 5.255 | 5.262 | [5.245, 5.278] | +0.02% | reject |
| `-Ofast` | 5.279, 5.255, 5.251 | 5.261 | [5.224, 5.299] | +0.01% | reject |
| `-fgraphite-identity` | 5.260, 5.262, 5.258 | 5.260 | [5.255, 5.265] | -0.01% | reject |
| `-fprefetch-loop-arrays` | 5.251, 5.252, 5.267 | 5.256 | [5.234, 5.279] | -0.08% | reject |
| `-fipa-pta` | 5.255, 5.258, 5.241 | 5.251 | [5.228, 5.275] | -0.17% | reject |
| `-freorder-blocks-and-partition` | 5.230, 5.260, 5.254 | 5.248 | [5.208, 5.288] | -0.24% | reject |
| `-fno-semantic-interposition` | 5.230, 5.245, 5.268 | 5.247 | [5.200, 5.295] | -0.25% | reject |
| `-freorder-functions` | 5.237, 5.221, 5.264 | 5.240 | [5.186, 5.294] | -0.38% | reject |

**`-march=native`'s accept is the one the flagged offset touches.** Its CI ([5.332, 5.358]) clears the
baseline's upper bound (5.321) by only 0.2%. Against a baseline nearer 5.23 it would be about +2.2% and
still accepted. Either way it didn't make the final set, so the offset changes nothing.

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -flto` | 5.539, 5.540, 5.547 | 5.542 | [5.532, 5.553] | +5.35% vs baseline | accept |
| 2 | `+ -march=native` | 5.554, 5.565, 5.562 | 5.560 | | +0.34% vs step 1 | reject |
| Pair | `-flto` + `-march=native` | 5.551, 5.539, 5.567 | 5.553 | | +5.55% vs baseline | accept, but doesn't replace the greedy winner |

`-march=native` adds only +0.34% on top of LTO, under the 1% bar. Its +1.61% alone mostly overlaps
with what LTO already gains.

## Phase 6 multipliers (on `-O3 -flto`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta vs `-O3 -flto` | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -flto -fprofile-use` | 5.074, 5.066, 5.052 | 5.064 | [5.036, 5.091] | **-8.63%** | reject (CI-clear below) |
| Microarch | `+ -march=znver5` | 5.576, 5.564, 5.534 | 5.558 | [5.504, 5.611] | +0.28% | reject |
| Microarch | `+ -mtune=znver5` | 5.520, 5.537, 5.511 | 5.523 | [5.491, 5.555] | -0.35% | reject |
| Vector width | — | | | | | skipped (no `-march=` in the winning set) |

- **PGO: -8.63%**, between gem5_r's -10.6% (this host) and -6.7% (old host). #21's follow-up on gem5_r found
  `-fprofile-partial-training` removed the regression but added no clear gain, so it's not worth
  repeating here.
- **`-march=znver5` +0.28%**, consistent with `-march=native`'s +0.34% on top of LTO in Phase 5.

## Compared with `735.gem5_r`

| | `735.gem5_r` (2026-10-20) | `835.gem5_s` (this run) |
|---|---|---|
| Copies / threads | 16 copies | 16 pthreads, unpinned |
| Shape | frontend-bound 60.3% | frontend-bound 40.4% |
| Winner | `-O3 -flto`, +11.01% | `-O3 -flto`, +5.35% |
| PGO on top of `-flto` | -10.6% | -8.63% |
| `-march=native` | fast-tracked, +0.15%, rejected | +1.61% alone (accepted); +0.34% on top of LTO |

Speed against rate now goes LTO-smaller on two of three benchmarks (ns3 and gem5); vpr went the other
way. In both of the smaller cases, the rate shape was more frontend-bound (about 60% against about 40%),
which fits LTO paying more where instruction-cache pressure is higher. That's suggestive, not shown.

# `cfm mine` results: 834.vpr_s on `niwot`, 2026-10-24

This is the first SPECspeed benchmark cfm has mined on either host. `834.vpr_s` is the speed version of
`734.vpr_r` (VPR, FPGA place-and-route), run as a single 16-thread process rather than 16 copies. It's also
the first mine since PR #53 (PGO always attempted) and PR #49 (vector width deferred to Phase 6) to reach
Phase 6.

## Headline result

**`-O3 -flto -fprofile-use -march=znver5`, +25.17% over plain `-O3`** (ratio 4.111 → 5.145).

- **LTO is most of the win:** +17.66% on its own. PGO adds +4.87% on top of it, and `-march=znver5`
  another +1.60%.
- **This is the first niwot mine to get LTO and PGO in a single pass on a memory-bound benchmark.**
  `734.vpr_r`'s mine excluded `-flto` and skipped PGO on shape, so only a follow-up found them (+15.77%
  overall). Here the shape was a weak 35.9%, under the 55% confidence gate, so `-flto` was screened like
  any other candidate. PGO no longer has a shape skip (#25).
- **Every measurement was steady.** The baseline reps spread 0.7%, nothing needed a slow-rep rerun, the
  bandwidth gate only waited on its first call, and nothing logged an audit warning.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 834.vpr_s` (uncapped, queued ahead of `853.ns3_s`) |
| Code | `main` at `9e0d86e` (PR #55, SPECspeed thread placement) |
| Experiment id | 167 |
| Started / finished | 2026-10-24T02:09:22Z / 2026-10-24T10:09:48Z (8h00m) |
| Final status | `converged` |
| Trials | 83 (692-774) |
| Candidates screened / confirmed | 11 / 3 |
| Fast-tracked (M4) | none |
| Winning flags | `["-O3", "-flto", "-fprofile-use", "-march=znver5"]`, +25.17% |
| Threads | 16 (`threads = 16` from the base config) |
| Thread placement | pthread, not pinned (PR #55 can't pin individual pthreads) |
| Guards | bandwidth gate 43.8-46.1 GB/s before every run, waited only before the first; no slow-rep reruns |
| Power profile | `balanced`; CPU temp 77.4-83.1°C, package power 20.1-23.0 W |

The trials are short (the timed run is about 230 s at `-O3`), so the mine's 8 hours are mostly the 83
builds. A PGO trial takes about 9 minutes against about 5 for the others.

A single-iteration `cfm measure` trial the evening before (experiment 166, trial 691) checked the speed
path end to end first: ratio 4.118, validated, against 4.215 for an earlier intspeed base run
(`-g -O3 -march=native`, CPU2026.002).

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 692 | warm-up (excluded from CI) | 4.129 |
| 693 | warm-up (excluded from CI) | 4.126 |
| 694 | calibration | 4.121 |
| 695 | calibration | 4.100 |
| 696 | calibration | 4.111 |
| 741 | recheck after Phase 4 | 4.132 (+0.53%, not flagged) |

Calibration mean **4.1105**, 95% CI **[4.084, 4.137]** (±0.6%).

Running 16 pthreads on mixed Zen5 and Zen5c cores didn't make the runs noisy. The scheduler places
each thread differently every run, but all 16 CPUs are busy, so it evens out.

**Shape: `memory-bound`, 35.9%**, `vectorization_density=moderate`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`). That's much weaker than vpr_r's 45.4%. At 35.9% it's below
`CONFIDENT_SHAPE_MIN_PCT` (55%), so Phase 2 excluded nothing on `resource_dominance`.

## Phase 2 and M4

Eleven candidates went to screening. Both `-mprefer-vector-width=` candidates were held for Phase 6
(`defer_vector_width_candidates()`, PR #49), the first time a real mine has done this.

M4 found seven memory-bound priors (from sqlite, abc, vpr_r, gcc, zstd and lbm). None qualified for the
fast track: since PR #50 that needs a strict majority of accepts, and the best was `-march=native` at 2 of
5. So every candidate was screened normally.

## Phase 3 screening (vs. most recent calibration rep, 4.1106)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 697 | `-O3 -fprefetch-loop-arrays` | 4.157 | +1.13% | survived |
| 698 | `-O3 -fgraphite-identity` | 4.099 | -0.29% | survived |
| 699 | `-O3 -flto` | 4.779 | **+16.26%** | survived |
| 700 | `-O3 -freorder-blocks-and-partition` | 4.098 | -0.32% | survived |
| 701 | `-O3 -freorder-functions` | 4.118 | +0.17% | survived |
| 702 | `-O3 -fno-semantic-interposition` | 4.113 | +0.05% | survived |
| 703 | `-O3 -funroll-loops` | 4.148 | +0.90% | survived |
| 704 | `-O3 -march=native` | 4.201 | +2.21% | survived |
| 705 | `-O3 -Ofast` | 4.149 | +0.93% | survived |
| 706 | `-O3 -ffast-math` | 4.143 | +0.79% | survived |
| 707 | `-O3 -fipa-pta` | 4.128 | +0.43% | survived |

Nothing came close to the -5% prune bar.

## Phase 4 confirmation (3 reps each, vs. baseline CI [4.084, 4.137])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` | 4.846, 4.843, 4.819 | 4.836 | [4.800, 4.873] | **+17.66%** | **accept** |
| `-Ofast` | 4.180, 4.182, 4.172 | 4.178 | [4.164, 4.192] | **+1.64%** | **accept** |
| `-ffast-math` | 4.184, 4.169, 4.161 | 4.171 | [4.141, 4.201] | **+1.48%** | **accept** |
| `-march=native` | 4.201, 4.153, 4.172 | 4.175 | [4.116, 4.235] | +1.57% | reject (CIs overlap) |
| `-funroll-loops` | 4.167, 4.128, 4.180 | 4.158 | [4.092, 4.225] | +1.16% | reject (CIs overlap) |
| `-fprefetch-loop-arrays` | 4.136, 4.130, 4.150 | 4.139 | [4.113, 4.164] | +0.68% | reject |
| `-fipa-pta` | 4.148, 4.132, 4.124 | 4.135 | [4.105, 4.165] | +0.59% | reject |
| `-freorder-blocks-and-partition` | 4.134, 4.135, 4.097 | 4.122 | [4.069, 4.175] | +0.28% | reject |
| `-freorder-functions` | 4.097, 4.130, 4.113 | 4.113 | [4.072, 4.155] | +0.07% | reject |
| `-fgraphite-identity` | 4.094, 4.127, 4.117 | 4.113 | [4.071, 4.155] | +0.06% | reject |
| `-fno-semantic-interposition` | 4.113, 4.116, 4.107 | 4.112 | [4.101, 4.123] | +0.04% | reject |

- **`-flto` is the big one, as on vpr_r's follow-up** (+11.35% there, on top of `-march=native`). VPR is a
  large C++ program with many small functions across files, so cross-file inlining pays.
- **`-Ofast` and `-ffast-math` were accepted at about +1.5%, just over the 1.0% bar.** Both passed SPEC's
  validate step on every trial. They were excluded at Phase 2 in every earlier memory-bound mine, so this
  is the first time they've been measured on one.
- **`-march=native` measured +1.57%, about the same as `-Ofast`, but was rejected.** One low rep (4.153)
  widened its CI into the baseline's. vpr_r accepted it at +1.31%, so it's probably real, and it comes
  back as `-march=znver5` in Phase 6.

## Phase 5 combination

Greedy walk, starting from `-flto`, the largest single gain:

| Step | Flags | Ratios | Mean | Delta vs running set | Verdict |
|---|---|---|---|---|---|
| 1 | `-O3 -flto` | 4.844, 4.801, 4.843 | 4.829 | +17.48% vs baseline | accept |
| 2 | `+ -Ofast` | 4.867, 4.884, 4.894 | 4.881 | +1.08% | reject |
| 3 | `+ -ffast-math` | 4.871, 4.892, 4.882 | 4.882 | +1.09% | reject |

Pair tournament, against baseline:

| Pair | Mean | Delta | Verdict |
|---|---|---|---|
| `-Ofast` + `-flto` | 4.851 | +18.02% | accept |
| `-ffast-math` + `-flto` | 4.852 | +18.05% | accept |
| `-Ofast` + `-ffast-math` | 4.171 | +1.47% | reject |

- **Both fast-math steps clear 1.0% on top of `-flto`, but their CIs overlap the running set's** ([4.769,
  4.889]), so they're rejected. Their means (4.881, 4.882) sit about 1% above `-flto` alone. A real gain
  that small needs more reps to resolve.
- **The tournament pairs didn't replace the greedy winner.** They beat baseline by about 18%, but not
  `-O3 -flto` by enough to count. So the combination is `-O3 -flto`, at 4.829.
- `-Ofast` already implies `-ffast-math`, which is why the two together (+1.47%) match either alone.

## Phase 6 multipliers

| Stage | Flags | Ratios | Mean | 95% CI | Delta vs previous | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -flto -fprofile-use` | 5.070, 5.062, 5.060 | 5.064 | [5.051, 5.077] | **+4.87%** | **accept** |
| Microarch | `+ -march=znver5` | 5.132, 5.166, 5.138 | 5.145 | [5.101, 5.190] | **+1.60%** | **accept** |
| Microarch | `+ -mtune=znver5` (instead) | 5.075, 5.056, 5.051 | 5.061 | [5.028, 5.093] | -0.07% | reject |
| Vector width | `+ -mprefer-vector-width=256` | 5.133, 5.138, 5.148 | 5.140 | [5.121, 5.158] | -0.11% | reject |
| Vector width | `+ -mprefer-vector-width=512` | 5.132, 5.169, 5.138 | 5.146 | [5.097, 5.195] | +0.02% | reject |

- **PGO: attempted and accepted.** This is #25's first real mine: under the old rule, a confident
  memory-bound shape could have skipped it. +4.87% over `-flto` is close to vpr_r's +4.05% over
  `-march=native`, and PGO's CI is tight and well clear. No near-miss variant was tried: no Phase 4
  reject was CI-clear of baseline while under the 1% bar.
- **Microarch: `-march=znver5` accepted, `-mtune=znver5` flat.** The gain comes from the instruction set
  (AVX-512 and the rest), not from scheduling. That matches `-march=native`'s +1.57% at Phase 4.
- **Vector width: both rejected.** This is the first time `-mprefer-vector-width` has been tested on top of
  a real `-march=` (#23). On vpr, 256 and 512 match the znver5 default exactly. VPR isn't a vector code, so
  the AVX-512 width question doesn't matter here. fprate is where it should.

## Compared with `734.vpr_r`

| | `734.vpr_r` (2026-10-20) | `834.vpr_s` (this run) |
|---|---|---|
| Shape | memory-bound 45.4% | memory-bound 35.9% |
| Mine's winner | `-O3 -march=native`, +1.31% | `-O3 -flto -fprofile-use -march=znver5`, +25.17% |
| Best known | `-O3 -march=native -flto -fprofile-use`, +15.77% (follow-up) | same as the mine's |
| `-flto` | +11.35% (follow-up, on top of `-march=native`) | +17.66% alone |
| PGO | +4.05% (follow-up) | +4.87% |
| `-march` | +1.31% (`native`) | +1.60% (`znver5`) |

The flags that win are the same. LTO pays more in the speed version, by about 6 points. A rate run
measures 16 independent copies and a speed run one 16-thread process, so their bottlenecks differ. In the
speed version, cross-file inlining probably reaches hot paths in VPR's threaded routing code that matter
less in the rate version. That explanation isn't verified.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-flto` | 1 | 1 | +17.66% |
| `-fprofile-use` | 1 | 1 | +4.87% |
| `-Ofast` | 1 | 1 | +1.64% |
| `-ffast-math` | 1 | 1 | +1.48% |
| `-fprefetch-loop-arrays` | 7 | 1 | +1.18% |
| `-funroll-loops` | 1 | 0 | +1.16% |
| `-march=native` | 6 | 2 | +0.81% |
| `-fipa-pta` | 1 | 0 | +0.59% |
| `-fgraphite-identity` | 6 | 0 | +0.29% |
| `-freorder-blocks-and-partition` | 1 | 0 | +0.28% |
| `-march=znver5` | 4 | 1 | +0.15% |
| `-mtune=znver5` | 4 | 0 | +0.13% |
| `-freorder-functions` | 1 | 0 | +0.07% |
| `-fno-semantic-interposition` | 1 | 0 | +0.04% |
| `-mprefer-vector-width=512` | 4 | 0 | -0.11% |
| `-mprefer-vector-width=256` | 4 | 0 | -2.25% |

- **`-flto`, `-fprofile-use`, `-Ofast` and `-ffast-math` now each have one accepted memory-bound record**,
  all from this run. Under the majority rule, 1 of 1 qualifies, so the next memory-bound mine will
  fast-track `-flto`, `-Ofast` and `-ffast-math` to Phase 4. (`-fprofile-use` never takes the fast track;
  PGO always runs in Phase 6.) That's the intended behaviour, but it rests on a single speed benchmark, and
  the knowledge table doesn't separate rate from speed. `853.ns3_s`, mined next, characterized as
  frontend-bound, so it draws on that cluster's priors instead.
- The microarch and vector-width multipliers upsert their candidate flags too, which is where
  `-march=znver5`'s first accept came from.

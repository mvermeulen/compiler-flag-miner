# `cfm mine` results: 853.ns3_s on `niwot`, 2026-10-24

The second SPECspeed benchmark mined on `niwot`, after [`834.vpr_s`](mining_results.834.vpr_s.2026-10-24.md).
`853.ns3_s` is the speed version of `753.ns3_r` (the ns-3 network simulator). It's single-threaded, so it's
the first real mine to use PR #55's `taskset` pinning: every timed run went to CPU 2, a Zen5 core.

## Headline result

**`-O3 -flto -fprofile-use`, +16.46% over plain `-O3`** (ratio 6.527 → 7.602).

- **The same winning set as `753.ns3_r`** on this host (+26.66%), with a smaller LTO share: `-flto` +10.30%
  here against +21.40% there. PGO adds +5.59% on top, a little more than ns3_r's +4.33%.
- **The pinned runs were very steady.** The three baseline calibration reps spread 0.18% (CI ±0.23%),
  and most confirmed flag sets had a CI under ±0.5%. The widest, `-flto` and
  `-fno-semantic-interposition`, were about ±1.3%. That let the run resolve differences well under 1%: `-Ofast` and `-ffast-math` came out CI-clear of baseline at +0.67% and +0.79%, and
  `-mtune=znver5` CI-clear *below* PGO at -0.86%.
- **Nothing else helped.** The shape was a weak 39.4%, so Phase 2 excluded nothing and ten candidates were
  screened (ns3_r screened five). All ten were flat.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 853.ns3_s` (uncapped, queued after `834.vpr_s`) |
| Code | `main` at `9e0d86e` (PR #55, SPECspeed thread placement) |
| Experiment id | 168 |
| Started / finished | 2026-10-24T10:09:48Z / 2026-10-24T17:29:23Z (7h20m) |
| Final status | `converged` |
| Trials | 64 (775-838) |
| Candidates screened / confirmed | 10 / 0 (plus 1 fast-tracked, accepted) |
| Fast-tracked (M4) | `-flto` (accepted) |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +16.46% |
| Thread placement | single-threaded, `taskset -c 2` (confirmed in `speccmds.cmd`) |
| Guards | bandwidth gate 42.0-46.2 GB/s before every run, waited only before the first; no slow-rep reruns; no audit warnings |
| Power profile | `balanced`; CPU temp 77.2-82.1°C, package power 21.1-24.0 W |

A trial takes about 5 minutes (a PGO trial about 13.5), so the 7h20m is mostly builds, as on vpr_s.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 775 | warm-up (excluded from CI) | 6.549 |
| 776 | warm-up (excluded from CI) | 6.513 |
| 777 | calibration | 6.526 |
| 778 | calibration | 6.534 |
| 779 | calibration | 6.523 |
| 823 | recheck after Phase 4 | 6.533 (+0.08%, not flagged) |

Calibration mean **6.5275**, 95% CI **[6.512, 6.543]** (±0.23%). For comparison, vpr_s (16 unpinned
threads) was ±0.6% and ns3_r (16 copies) ±0.5%.

**Shape: `frontend-bound`, 39.4%**, `vectorization_density=moderate`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`). ns3_r's corpus entry read 60.7%. At 39.4% it's under
`CONFIDENT_SHAPE_MIN_PCT` (55%), so none of the six exclusions ns3_r had (`-funroll-loops`, `-Ofast`,
`-ffast-math`, `-fprefetch-loop-arrays`, `-fipa-pta`, `-fgraphite-identity`) applied here.

## Phase 2 and M4

Eleven candidates. Both `-mprefer-vector-width=` settings were held for Phase 6.

M4 found nine frontend-bound priors. `-flto` (5 of 6 accepted) qualified and was fast-tracked to Phase 4.
`-march=native` (1 of 7) and the rest were screened normally. `-fprofile-use` (5 of 7) doesn't use the
fast track; PGO always runs in Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 6.5226)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 780 | `-O3 -freorder-blocks-and-partition` | 6.504 | -0.29% | survived |
| 781 | `-O3 -freorder-functions` | 6.506 | -0.25% | survived |
| 782 | `-O3 -fno-semantic-interposition` | 6.524 | +0.02% | survived |
| 783 | `-O3 -funroll-loops` | 6.492 | -0.47% | survived |
| 784 | `-O3 -fprefetch-loop-arrays` | 6.534 | +0.17% | survived |
| 785 | `-O3 -march=native` | 6.557 | +0.53% | survived |
| 786 | `-O3 -Ofast` | 6.375 | -2.26% | survived |
| 787 | `-O3 -ffast-math` | 6.573 | +0.77% | survived |
| 788 | `-O3 -fipa-pta` | 6.487 | -0.54% | survived |
| 789 | `-O3 -fgraphite-identity` | 6.535 | +0.19% | survived |

`-Ofast`'s screening trial was low (-2.26%) but its three confirmation reps came out +0.67%, so that one
trial was noise. Its bandwidth probe (42.0 GB/s) was the session's lowest, though still above the gate's
85% bar.

## Phase 4 confirmation (3 reps each, vs. baseline CI [6.512, 6.543])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 7.156, 7.208, 7.228 | 7.197 | [7.105, 7.289] | **+10.26%** | **accept** |
| `-ffast-math` | 6.579, 6.568, 6.591 | 6.579 | [6.550, 6.609] | +0.79% | reject (under 1%, CI-clear) |
| `-Ofast` | 6.564, 6.574, 6.575 | 6.571 | [6.556, 6.586] | +0.67% | reject (under 1%, CI-clear) |
| `-fgraphite-identity` | 6.534, 6.550, 6.548 | 6.544 | [6.522, 6.565] | +0.25% | reject |
| `-fprefetch-loop-arrays` | 6.528, 6.540, 6.532 | 6.533 | [6.518, 6.548] | +0.09% | reject |
| `-freorder-blocks-and-partition` | 6.524, 6.542, 6.520 | 6.528 | [6.500, 6.557] | +0.01% | reject |
| `-freorder-functions` | 6.546, 6.511, 6.523 | 6.527 | [6.483, 6.570] | -0.01% | reject |
| `-march=native` | 6.530, 6.531, 6.481 | 6.514 | [6.444, 6.585] | -0.21% | reject |
| `-fno-semantic-interposition` | 6.524, 6.461, 6.516 | 6.501 | [6.416, 6.586] | -0.41% | reject |
| `-funroll-loops` | 6.494, 6.492, 6.509 | 6.498 | [6.475, 6.522] | -0.45% | reject |
| `-fipa-pta` | 6.506, 6.484, 6.502 | 6.497 | [6.469, 6.526] | -0.46% | reject |

- **`-flto` is the only real gain.** ns-3 is many small C++ modules with thin layers between them, and
  cross-module inlining removes them. It pays half as much here as in ns3_r (below).
- **`-ffast-math` and `-Ofast` are CI-clear but under the 1.0% bar.** ns-3 does little floating point, so
  under 1% is about what to expect. They became the near-miss candidates for Phase 6's PGO variant.
- **`-march=native` is flat**, as on ns3_r (fast-tracked and rejected there). ns-3 doesn't vectorize much.

## Phase 5 combination

Only `-flto` was accepted, so the greedy walk has one step and there's no pair tournament.

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -flto` | 7.194, 7.203, 7.203 | 7.200 | [7.187, 7.212] | +10.30% vs baseline | accept |

## Phase 6 multipliers

| Stage | Flags | Ratios | Mean | 95% CI | Delta vs previous | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -flto -fprofile-use` | 7.606, 7.589, 7.612 | 7.602 | [7.573, 7.631] | **+5.59%** | **accept** |
| PGO + near miss | `-O3 -flto -ffast-math -fprofile-use` | 7.610, 7.600, 7.599 | 7.603 | [7.588, 7.618] | +5.60% | accept, but no better than plain PGO |
| Microarch | `+ -march=znver5` | 7.590, 7.586, 7.557 | 7.578 | [7.533, 7.623] | -0.32% | reject |
| Microarch | `+ -mtune=znver5` (instead) | 7.530, 7.545, 7.535 | 7.537 | [7.517, 7.556] | -0.86% | reject (CI-clear below) |
| Vector width | — | — | — | — | — | skipped (no `-march=` in the winning set) |

- **PGO: accepted, +5.59% over `-flto`.** Only the timed run is pinned. The pass-1 training run's
  `speccmds.cmd` has no `taskset`, because `use_submit_for_speed` covers the timed runs, not the FDO
  training step. The profile is the same either way, since the program is single-threaded and its
  branch and call counts don't depend on which core it runs on.
- **The near-miss variant matched plain PGO** (7.603 against 7.602), so `-ffast-math`'s +0.79% doesn't
  survive on top of PGO. `-Ofast` was the second near miss; only the best one is tried.
- **`-mtune=znver5` is a small real regression**: its CI sits entirely below PGO's. That's the first
  time a microarch candidate has resolved as CI-clear worse on this host. It's -0.86%, so it doesn't
  change any decision, but it shows how fine-grained a pinned single-threaded run can be.

## Compared with `753.ns3_r`

| | `753.ns3_r` (2026-10-21) | `853.ns3_s` (this run) |
|---|---|---|
| Copies / threads | 16 copies | 1 thread, pinned to CPU 2 |
| Shape | frontend-bound 60.7% | frontend-bound 39.4% |
| Baseline CI | ±0.5% | ±0.23% |
| Winner | `-O3 -flto -fprofile-use`, +26.66% | `-O3 -flto -fprofile-use`, +16.46% |
| `-flto` | +21.40% | +10.30% |
| PGO on top | +4.33% | +5.59% |
| `-march=native` | fast-tracked, rejected | screened, -0.21% |

The flags that win are the same. LTO pays about half as much in the speed version. Two differences
could explain that, and this run can't tell them apart:

- **Different workloads.** ns3_s runs four ns-3 scenarios (`traffic-fqcodel`, `tcp-pacing`,
  `tcp-validation`, `wifi-mixed-network`), so its hot paths may cross fewer module boundaries.
- **One copy against sixteen.** Sixteen copies share the L3 and memory bandwidth, so code size and
  instruction-cache misses cost more. LTO's inlining and dead-code removal may pay more under that
  pressure. A single pinned copy has the whole L3 to itself. The shape agrees: frontend-bound at 60.7%
  in rate, 39.4% in speed.

On vpr_s it went the other way (LTO +17.66% in speed against +11.35% in rate), so neither direction is
a rule.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-flto` | 7 | 6 | +9.29% |
| `-fprofile-use` | 8 | 6 | +8.72% |
| `-march=native` | 8 | 1 | +5.38% |
| `-ffast-math` | 1 | 0 | +0.79% |
| `-Ofast` | 1 | 0 | +0.67% |
| `-fgraphite-identity` | 1 | 0 | +0.25% |
| `-march=znver5` | 7 | 0 | +0.10% |
| `-freorder-blocks-and-partition` | 8 | 0 | +0.09% |
| `-fprefetch-loop-arrays` | 1 | 0 | +0.09% |
| `-mprefer-vector-width=512` | 4 | 0 | +0.07% |
| `-freorder-functions` | 8 | 0 | +0.06% |
| `-mtune=znver5` | 7 | 0 | -0.02% |
| `-fno-semantic-interposition` | 8 | 0 | -0.05% |
| `-mprefer-vector-width=256` | 4 | 0 | -0.10% |
| `-funroll-loops` | 1 | 0 | -0.45% |
| `-fipa-pta` | 1 | 0 | -0.46% |

The six flags with n = 1 were excluded on shape in every earlier frontend-bound mine. This is their first
frontend-bound measurement, and all six are within ±0.8%.

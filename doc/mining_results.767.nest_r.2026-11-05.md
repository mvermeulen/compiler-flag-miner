# `cfm mine` results: 767.nest_r on `niwot`, 2026-11-05

`767.nest_r` is NEST, a C++ spiking neural network simulator, 16 copies under SPECrate. It ran fifth in the
unattended queue, with `--settle-seconds 600`, and is the first nest mine on any host.

## Headline result

**`-O3 -march=native`, +1.31% over plain `-O3`** (ratio 42.970 → 43.532).

- **A small but real win.** `-march=native` confirmed at +1.88% (CI [43.34, 44.21], clear of baseline's
  [42.72, 43.22]) and re-measured at +1.31% as the greedy step, still over the 1% bar.
- **Nothing else helped, and three flags hurt clearly:** `-fno-pie -no-pie` -3.43%, `-fno-unswitch-loops` -2.92%,
  and `-fgraphite-identity` -5.72% at screening (pruned).
- **PGO lost 6.36%** on its three reproducible builds, and `-flto` lost 1.65%.
- **A clean run, the tightest baseline yet on niwot's fprate:** CI ±0.59%, no reruns of any kind, nothing flagged.
  Package power moved with the code (33 W to 45 W per flagset), but each flagset's reps agreed with each other.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 767.nest_r --settle-seconds 600` (uncapped, 10 min idle after `748.flightdm_r`) |
| Code | `main` at `c946ed9` |
| Experiment id | 191 |
| Started / finished | 2026-11-05T23:32:33Z / 2026-11-06T19:15:14Z (19h43m, about 12 h of it settle) |
| Final status | `converged` |
| Trials | 72 (1723-1794) |
| Candidates screened / confirmed | 15 / 14 (`-fgraphite-identity` pruned) |
| Fast-tracked (M4) | none (`-march=native` at 4 of 12 memory-bound doesn't qualify) |
| Excluded on shape | none (memory-bound 47.9%, under the 55% margin) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-march=native"]`, +1.31% |
| Guards | no slow-rep, spread or low-power reruns; no audit warnings; baseline recheck not flagged (-0.08%) |
| Power / temperature | package power median 32.1-45.1 W per trial (baseline 38-40 W); CPU 97-100 °C |

Each trial took about 16 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1723 | warm-up | 42.690 |
| 1724 | warm-up | 43.017 |
| 1725 | calibration | 42.853 |
| 1726 | calibration | 43.022 |
| 1727 | calibration | 43.035 |
| 1785 | recheck after Phase 4 | 42.934 (-0.08%, not flagged) |

Calibration mean **42.970**, 95% CI **[42.717, 43.223]** (±0.59%). Warm-up settled after 2 reps (1980 s). Unlike
the other fprate mines here, the first rep read low, not high.

**Shape: `memory-bound`, 47.9%**, `vectorization_density=high`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). Under the 55% gate, so nothing was excluded, and PR #57's opt-outs and the
fast-math family all ran.

## Phase 3 screening (vs. most recent calibration rep, 43.035)

| Flags | Ratio | Delta |
|---|---|---|
| `-fno-stack-protector` | 43.301 | +0.62% |
| `-fno-ipa-cp-clone` | 43.256 | +0.51% |
| `-march=native` | 43.127 | +0.21% |
| `-fcf-protection=none` | 43.072 | +0.09% |
| `-fno-math-errno` | 43.063 | +0.07% |
| `-U_FORTIFY_SOURCE` | 43.011 | -0.06% |
| `-fipa-pta` | 42.879 | -0.36% |
| `-ffast-math` | 42.803 | -0.54% |
| `-fno-unswitch-loops` | 42.624 | -0.95% |
| `-fprefetch-loop-arrays` | 42.584 | -1.05% |
| `-funroll-loops` | 42.539 | -1.15% |
| `-flto` | 42.532 | -1.17% |
| `-Ofast` | 42.341 | -1.61% |
| `-fno-pie -no-pie` | 42.220 | -1.89% |
| `-fgraphite-identity` | 40.574 | **-5.72%, pruned** |

`-march=native` screened at only +0.21% and then confirmed at +1.88%: one screening run is within noise of a 1-2%
effect, which is why Phase 3 only prunes clearly-worse candidates.

## Phase 4 confirmation (3 reps each, vs. baseline CI [42.717, 43.223])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` | 43.778 | [43.341, 44.215] | **+1.88%** | **accept** |
| `-fno-ipa-cp-clone` | 43.345 | [43.030, 43.660] | +0.87% | reject (CI overlap) |
| `-fno-stack-protector` | 43.302 | [42.811, 43.794] | +0.77% | reject |
| `-fcf-protection=none` | 43.041 | [42.968, 43.114] | +0.17% | reject |
| `-ffast-math` | 42.966 | [42.832, 43.101] | -0.01% | reject |
| `-fipa-pta` | 42.821 | [42.581, 43.060] | -0.35% | reject |
| `-funroll-loops` | 42.790 | [42.752, 42.828] | -0.42% | reject |
| `-Ofast` | 42.698 | [42.350, 43.046] | -0.63% | reject |
| `-U_FORTIFY_SOURCE` | 42.624 | [42.344, 42.904] | -0.80% | reject |
| `-fno-math-errno` | 42.622 | [42.132, 43.112] | -0.81% | reject |
| `-fprefetch-loop-arrays` | 42.364 | [41.380, 43.349] | -1.41% | reject |
| `-flto` | 42.260 | [41.549, 42.971] | -1.65% | reject |
| `-fno-unswitch-loops` | 41.714 | [41.490, 41.938] | **-2.92%** | reject |
| `-fno-pie -no-pie` | 41.495 | [41.355, 41.635] | **-3.43%** | reject |

- **`-fno-pie -no-pie` lost 3.4% on three tight reps (±0.34%)**, and all three drew 33-34 W against the baseline's
  39 W. They read more than 8% below the baseline power reference, but PR #68's sibling check correctly kept them:
  the reps agreed, so the low power came from the code. The non-PIE build is genuinely slower here. Why is open;
  possibly a layout change in the hot spike-delivery loop.
- **`-fgraphite-identity`'s -5.72% screening run also drew low power** (32.1 W). As a single screening run it got no
  rerun check, but it was probably also a code effect.
- **The fast-math family was flat** (-0.8% to 0.0%) and all passed validation: nest's hot loops aren't
  float-reassociation-bound.

## Phase 5 combination

| Step | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | 43.532 | [43.301, 43.763] | +1.31% vs baseline | accept |

Only one flag was accepted, so there was no further greedy step and no pair tournament.

## Phase 6 multipliers (on `-O3 -march=native`, 43.532)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 40.764 | [39.910, 41.619] | **-6.36%** | reject |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | — | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 43.523 | [43.442, 43.603] | -0.02% | reject |

- **PGO's three builds shared one fingerprint** (`d9a480c4`) and drew the most power of the run (43.5-45.1 W), so it
  wasn't a bad build or a throttled run: the profile-guided code is slower and busier. A training workload that
  doesn't represent the reference run is the usual cause.
- **`=256` made no difference** on top of `-march=native`, as on astcenc.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 13 | 5 | +11.92% |
| `-flto` | 7 | 2 | +4.15% |
| `-fno-ipa-cp-clone` | 1 | 0 | +0.87% |
| `-fno-stack-protector` | 1 | 0 | +0.77% |
| `-fgraphite-identity` | 12 | 0 | +0.54% |

`-march=native` is now 5 of 13 accepted in the memory-bound cluster, still short of the majority the fast track
needs.

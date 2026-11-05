# `cfm mine` results: 748.flightdm_r on `niwot`, 2026-11-05

`748.flightdm_r` is a C++ flight-dynamics simulator, 16 copies under SPECrate. It ran fourth in the unattended
queue, with `--settle-seconds 600`, and is the first flightdm mine on any host.

## Headline result

**`-O3 -flto -fprofile-use`, +25.81% over plain `-O3`** (ratio 47.765 → 60.094).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 47.765 | — |
| `-O3 -flto` | 53.155 | +11.28% |
| `+ -fprofile-use` | 60.094 | +13.06% |

- **LTO and PGO won, nothing else did.** flightdm behaves like the frontend-bound interpreter- and compiler-style
  codes (cpython, omnetpp, ns3), not like astcenc, even though its corpus read is under the margin
  (frontend-bound 42.0%) and its vectorization density is high.
- **`-march=native` was flat** (+1.01%, CI overlap), and so were `-march=znver5`/`-mtune=znver5` on top of PGO.
- **The fast-math candidates couldn't do anything here.** The SPEC config's portability section gives flightdm
  `PORTABILITY = -fno-fast-math`, which lands after `OPTIMIZE` on every compile line and cancels `-ffast-math`.
  `-ffast-math` and `-fno-math-errno` both built the same code as `-O3` (fingerprint `61a5f98a`) and were skipped
  (#58). `-Ofast` built different code (its non-fast-math parts survive) and measured +0.98%. `737.gmsh_r`, later in
  the queue, has the same portability flag.
- **A clean run:** baseline CI ±2.4%, package power 49-51 W, no throttle signs, one spread-rule rerun.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 748.flightdm_r --settle-seconds 600` (uncapped, 10 min idle after `731.astcenc_r`) |
| Code | `main` at `3814919` |
| Experiment id | 190 |
| Started / finished | 2026-11-05T06:04:22Z / 2026-11-05T23:22:32Z (17h18m, about 11.8 h of it settle) |
| Final status | `converged` |
| Trials | 73 (1650-1722) |
| Candidates screened / confirmed | 14 / 13 (12 rejected, plus `-flto` fast-tracked and accepted) |
| Fast-tracked (M4) | `-flto` (9 of 13 frontend-bound) |
| Excluded on shape | none (frontend-bound 42.0%, under the 55% margin) |
| Skipped as unchanged code (#58) | `-O3 -ffast-math`, `-O3 -fno-math-errno` (both the same code as `-O3`) |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +25.81% |
| Guards | one spread-rule rerun (`-Ofast`); no low-power reruns; baseline recheck not flagged (+0.83%) |
| Power / temperature | package power median 49.0-51.1 W per trial; CPU 95-100 °C |
| Audit | `-ffast-math` NOT FOUND on trial 1666: GCC drops an option a later `-fno-fast-math` cancels, so this is the portability flag, not a lost flag |

Each trial took about 14.5 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1650 | warm-up | 48.560 |
| 1651 | warm-up | 47.782 |
| 1652 | warm-up | 47.536 |
| 1653 | calibration | 47.465 |
| 1654 | calibration | 48.301 |
| 1655 | calibration | 47.530 |
| 1710 | recheck after Phase 4 | 48.160 (+0.83%, not flagged) |

Calibration mean **47.765**, 95% CI **[46.610, 48.920]** (±2.42%). Warm-up settled after 3 reps. As usual on this
host, the first rep after idle read high (+1.7%).

**Shape: `frontend-bound`, 42.0%**, `vectorization_density=high`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`). `-mprefer-vector-width=256` was deferred to Phase 6 and never ran (no `-march=`
in the winning set).

## Phase 3 screening (vs. most recent calibration rep, 47.530)

| Flags | Ratio | Delta |
|---|---|---|
| `-fno-stack-protector` | 49.698 | +4.56% |
| `-Ofast` | 48.733 | +2.53% |
| `-fcf-protection=none` | 48.344 | +1.71% |
| `-fgraphite-identity` | 48.292 | +1.60% |
| `-fipa-pta` | 48.168 | +1.34% |
| `-funroll-loops` | 48.065 | +1.13% |
| `-march=native` | 48.019 | +1.03% |
| `-fno-unswitch-loops` | 48.012 | +1.01% |
| `-U_FORTIFY_SOURCE` | 47.839 | +0.65% |
| `-fno-ipa-cp-clone` | 47.671 | +0.30% |
| `-fno-pie -no-pie` | 47.586 | +0.12% |
| `-fprefetch-loop-arrays` | 47.387 | -0.30% |
| `-ffast-math` | — | skipped, same code as `-O3` |
| `-fno-math-errno` | — | skipped, same code as `-O3` |

The 12 that ran all survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [46.610, 48.920])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-flto` (fast-tracked) | 52.826 | [51.393, 54.260] | **+10.60%** | **accept** |
| `-funroll-loops` | 48.659 | [47.539, 49.778] | +1.87% | reject |
| `-fgraphite-identity` | 48.464 | [47.524, 49.403] | +1.46% | reject |
| `-fno-stack-protector` | 48.431 | [46.956, 49.905] | +1.39% | reject |
| `-fno-unswitch-loops` | 48.269 | [47.079, 49.459] | +1.05% | reject |
| `-march=native` | 48.247 | [47.229, 49.265] | +1.01% | reject |
| `-Ofast` | 48.235 | [47.721, 48.749] | +0.98% | reject |
| `-U_FORTIFY_SOURCE` | 48.074 | [47.013, 49.134] | +0.65% | reject |
| `-fprefetch-loop-arrays` | 48.057 | [47.101, 49.013] | +0.61% | reject |
| `-fno-ipa-cp-clone` | 47.928 | [47.281, 48.576] | +0.34% | reject |
| `-fipa-pta` | 47.893 | [46.901, 48.885] | +0.27% | reject |
| `-fcf-protection=none` | 47.883 | [46.870, 48.895] | +0.25% | reject |
| `-fno-pie -no-pie` | 47.225 | [46.380, 48.071] | -1.13% | reject |

- **Several flags landed at +1% to +1.9%, all inside the baseline CI.** With a ±2.4% baseline CI, a real 1-2% gain
  here can't be told from noise in three reps. None is likely large: their own CIs all reach back to baseline's mean.
- **`-fno-stack-protector`'s +4.56% screening read didn't hold** (+1.39% confirmed).
- **`-Ofast`'s first confirmation rep (47.133) was replaced by the spread rule** (2.27% below its slowest sibling,
  whose siblings agreed within 0.46%). The rerun read 48.033.

## Phase 5 combination

| Step | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| 1 | `-O3 -flto` | 53.155 | [51.153, 55.157] | +11.28% vs baseline | accept |

Only one flag was accepted, so there was no further greedy step and no pair tournament.

## Phase 6 multipliers (on `-O3 -flto`, 53.155)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 60.094 | [58.511, 61.677] | **+13.06%** | **accept** |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | `+ -march=znver5` | 59.920 | [59.727, 60.113] | -0.29% | reject |
| Microarch | `+ -mtune=znver5` | 60.338 | [59.008, 61.667] | +0.40% | reject |
| Vector width | — | | | | skipped (no `-march=` in the winning set) |

- **PGO's three builds shared one fingerprint** (`4c3e4ce5`), as on astcenc: SPECrate's PGO builds reproduce here,
  unlike SPECspeed's (#32).
- **LTO + PGO together is +25.8%**, close to the same pair's gain on this host's cpython_r (+36.49%) and omnetpp_r
  (+29.94%).

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 15 | 10 | +6.68% |
| `-flto` | 14 | 10 | +6.23% |
| `-march=native` | 15 | 3 | +4.99% |
| `-funroll-loops` | 5 | 1 | +3.19% |
| `-ffast-math` | 4 | 1 | +1.41% |
| `-Ofast` | 5 | 1 | +1.17% |
| `-fno-stack-protector` | 6 | 1 | +1.10% |

`-Ofast`'s row now includes a trial where most of `-Ofast` was cancelled by the benchmark's own portability flag.
That measures the config, not the flag. The catalog could skip the fast-math family for a benchmark whose
`PORTABILITY` has `-fno-fast-math`; #58 already makes the two pure fast-math flags cost a build each, but `-Ofast`
still cost five timed runs (#38).

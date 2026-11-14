# `cfm mine` results: 766.femflow_r on `niwot`, 2026-11-14 (`--no-shape-filter` re-mine)

`766.femflow_r` is a C++ finite-element flow solver built on deal.II, 16 copies under SPECrate. This is a re-mine of
the 2026-11-09 run ([write-up](mining_results.766.femflow_r.2026-11-09.md), experiment 195) with
`--no-shape-filter`, the third of three re-mines testing #30. That run's corpus shape (memory-bound 69.4%) excluded
11 of 15 candidates. Same `--settle-seconds 600`.

## Headline result

**`-O3 -march=native`, +108.68% over plain `-O3`** (ratio 42.464 → 88.614): the same winner as the shape-filtered
mine (+106.58%), on the same code (fingerprint `ad9afc91` in both).

- **Most of the 11 excluded flags lost on scalar `-O3`.** `-Ofast` (-2.95%), `-ffast-math` (-2.58%),
  `-U_FORTIFY_SOURCE` (-1.27%), `-fno-unswitch-loops` (-1.07%), `-funroll-loops` (-1.00%), `-fipa-pta` (-0.84%) and
  `-fcf-protection=none` (-0.72%) all came in below baseline. `-fno-math-errno` (+0.51%), `-fno-pie -no-pie` (+0.52%)
  and `-fno-stack-protector` (+0.11%) were flat.
- **The one exception, `-fno-ipa-cp-clone` (+2.31%, accepted), added nothing on top of `-march=native`** (+0.15% as a
  greedy step, rejected). It had been 0 for 4 in the memory-bound cluster.
- **`-fno-math-errno`, which PR #71 now exempts from the filter, was flat here** (+0.51%, rejected). It went to Phase 4
  directly on its prior (2 of 3 accepted before), which this result drops to 2 of 4, so it won't fast-track again.
- **PGO lost 30.07% on top of `-march=native`**, building the same binary as experiment 195's PGO (`b72ab998`), which
  lost 27.18%. The #40 loss is reproducible. `-mprefer-vector-width=256` lost 12.10% (195: -10.92%).
- **So on femflow the shape filter cost nothing**, and dropping it cost 54 more trials (about 24 hours).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 766.femflow_r --settle-seconds 600 --no-shape-filter` (uncapped, 10 min idle after the marian re-mine) |
| Code | `main` at `7f80dd4` (includes PR #71, which only matters for the fast-track here, since the filter was off) |
| Experiment id | 199 |
| Started / finished | 2026-11-12T11:05:10Z / 2026-11-14T00:01:01Z (36h56m, about 14 h of it settle) |
| Final status | `converged` |
| Trials | 85 (2226-2310) |
| Candidates screened / confirmed | 14 / 13 (`-fgraphite-identity` pruned), plus `-fno-math-errno` fast-tracked |
| Fast-tracked (M4) | `-fno-math-errno` (2 of 3 accepted before, mean +2.53%) |
| Excluded on shape | none (`--no-shape-filter`) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-march=native"]`, +108.68% |
| Guards | bandwidth gate waited once (30 s, trial 2226); one slow-rep rerun (trial 2278, `-fno-unswitch-loops`, replaced by 2281); one spread rerun (trial 2309, `=256`, replaced by 2310); **baseline recheck flagged (-0.55%)** |
| Power / temperature | package power median 45-48 W for scalar builds, 34-35 W for `-march=native`, 43 W for PGO, 40-41 W for `=256`; CPU 96-100 °C; bandwidth probes 43.6-45.7 GB/s |
| Audit | clean |

A scalar trial took about 27 minutes, a `-march=native` trial about 19-22 and a PGO trial about 47, 10 minutes of each
the settle.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 2226 | warm-up | 42.571 |
| 2227 | warm-up | 42.683 |
| 2228 | calibration | 42.386 |
| 2229 | calibration | 42.530 |
| 2230 | calibration | 42.476 |
| 2288 | recheck after Phase 4 | 42.230 (-0.55%, **flagged**) |

Calibration mean **42.464**, 95% CI **[42.284, 42.644]** (±0.42%). Warm-up settled after 2 reps (3241 s). Every `-O3`
build had experiment 195's fingerprint (`4302cdf0`); this session's `-O3` reads 1.43% below that run's 43.082. The
recheck sits 0.13% under the CI's low end and drew 45.0 W against the calibration reps' 48.1 W; like 195's flag, it is
too small to affect any verdict here.

**Shape: `memory-bound`, 69.4%**, `vectorization_density=high`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`), as before. `-mprefer-vector-width=256` was still deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 42.476)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 87.887 | **+106.91%** |
| `-flto` | 49.315 | **+16.10%** |
| `-fno-ipa-cp-clone` | 43.816 | +3.15% |
| `-fno-pie -no-pie` | 42.880 | +0.95% |
| `-fno-unswitch-loops` | 42.864 | +0.91% |
| `-U_FORTIFY_SOURCE` | 42.679 | +0.48% |
| `-fcf-protection=none` | 42.666 | +0.45% |
| `-fipa-pta` | 42.652 | +0.41% |
| `-fprefetch-loop-arrays` | 42.271 | -0.48% |
| `-fno-stack-protector` | 42.136 | -0.80% |
| `-funroll-loops` | 42.105 | -0.87% |
| `-ffast-math` | 41.811 | -1.57% |
| `-Ofast` | 41.143 | -3.14% |
| `-fgraphite-identity` | 40.164 | **-5.44%, pruned** |

`-fgraphite-identity` was pruned again (195: -6.36%). `-fno-math-errno` skipped screening (fast-tracked).

## Phase 4 confirmation (3 reps each, vs. baseline CI [42.284, 42.644])

| Flags | Shape-filtered on 11-09? | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | no | 88.614 | [87.865, 89.362] | **+108.68%** | **accept** |
| `-flto` | no | 49.019 | [48.755, 49.284] | **+15.44%** | **accept** |
| `-fno-ipa-cp-clone` | **yes** | 43.447 | [43.014, 43.880] | **+2.31%** | **accept** |
| `-fno-pie -no-pie` | yes | 42.683 | [42.307, 43.059] | +0.52% | reject |
| `-fno-math-errno` (fast-tracked) | yes | 42.683 | [42.069, 43.296] | +0.51% | reject |
| `-fprefetch-loop-arrays` | no | 42.533 | [41.808, 43.258] | +0.16% | reject |
| `-fno-stack-protector` | yes | 42.510 | [42.099, 42.921] | +0.11% | reject |
| `-fcf-protection=none` | yes | 42.157 | [41.614, 42.700] | -0.72% | reject |
| `-fipa-pta` | yes | 42.109 | [41.446, 42.773] | -0.84% | reject |
| `-funroll-loops` | yes | 42.037 | [41.846, 42.229] | -1.00% | reject |
| `-fno-unswitch-loops` | yes | 42.009 | [41.364, 42.653] | -1.07% | reject |
| `-U_FORTIFY_SOURCE` | yes | 41.926 | [41.343, 42.510] | -1.27% | reject |
| `-ffast-math` | yes | 41.369 | [40.902, 41.837] | **-2.58%** | reject |
| `-Ofast` | yes | 41.212 | [40.852, 41.571] | **-2.95%** | reject |

- **`-fno-unswitch-loops`'s first rep (trial 2278) read 36.14**, 14% below its siblings, drawing 40.0 W against their
  45-46 W; the bandwidth probe before it read a normal 45.6 GB/s, so the throttle began mid-run. The slow-rep rule
  replaced it (re-run 42.20). The reported mean and CI above are of the three kept reps; the flag is a reject either way.
- **Fast-math costs femflow about 2.6-3% even on scalar code**, where it gained 4.6% on marian. femflow has no
  `PORTABILITY` flag in this config (#38's cancellation doesn't apply), so this is fast-math itself, not a no-op. Why it loses here
  hasn't been checked.
- **`-fno-ipa-cp-clone` +2.31%** is the first memory-bound accept for that flag (`827.cppcheck_s`, frontend-bound,
  read +1.84% and was rejected on CI overlap). All three reps (43.25-43.56) sit above every `-O3` rep.
- `-march=native` and `-flto` read within 0.5 points of experiment 195 (+106.58%, +15.13%) on the same fingerprints
  (`ad9afc91`, `4d982b3d`). Pooled with 195's three reps, `-march=native` averages 88.81.

## Phase 5 combination

| Step | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | (reused from Phase 4) | 88.614 | [87.865, 89.362] | +108.68% vs baseline | accept |
| 2 | `+ -flto` | 88.838, 88.457, 88.579 | 88.625 | [88.142, 89.108] | +0.01% vs step 1 | reject |
| 3 | `+ -fno-ipa-cp-clone` | 89.104, 88.507, 88.626 | 88.746 | [87.960, 89.532] | +0.15% | reject |

Step 2 built 195's step-2 code again (`5673a072`) and read +0.01% (195: +0.03%).

**Pair tournament** (3 pairs, vs. baseline, then against the greedy winner's 88.614):

| Pair | Mean | 95% CI | Delta vs baseline | Same code as |
|---|---|---|---|---|
| `-fno-ipa-cp-clone` + `-march=native` | 88.753 | [88.679, 88.827] | +109.01% | step 3 (`3442d13b`) |
| `-flto` + `-march=native` | 88.022 | [85.418, 90.627] | +107.29% | step 2 (`5673a072`) |
| `-flto` + `-fno-ipa-cp-clone` | 47.332 | [46.724, 47.940] | +11.46% | |

- **Two of the three pairs re-measured a greedy step's code**, six timed runs, about 2 hours (#35).
- `-fno-ipa-cp-clone` + `-march=native` read 0.16% above the winner, with its CI inside the winner's, so it didn't
  replace it. Pooled with step 3, that binary averages 88.75, 0.15% above `-march=native` alone: a real but tiny
  effect at best.
- `-flto` + `-fno-ipa-cp-clone` (+11.46%) is below `-flto` alone (+15.44%): the scalar flags don't combine either.

## Phase 6 multipliers (on `-O3 -march=native`, 88.614)

| Stage | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 62.225, 63.495, 60.179 | 61.966 | [57.810, 66.122] | **-30.07%** | reject |
| PGO near-miss | — | | | | | none (no CI-clear Phase 4 reject) |
| Microarch | — | | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 78.293, 78.122, 77.267 (after one rerun) | 77.338 | [75.429, 79.246] | **-12.10%** | reject |

- **PGO built experiment 195's binary again** (`b72ab998`, all three builds), so SPECrate PGO reproduces on femflow
  across sessions, and the loss is the code, not a bad training run. But the same binary read 64.81 (49 W) in 195 and
  61.97 (43 W) here, 4.4% apart, with a 5.2% spread between this run's own reps: the widest session-to-session gap of
  any femflow binary (`-O3` 1.4%, `-march=native` 0.4%, `=256` 2.5%). Either way it is far below `-march=native`.
- `=256`'s third rep (75.67) was replaced by the spread rule (re-run 77.27). The reported mean is from 78.293, 78.122
  and 77.267, which is what the summary records.

## Comparison with the shape-filtered mine and with `chicago`

| | `niwot` 11-09 (shape filter) | `niwot` 11-14 (`--no-shape-filter`) | `chicago` 11-07 (shape filter) |
|---|---|---|---|
| Candidates run | 4 | 15 | 4 |
| Winning flags | `-O3 -march=native` | `-O3 -march=native` | `-O3 -flto -march=native` |
| Gain | +106.58% | +108.68% | +132.01% |
| Fast-math family alone | not run | -2.6% to -3.0% | not run |
| `-fno-math-errno` alone | not run | +0.51%, rejected | not run |
| `-fno-ipa-cp-clone` alone / on top | not run | +2.31% / +0.15% | not run |
| PGO on the winner | -27.18% | -30.07% (same binary) | -2.01% (on `-flto -march=native`) |
| `-mprefer-vector-width=256` | -10.92% | -12.10% | -15.68% |
| Trials / wall-clock | 31 / 13h18m | 85 / 36h56m | |

## What this means

#30's three re-mines are done:

| Benchmark | Excluded flags accepted alone | Gain on top of `-march=native` | Cost of the filter | Extra trials |
|---|---|---|---|---|
| `736.ocio_r` | `-fno-math-errno`, `-fcf-protection=none` | `-fno-math-errno` +2.10% | about 2 points | 55 (~15 h) |
| `772.marian_r` | five, +1.5% to +4.8% | none (fast-math -2.5%) | none | 78 (~23 h) |
| `766.femflow_r` | `-fno-ipa-cp-clone` | none (+0.15%) | none | 54 (~24 h) |

Only `-fno-math-errno` ever paid on top of the winner, and only on ocio, so PR #71's narrow exemption captures
everything the filter cost on these three. Its record is now one win (ocio), one flat to negative (marian), one flat
(femflow); at a screening run and a few confirmation runs per mine, it's still cheap to keep exempt. Dropping the filter
outright cost about 62 hours across the three for those 2 points.

The PGO loss (#40) is now confirmed on one binary measured in two sessions. The next step is still the
`cfm measure -O3 -march=native -flto -fprofile-use` that would test whether `-flto` explains `chicago`'s much smaller
loss.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 21 | 11 | +26.04% |
| `-flto` | 15 | 5 | +4.20% |
| `-fno-math-errno` | 4 | 2 | +2.03% |
| `-fcf-protection=none` | 5 | 2 | +1.07% |
| `-ffast-math` | 7 | 2 | +0.67% |
| `-fno-ipa-cp-clone` | 5 | 1 | +0.66% |
| `-Ofast` | 8 | 2 | +0.58% |
| `-mprefer-vector-width=256` | 13 | 2 | -1.66% |
| `-fprofile-use` | 16 | 2 | -4.11% |

**`-march=native` is now 11 of 21 in the memory-bound cluster, a strict majority, so it will be fast-tracked straight
to Phase 4** on the next memory-bound mine, starting with `709.cactus_r`. `-fno-math-errno` drops to 2 of 4 and no
longer qualifies.

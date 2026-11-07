# `cfm mine` results: 737.gmsh_r on `niwot`, 2026-11-06

`737.gmsh_r` is Gmsh, a C++ finite-element mesh generator, 16 copies under SPECrate. It ran sixth in the unattended
queue, with `--settle-seconds 600`, and is the first gmsh mine on any host.

## Headline result

**Nothing accepted: the winner is plain `-O3`** (ratio 27.829), but `-flto` is very likely a real +1.7% that Phase 5
threw away.

- **`-flto` measured +1.6% to +2.4% on all seven of its runs**, every one the same code (fingerprint `af7dfc6a`). Phase 4
  accepted it (+1.69%, CI [28.19, 28.41], clear of baseline's [27.54, 28.11]). Phase 5's greedy step re-measured the
  same flagset at +1.76%, but one high rep (28.488) widened its CI to [27.95, 28.69], which overlapped baseline, and
  it was rejected. With no greedy step accepted, the mine fell back to `-O3`. Pooled, the six confirmation-grade reps
  give 28.309, CI [28.205, 28.412], **+1.72%**, clear of baseline (#39).
- **Every other flag was flat** (-1.13% to +0.41%), including `-march=native` (-0.53%), PGO (-0.86%) and the
  hardening opt-outs.
- **The fast-math flags were cancelled again** by the config's `PORTABILITY = -fno-fast-math`, as on flightdm (#38):
  `-ffast-math` and `-fno-math-errno` built the same code as `-O3` and were skipped, and `-Ofast` measured +0.06%.
- **A clean run:** baseline CI ±1.02%, package power flat at 27-28 W, no reruns, nothing flagged.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 737.gmsh_r --settle-seconds 600` (uncapped, 10 min idle after `767.nest_r`) |
| Code | `main` at `a2d2cab` |
| Experiment id | 192 |
| Started / finished | 2026-11-06T19:25:14Z / 2026-11-07T14:13:29Z (18h48m, about 11.7 h of it settle) |
| Final status | `converged` |
| Trials | 72 (1795-1866) |
| Candidates screened / confirmed | 15 / 13 (plus the two skipped fast-math flags) |
| Fast-tracked (M4) | none (`-flto` at 2 of 7 memory-bound doesn't qualify) |
| Excluded on shape | none (memory-bound 42.7%, under the 55% margin) |
| Skipped as unchanged code (#58) | `-O3 -ffast-math`, `-O3 -fno-math-errno` (both the same code as `-O3`) |
| Winning flags | `["-O3"]`, 0.0% |
| Guards | no slow-rep, spread or low-power reruns; baseline recheck not flagged (-0.75%) |
| Power / temperature | package power median 27.0-28.1 W per trial; CPU 89-94 °C |
| Audit | `-ffast-math` NOT FOUND on trial 1810: cancelled by the portability flag, as on flightdm |

Each trial took about 16 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1795 | warm-up | 27.761 |
| 1796 | warm-up | 27.986 |
| 1797 | calibration | 27.770 |
| 1798 | calibration | 27.961 |
| 1799 | calibration | 27.756 |
| 1854 | recheck after Phase 4 | 27.619 (-0.75%, not flagged) |

Calibration mean **27.829**, 95% CI **[27.544, 28.114]** (±1.02%). Warm-up settled after 2 reps (1936 s). The reps
alternate between about 27.76 and 27.97; all six `-O3` builds had the same fingerprint (`e3e8440c`).

**Shape: `memory-bound`, 42.7%**, from the corpus (`reference-matrix:amd-370-64gb`). Under the 55% gate, so nothing
was excluded.

## Phase 3 screening (vs. most recent calibration rep, 27.756)

| Flags | Ratio | Delta |
|---|---|---|
| `-flto` | 28.315 | +2.01% |
| `-fno-ipa-cp-clone` | 27.994 | +0.86% |
| `-fno-stack-protector` | 27.938 | +0.66% |
| `-fgraphite-identity` | 27.904 | +0.53% |
| `-fno-pie -no-pie` | 27.853 | +0.35% |
| `-fcf-protection=none` | 27.835 | +0.29% |
| `-U_FORTIFY_SOURCE` | 27.823 | +0.24% |
| `-Ofast` | 27.744 | -0.04% |
| `-fprefetch-loop-arrays` | 27.722 | -0.12% |
| `-march=native` | 27.681 | -0.27% |
| `-fno-unswitch-loops` | 27.609 | -0.53% |
| `-fipa-pta` | 27.456 | -1.08% |
| `-funroll-loops` | 27.386 | -1.33% |
| `-ffast-math` | — | skipped, same code as `-O3` |
| `-fno-math-errno` | — | skipped, same code as `-O3` |

The 13 that ran all survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [27.544, 28.114])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-flto` | 28.299 | [28.192, 28.406] | **+1.69%** | **accept** |
| `-fno-pie -no-pie` | 27.943 | [27.602, 28.284] | +0.41% | reject |
| `-fcf-protection=none` | 27.895 | [27.396, 28.394] | +0.24% | reject |
| `-Ofast` | 27.846 | [27.572, 28.121] | +0.06% | reject |
| `-U_FORTIFY_SOURCE` | 27.799 | [27.521, 28.077] | -0.11% | reject |
| `-fno-stack-protector` | 27.793 | [27.600, 27.987] | -0.13% | reject |
| `-fno-ipa-cp-clone` | 27.772 | [27.709, 27.834] | -0.21% | reject |
| `-fgraphite-identity` | 27.770 | [27.688, 27.853] | -0.21% | reject |
| `-fprefetch-loop-arrays` | 27.740 | [27.645, 27.835] | -0.32% | reject |
| `-fno-unswitch-loops` | 27.712 | [27.613, 27.810] | -0.42% | reject |
| `-march=native` | 27.682 | [27.316, 28.048] | -0.53% | reject |
| `-funroll-loops` | 27.585 | [26.996, 28.174] | -0.88% | reject |
| `-fipa-pta` | 27.514 | [27.123, 27.906] | -1.13% | reject |

## Phase 5 combination

| Step | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -flto` | 28.488, 28.258, 28.210 | 28.319 | [27.950, 28.687] | +1.76% vs baseline | **reject (CI overlap)** |

The greedy step re-measures a single accepted flag on its own, so step 1 here is the same flagset, and the same
code, as the Phase 4 accept. Its mean was higher than Phase 4's, but three reps with a 0.28 spread gave a CI
that reached below baseline's upper bound (27.950 < 28.114). Nothing was left to combine, so there was no pair
tournament.

## Phase 6 multipliers (on `-O3`, 27.829)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 27.589 | [27.170, 28.009] | -0.86% | reject |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | `+ -march=znver5` | 27.693 | [27.527, 27.859] | -0.49% | reject |
| Microarch | `+ -mtune=znver5` | 27.887 | [27.347, 28.428] | +0.21% | reject |
| Vector width | — | | | | skipped (no `-march=` in the winning set) |

PGO ran on plain `-O3`, not on `-flto`, because of the Phase 5 reject. Its three builds shared one fingerprint
(`a7fd74e1`). `-flto -fprofile-use` was never measured.

## What this means

gmsh is one of the flattest benchmarks mined on this host: no flag moved it more than 2%. The one real effect,
`-flto` at about +1.7%, was lost to a Phase 5 rule that re-measures a Phase 4 accept from scratch and requires
the second sample to clear on its own. Pooling the two samples of the same code, or letting Phase 5's first step
keep the Phase 4 verdict when the fingerprint matches, would have kept it (#39). The best known setting for gmsh
on `niwot` is therefore `-O3 -flto` (+1.72% pooled), but the mine's recorded result stays `-O3`. `chicago`'s gmsh mine
accepted the same `-O3 -flto`, at +2.40% ([host_chicago](host_chicago.md)).

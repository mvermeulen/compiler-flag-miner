# `cfm mine` results: 731.astcenc_r on `niwot`, 2026-11-04

This is the first fprate benchmark mined to completion on `niwot`, and the first astcenc mine on any host. `731.astcenc_r` is
ARM's ASTC texture compressor: SIMD-heavy floating-point block encoding, 16 copies under SPECrate. It ran third in
the unattended queue, with `--settle-seconds 600`.

## Headline result

**`-O3 -march=native -Ofast`, +29.64% over plain `-O3`** (ratio 36.591 → 47.438).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 36.591 | — |
| `-O3 -march=native` | 44.084 | +20.48% |
| `+ -Ofast` | 47.438 | +7.61% |

- **`-march=native` +19.77% alone.** astcenc is written around SIMD vectors, and the generic x86-64 target leaves it on
  SSE2. The frontend-bound read
  (44.3%) is under the confidence margin, so it says little about this code.
- **`-Ofast` and `-ffast-math` both paid** (+5.51% and +4.94% alone), and both passed SPEC's validation, so astcenc's
  output tolerance accepts reassociated float math. On top of `-march=native`, `-Ofast` gained more (+7.61%) than it
  did alone. `-ffast-math` on top of that was skipped as unchanged code: `-Ofast` already includes it.
- **The cleanest mine on this host's fprate yet:** baseline CI ±1.47%, package power flat at 50-53 W, no slow-rep or
  low-power reruns, nothing flagged. astcenc never showed the memory throttle that ruined lbm.
- **PGO lost 2.45%** and `-mprefer-vector-width=256` was flat (+0.23%).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 731.astcenc_r --settle-seconds 600` (uncapped, 10 min idle after `782.lbm_r`) |
| Code | `main` at `3ded01d` |
| Experiment id | 189 |
| Started / finished | 2026-11-04T06:31:04Z / 2026-11-05T05:54:21Z (23h23m, about 14.5 h of it settle) |
| Final status | `converged` |
| Trials | 88 (1562-1649) |
| Candidates screened / confirmed | 14 / 3 (plus `-flto` fast-tracked, rejected) |
| Fast-tracked (M4) | `-flto` (9 of 12 frontend-bound) |
| Excluded on shape | none (frontend-bound 44.3%, under the 55% margin) |
| Skipped as unchanged code (#58) | `-O3 -march=native -Ofast -ffast-math` (greedy step 3) |
| Winning flags | `["-O3", "-march=native", "-Ofast"]`, +29.64% |
| Guards | no slow-rep or low-power reruns; no audit warnings; baseline recheck not flagged (+0.31%) |
| Power | package power median 50.1-53.1 W per trial |

Each trial took about 16 minutes, 10 of them the settle. So the settle more than doubled this mine's length and,
judging by the clean data, bought nothing here.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1562 | warm-up | 37.016 |
| 1563 | warm-up | 36.419 |
| 1564 | warm-up | 36.407 |
| 1565 | calibration | 36.712 |
| 1566 | calibration | 36.720 |
| 1567 | calibration | 36.342 |
| 1627 | recheck after Phase 4 | 36.703 (+0.31%, not flagged) |

Calibration mean **36.591**, 95% CI **[36.055, 37.128]** (±1.47%). Warm-up settled after 3 reps (2986 s). The first rep
read 1.6% high after idle, the usual pattern on this host.

**Shape: `frontend-bound`, 44.3%**, `vectorization_density=high`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`). Under the 55% gate, so nothing was excluded on `resource_dominance`.
`-mprefer-vector-width=256` was deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 36.342)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 43.805 | **+20.54%** |
| `-Ofast` | 39.014 | **+7.35%** |
| `-ffast-math` | 38.717 | **+6.54%** |
| `-fcf-protection=none` | 36.893 | +1.52% |
| `-fno-pie -no-pie` | 36.833 | +1.35% |
| `-fno-stack-protector` | 36.689 | +0.96% |
| `-fprefetch-loop-arrays` | 36.660 | +0.88% |
| `-fipa-pta` | 36.628 | +0.79% |
| `-U_FORTIFY_SOURCE` | 36.598 | +0.71% |
| `-fno-unswitch-loops` | 36.550 | +0.57% |
| `-funroll-loops` | 36.529 | +0.52% |
| `-fno-math-errno` | 36.488 | +0.40% |
| `-fgraphite-identity` | 36.430 | +0.24% |
| `-fno-ipa-cp-clone` | 36.327 | -0.04% |

All 14 survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [36.055, 37.128])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` | 43.824 | [43.034, 44.613] | **+19.77%** | **accept** |
| `-Ofast` | 38.606 | [38.346, 38.867] | **+5.51%** | **accept** |
| `-ffast-math` | 38.399 | [38.335, 38.463] | **+4.94%** | **accept** |
| `-fno-math-errno` | 36.906 | [36.244, 37.568] | +0.86% | reject |
| `-fprefetch-loop-arrays` | 36.794 | [35.329, 38.260] | +0.55% | reject |
| `-fcf-protection=none` | 36.756 | [36.183, 37.330] | +0.45% | reject |
| `-fno-pie -no-pie` | 36.743 | [35.934, 37.552] | +0.41% | reject |
| `-fno-stack-protector` | 36.629 | [35.925, 37.333] | +0.10% | reject |
| `-fno-unswitch-loops` | 36.619 | [36.063, 37.175] | +0.08% | reject |
| `-fno-ipa-cp-clone` | 36.570 | [35.706, 37.434] | -0.06% | reject |
| `-U_FORTIFY_SOURCE` | 36.540 | [36.119, 36.961] | -0.14% | reject |
| `-fgraphite-identity` | 36.411 | [35.951, 36.870] | -0.49% | reject |
| `-fipa-pta` | 36.311 | [36.022, 36.600] | -0.77% | reject |
| `-flto` (fast-tracked) | 36.266 | [35.275, 37.257] | -0.89% | reject |
| `-funroll-loops` | 36.031 | [35.640, 36.422] | -1.53% | reject |

- **`-fno-math-errno` alone did nothing** (+0.86%, CIs overlap), so `-Ofast`'s gain comes from reassociation,
  reciprocal approximations and the other fast-math pieces, not from dropping `errno`.
- **The hardening opt-outs were flat** (-0.14% to +0.45%) on vector-heavy code, the same as on diamond_s (#30).
- **`-flto` lost** on frontend-bound code for the fourth time (9 of 13 accepted now). astcenc's hot paths are
  already inlined within a few translation units.

## Phase 5 combination

| Step | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | 44.084 | [42.900, 45.267] | +20.48% vs baseline | accept |
| 2 | `+ -Ofast` | 47.438 | [46.410, 48.466] | +7.61% vs step 1 | accept |
| 3 | `+ -ffast-math` | — | | | skipped: same code as step 2 (#58) |
| Pair | `-Ofast` + `-march=native` | 47.589 | [46.705, 48.473] | +30.06% vs baseline | same code as the greedy winner (`095e23b9`, #35) |
| Pair | `-ffast-math` + `-march=native` | 47.460 | [46.599, 48.322] | +29.70% vs baseline | no change |
| Pair | `-Ofast` + `-ffast-math` | 38.740 | [38.346, 39.134] | +5.87% vs baseline | same code as `-Ofast` alone (`eb9a7597`, #37) |

Two of the three pairs re-measured code the mine had already timed, at three runs (about 45 minutes) each.

## Phase 6 multipliers (on `-O3 -march=native -Ofast`, 47.438)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 46.275 | [45.523, 47.027] | -2.45% | reject |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | — | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 47.547 | [46.939, 48.156] | +0.23% | reject |

- **PGO's three builds shared one fingerprint** (`d39e6069`), unlike SPECspeed's (#32), and still lost.
- **`=256` made no difference** on top of `-march=native`.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 14 | 9 | +6.23% |
| `-flto` | 13 | 9 | +5.89% |
| `-march=native` | 14 | 3 | +5.27% |
| `-funroll-loops` | 4 | 1 | +3.52% |
| `-ffast-math` | 4 | 1 | +1.41% |
| `-Ofast` | 4 | 1 | +1.21% |
| `-mprefer-vector-width=256` | 5 | 0 | -0.04% |

The frontend-bound cluster now mixes interpreter- and compiler-style code (where LTO/PGO win and `-march=native`
doesn't) with SIMD kernels whose read is under the margin (astcenc, graph500). The per-cluster priors describe
neither group well. That's another reason to want the margin and vectorization density in the knowledge key.

# `cfm mine` results: 736.ocio_r on `niwot`, 2026-11-10 (`--no-shape-filter` re-mine)

`736.ocio_r` is OpenColorIO, a C++ color-management library, 16 copies under SPECrate. This is a re-mine of the
2026-11-07 run ([write-up](mining_results.736.ocio_r.2026-11-07b.md), experiment 193) with `--no-shape-filter`, asked
for to test #30: that run's corpus shape (memory-bound 58.5%) cleared the 55% gate by 3.5 points and excluded 11 of
15 candidates, among them the fast-math family and the hardening opt-outs. Same `--settle-seconds 600`.

## Headline result

**`-O3 -march=native -fno-math-errno`, +26.21% over plain `-O3`** (ratio 38.325 → 48.370), against +22.35% for
`-O3 -march=native` in the shape-filtered mine.

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 38.325 | — |
| `+ -march=native` | 47.376 | +23.62% |
| `+ -fno-math-errno` | 48.370 | +2.10% |

- **The shape filter did cost something here.** Two of the 11 flags it excluded were accepted in Phase 4:
  `-fno-math-errno` (+4.00% alone) and `-fcf-protection=none` (+1.46% alone). `-fno-math-errno` kept +2.10% on top of
  `-march=native` (CIs clear), and `-fcf-protection=none` added nothing on top of that (-0.07%).
- **Measured in the same session, the filter's cost is about 2 points of gain.** In absolute ratios the winner is
  48.370 against experiment 193's 47.580, +1.66%. This session's `-O3` and `-march=native` both read about 1% lower
  than experiment 193's, on identical code (fingerprints `7010c36c` and `d124592b` in both).
- **`-ffast-math` and `-Ofast` were rejected** (+1.28% and +1.52%, CI overlap), well below `-fno-math-errno` alone,
  although `-ffast-math` includes it. ocio's `PORTABILITY = -fno-finite-math-only` comes after `OPTIMIZE`, so the
  rest of fast-math (`-funsafe-math-optimizations`, `-fno-signed-zeros`, `-fno-trapping-math`, ...) did reach the
  compiler, and apparently cost back most of what `-fno-math-errno` gives. Which part costs it hasn't been checked.
- **Everything else excluded last time was flat:** `-funroll-loops` +1.78%, `-fno-pie -no-pie` +1.68%,
  `-fno-stack-protector` +1.04%, `-fipa-pta` +0.51%, `-fno-unswitch-loops` +0.46%, `-fno-ipa-cp-clone` +0.45%,
  `-U_FORTIFY_SOURCE` +0.23%, all rejected on CI overlap.
- **PGO lost 2.10%** on top of the winner (experiment 193: -4.60%), and `-mprefer-vector-width=256` was flat
  (-0.18%).
- **A clean run:** baseline CI ±0.93%, no reruns of any kind, recheck +0.13%, bandwidth 44.1-45.6 GB/s throughout,
  package power 46-48 W on every trial.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 736.ocio_r --settle-seconds 600 --no-shape-filter` (uncapped, 10 min idle after `722.palm_r`) |
| Code | `main` at `2a54723` (includes PR #69) |
| Experiment id | 197 |
| Started / finished | 2026-11-09T19:48:41Z / 2026-11-10T19:45:35Z (23h57m, about 14.5 h of it settle) |
| Final status | `converged` |
| Trials | 87 (2017-2103) |
| Candidates screened / confirmed | 15 / 15 (none pruned at screening) |
| Fast-tracked (M4) | none (`-march=native` at 8 of 18 memory-bound doesn't qualify) |
| Excluded on shape | none (`--no-shape-filter`) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-march=native", "-fno-math-errno"]`, +26.21% |
| Guards | bandwidth gate waited once (30 s, trial 2017); no slow-rep, spread or low-power reruns; baseline recheck not flagged (+0.13%) |
| Power / temperature | package power median 46.0-48.1 W per trial; CPU 95-100 °C; bandwidth probes 44.1-45.6 GB/s |
| Audit | clean |

Each trial took about 16.5 minutes, 10 of them the settle. The 11 extra candidates and the larger Phase 5 that followed cost 55
more trials than experiment 193 (about 15 hours).

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 2017 | warm-up | 38.413 |
| 2018 | warm-up | 38.366 |
| 2019 | calibration | 38.323 |
| 2020 | calibration | 38.182 |
| 2021 | calibration | 38.470 |
| 2082 | recheck after Phase 4 | 38.377 (+0.13%, not flagged) |

Calibration mean **38.325**, 95% CI **[37.967, 38.683]** (±0.93%). Warm-up settled after 2 reps (2040 s). All six
`-O3` builds had experiment 193's fingerprint (`7010c36c`); this session's `-O3` reads 1.45% below that run's 38.888.

**Shape: `memory-bound`, 58.5%**, `vectorization_density=high`, `allocation_pressure=high`, from the corpus
(`reference-matrix:amd-370-64gb`), as before. `-mprefer-vector-width=256` was still deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 38.470)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 47.259 | **+22.85%** |
| `-fno-math-errno` | 39.940 | **+3.82%** |
| `-fno-pie -no-pie` | 39.365 | +2.33% |
| `-funroll-loops` | 38.963 | +1.28% |
| `-Ofast` | 38.892 | +1.10% |
| `-ffast-math` | 38.833 | +0.94% |
| `-flto` | 38.617 | +0.38% |
| `-fipa-pta` | 38.568 | +0.25% |
| `-fno-ipa-cp-clone` | 38.452 | -0.05% |
| `-fgraphite-identity` | 38.443 | -0.07% |
| `-fcf-protection=none` | 38.427 | -0.11% |
| `-fno-unswitch-loops` | 38.335 | -0.35% |
| `-fprefetch-loop-arrays` | 38.287 | -0.48% |
| `-U_FORTIFY_SOURCE` | 38.277 | -0.50% |
| `-fno-stack-protector` | 38.242 | -0.59% |

All 15 survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [37.967, 38.683])

| Flags | Shape-filtered on 11-07? | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | no | 47.376 | [46.999, 47.752] | **+23.62%** | **accept** |
| `-fno-math-errno` | **yes** | 39.857 | [39.079, 40.635] | **+4.00%** | **accept** |
| `-fcf-protection=none` | **yes** | 38.886 | [38.756, 39.015] | **+1.46%** | **accept** |
| `-flto` | no | 39.056 | [38.395, 39.717] | +1.91% | reject |
| `-funroll-loops` | yes | 39.006 | [38.477, 39.535] | +1.78% | reject |
| `-fno-pie -no-pie` | yes | 38.968 | [38.193, 39.742] | +1.68% | reject |
| `-Ofast` | yes | 38.906 | [38.643, 39.170] | +1.52% | reject |
| `-ffast-math` | yes | 38.815 | [38.069, 39.561] | +1.28% | reject |
| `-fno-stack-protector` | yes | 38.722 | [38.557, 38.887] | +1.04% | reject |
| `-fprefetch-loop-arrays` | no | 38.653 | [38.313, 38.993] | +0.86% | reject |
| `-fipa-pta` | yes | 38.522 | [38.186, 38.858] | +0.51% | reject |
| `-fgraphite-identity` | no | 38.517 | [37.776, 39.258] | +0.50% | reject |
| `-fno-unswitch-loops` | yes | 38.500 | [37.920, 39.080] | +0.46% | reject |
| `-fno-ipa-cp-clone` | yes | 38.498 | [38.427, 38.569] | +0.45% | reject |
| `-U_FORTIFY_SOURCE` | yes | 38.412 | [37.907, 38.918] | +0.23% | reject |

- **`-fno-math-errno`'s three reps (39.53-40.15) all beat every `-O3` rep (38.18-38.47).** Without `errno`, GCC can
  inline `sqrt` as one instruction and treat other libm calls as pure, so it can vectorize loops that contain them.
  Which of ocio's calls benefit hasn't been checked.
- **`-fcf-protection=none`'s reps sat within 0.1 of each other** (CI ±0.33%), just clear of the baseline's upper
  bound; a small, precisely measured effect.
- **`-ffast-math` and `-Ofast` built their own code** (`c789d078`, `1c62ab7c`), distinct from `-fno-math-errno`'s
  (`341e500e`), so the portability flag didn't reduce them to it.
- **`-flto` read +1.91%** this time, against +0.47% in experiment 193 and +1.17% (accepted) on `chicago`, with CI
  overlap again. LTO on ocio is worth about 1% on both hosts, but `niwot`'s noise floor keeps rejecting it.

## Phase 5 combination

| Step | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | (reused from Phase 4) | 47.376 | [46.999, 47.752] | +23.62% vs baseline | accept |
| 2 | `+ -fno-math-errno` | 48.365, 48.535, 48.210 | 48.370 | [47.965, 48.774] | **+2.10% vs step 1** | **accept** |
| 3 | `+ -fcf-protection=none` | 48.236, 48.187, 48.579 | 48.334 | [47.803, 48.865] | -0.07% vs step 2 | reject |

Step 1 reused the Phase 4 accept (PR #69's hypothesis on trial 2061).

**Pair tournament** (vs. baseline, then against the greedy winner's 48.370):

| Pair | Mean | 95% CI | Delta vs baseline | vs greedy winner |
|---|---|---|---|---|
| `-fno-math-errno` + `-march=native` | 48.255 | [47.428, 49.081] | +25.91% | -0.24% |
| `-fcf-protection=none` + `-march=native` | 47.261 | [46.520, 48.002] | +23.32% | -2.29% |
| `-fcf-protection=none` + `-fno-math-errno` | 39.869 | [39.060, 40.679] | +4.03% | -17.57% |

None replaced the greedy winner. The first pair built the same code as greedy step 2 (`e21abce5`) and re-measured it
for three timed runs (#35). `-fcf-protection=none`'s +1.46% alone doesn't survive in any combination: with
`-fno-math-errno` it reads +4.03% against +4.00% without, and with `-march=native` -0.24% against `-march=native`
alone.

## Phase 6 multipliers (on `-O3 -march=native -fno-math-errno`, 48.370)

| Stage | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 47.279, 47.315, 47.473 | 47.355 | [47.099, 47.612] | **-2.10%** | reject |
| PGO near-miss | — | | | | | none |
| Microarch | — | | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 47.792, 48.622, 48.441 | 48.285 | [47.200, 49.370] | -0.18% | reject |

- **PGO's three builds had two fingerprints** (`43e7b0d4` twice, `26aa8fb1` once) and agreed within 0.4%. Last time
  all three differed (#32). The loss is smaller than experiment 193's -4.60% on `-march=native` alone, but still a loss,
  as on `chicago` (-5.13%).
- **No near-miss variant:** `-fno-stack-protector` (+1.04%) was the only reject over 1%, but its CI overlapped the
  baseline's, so it wasn't CI-clear.

## Comparison with the shape-filtered mine and with `chicago`

| | `niwot` 11-07 (shape filter) | `niwot` 11-10 (`--no-shape-filter`) | `chicago` 11-07 (shape filter) |
|---|---|---|---|
| Candidates run | 4 | 15 | 4 |
| Winning flags | `-O3 -march=native` | `-O3 -march=native -fno-math-errno` | `-O3 -march=native -flto` |
| Gain | +22.35% | +26.21% | +22.04% |
| Winner's ratio | 47.580 | 48.370 | |
| `-march=native` alone | +22.96% | +23.62% | +20.52% |
| `-flto` alone | +0.47%, rejected | +1.91%, rejected | +1.17%, accepted |
| PGO on the winner | -4.60% | -2.10% | -5.13% |
| Trials / wall-clock | 32 / 8h50m | 87 / 23h57m | |

## What this means

This answers #30 for ocio: the exclusion cost about 2 points. Only one of the 11 excluded flags, `-fno-math-errno`,
contributed to the final result, and its effect (inlining and vectorizing around libm calls) doesn't depend on whether the code is
memory-, frontend- or compute-bound. That argues for exempting `-fno-math-errno` from the shape filter, as `-flto`
already is, rather than turning the filter off: the other ten excluded flags cost 40 Phase 3-4 trials, plus nine in
Phase 5 for `-fcf-protection=none`, about 13 hours, for nothing that survived. The marian and femflow re-mines
queued next will show whether this generalizes.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 19 | 9 | +19.68% |
| `-flto` | 13 | 4 | +3.68% |
| `-fno-math-errno` | 2 | 1 | +1.59% |
| `-fcf-protection=none` | 3 | 1 | +0.62% |
| `-ffast-math` | 5 | 1 | +0.54% |
| `-Ofast` | 6 | 1 | +0.47% |
| `-funroll-loops` | 6 | 0 | +0.07% |

`-march=native` is now 9 of 19 accepted in the memory-bound cluster, one short of the majority the fast track needs.

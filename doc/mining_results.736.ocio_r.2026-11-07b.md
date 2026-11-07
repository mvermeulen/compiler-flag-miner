# `cfm mine` results: 736.ocio_r on `niwot`, 2026-11-07

`736.ocio_r` is OpenColorIO, a C++ color-management library that applies color transforms to image data, 16 copies
under SPECrate. It ran seventh in the unattended queue, with `--settle-seconds 600`. `chicago` mined it earlier the
same day ([write-up](mining_results.736.ocio_r.2026-11-07.md)); this file carries a `b` suffix to keep the two apart.

## Headline result

**`-O3 -march=native`, +22.35% over plain `-O3`** (ratio 38.888 → 47.580).

- **`-march=native` is the whole win.** It confirmed at +22.96% (CI [47.04, 48.60], far clear of baseline's
  [38.51, 39.26]) and re-measured at +22.35% as the greedy step. Every one of its seven runs (47.49-48.11) beat
  every `-O3` run (38.55-39.38) by more than 20%. That matches `chicago`'s +20.52% for the same flag.
- **`-flto` was flat here (+0.47%, CI overlap)**, where `chicago` accepted it at +1.17%.
- **PGO lost 4.60%** on top of `-march=native` (`chicago`: -5.13% on top of `-march=native -flto`), and
  `-mprefer-vector-width=256` made no difference (+0.24%).
- **Only four candidates ran.** The corpus shape (memory-bound 58.5%) cleared the 55% margin, so the shape filter
  dropped 11 candidates, the fast-math family and the hardening opt-outs among them, as on `chicago`.
- **A clean run:** baseline CI ±0.97%, package power flat at 48-50 W on every trial, no reruns, nothing flagged.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 736.ocio_r --settle-seconds 600` (uncapped, 10 min idle after `737.gmsh_r`) |
| Code | `main` at `a2d2cab` (before PR #69) |
| Experiment id | 193 |
| Started / finished | 2026-11-07T14:23:30Z / 2026-11-07T23:13:59Z (8h50m, about 5.3 h of it settle) |
| Final status | `converged` |
| Trials | 32 (1867-1898) |
| Candidates screened / confirmed | 4 / 4 |
| Fast-tracked (M4) | none (`-march=native` at 5 of 14 memory-bound doesn't qualify) |
| Excluded on shape | 11: `-Ofast`, `-ffast-math`, `-fno-math-errno`, `-funroll-loops`, `-fipa-pta`, and the six frontend-tagged flags (`-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops`) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-march=native"]`, +22.35% |
| Guards | bandwidth gate waited once (30 s, trial 1867); no slow-rep, spread or low-power reruns; baseline recheck not flagged (-0.53%) |
| Power / temperature | package power median 48.1-50.0 W per trial; CPU 96-100 °C; bandwidth probes 45.0-46.2 GB/s |
| Audit | clean (`-flto`/`-march=native` not independently checkable, as usual) |

Each trial took about 16.5 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1867 | warm-up | 39.378 |
| 1868 | warm-up | 38.548 |
| 1869 | warm-up | 38.704 |
| 1870 | calibration | 38.765 |
| 1871 | calibration | 38.842 |
| 1872 | calibration | 39.057 |
| 1889 | recheck after Phase 4 | 38.683 (-0.53%, not flagged) |

Calibration mean **38.888**, 95% CI **[38.512, 39.264]** (±0.97%). Warm-up settled after 3 reps (3031 s); as usual
on this host, the first rep after idle read high (+1.3%). All seven `-O3` builds had the same fingerprint
(`7010c36c`).

**Shape: `memory-bound`, 58.5%**, `vectorization_density=high`, `allocation_pressure=high`, from the corpus
(`reference-matrix:amd-370-64gb`). This is the first fprate mine on `niwot` whose read cleared the 55% gate, so the
shape filter excluded 11 of 15 candidates (`-flto` is exempt). `-mprefer-vector-width=256` was deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 39.057)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 47.515 | **+21.66%** |
| `-flto` | 39.370 | +0.80% |
| `-fprefetch-loop-arrays` | 38.885 | -0.44% |
| `-fgraphite-identity` | 38.721 | -0.86% |

All four survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [38.512, 39.264])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` | 47.817 | [47.037, 48.598] | **+22.96%** | **accept** |
| `-flto` | 39.071 | [38.796, 39.346] | +0.47% | reject |
| `-fgraphite-identity` | 39.053 | [38.926, 39.181] | +0.43% | reject |
| `-fprefetch-loop-arrays` | 38.730 | [38.150, 39.311] | -0.41% | reject |

`-flto`'s three reps (38.97-39.19) sit inside the `-O3` range. On `chicago` its reps all beat every `-O3` rep; here
the effect, if any, is under half a percent.

## Phase 5 combination

| Step | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | 47.651, 47.560, 47.529 | 47.580 | [47.423, 47.737] | +22.35% vs baseline | accept |

Only one flag was accepted, so there was no further step and no pair tournament. This mine ran before PR #69, so
step 1 re-measured the Phase 4 accept (same fingerprint, `d124592b`). With the fix it would have reused the Phase 4
outcome and saved three timed runs, about 50 minutes; the verdict is the same either way.

## Phase 6 multipliers (on `-O3 -march=native`, 47.580)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 45.390 | [44.592, 46.188] | **-4.60%** | reject |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | — | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 47.693 | [47.083, 48.302] | +0.24% | reject |

- **PGO's three builds had three different fingerprints** (`f676c4bb`, `571e14f3`, `315e9133`), unlike flightdm,
  nest and gmsh, whose SPECrate PGO builds reproduced. They still agreed within 1.3% (45.02-45.59), all well below the
  winner, and `chicago`'s PGO loss was the same size, so the loss is real (#32).
- **`=256` made no difference** on top of `-march=native`, as on astcenc, nest and `chicago`'s ocio.

## Comparison with `chicago`

| | `chicago` | `niwot` |
|---|---|---|
| Winning flags | `-O3 -march=native -flto` | `-O3 -march=native` |
| Gain | +22.04% | +22.35% |
| `-march=native` alone | +20.52% | +22.96% (Phase 4), +22.35% (greedy) |
| `-flto` alone | +1.17%, accepted | +0.47%, rejected |
| PGO on the winner | -5.13% | -4.60% |
| Excluded on shape | the same 11 | the same 11 |

The two hosts agree: ocio is an AVX-512 code (`vectorization_density=high`), and `-march=native` is worth about
+21-23% on both Zen5 parts. LTO is small on both.

## What this means

The shape filter is the open question. A color-transform library is the kind of code `-ffast-math` and `-Ofast`
often help, and the 58.5% read only just cleared the margin. ocio's portability flag is `-fno-finite-math-only`, not
`-fno-fast-math` as on flightdm and gmsh (#38), so most of `-ffast-math` would reach the compiler. A
`--no-shape-filter` re-mine of ocio, on either host, would answer it (`chicago`'s open item 8; #30 here).

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 15 | 6 | +11.82% |
| `-flto` | 9 | 3 | +3.47% |
| `-mtune=znver5` | 9 | 0 | +0.49% |
| `-fgraphite-identity` | 14 | 0 | +0.48% |

`-march=native` is now 6 of 15 accepted in the memory-bound cluster, still short of the majority the fast track
needs.

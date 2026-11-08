# `cfm mine` results: 772.marian_r on `niwot`, 2026-11-08

`772.marian_r` is Marian, a C++ neural machine-translation decoder, 16 copies under SPECrate. It ran eighth in the
unattended queue, with `--settle-seconds 600`. `chicago` mined it the same day
([write-up](mining_results.772.marian_r.2026-11-08.md)); this file carries a `b` suffix to keep the two apart. It is
the first mine on `niwot` with PR #69's greedy step 1 reuse (#39).

## Headline result

**`-O3 -march=native`, +63.40% over plain `-O3`** (ratio 57.103 → 93.307), the largest gain on `niwot`'s fprate so
far.

- **`-march=native` is the whole win.** It screened at +63.9% and confirmed at +63.40% (CI [92.05, 94.56], against
  baseline's [56.66, 57.55]). Marian's matrix kernels are plain loops for GCC to vectorize, and `-march=native` gives
  it AVX-512 and FMA. `chicago` got +72.43% from the same flag.
- **`-fprefetch-loop-arrays` (+19.06%) and `-fgraphite-identity` (+15.60%) were accepted alone, but add nothing on top
  of `-march=native`** (-1.22% and -0.07% as greedy steps). Together, without `-march=native`, they read +8.15%, less
  than prefetching alone. `chicago` saw the same pattern (+15.23%, +10.50%, then nothing on top).
- **PGO (-0.80%), `-mprefer-vector-width=256` (-0.67%) and `-flto` (-0.67%) were all flat.**
- **PR #69 worked as intended:** combination step 1 reused the Phase 4 accept instead of re-measuring it, saving three
  timed runs (about 50 minutes).
- **`-march=native` runs draw about 28 W against 49-51 W for `-O3`**, and PR #68's sibling check correctly kept them
  (see below). Otherwise a clean run: baseline CI ±0.78%, no reruns, nothing flagged.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 772.marian_r --settle-seconds 600` (uncapped, 10 min idle after `736.ocio_r`) |
| Code | `main` at `3cc6488` (includes PR #69) |
| Experiment id | 194 |
| Started / finished | 2026-11-07T23:23:59Z / 2026-11-08T15:00:38Z (15h37m, about 7.3 h of it settle) |
| Final status | `converged` |
| Trials | 44 (1899-1942) |
| Candidates screened / confirmed | 4 / 4 |
| Fast-tracked (M4) | none (`-march=native` at 6 of 15 memory-bound doesn't qualify) |
| Excluded on shape | 11, the same as ocio's: `-Ofast`, `-ffast-math`, `-fno-math-errno`, `-funroll-loops`, `-fipa-pta` and the six frontend-tagged flags |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-march=native"]`, +63.40% |
| Guards | bandwidth gate waited once (30 s, trial 1899); no slow-rep, spread or low-power reruns; baseline recheck not flagged (+0.33%) |
| Power / temperature | package power median 49.0-51.1 W for non-`-march=native` builds, 27.1-28.1 W for `-march=native` ones; CPU 95-99 °C; bandwidth probes 44.7-46.2 GB/s |
| Audit | clean |

Trials took about 16-19 minutes, 10 of them the settle, except PGO's: about 75 minutes each, because the training
run is long.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1899 | warm-up | 56.788 |
| 1900 | warm-up | 57.513 |
| 1901 | warm-up | 57.661 |
| 1902 | calibration | 57.300 |
| 1903 | calibration | 57.063 |
| 1904 | calibration | 56.946 |
| 1921 | recheck after Phase 4 | 57.289 (+0.33%, not flagged) |

Calibration mean **57.103**, 95% CI **[56.655, 57.550]** (±0.78%). Warm-up settled after 3 reps (3431 s). As on nest,
the first rep read low, not high. All seven `-O3` builds had the same fingerprint (`00969ecd`).

**Shape: `memory-bound`, 63.1%**, `vectorization_density=high`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). Over the 55% gate, so the shape filter left four candidates (`-flto` is exempt);
`-mprefer-vector-width=256` was deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 56.946)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 93.347 | **+63.92%** |
| `-fprefetch-loop-arrays` | 68.201 | **+19.76%** |
| `-fgraphite-identity` | 66.785 | **+17.28%** |
| `-flto` | 56.441 | -0.89% |

All four survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [56.655, 57.550])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` | 93.307 | [92.053, 94.561] | **+63.40%** | **accept** |
| `-fprefetch-loop-arrays` | 67.987 | [67.207, 68.768] | **+19.06%** | **accept** |
| `-fgraphite-identity` | 66.012 | [65.164, 66.859] | **+15.60%** | **accept** |
| `-flto` | 56.723 | [55.971, 57.474] | -0.67% | reject |

**`-march=native` ran at about 28 W**, against the baseline's 49.5 W reference, more than 8% below it. The
low-power rule would have rerun each rep, but PR #68's sibling check kept them: all three reps drew the same power,
so the low draw came from the code. The vectorized binary finishes in about 63% of `-O3`'s time and draws about
half the power; why is open. `-fprefetch-loop-arrays` and `-fgraphite-identity` drew slightly *more*
than `-O3` (51 W).

## Phase 5 combination

| Step | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | (reused from Phase 4) | 93.307 | [92.053, 94.561] | +63.40% vs baseline | accept |
| 2 | `+ -fprefetch-loop-arrays` | 92.303, 91.880, 92.316 | 92.166 | [91.550, 92.782] | -1.22% vs step 1 | reject |
| 3 | `+ -fgraphite-identity` | 93.291, 93.221, 93.199 | 93.237 | [93.118, 93.356] | -0.07% vs step 1 | reject |

Step 1 recorded the hypothesis "combination step 1 reuses this Phase 4 accept of ['-O3', '-march=native'] (same
flagset, same baseline comparison) instead of re-measuring it" on trial 1918. This is the first real run of the #39
fix.

**Pair tournament** (vs. baseline, then against the greedy winner's 93.307):

| Pair | Mean | 95% CI | Delta vs baseline | vs greedy winner |
|---|---|---|---|---|
| `-fgraphite-identity` + `-fprefetch-loop-arrays` | 61.755 | [61.425, 62.084] | +8.15% | -33.82% |
| `-fprefetch-loop-arrays` + `-march=native` | 93.080 | [91.830, 94.331] | +63.00% | -0.24% |
| `-fgraphite-identity` + `-march=native` | 92.804 | [90.819, 94.789] | +62.52% | -0.54% |

None replaced the greedy winner. The last two pairs built the same code as greedy steps 2 and 3 (fingerprints
`02da181c` and `eb1c73fe`) and spent six timed runs re-measuring them (#35).

## Phase 6 multipliers (on `-O3 -march=native`, 93.307)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 92.563 | [91.316, 93.810] | -0.80% | reject |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | — | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 92.681 | [92.175, 93.187] | -0.67% | reject |

- **PGO's three builds had three different fingerprints** (`8fbd194b`, `81ffe8db`, `4a914551`), as on ocio the day
  before, and agreed within 1.1% (#32). `chicago` measured PGO at -4.06%; here it was flat.
- **`=256` lost a little**: marian's kernels want the full 512-bit width.

## Comparison with `chicago`

| | `chicago` | `niwot` |
|---|---|---|
| Winning flags | `-O3 -march=native` | `-O3 -march=native` |
| Gain | +72.43% | +63.40% |
| `-fprefetch-loop-arrays` alone | +15.23%, accepted | +19.06%, accepted |
| `-fgraphite-identity` alone | +10.50%, accepted | +15.60%, accepted |
| Either on top of `-march=native` | +1.68% (CI overlap) / -1.49% | -1.22% / -0.07% |
| PGO on the winner | -4.06% | -0.80% |
| Excluded on shape | the same 11 | the same 11 |

## What this means

Marian is a vectorization benchmark: `-march=native` is worth +63% here and +72% on `chicago`'s Zen5, and the
loop-level flags only help a scalar build. As with ocio, the shape filter dropped fast-math and `-funroll-loops`, the
flags most likely to matter on top of a vectorized build; `chicago`'s open item 11 proposes a `--no-shape-filter`
re-mine (#30 here).

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 16 | 7 | +15.05% |
| `-flto` | 10 | 3 | +3.06% |
| `-fgraphite-identity` | 15 | 1 | +1.49% |
| `-fprefetch-loop-arrays` | 17 | 3 | +1.20% |

`-march=native` is now 7 of 16 accepted in the memory-bound cluster, still short of the majority the fast track needs.
`-fgraphite-identity` has its first accept on this host.

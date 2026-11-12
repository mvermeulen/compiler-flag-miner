# `cfm mine` results: 772.marian_r on `niwot`, 2026-11-12 (`--no-shape-filter` re-mine)

`772.marian_r` is Marian, a C++ neural machine-translation decoder, 16 copies under SPECrate. This is a re-mine of
the 2026-11-08 run ([write-up](mining_results.772.marian_r.2026-11-08b.md), experiment 194) with
`--no-shape-filter`, the second of three re-mines testing #30. That run's corpus shape (memory-bound 63.1%) excluded
11 of 15 candidates. Same `--settle-seconds 600`.

## Headline result

**`-O3 -march=native`, +64.13% over plain `-O3`** (ratio 56.710 → 93.075): the same winner as the shape-filtered
mine (+63.40%), on the same code (fingerprint `7c37ddc2` in both).

- **Five of the 11 excluded flags paid on scalar `-O3`.** `-Ofast` (+4.78%), `-ffast-math` (+4.59%),
  `-fno-math-errno` (+4.42%), `-fcf-protection=none` (+4.18%) and `-U_FORTIFY_SOURCE` (+1.51%) were all accepted in
  Phase 4, with `-march=native` (+64.13%), `-fprefetch-loop-arrays` (+20.92%) and `-fgraphite-identity` (+15.77%).
- **None of them adds anything on top of `-march=native`.** All seven greedy steps were rejected: fast-math and
  `-Ofast` *lost* about 2.5%, the rest were within ±1.1%. So on marian the shape filter's exclusion cost nothing,
  unlike ocio (#30).
- **`-fno-math-errno`, which PR #71 now exempts from the filter, read +0.32% on top of `-march=native` as a greedy
  step and -2.32% when the pair tournament re-measured the same code** (`7f4aa8fa`). Pooled, the six reps average
  92.146, 1.0% below `-march=native` alone. It paid on ocio, not here.
- **PGO (-0.96%) and `-mprefer-vector-width=256` (-1.14%) were flat to slightly negative**, as in the first mine.
- **A clean run:** baseline CI ±0.52%, one spread rerun (`-fprefetch-loop-arrays`), recheck +0.12%. It took 38h59m,
  against 15h37m for the shape-filtered mine.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 772.marian_r --settle-seconds 600 --no-shape-filter` (uncapped, 10 min idle after the ocio re-mine) |
| Code | `main` at `e6b01f7` (before PR #71; irrelevant here, since the filter was off) |
| Experiment id | 198 |
| Started / finished | 2026-11-10T19:55:55Z / 2026-11-12T10:54:28Z (38h59m, about 20 h of it settle) |
| Final status | `converged` |
| Trials | 122 (2104-2225) |
| Candidates screened / confirmed | 15 / 14 (`-fno-unswitch-loops` pruned) |
| Fast-tracked (M4) | none (`-march=native` at 9 of 19 memory-bound doesn't qualify) |
| Excluded on shape | none (`--no-shape-filter`) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-march=native"]`, +64.13% |
| Guards | bandwidth gate waited once (30 s, trial 2104); one spread rerun (trial 2127, `-fprefetch-loop-arrays`, replaced by 2128); baseline recheck not flagged (+0.12%) |
| Power / temperature | package power median 47-50 W for scalar builds, 26-28 W for every `-march=native` build; CPU 96-100 °C; bandwidth probes 43.8-45.6 GB/s |
| Audit | clean |

Each trial took about 16-18 minutes, 10 of them the settle; each PGO trial about 75.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 2104 | warm-up | 56.468 |
| 2105 | warm-up | 57.231 |
| 2106 | warm-up | 57.738 |
| 2107 | calibration | 56.576 |
| 2108 | calibration | 56.756 |
| 2109 | calibration | 56.798 |
| 2168 | recheck after Phase 4 | 56.777 (+0.12%, not flagged) |

Calibration mean **56.710**, 95% CI **[56.417, 57.003]** (±0.52%). Warm-up settled after 3 reps (3437 s). All `-O3`
builds had experiment 194's fingerprint (`00969ecd`); this session's `-O3` reads 0.69% below that run's 57.103.

**Shape: `memory-bound`, 63.1%**, `vectorization_density=high`, `allocation_pressure=moderate`, from the corpus, as
before. `-mprefer-vector-width=256` was still deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 56.798)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 93.860 | **+65.25%** |
| `-fprefetch-loop-arrays` | 67.951 | **+19.64%** |
| `-fgraphite-identity` | 65.066 | **+14.56%** |
| `-Ofast` | 59.590 | +4.92% |
| `-fno-math-errno` | 59.473 | +4.71% |
| `-ffast-math` | 59.227 | +4.28% |
| `-fcf-protection=none` | 58.679 | +3.31% |
| `-funroll-loops` | 57.394 | +1.05% |
| `-fno-stack-protector` | 57.390 | +1.04% |
| `-fipa-pta` | 57.114 | +0.56% |
| `-fno-ipa-cp-clone` | 57.112 | +0.55% |
| `-U_FORTIFY_SOURCE` | 56.953 | +0.27% |
| `-fno-pie -no-pie` | 56.725 | -0.13% |
| `-flto` | 56.346 | -0.80% |
| `-fno-unswitch-loops` | 51.404 | **-9.50%, pruned** |

## Phase 4 confirmation (3 reps each, vs. baseline CI [56.417, 57.003])

| Flags | Shape-filtered on 11-08? | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | no | 93.075 | [92.179, 93.972] | **+64.13%** | **accept** |
| `-fprefetch-loop-arrays` | no | 68.266 | [67.022, 69.511] | **+20.92%** | **accept** |
| `-fgraphite-identity` | no | 65.655 | [64.300, 67.010] | **+15.77%** | **accept** |
| `-Ofast` | **yes** | 59.420 | [59.317, 59.523] | **+4.78%** | **accept** |
| `-ffast-math` | **yes** | 59.312 | [58.211, 60.412] | **+4.59%** | **accept** |
| `-fno-math-errno` | **yes** | 59.214 | [59.082, 59.347] | **+4.42%** | **accept** |
| `-fcf-protection=none` | **yes** | 59.083 | [58.633, 59.533] | **+4.18%** | **accept** |
| `-U_FORTIFY_SOURCE` | **yes** | 57.564 | [57.059, 58.069] | **+1.51%** | **accept** |
| `-fipa-pta` | yes | 57.097 | [55.508, 58.685] | +0.68% | reject |
| `-fno-stack-protector` | yes | 57.016 | [56.565, 57.466] | +0.54% | reject |
| `-fno-pie -no-pie` | yes | 56.622 | [55.744, 57.501] | -0.15% | reject |
| `-funroll-loops` | yes | 56.669 | [56.517, 56.822] | -0.07% | reject |
| `-fno-ipa-cp-clone` | yes | 56.639 | [54.952, 58.327] | -0.12% | reject |
| `-flto` | no | 56.552 | [56.052, 57.052] | -0.28% | reject |

- `-fprefetch-loop-arrays`'s third rep (67.34) was replaced by the spread rule (re-run 67.92).
- **The fast-math family and `-fno-math-errno` all land at +4.4% to +4.8%** with tight CIs. Unlike ocio, marian has
  no portability flag taking part of fast-math back, and the whole family gives about the same gain as
  `-fno-math-errno` alone, which suggests that one piece does the work on scalar code.
- **`-fcf-protection=none` +4.18%** is large for a hardening opt-out (ocio: +1.46%; on frontend-bound intspeed it
  never cleared 1%). Why marian's scalar build pays this much for CET hasn't been checked.

## Phase 5 combination

| Step | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | (reused from Phase 4) | 93.075 | [92.179, 93.972] | +64.13% vs baseline | accept |
| 2 | `+ -fprefetch-loop-arrays` | 91.892, 92.605, 91.889 | 92.129 | [91.104, 93.154] | -1.02% vs step 1 | reject |
| 3 | `+ -fgraphite-identity` | 92.242, 92.221, 91.711 | 92.058 | [91.311, 92.804] | -1.09% | reject |
| 4 | `+ -Ofast` | 91.439, 90.501, 90.421 | 90.787 | [89.381, 92.193] | **-2.46%** | reject |
| 5 | `+ -ffast-math` | 90.514, 90.469, 91.221 | 90.735 | [89.687, 91.782] | **-2.52%** | reject |
| 6 | `+ -fno-math-errno` | 92.675, 93.469, 93.982 | 93.375 | [91.739, 95.011] | +0.32% | reject |
| 7 | `+ -fcf-protection=none` | 93.124, 92.186, 92.689 | 92.666 | [91.500, 93.833] | -0.44% | reject |
| 8 | `+ -U_FORTIFY_SOURCE` | 92.361, 92.915, 93.692 | 92.989 | [91.329, 94.650] | -0.09% | reject |

Every step was rejected, so each was tried on `-O3 -march=native` alone. Steps 2 and 3 built the same code as in
experiment 194 (`02da181c`, `eb1c73fe`) and read within 1% of it again. Every `-march=native` build drew 26-28 W,
fast-math or not.

**Pair tournament** (10 pairs, vs. baseline, then against the greedy winner's 93.075):

| Pair | Mean | 95% CI | Delta vs baseline | Same code as |
|---|---|---|---|---|
| `-U_FORTIFY_SOURCE` + `-march=native` | 93.080 | [90.498, 95.661] | +64.13% | step 8 |
| `-fcf-protection=none` + `-march=native` | 91.654 | [90.984, 92.324] | +61.62% | step 7 |
| `-Ofast` + `-march=native` | 91.424 | [90.125, 92.723] | +61.21% | step 4 |
| `-fno-math-errno` + `-march=native` | 90.917 | [90.166, 91.669] | +60.32% | step 6 |
| `-ffast-math` + `-march=native` | 90.895 | [88.955, 92.835] | +60.28% | step 5 |
| `-fcf-protection=none` + `-fgraphite-identity` | 65.442 | [64.774, 66.111] | +15.40% | |
| `-fno-math-errno` + `-fprefetch-loop-arrays` | 62.969 | [62.083, 63.854] | +11.04% | |
| `-U_FORTIFY_SOURCE` + `-fprefetch-loop-arrays` | 62.002 | [60.771, 63.234] | +9.33% | |
| `-U_FORTIFY_SOURCE` + `-fgraphite-identity` | 61.489 | [60.246, 62.732] | +8.43% | |
| `-fcf-protection=none` + `-fno-math-errno` | 58.759 | [58.403, 59.115] | +3.61% | |

- **Half the pairs re-measured a greedy step's code**: five pairs, 15 timed runs, about 4 hours (#35).
- **The re-measurements show the noise between sessions of the same binary**: within 1.2% for four of the five, but
  2.6% for `-fno-math-errno` (93.375 as step 6 at 19:35-20:07Z, 90.917 as a pair at 05:49-06:21Z), at the same
  26-28 W. That is wider than either CI and is what #37 (a)'s pooling would average out.
- **The scalar flags don't combine either**: every scalar pair is below its better member alone, e.g.
  `-fno-math-errno` + `-fprefetch-loop-arrays` +11.04% against prefetching's +20.92% alone.
- None replaced the greedy winner. `-U_FORTIFY_SOURCE` + `-march=native` read 0.005% above it, nowhere near CI-clear.

## Phase 6 multipliers (on `-O3 -march=native`, 93.075)

| Stage | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 92.397, 92.432, 91.727 | 92.185 | [91.198, 93.172] | -0.96% | reject |
| PGO near-miss | — | | | | | none (no CI-clear Phase 4 reject) |
| Microarch | — | | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 92.289, 91.964, 91.784 | 92.012 | [91.377, 92.648] | -1.14% | reject |

PGO's three builds had three fingerprints again, but two of them (`4a914551`, `8fbd194b`) are fingerprints that
experiment 194's PGO builds also produced: SPEC's retrained PGO builds of marian land on a small set of distinct
binaries rather than a new one every time (#32).

## Comparison with the shape-filtered mine and with `chicago`

| | `niwot` 11-08 (shape filter) | `niwot` 11-12 (`--no-shape-filter`) | `chicago` 11-08 (shape filter) |
|---|---|---|---|
| Candidates run | 4 | 15 | 4 |
| Winning flags | `-O3 -march=native` | `-O3 -march=native` | `-O3 -march=native` |
| Gain | +63.40% | +64.13% | +72.43% |
| Fast-math family alone | not run | +4.4% to +4.8%, accepted | not run |
| Fast-math on top of `-march=native` | not run | -2.5% (`-fno-math-errno` about -1%, pooled) | not run |
| PGO on the winner | -0.80% | -0.96% | -4.06% |
| Trials / wall-clock | 44 / 15h37m | 122 / 38h59m | |

## What this means

The answer to #30 on marian is "no cost": the excluded flags are real gains on a scalar build (+4% each for
fast-math, `-fno-math-errno` and `-fcf-protection=none`), but `-march=native`'s AVX-512 build absorbs all of them,
and fast-math costs 2.5% on top of it. With ocio's +2.1%, the record for `-fno-math-errno` on top of
`-march=native` is now one win and one flat-to-negative, which still fits PR #71's narrow exemption: on a benchmark like
marian it costs a screening run, three confirmation runs and a greedy step, and on ocio it found 2 points. Dropping the filter outright cost 78 more trials (about
23 hours) here for nothing. The femflow re-mine, next, is the third data point.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 20 | 10 | +21.90% |
| `-fno-math-errno` | 3 | 2 | +2.53% |
| `-fgraphite-identity` | 18 | 2 | +2.13% |
| `-fprefetch-loop-arrays` | 21 | 4 | +1.86% |
| `-fcf-protection=none` | 4 | 2 | +1.51% |
| `-ffast-math` | 6 | 2 | +1.21% |
| `-Ofast` | 7 | 2 | +1.08% |
| `-U_FORTIFY_SOURCE` | 4 | 1 | +0.21% |

`-march=native` is now exactly 10 of 20 in the memory-bound cluster, still not the strict majority the fast track
needs.

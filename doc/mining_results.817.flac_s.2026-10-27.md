# `cfm mine` results: 817.flac_s on `niwot`, 2026-10-27

The eighth SPECspeed benchmark mined on `niwot`. `817.flac_s` is the FLAC lossless audio encoder, run as
`flac -j 16`, which encodes with 16 pthreads. There's no rate counterpart in this suite, so this is its first
mine on either host. It runs unpinned. It's also the first mine on PRs #57 (catalog pruning and opt-out
candidates) and #58 (skipping timed runs when the code doesn't change).

## Headline result

**`-O3 -fprefetch-loop-arrays -march=native -mprefer-vector-width=256`, +148.2% over plain `-O3`** (ratio
2.387 → 5.923). By far the largest gain on either host. The previous largest was stockfish_r's
`-march=native`, at +48%.

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 2.387 | — |
| `-O3 -march=native` | 5.455 | **+128.5%** |
| `+ -fprefetch-loop-arrays` (pair tournament) | 5.503 | +0.88% |
| `+ -mprefer-vector-width=256` | 5.923 | **+7.64%** |

- **`-march=native` more than doubles the speed.** The run passed SPEC's output check
  (`valid: S`, `Success: 1x817.flac_s`), and all three confirmation reps agree to ±0.05%.
- **Not from flac's own SIMD code.** SPEC's `spec_config.h` defines `FLAC__NO_ASM` and leaves
  `FLAC__USE_AVX` unset, which turns off flac's intrinsic paths for every `-march`. So the gain is GCC's
  own vectorization of the encoder's integer loops. Not investigated further. One plausible reason:
  baseline x86-64 has only SSE2, which has no packed 32-bit integer multiply (`pmulld` is SSE4.1), and the
  LPC loops need one.
- **`-mprefer-vector-width=256` adds +7.6% on top.** Under `-march=native` GCC prefers 512-bit vectors on
  Zen5. Here 256 is clearly better, the first accept for this flag on `niwot`.
- **`-fprefetch-loop-arrays` is +2.75% alone** but only +0.88% on top of `-march=native`. It entered the
  winning set through the pair tournament, which has no 1% bar (see Phase 5 below).
- **PGO lost 1.26%.**

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 817.flac_s` (uncapped, queued after `801.xz_s`) |
| Code | `main` at `8c69c53` (PRs #56-58) |
| Experiment id | 180 |
| Started / finished | 2026-10-26T23:18:37Z / 2026-10-27T05:11:28Z (5h53m) |
| Final status | `converged` |
| Trials | 37 (1087-1123) |
| Candidates screened / confirmed | 4 / 2 |
| Fast-tracked (M4) | none |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-fprefetch-loop-arrays", "-march=native", "-mprefer-vector-width=256"]`, +148.16% |
| Thread placement | pthread, not pinned |
| Guards | bandwidth gate 44.5-46.1 GB/s before every run, waited only before the first (30 s); no slow-rep reruns; no audit warnings; baseline recheck not flagged (+0.18%) |
| Power profile | `balanced`; CPU temp 80.8-84.6°C, package power 21.0-23.1 W |

About 13 minutes per `-O3`-speed trial, and 6 minutes once `-march=native` is in.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1087 | warm-up (excluded from CI) | 2.4068 |
| 1088 | warm-up (excluded from CI) | 2.3846 |
| 1089 | calibration | 2.3857 |
| 1090 | calibration | 2.3872 |
| 1091 | calibration | 2.3881 |
| 1108 | recheck after Phase 4 | 2.3913 (+0.18%, not flagged) |

Calibration mean **2.3870**, 95% CI **[2.3839, 2.3900]** (±0.13%). That's the tightest of the eight speed mines,
pinned ones included. As on ntest_s, the first warm-up read high after idle time (here +0.8%).

**Shape: `memory-bound`, 65.1%**, `vectorization_density=moderate`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`). That's past the 55% gate, and a 2.3x `-march=native` gain says the shape
says little about what pays here. See "Phase 2" below.

## Phase 2: eleven exclusions, including all seven of PR #57's new flags

| Excluded | Tagged |
|---|---|
| `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE` (new, #57) | frontend-bound |
| `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (new, #57) | frontend-bound |
| `-fno-math-errno` (new, #57) | compute-bound |
| `-Ofast`, `-ffast-math` | compute-bound |
| `-funroll-loops` | compute- and backend-bound |
| `-fipa-pta` | backend-bound |

`-flto` was kept under #28. `-mprefer-vector-width=256` was held for Phase 6. #57 removed the `=512` setting,
since it's the default under `-march=znver5`/`native`. That left four candidates to screen.

**So this mine tested none of #57's new candidates.** A confident memory-bound shape excludes all of them.
Whether the hardening opt-outs should be shape-exempt like `-flto` is an open question (below).

## Phase 3 screening (vs. most recent calibration rep, 2.3881)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 5.4519 | **+128.29%** |
| `-fprefetch-loop-arrays` | 2.4523 | **+2.69%** |
| `-flto` | 2.3864 | -0.07% |
| `-fgraphite-identity` | 2.3795 | -0.36% |

All four survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [2.3839, 2.3900])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | 5.4566, 5.4554, 5.4575 | 5.4565 | [5.4538, 5.4592] | **+128.60%** | **accept** |
| `-fprefetch-loop-arrays` | 2.4548, 2.4525, 2.4507 | 2.4527 | [2.4476, 2.4577] | **+2.75%** | **accept** |
| `-flto` | 2.3870, 2.3866, 2.3859 | 2.3865 | [2.3850, 2.3880] | -0.02% | reject |
| `-fgraphite-identity` | 2.3765, 2.3789, 2.3792 | 2.3782 | [2.3746, 2.3818] | -0.37% | reject |

`-flto` is about as flat as a measurement gets here. Both mines since #28 kept it past a confident memory-bound shape
have found nothing (xz_s +0.08%, flac_s -0.02%), against abc_s's +2.32% follow-up.

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | 5.4553, 5.4551, 5.4542 | 5.4549 | [5.4534, 5.4564] | +128.53% vs baseline | accept |
| 2 | `+ -fprefetch-loop-arrays` | 5.5116, 5.5051, 5.5070 | 5.5079 | [5.4996, 5.5161] | +0.97% vs step 1 | reject (under the 1% bar) |
| Pair | `-fprefetch-loop-arrays` + `-march=native` | 5.5043, 5.5023, 5.5019 | 5.5029 | [5.4997, 5.5061] | +130.54% vs baseline | accept, **replaces the greedy winner** |

**The pair tournament let in a flag the greedy walk had just rejected.** The greedy step measured the same two
flags (in a different order) at +0.97% over `-march=native` alone, and rejected it for missing the 1% bar by
0.03%. The pair trial then measured +0.88% over the greedy winner. The replacement rule
(`greedy_combine()`, orchestrator.py) requires a higher mean and a non-overlapping CI against the running set,
but not `MIN_PRACTICAL_SIGNIFICANCE_PCT`. Each rule is reasonable on its own, but together they disagree about
the same flags. The effect is real here (both CIs clear the greedy winner's), so the result stands. The
inconsistency is worth a small fix, recorded as opportunity #29.

## Phase 6 multipliers (on `-O3 -fprefetch-loop-arrays -march=native`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 5.4242, 5.4367, 5.4403 | 5.4337 | [5.4128, 5.4547] | **-1.26%** | reject (CI-clear below) |
| Microarch | — | | | | | skipped (`-march=native` already in the winning set) |
| Vector width | `+ -mprefer-vector-width=256` | 5.9224, 5.9248, 5.9232 | 5.9234 | [5.9204, 5.9264] | **+7.64%** | **accept** |

The audit confirmed `-O3 -fprefetch-loop-arrays -mprefer-vector-width=256` in the final binary. As always,
`-march=native` can't be checked from the recorded switches.

## PR #58 in practice

Every trial recorded a `code_fingerprint`. All six `-O3` reps share one, as expected, and every candidate's
differs from it, so no timed run was skipped (`flagsets_skipped_as_unchanged_code: []`). The skip can only
fire for a flag that leaves the code unchanged. The likely candidates for that were the opt-outs #57 added,
and none of them got this far. The skip itself is still untested in a real mine.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 11 | 4 | +12.97% |
| `-flto` | 5 | 2 | +4.48% |
| `-fprefetch-loop-arrays` | 12 | 2 | +0.83% |
| `-fprofile-use` | 6 | 2 | +0.83% |
| `-mprefer-vector-width=256` | 5 | 1 | -0.27% |

flac's +128.6% pulls `-march=native`'s memory-bound mean from +1.41% to +12.97%. One benchmark
now dominates the mean. At 4 of 11 it still doesn't qualify for the
fast track, so the outlier changes no future candidate order. But a mean is a poor summary for this flag.

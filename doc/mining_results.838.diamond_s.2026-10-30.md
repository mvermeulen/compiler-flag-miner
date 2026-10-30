# `cfm mine` results: 838.diamond_s on `niwot`, 2026-10-30

The eleventh SPECspeed benchmark mined on `niwot`. `838.diamond_s` is DIAMOND, a protein sequence aligner,
which runs its search on pthreads, unpinned. There's no rate counterpart in this suite, so this is its first mine on
either host. It's also the second mine on #59's warm-up and power-median rules, and the first compute-bound
speed mine.

## Headline result

**`-O3 -flto -funroll-loops -march=znver5`, +34.49% over plain `-O3`** (ratio 0.9384 → 1.2620).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 0.9384 | — |
| `-O3 -flto` | 0.9543 | +1.69% |
| `+ -funroll-loops` | 0.9649 | +1.16% |
| `+ -march=znver5` (microarch multiplier) | 1.2620 | **+30.73%** |

- **`-march=native` measured -6.17% in Phase 4, and `-march=znver5` measured +30.73% in Phase 6.** On this host
  the two are nearly the same target. GCC's `-march=native` expands to `-march=znver5 -mtune=znver5` plus the
  same cache `--param`s znver5 already defaults to (L1 48 KB, L2 1024 KB), and three ISA bits differ
  (`-mprefetchi` and `-mrdseed` off, `-mshstk` on). Neither difference plausibly moves a sequence aligner
  by 37 points. What *did* differ is what each was layered on: `-march=native` went on plain `-O3`, and
  `-march=znver5` went on `-O3 -flto -funroll-loops`. So the likely story is an interaction: the wider ISA
  hurts alone and pays big with LTO and unrolling. That isn't measured yet (opportunity #34).
- **Both readings are tight.** The `-march=native` reps agree to ±0.02% (0.8803-0.8807), and the znver5 reps
  to ±0.48%. Both passed SPEC's validation, and the audit confirmed `-march=znver5` in the final binary.
- **Not diamond's own SIMD.** SPEC's `object.pm` builds with `-DDISPATCH_ARCH=ARCH_GENERIC`, which turns off
  DIAMOND's hand-written SSE/AVX dispatch for every `-march`. So, as on flac_s, the gain is GCC's own
  vectorization.
- **Only the microarch multiplier could have found this.** Phase 4 rejected `-march=native`, so it never
  reached Phase 5. Phase 6 then tried `-march=znver5` on the winning set only because `-march=native` wasn't
  in it. Had `-march=native` been in that set, the multiplier would have been skipped.
- **PGO lost 0.62%**, and its near-miss variant (`+ -fno-pie -no-pie`) lost 0.60%.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 838.diamond_s` (uncapped, queued after `827.cppcheck_s`) |
| Code | `main` at `fcf7e05` |
| Experiment id | 184 |
| Started / finished | 2026-10-29T15:04:58Z / 2026-10-30T17:39:42Z (26h35m) |
| Final status | `converged` |
| Trials | 85 (1237-1321) |
| Candidates screened / confirmed | 13 / 2 (plus 2 fast-tracked: `-flto` accepted, `-march=native` rejected) |
| Fast-tracked (M4) | `-march=native` (3 of 3 compute-bound), `-flto` (1 of 1) |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-flto", "-funroll-loops", "-march=znver5"]`, +34.49% |
| Thread placement | pthread, not pinned |
| Guards | bandwidth gate 43.1-45.9 GB/s, waited only before the first run (30 s); no slow-rep or low-power reruns; no audit warnings; baseline recheck not flagged (+0.11%) |
| Power profile | `balanced`; CPU temp 87.0-92.9°C, package power median 39.1-40.0 W |

About 18.6 minutes per `-O3`-speed trial, 22 for PGO (two builds and a training run), and 14.6 once
`-march=znver5` is in.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1237 | warm-up (excluded from CI) | 0.9444 |
| 1238 | warm-up (excluded from CI) | 0.9385 |
| 1239 | calibration | 0.9382 |
| 1240 | calibration | 0.9388 |
| 1241 | calibration | 0.9381 |
| 1300 | recheck after Phase 4 | 0.9394 (+0.11%, not flagged) |

Calibration mean **0.93838**, 95% CI **[0.93750, 0.93926]** (±0.09%), the tightest baseline of the speed mines.
Warm-up settled after two reps (2253 s). The first read +0.6% high after idle, as on ntest_s and flac_s.

**Shape: `compute-bound`, 45.4%**, `vectorization_density=low`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`). That's under the 55% gate, so Phase 2 excluded nothing on
`resource_dominance`.

## Phase 2

Nothing excluded on `resource_dominance`. One candidate was excluded on vectorization:
`-mprefer-vector-width=256` (tagged `vectorization-density-high`, against a corpus read of `low`).
So Phase 6's vector-width stage had nothing deferred to try, even though the final winning set has an `-march=`. Since `-march=znver5`
gained 30% here through GCC's vectorizer, the "low" read was wrong about what matters. On flac_s, `=256`
added +7.6% on top of `-march=native`, so it's worth a check here too (#34). `-march=native` and `-flto`
were fast-tracked on their priors, leaving 13 to screen. This is the first
mine that measured all of PR #57's new candidates on a non-frontend-bound benchmark.

## Phase 3 screening (vs. most recent calibration rep, 0.93814)

| Flags | Ratio | Delta |
|---|---|---|
| `-funroll-loops` | 0.9525 | **+1.53%** |
| `-fno-pie -no-pie` | 0.9412 | +0.33% |
| `-fprefetch-loop-arrays` | 0.9406 | +0.26% |
| `-fcf-protection=none` | 0.9401 | +0.20% |
| `-fno-ipa-cp-clone` | 0.9399 | +0.19% |
| `-U_FORTIFY_SOURCE` | 0.9382 | +0.01% |
| `-Ofast` | 0.9380 | -0.01% |
| `-fno-stack-protector` | 0.9378 | -0.04% |
| `-fno-math-errno` | 0.9377 | -0.05% |
| `-fgraphite-identity` | 0.9376 | -0.06% |
| `-ffast-math` | 0.9373 | -0.09% |
| `-fno-unswitch-loops` | 0.9360 | -0.22% |
| `-fipa-pta` | 0.9350 | -0.34% |

All 13 survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [0.93750, 0.93926])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-flto` (fast-tracked) | 0.9545 | [0.9542, 0.9549] | **+1.72%** | **accept** |
| `-funroll-loops` | 0.9523 | [0.9520, 0.9526] | **+1.48%** | **accept** |
| `-fno-pie -no-pie` | 0.9415 | [0.9411, 0.9419] | +0.34% | reject (CI-clear, under 1%) |
| `-fprefetch-loop-arrays` | 0.9411 | [0.9399, 0.9422] | +0.29% | reject (CI-clear, under 1%) |
| `-fno-ipa-cp-clone` | 0.9404 | [0.9403, 0.9405] | +0.21% | reject (CI-clear, under 1%) |
| `-fcf-protection=none` | 0.9400 | [0.9397, 0.9402] | +0.17% | reject (CI-clear, under 1%) |
| `-U_FORTIFY_SOURCE` | 0.9393 | [0.9383, 0.9403] | +0.10% | reject |
| `-fgraphite-identity` | 0.9388 | [0.9371, 0.9405] | +0.04% | reject |
| `-fno-stack-protector` | 0.9380 | [0.9376, 0.9383] | -0.04% | reject |
| `-Ofast` | 0.9374 | [0.9366, 0.9382] | -0.11% | reject |
| `-fipa-pta` | 0.9367 | [0.9363, 0.9372] | -0.17% | reject |
| `-fno-math-errno` | 0.9364 | [0.9329, 0.9398] | -0.22% | reject |
| `-ffast-math` | 0.9362 | [0.9345, 0.9380] | -0.23% | reject |
| `-fno-unswitch-loops` | 0.9359 | [0.9297, 0.9421] | -0.27% | reject |
| `-march=native` (fast-tracked) | 0.8805 | [0.8803, 0.8807] | **-6.17%** | reject |

- **`-march=native`'s first compute-bound loss**, after +14-20% on ntest_r and sealcrypto_r. See the
  headline: on top of LTO and unrolling the same ISA gained +30.7%.
- **The hardening opt-outs were flat** (-0.04% to +0.34%) on compute-bound code, against +2.92% for
  `-fno-stack-protector` on cppcheck_s (#30).
- **`-Ofast`/`-ffast-math`/`-fno-math-errno` were flat.** DIAMOND is integer code (alignment scores), so that's
  expected.

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -flto` | 0.9547, 0.9545, 0.9538 | 0.9543 | [0.9533, 0.9552] | +1.69% vs baseline | accept |
| 2 | `+ -funroll-loops` | 0.9651, 0.9656, 0.9653 | 0.9653 | | +1.16% vs step 1 | accept |
| Pair | `-flto` + `-funroll-loops` | 0.9654, 0.9642, 0.9639 | 0.9645 | | +2.78% vs baseline | same flagset as the greedy winner, no change |

LTO and unrolling stack almost exactly (+1.72% and +1.48% alone, +2.83% together). Across all six reps the
winner reads 0.9649, CI [0.9642, 0.9656].

## Phase 6 multipliers (on `-O3 -flto -funroll-loops`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 0.9608, 0.9586, 0.9587 | 0.9593 | [0.9563, 0.9624] | -0.62% | reject |
| PGO near-miss | `+ -fno-pie -no-pie -fprofile-use` | 0.9592, 0.9595, 0.9600 | 0.9595 | [0.9585, 0.9606] | -0.60% | reject |
| Microarch | `+ -march=znver5` | 1.2632, 1.2592, 1.2636 | 1.2620 | [1.2560, 1.2680] | **+30.73%** | **accept** |
| Microarch | `+ -mtune=znver5` | 0.9484, 0.9478, 0.9465 | 0.9476 | [0.9452, 0.9500] | -1.84% | reject |
| Vector width | — | | | | | skipped (`=256` excluded in Phase 2 on vectorization density) |

- **The ISA is what pays, not the tuning.** `-mtune=znver5` alone lost 1.84%. `-march=znver5` gained 30.7%.
- **PGO variance was small this time (#32).** All six PGO builds had different code fingerprints again, but
  they spread only 0.23% (0.9586-0.9608), close to one non-PGO binary's 0.18% over six reps.
  llvm_s and cppcheck_s were much wider.
- **Power.** The znver5 trials drew a median 39.1 W against 40.0 W for everything else, 2% lower and well
  inside the 8% low-power bar (#33).

## Knowledge table after this run (`compute-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=znver5` | 1 | 1 | +30.73% |
| `-march=native` | 4 | 3 | +10.93% |
| `-fprofile-use` | 2 | 1 | +5.35% |
| `-flto` | 2 | 2 | +2.66% |
| `-funroll-loops` | 4 | 1 | +0.28% |
| `-mtune=znver5` | 1 | 0 | -1.84% |

`-march=native` still qualifies for the fast track at 3 of 4. The table records the -6.17% against
`-march=native` and the +30.73% against `-march=znver5`. It can't tell that both are the same ISA on different bases,
which is the knowledge table's per-flag blind spot.

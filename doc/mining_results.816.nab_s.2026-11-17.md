# `cfm mine` results: 816.nab_s on `niwot`, 2026-11-17

This is the first fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `816.nab_s` is based on
Nucleic Acid Builder (NAB), a C molecular-modeling code parallelized with OpenMP. `chicago` mined it on 2026-11-10
([write-up](mining_results.816.nab_s.2026-11-10.md)). Its corpus shape is memory-bound at 46.6%, under the 55% shape
margin, so no candidate was excluded on shape. It is the first mine run with PR #72's throttle stop and the
`-ftree-parallelize-loops=16` config; neither touched nab (the config's flag is scoped to the `doconcurrent`
benchmark, `800.pot3d_s`, and nab's baseline never came near throttling).

## Headline result

**`-O3 -Ofast -fprofile-use -march=znver5`, +15.49% over plain `-O3`** (ratio 1.6230 → 1.8744).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.6230 | — |
| `-O3 -Ofast` | 1.6786 | +3.42% |
| `+ -fprofile-use` | 1.7511 | +4.32% |
| `+ -march=znver5` | 1.8744 | +7.04% |

- **The same three ingredients as `chicago`, in a different order, for almost the same total** (+15.49% against
  +15.10%). `chicago` won with `-ffast-math -march=native -fprofile-use`; here `-Ofast` won Phase 4 by a hair over
  `-ffast-math` (+3.42% against +3.23%) and builds the same code once the two are combined (fingerprint `3ff2532a`,
  the same as on `chicago`).
- **`-march=native` gave +0.26% alone and was rejected, but `-march=znver5` gave +7.04% on top of fast-math and
  PGO.** This is the interaction `chicago` saw (+1.37% alone, +5.6% on top of `-ffast-math`): fast-math lets GCC
  vectorize floating-point reductions and math it otherwise keeps scalar, and AVX-512 widens those vectors. On
  `chicago` the greedy walk found it; here `-march=native` never reached Phase 5, and the microarch multiplier
  found it instead. Without Phase 6's microarch slice this mine would have stopped at +7.89%.
- **PGO added +4.32%**, about as on `chicago` (+4.17%). No near-miss variant: no Phase 4 reject was CI-clear of
  baseline.
- **`-mtune=znver5` lost 0.78%** and `-mprefer-vector-width=256` on top of the winner was flat (+0.04%).
- **Every other candidate was within ±1% of `-O3`**, and none of them clear of it in the positive direction.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 816.nab_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `17f1869` (PR #72, throttle stop) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16`; `-ftree-parallelize-loops=16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 203 |
| Started / finished | 2026-11-17T04:08:46Z / 2026-11-18T09:54:33Z (29h46m) |
| Final status | `converged` |
| Trials | 83 (2444-2526), no reruns, 1 skipped as unchanged code |
| Candidates screened / confirmed | 14 / 14 (all survived screening; plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | none (memory-bound 46.6%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 12 of 21, mean +26.57%, after the 2026-11-17 knowledge cleanup) |
| Accepted in Phase 4 | `-Ofast` +3.42%, `-ffast-math` +3.23% |
| Winning flags | `["-O3", "-Ofast", "-fprofile-use", "-march=znver5"]`, +15.49% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (44.1-46.4 GB/s); no reruns; baseline recheck **flagged** (-0.79%, see below) |
| Power | package power median 47.0 W through trial 2485, then 43.0-45.0 W; CPU temperature 95.9-99.4°C |

A trial took about 22 minutes: an 11-minute timed run plus the 10-minute settle. On `chicago` a trial took about 6
minutes with no settle. Every trial's `.rsf` reads `valid: S`.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 46.6%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2444 | warm-up | 1.62431 |
| 2445 | warm-up | 1.60006 |
| 2446 | warm-up | 1.62369 |
| 2447 | warm-up | 1.62357 |
| 2448 | calibration | 1.6236 |
| 2449 | calibration | 1.6222 |
| 2450 | calibration | 1.6234 |
| 2510 | recheck | 1.61025 |

Warm-up settled after 4 reps (5273 s). The calibration mean is 1.62304, 95% CI about ±0.12%. The Phase 1 reps span
1.6%, so the throttle stop (2 or more reps more than 10% below the fastest) was nowhere near firing. On `chicago` the
same benchmark reads 3.364 at 85 W against 1.623 at 47 W here, about what the smaller part should give.

## Phase 3/4: screening and confirmation

All 14 screened candidates survived. Screening read within ±0.9% of `-O3`'s last calibration rep for twelve and +4.6% for `-Ofast` (1.699)
and `-ffast-math` (1.697).

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-Ofast` | 1.682, 1.679, 1.675 | 1.6786 | +3.42% | **accept** |
| `-ffast-math` | 1.672, 1.674, 1.680 | 1.6755 | +3.23% | **accept** |
| `-march=native` (fast-tracked) | 1.626, 1.628, 1.628 | 1.6273 | +0.26% | reject |
| `-fgraphite-identity` | 1.626, 1.624, 1.624 | 1.6246 | +0.10% | reject |
| `-fno-math-errno` | 1.623, 1.624, 1.624 | 1.6238 | +0.05% | reject |
| `-fno-pie -no-pie` | 1.624, 1.624, 1.622 | 1.6231 | +0.01% | reject |
| `-fprefetch-loop-arrays` | 1.622, 1.622, 1.620 | 1.6212 | -0.11% | reject |
| `-flto` | 1.620, 1.617, 1.624 | 1.6202 | -0.18% | reject |
| `-fno-stack-protector` | 1.622, 1.614, 1.621 | 1.6192 | -0.24% | reject |
| `-U_FORTIFY_SOURCE` | 1.620, 1.616, 1.617 | 1.6177 | -0.33% | reject |
| `-fno-unswitch-loops` | 1.617, 1.616, 1.617 | 1.6167 | -0.39% | reject |
| `-funroll-loops` | 1.617, 1.616, 1.612 | 1.6151 | -0.49% | reject |
| `-fno-ipa-cp-clone` | 1.613, 1.616, 1.615 | 1.6147 | -0.52% | reject |
| `-fcf-protection=none` | 1.616, 1.609, 1.616 | 1.6138 | -0.57% | reject |
| `-fipa-pta` | 1.614, 1.604, 1.605 | 1.6081 | -0.92% | reject |

The small negative deltas late in the table are mostly the power drift below, not the flags: the six flagsets
confirmed after trial 2485 read -0.33% to -0.92%, the ones before it -0.24% to +0.10%. No verdict depends on it.
`-march=native` was measured at 43-44 W and might have read nearer +1% at 47 W, still about `chicago`'s +1.37%,
borderline at best.

## Phase 5: combination

The greedy walk started from `-O3 -Ofast` (Phase 4's top accept, reused under #39). Adding `-ffast-math` built the
same code (`3ff2532a`) and was skipped without a timed run (trial 2511). The pair tournament then measured
`-Ofast` + `-ffast-math` against baseline anyway: 1.684 ×3, the same binary as the greedy winner, three timed runs
(about 65 minutes) spent re-measuring it (#35). It read 0.3% above the greedy winner's Phase 4 reps, inside the
CI, so the greedy winner stood.

## Phase 6: multipliers

| Flagset (on `-O3 -Ofast`) | Reps | Mean | Delta on the step before | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 1.750, 1.751, 1.752 | 1.7511 | +4.32% | **accept** |
| `-fprofile-use -march=znver5` | 1.873, 1.877, 1.873 | 1.8744 | +7.04% | **accept** |
| `-fprofile-use -mtune=znver5` | 1.736, 1.738, 1.739 | 1.7375 | -0.78% | reject |
| `-fprofile-use -march=znver5 -mprefer-vector-width=256` | 1.876, 1.875, 1.874 | 1.8752 | +0.04% | reject |

The three PGO reps spread 0.1%, so the retrained builds (#32) didn't vary here. The vector-width step ran because
the winning set now carries an `-march=`; capping AVX-512 at 256 bits changed nothing measurable.

## Power drift and the flagged recheck

Package power read 47.0 W on every trial through 2485 (19:46Z), then 43.0-45.0 W for the rest of the run, with the
CPU at 97-99°C throughout. The step is small and was not a memory-throttle level: bandwidth stayed at 44-46 GB/s, and
flat flagsets read about 0.5% lower after it. The baseline recheck (trial 2510, at 44 W) read 1.6102, -0.79% against
the calibration mean and outside its ±0.12% CI, so it was flagged.

The low-power rerun didn't fire: the lowest reps (43.0 W, `-Ofast` and `-ffast-math`) were 8.5% below the 47.0 W
reference but within 2.3% of their own highest-power sibling, so PR #68's sibling check held them. That is the
intended behavior; nothing in nab's power pattern looks like graph500_s's inverted power/speed relation (#36).

Effect on the result: the Phase 6 steps were measured at 44-45 W against a 47 W baseline, so if anything the
+15.49% is slightly understated (by up to the recheck's 0.8%). The accepts clear their CIs by 3-7%, well beyond it.

## Knowledge table

The memory-bound rows this run changed:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 12 of 21, +26.57% | 12 of 22, +25.37% (still fast-tracks) |
| `-Ofast` | 2 of 8, +0.58% | 3 of 9, +0.90% |
| `-ffast-math` | 2 of 7, +0.67% | 3 of 8, +0.99% |
| `-fprofile-use` | 2 of 16, -4.30% | 3 of 17, -3.79% |
| `-march=znver5` | 2 of 9, +0.36% | 3 of 10, +1.02% |
| `-mtune=znver5` | 0 of 9, +0.05% | 0 of 10, -0.04% |

## Compared with `chicago`

| | `chicago` (2026-11-10) | `niwot` |
|---|---|---|
| Baseline | 3.3639, ±0.22%, 85 W | 1.6230, ±0.12%, 47 W |
| Fast-math | `-ffast-math` +4.61%, `-Ofast` +4.56% | `-Ofast` +3.42%, `-ffast-math` +3.23% |
| `-march=native` alone | +1.37%, accepted | +0.26%, rejected |
| `-march` on top of fast-math | +5.62% (greedy step) | +7.04% (`-march=znver5`, on top of PGO too) |
| PGO | +4.17% | +4.32% |
| Total | +15.10% | +15.49% |
| Run | 89 trials, 8h47m | 83 trials, 29h46m |

The win is portable across the two hosts, and in both it depends on measuring `-march` on top of fast-math rather
than alone.

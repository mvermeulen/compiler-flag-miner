# `cfm mine` results: 857.namd_s on `niwot`, 2026-11-18

The second fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `857.namd_s` is based on NAMD,
a C++ molecular-dynamics code parallelized with OpenMP. `chicago` mined it on 2026-11-11
([write-up](mining_results.857.namd_s.2026-11-11.md)). Its corpus shape is memory-bound at 41.2%, under the 55% shape
margin, so no candidate was excluded on shape.

## Headline result

**`-O3 -march=native`, +20.67% over plain `-O3`** (ratio 1.2139 → 1.4648).

- **`-march=native` was the whole win, as on `chicago` (+17.52%).** It was fast-tracked on the memory-bound prior
  (12 of 22) and all three reps (1.464-1.466) sat far above every `-O3` rep (1.210-1.215).
- **Fast-math lost, as on `chicago`:** `-Ofast` -2.65% and `-ffast-math` -2.70%, both CI-clear below baseline,
  built the same code (`27b404c8`, the same fingerprint as `chicago`'s pair). On nab_s the same flags were a +3.4%
  win on this host, so the sign is per benchmark, not per host.
- **Nothing added to `-march=native`.** PGO +0.65%, PGO with the near-miss `-fprefetch-loop-arrays` +0.56%, and
  `-mprefer-vector-width=256` +0.51%, all CI-clear of the winner but under the 1% bar. `chicago` read +0.47%, +0.31%
  and +0.57% for the same three.
- **Every other candidate was within ±0.5% of `-O3`.** `-fno-ipa-cp-clone` built the same code as `-O3` (`cd9bb5b5`)
  and was skipped without a timed run, as on `chicago`.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 857.namd_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `8cfe190` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 204 |
| Started / finished | 2026-11-18T10:04:33Z / 2026-11-19T23:37:17Z (37h33m) |
| Final status | `converged` |
| Trials | 71 (2527-2597), no reruns, 1 skipped as unchanged code |
| Candidates screened / confirmed | 14 / 13 (plus `-march=native` fast-tracked; `-fno-ipa-cp-clone` skipped) |
| Excluded on shape (Phase 2) | none (memory-bound 41.2%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 12 of 22, mean +25.37%) |
| Accepted in Phase 4 | `-march=native` +20.67% |
| Winning flags | `["-O3", "-march=native"]`, +20.67% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (44.0-46.2 GB/s); no reruns; baseline recheck not flagged (-0.20%) |
| Power | package power median 40-41 W on `-O3`-class code, 44 W on `-march=native`, 43 W on its PGO builds; CPU temperature 95.6-99.4°C |

A trial took about 30 minutes: a 20-minute timed run plus the 10-minute settle and the build. `chicago` took 14h33m
for the same 71 trials. Every trial's `.rsf` reads `valid: S`.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 41.2%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2527 | warm-up | 1.21464 |
| 2528 | warm-up | 1.21029 |
| 2529 | calibration | 1.21373 |
| 2530 | calibration | 1.21369 |
| 2531 | calibration | 1.21423 |
| 2588 | recheck | 1.21151 |

Warm-up settled after the minimum 2 reps. The calibration mean is 1.21388, 95% CI about ±0.06%, the tightest
baseline of any niwot mine so far. The recheck, 30 hours later, read -0.20%, inside the 1% warning bar. Unlike nab_s,
power held steady for the whole run: the `-O3`-class trials all read 40-41 W.

## Phase 3/4: screening and confirmation

All 14 screened candidates were within 1% of baseline except `-Ofast` and `-ffast-math` (1.179, -2.9%), which
still survived the 5% screening bar.

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` (fast-tracked) | 1.466, 1.465, 1.464 | 1.4648 | +20.67% | **accept** |
| `-fprefetch-loop-arrays` | 1.219, 1.220, 1.219 | 1.2195 | +0.46% | reject (CI-clear, under 1%; PGO's near-miss) |
| `-fcf-protection=none` | 1.218, 1.215, 1.217 | 1.2167 | +0.23% | reject |
| `-fno-stack-protector` | 1.215, 1.217, 1.216 | 1.2159 | +0.17% | reject |
| `-fipa-pta` | 1.211, 1.217, 1.217 | 1.2152 | +0.10% | reject |
| `-fno-pie -no-pie` | 1.214, 1.216, 1.215 | 1.2150 | +0.09% | reject |
| `-fgraphite-identity` | 1.216, 1.214, 1.214 | 1.2147 | +0.07% | reject |
| `-fno-unswitch-loops` | 1.216, 1.214, 1.214 | 1.2147 | +0.06% | reject |
| `-fno-math-errno` | 1.213, 1.213, 1.211 | 1.2123 | -0.13% | reject |
| `-U_FORTIFY_SOURCE` | 1.212, 1.213, 1.212 | 1.2122 | -0.14% | reject |
| `-flto` | 1.211, 1.212, 1.211 | 1.2114 | -0.21% | reject |
| `-funroll-loops` | 1.212, 1.210, 1.209 | 1.2100 | -0.32% | reject |
| `-Ofast` | 1.181, 1.181, 1.184 | 1.1818 | -2.65% | reject (CI clear below) |
| `-ffast-math` | 1.182, 1.181, 1.181 | 1.1811 | -2.70% | reject (CI clear below) |

## Phase 5: combination

Only `-march=native` was accepted, so there was nothing to combine; its Phase 4 reps were reused (#39) and Phase 5
spent no trials.

## Phase 6: multipliers

| Flagset (on `-O3 -march=native`) | Reps | Mean | Delta on `-march=native` | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 1.475, 1.475, 1.474 | 1.4743 | +0.65% | reject (under 1%) |
| `-fprefetch-loop-arrays -fprofile-use` | 1.472, 1.474, 1.473 | 1.4729 | +0.56% | reject |
| `-mprefer-vector-width=256` | 1.472, 1.473, 1.472 | 1.4722 | +0.51% | reject |

The microarch multiplier was skipped because the winning set already has `-march=native`. The three plain-PGO builds
had one fingerprint (`9d708c9b`), so SPEC's retraining (#32) produced the same binary each time here; the near-miss
variant's three builds had two (`c7998581` ×2, `bb16befa`), spread 0.1%.

PGO, the near-miss and vector width all land between +0.5% and +0.65% on both hosts. Each alone is under the bar; a
`-march=native -mprefer-vector-width=256 -fprofile-use` stack might clear 1%, but no phase measures a stack of
sub-bar multipliers.

## Knowledge table

The memory-bound rows this run changed most:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 12 of 22, +25.37% | 13 of 23, +25.17% |
| `-Ofast` | 3 of 9, +0.90% | 3 of 10, +0.54% |
| `-ffast-math` | 3 of 8, +0.99% | 3 of 9, +0.58% |
| `-fprofile-use` | 3 of 17, -3.79% | 3 of 18, -3.55% |
| `-mprefer-vector-width=256` | 2 of 15, -1.43% | 2 of 16, -1.31% |

## Compared with `chicago`

| | `chicago` (2026-11-11) | `niwot` |
|---|---|---|
| Baseline | 2.4912, ±0.13%, 85 W | 1.2139, ±0.06%, 40 W |
| `-march=native` | +17.52% | +20.67% |
| Fast-math | `-Ofast` -2.83%, `-ffast-math` -2.72% | `-Ofast` -2.65%, `-ffast-math` -2.70% |
| PGO / near-miss / vector width on top | +0.47% / +0.31% / +0.57% | +0.65% / +0.56% / +0.51% |
| Run | 71 trials, 14h33m | 71 trials, 37h33m |

The two mines agree flag for flag; `niwot` gains a little more from `-march=native`.

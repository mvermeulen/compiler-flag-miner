# `cfm mine` results: 872.marian_s on `niwot`, 2026-11-20

The fourth fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `872.marian_s` is based on
Marian, a C++ neural machine-translation engine, threaded with C++ threads (`@benchsets` has `cxxthreads`, so cfm
leaves it unpinned). `chicago` mined it on 2026-11-12 ([write-up](mining_results.872.marian_s.2026-11-12.md)). Its
corpus shape is memory-bound at 86.9%, so the shape filter dropped 10 candidates, `-Ofast` and `-ffast-math` among
them, the same 10 as on `chicago`.

## Headline result

**`-O3 -march=native`, +17.68% over plain `-O3`** (ratio 2.2856 → 2.6896).

- **`-march=native` won, but at a third of `chicago`'s gain** (+56.38%). On marian_r the two hosts were close
  (+63.40% here, +72.43% there), so the gap is specific to the speed benchmark on this host, not to this core's
  AVX-512. Unexplained so far (#42).
- **`-fprefetch-loop-arrays` (+9.73%) and `-fgraphite-identity` (+6.21%) were accepted alone, but neither adds
  anything on top of `-march=native`** (-1.05% and -0.94% as greedy steps). `chicago` had prefetching at +4.78% alone
  and graphite at -2.64%.
- **`-mprefer-vector-width=256` cost 6.66%** on top of `-march=native` (`chicago`: -15.07%), so the 512-bit vectors
  matter here too, just less.
- **PGO lost 1.73%** (`chicago`: -1.0%). Each PGO trial took about 2h20m, the training run included.
- **`-flto` lost 1.86%** (`chicago` screened it at -15.0%) and `-fno-math-errno` read +1.10% with a ±2% CI, rejected.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 872.marian_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `63fa65c` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | pthread (`cxxthreads`): not pinned, left to the scheduler |
| Experiment id | 206 |
| Started / finished | 2026-11-20T13:15:44Z / 2026-11-21T11:19:13Z (22h03m) |
| Final status | `converged` |
| Trials | 48 (2631-2678), 1 slow-rep rerun, none skipped |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 10: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fipa-pta`, the four hardening opt-outs, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` |
| Fast-tracked (M4) | `-march=native` (accepted 14 of 24, mean +24.50%) |
| Accepted in Phase 4 | `-march=native` +17.68%, `-fprefetch-loop-arrays` +9.73%, `-fgraphite-identity` +6.21% |
| Winning flags | `["-O3", "-march=native"]`, +17.68% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (43.8-45.8 GB/s); one slow-rep rerun (2660 → 2663); baseline recheck not flagged (+0.76%) |
| Power | package power median 23-25 W on `-O3`-class code, 20 W on every `-march=native` build; CPU temperature 85.1-90.1°C |

A non-PGO trial took about 20 minutes, the settle included. `chicago` ran its 43 trials in 9h11m. Every trial's
`.rsf` reads `valid: S`. Power here is about half the other fpspeed mines' 40-47 W, and `chicago` read 85 W on every
trial; marian is the most memory-bound benchmark of the four (86.9%), so the cores spend more of the run waiting.

`chicago`'s write-up lists OpenMP placement for its run, while this one ran as pthread (unpinned). Both hosts run the
same classification code (`benchmark_threading()` reads `cxxthreads` as pthread), so that row of `chicago`'s
write-up is probably a copy-over; it doesn't change the comparison.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 86.9%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2631 | warm-up | 2.2634 |
| 2632 | warm-up | 2.3068 |
| 2633 | warm-up | 2.2863 |
| 2634 | calibration | 2.2661 |
| 2635 | calibration | 2.2915 |
| 2636 | calibration | 2.2992 |
| 2656 | recheck | 2.3029 |

Warm-up settled after 3 reps. The calibration mean is 2.2856, 95% CI ±1.88%, the noisiest fpspeed baseline here so
far (unpinned threads), though far from the throttle stop: the six Phase 1 reps span 1.9%.

## Phase 3/4: screening and confirmation

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` (fast-tracked) | 2.690, 2.691, 2.687 | 2.6896 | +17.68% | **accept** |
| `-fprefetch-loop-arrays` | 2.507, 2.516, 2.501 | 2.5080 | +9.73% | **accept** |
| `-fgraphite-identity` | 2.436, 2.424, 2.423 | 2.4275 | +6.21% | **accept** |
| `-fno-math-errno` | 2.289, 2.319, 2.324 | 2.3108 | +1.10% | reject (CI overlap) |
| `-flto` | 2.240, 2.237, 2.253 | 2.2431 | -1.86% | reject |

## Phase 5: combination

| Flagset | Reps | Mean | Verdict |
|---|---|---|---|
| greedy: `-march=native` + `-fprefetch-loop-arrays` | 2.662, 2.662, 2.661 | 2.6615 | reject (-1.05% on `-march=native`) |
| greedy: `-march=native` + `-fgraphite-identity` | 2.667, 2.662, 2.664 (2.292 replaced) | 2.6643 | reject (-0.94%) |
| pair: `-fgraphite-identity` + `-march=native` | 2.662, 2.666, 2.662 | 2.6633 | below the greedy winner |
| pair: `-fgraphite-identity` + `-fprefetch-loop-arrays` | 2.482, 2.513, 2.545 | 2.5133 | below the greedy winner |
| pair: `-fprefetch-loop-arrays` + `-march=native` | 2.662, 2.652, 2.660 | 2.6579 | below the greedy winner |

Two of the three pairs built the same code as a greedy step (`4263bb73`, `ea58019b`) and spent six timed runs, about
two hours, re-measuring them (#35). The pair of the two loop flags without `-march=native` built new code and gained
nothing over prefetching alone (+0.21%).

**The one slow rep was a power drop.** Trial 2660 read 2.2917, 14% under its siblings and about the `-O3` level,
with package power at 18.1 W against 20.0 W on every other `-march=native` rep, on the same binary (`4263bb73`). It's
the only rep in the run below its flagset's power level, and it looks like the memory throttle (#26) setting in for
one run. The slow-rep rule replaced it (2663, 2.6639).

## Phase 6: multipliers

| Flagset (on `-O3 -march=native`) | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 2.638, 2.642, 2.649 | 2.6432 | -1.73% | reject |
| `-mprefer-vector-width=256` | 2.510, 2.510, 2.511 | 2.5105 | -6.66% | reject |

The three PGO builds had three fingerprints (#32) and spread 0.4%. No near-miss variant (`-fno-math-errno`'s CI
overlapped baseline). The microarch multiplier was skipped because the winning set already has `-march=native`.

## Knowledge table

| Flag | Before | After |
|---|---|---|
| `-march=native` | 14 of 24, +24.50% | 15 of 25, +24.22% |
| `-fprefetch-loop-arrays` | 4 of 24, +1.70% | 5 of 25, +2.02% |
| `-fgraphite-identity` | 2 of 21, +1.56% | 3 of 22, +1.77% |
| `-flto` | 5 of 18, +3.02% | 5 of 19, +2.77% |
| `-fprofile-use` | 4 of 19, -3.18% | 4 of 20, -3.10% |
| `-mprefer-vector-width=256` | 2 of 17, -1.21% | 2 of 18, -1.51% |

## Compared with `chicago`

| | `chicago` (2026-11-12) | `niwot` |
|---|---|---|
| Baseline | 4.4193, 85 W | 2.2856, ±1.88%, 23 W |
| `-march=native` | +56.38% | +17.68% |
| `-fprefetch-loop-arrays` alone | +4.78% (accepted) | +9.73% (accepted) |
| `-fgraphite-identity` alone | -2.64% | +6.21% (accepted) |
| prefetch on top of `-march=native` | +1.63% (rejected on CI overlap; +1.77% pooled) | -1.05% |
| `-mprefer-vector-width=256` on top | -15.07% | -6.66% |
| PGO on top | -1.0% | -1.73% |
| Total | +56.38% | +17.68% |
| Run | 43 trials, 9h11m | 48 trials, 22h03m |

The winner is the same, but nearly everything else differs in size. On this host the loop-restructuring flags help
the scalar `-O3` build more and `-march=native` helps much less, as if the vectorized build hits a limit here that
it doesn't on `chicago`; the low power and 86.9% memory-bound shape point at memory bandwidth, but nothing here
tests that.

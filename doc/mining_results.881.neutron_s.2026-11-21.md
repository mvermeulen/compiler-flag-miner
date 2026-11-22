# `cfm mine` results: 881.neutron_s on `niwot`, 2026-11-21

The fifth fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `881.neutron_s` is a C
neutron-transport code built around XSBench's cross-section lookup kernel and parallelized with OpenMP. `chicago`
mined it on 2026-11-13 ([write-up](mining_results.881.neutron_s.2026-11-13.md)). Its corpus shape is memory-bound at
67.0%, so the shape filter dropped 10 candidates, the same 10 as on `chicago`.

## Headline result

**`-O3 -flto -march=znver5`, +9.11% over plain `-O3`** (ratio 1.1209 → 1.2230).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.1209 | — |
| `-O3 -flto` | 1.1842 | +5.64% |
| `+ -march=znver5` | 1.2230 | +3.28% |

- **The same code as `chicago`'s winner.** `chicago` won with `-O3 -flto -march=native` (+10.89%); the winning
  binary here has the same code fingerprint (`c4c36109`), so on these two Zen5 parts `-march=native` and
  `-march=znver5` build identical code. The `-O3` builds match too (`91d1de66`).
- **`-march=native` alone lost 1.05%** and was rejected (CI clear below baseline), where `chicago` read +2.04% and
  accepted it. On top of `-flto` the same target gained +3.28% here and +4.42% there. As on nab_s, the microarch
  multiplier found what the per-flag search couldn't: with only `-flto` accepted, Phase 5 had nothing to combine.
- **PGO lost 29.1%** on top of `-flto` (`chicago`: -25.4%), with package power dropping from 21 W to 16-17 W
  (`chicago`: 85 W to 73 W).
- **`-mtune=znver5` +0.86% and `-mprefer-vector-width=256` +0.19%** on top were rejected. `-fprefetch-loop-arrays`
  (+0.24%), `-fgraphite-identity` (+0.06%) and `-fno-math-errno` (+0.19%) were flat.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 881.neutron_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `1f70ff1` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 207 |
| Started / finished | 2026-11-21T11:29:13Z / 2026-11-22T01:19:39Z (13h50m) |
| Final status | `converged` |
| Trials | 37 (2679-2715), no reruns, none skipped |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 10: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fipa-pta`, the four hardening opt-outs, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` and `-fno-math-errno` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 15 of 25, mean +24.22%) |
| Accepted in Phase 4 | `-flto` +5.64% |
| Winning flags | `["-O3", "-flto", "-march=znver5"]`, +9.11% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (43.5-45.8 GB/s); no reruns; baseline recheck not flagged (-0.19%) |
| Power | package power median 22.0-22.1 W on `-O3`-class code, 21.0-21.1 W on `-flto` and `-mtune` builds, 16.1-17.0 W on PGO; CPU temperature 95.5-98.9°C |

A non-PGO trial took about 22 minutes, the settle included, and a PGO trial about 27. `chicago` ran its 37 trials in
4h14m. Every trial's `.rsf` reads `valid: S`. Power is as low as marian_s's (20-25 W) and half nab_s's or namd_s's,
on a benchmark with the same 67% memory-bound share as sph_exa_s (43 W); `chicago` read 85 W.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 67.0%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2679 | warm-up | 1.12596 |
| 2680 | warm-up | 1.11862 |
| 2681 | calibration | 1.12110 |
| 2682 | calibration | 1.11967 |
| 2683 | calibration | 1.12193 |
| 2703 | recheck | 1.11873 |

Warm-up settled after the minimum 2 reps (2712 s). The calibration mean is 1.12090, 95% CI ±0.25%. Every `-O3`
build had one fingerprint (`91d1de66`, as on `chicago`).

## Phase 3/4: screening and confirmation

All four screened candidates survived (1.119-1.193); `-flto` already read +6.3% in screening.

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-flto` | 1.177, 1.192, 1.184 | 1.1842 | +5.64% | **accept** |
| `-fprefetch-loop-arrays` | 1.125, 1.122, 1.124 | 1.1236 | +0.24% | reject |
| `-fno-math-errno` | 1.123, 1.125, 1.121 | 1.1230 | +0.19% | reject |
| `-fgraphite-identity` | 1.126, 1.118, 1.121 | 1.1215 | +0.06% | reject |
| `-march=native` (fast-tracked) | 1.111, 1.108, 1.109 | 1.1092 | -1.05% | reject (CI clear below) |

## Phase 5: combination

Only `-flto` was accepted; its Phase 4 reps were reused (#39), and Phase 5 spent no trials. On `chicago`,
`-march=native` was accepted alone too, so its greedy walk measured the pair.

## Phase 6: multipliers

| Flagset (on `-O3 -flto`) | Reps | Mean | Delta on the step before | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 0.842, 0.837, 0.840 | 0.8396 | -29.10% | reject |
| `-march=znver5` | 1.222, 1.225, 1.221 | 1.2230 | +3.28% | **accept** |
| `-mtune=znver5` | 1.195, 1.196, 1.192 | 1.1944 | +0.86% | reject |
| `-march=znver5 -mprefer-vector-width=256` | 1.226, 1.225, 1.225 | 1.2253 | +0.19% | reject |

No near-miss variant (no Phase 4 reject was CI-clear above baseline). The three PGO builds had two fingerprints
(`b3856312` ×2, `a9a70813`, #32) and read alike (0.837-0.842), so the loss isn't one bad build. The low-power rerun
didn't fire on them: all three drew the same lower power, so PR #68's sibling check held them, as on `chicago`.

### `-march` alone against `-march` on top of `-flto`

| Flagset | Code (`niwot`) | `niwot` | `chicago` |
|---|---|---|---|
| `-O3 -march=native` | `c1cfbef4` | -1.05% on `-O3` | +2.04% on `-O3` |
| `-O3 -flto -march=znver5` / `-march=native` | `c4c36109` (both hosts) | +3.28% on `-O3 -flto` | +4.42% on `-O3 -flto` |

Both hosts show the interaction `chicago`'s write-up describes: the target pays off once LTO has inlined across
files. Here the standalone step is a small loss rather than a small gain, which is what kept `-march=native` out of
Phase 5. The win still landed because the microarch multiplier tries `-march=znver5` on top of whatever Phase 5
left; this is the second fpspeed mine here (after nab_s) where that slice found the `-march` gain.

## Knowledge table

The memory-bound rows this run changed:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 15 of 25, +24.22% | 15 of 26, +23.25% |
| `-flto` | 5 of 19, +2.77% | 6 of 20, +2.91% |
| `-march=znver5` | 3 of 10, +1.02% | 4 of 11, +1.23% |
| `-fprofile-use` | 4 of 20, -3.10% | 4 of 21, -4.34% |
| `-mtune=znver5` | 0 of 10, -0.04% | 0 of 11, +0.05% |
| `-mprefer-vector-width=256` | 2 of 18, -1.51% | 2 of 19, -1.42% |
| `-fprefetch-loop-arrays` | 5 of 25, +2.02% | 5 of 26, +1.95% |

## Compared with `chicago`

| | `chicago` (2026-11-13) | `niwot` |
|---|---|---|
| Baseline | 2.0946, ±0.33%, 85 W | 1.1209, ±0.25%, 22 W |
| `-flto` | +6.19% | +5.64% |
| `-march=native` alone | +2.04%, accepted | -1.05%, rejected |
| `-march` on top of `-flto` | +4.42% (greedy, `-march=native`) | +3.28% (microarch multiplier, `-march=znver5`) |
| PGO on top | -25.42% | -29.10% |
| Vector width on top | +0.16% | +0.19% |
| Total | +10.89% | +9.11% |
| Run | 37 trials, 4h14m | 37 trials, 13h50m |

The same winning binary on both hosts, reached by different phases; this host gains a little less from each step.

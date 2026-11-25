# `cfm mine` results: 809.cactus_s on `niwot`, 2026-11-24

The ninth fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `809.cactus_s` is the SPECspeed
version of Cactus/BSSN (numerical relativity), parallelized with OpenMP. `chicago` mined it on 2026-11-10
([write-up](mining_results.809.cactus_s.2026-11-10.md)), and its rate counterpart was mined here on 2026-11-14
([write-up](mining_results.709.cactus_r.2026-11-14.md), +21.56% with `-march=native`). Its corpus shape is
memory-bound at 70.9%, so the shape filter dropped 10 candidates.

## Headline result

**`-O3 -march=native`, +22.66% over plain `-O3`** (ratio 2.2061 → 2.7060), the same winner as `chicago` (+14.53%).

- **`-march=native` gave +22.66%**, with all three reps (2.701-2.712) far above every `-O3` rep (2.200-2.239).
  Against all six `-O3` runs, the recheck included, it reads +22.11%. This is the first fpspeed benchmark where
  `niwot` gains *more* than `chicago` from `-march=native`, and it matches cactus_r here (+21.56%).
- **`-flto` was accepted alone at +1.70%, but most of that looks like drift.** The `-O3` recheck, run after it at
  the same package power, read 2.2387 (+1.48%, flagged), only 0.22% below `-flto`. On top of `-march=native` it read
  +0.07% and was rejected. `chicago` read +0.00%, and cactus_r here +0.29%.
- **PGO +0.41% and `-mprefer-vector-width=256` -0.29%** on top of `-march=native`, both rejected (`chicago`: +0.23%
  and -0.09%).
- **`-fprefetch-loop-arrays` +0.83%, `-fgraphite-identity` +0.50%, `-fno-math-errno` +0.09%**, all rejected.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 809.cactus_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `7537d4b` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 211 |
| Started / finished | 2026-11-24T21:29:21Z / 2026-11-25T08:49:31Z (11h20m) |
| Final status | `converged` |
| Trials | 37 (2852-2888), no reruns, none skipped |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 10: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fipa-pta`, the four hardening opt-outs, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` and `-fno-math-errno` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 16 of 29, mean +21.16%) |
| Accepted in Phase 4 | `-march=native` +22.66%, `-flto` +1.70% |
| Winning flags | `["-O3", "-march=native"]`, +22.66% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (43.3-46.0 GB/s); no reruns; baseline recheck **flagged** (+1.48%) |
| Power | package power median 41.1-42.1 W on the early `-O3`-class trials, creeping to 43-45 W by the end of the run on every flagset; CPU temperature 96.9-99.5°C |

A trial took about 19 minutes with the settle (about 17.5 for `-march=native` builds). `chicago` ran its 27 trials in
2h12m. Every timed run's `.rsf` reads `valid: S` for cactus. As on cactus_r, every build had a different code
fingerprint (Cactus compiles `__DATE__`/`__TIME__` in; CLAUDE.md's 2026-11-05 trap), so the no-code-change guard
couldn't skip anything and fingerprints can't be compared across trials.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 70.9%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 2852 | warm-up | 2.22534 | 42.1 W |
| 2853 | warm-up | 2.21355 | 42.0 W |
| 2854 | calibration | 2.20851 | 42.0 W |
| 2855 | calibration | 2.19971 | 41.1 W |
| 2856 | calibration | 2.21021 | 42.0 W |
| 2876 | recheck | 2.23874 (+1.48%, flagged) | 44.0 W |

Warm-up settled after the minimum 2 reps (2296 s). The calibration mean is 2.20614, 95% CI ±0.52%. The recheck,
nine hours into the run, read above every calibration rep, at 2 W more power.

## Phase 3/4: screening and confirmation

All four screened candidates survived (2.194-2.215).

| Flag | Reps | Mean | Power | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` (fast-tracked) | 2.701, 2.706, 2.712 | 2.7060 | 44-45 W | +22.66% | **accept** |
| `-flto` | 2.239, 2.248, 2.245 | 2.2437 | 44.0-44.6 W | +1.70% | **accept** |
| `-fprefetch-loop-arrays` | 2.224, 2.220, 2.229 | 2.2244 | 42-43 W | +0.83% | reject |
| `-fgraphite-identity` | 2.209, 2.219, 2.223 | 2.2171 | 43.0-43.1 W | +0.50% | reject |
| `-fno-math-errno` | 2.203, 2.211, 2.210 | 2.2081 | 43-44 W | +0.09% | reject |

## The `-flto` accept and the drift

Package power crept up by about 3 W over the run, on every flagset, and the `-O3` ratio seems to have crept with it:
the calibration reps (41-42 W) read 2.200-2.210, the recheck (44 W) 2.239. `-flto` ran just before the recheck, at
the same 44 W, and its mean (2.2437) is only 0.22% above the recheck. Measured as a greedy step on top of
`-march=native` it added +0.07%. On `chicago` it read +0.00% and on cactus_r here +0.29%. So the +1.70% accept is
most likely drift between the calibration reps and its own, not an LTO gain; it didn't reach the winning set.
The same drift may lift the later candidates' deltas by up to about 1.5%; it doesn't change the winner, whose gain is
far larger.

## Phase 5: combination

The greedy walk started from `-O3 -march=native` (Phase 4's top accept, reused under #39) and added `-flto`:
2.708, 2.705, 2.710, +0.07% on `-march=native`, rejected. The pair tournament then measured `-flto` +
`-march=native` against baseline: 2.707, 2.706, 2.700 (mean 2.7047), below the greedy winner. That pair is the same
flagset as the greedy step in another order, so it re-measured the same code, about 53 minutes (#35). Because cactus
stamps its build time into every binary, a fingerprint check could not have caught it here; only a sorted-flagset
comparison would.

## Phase 6: multipliers

| Flagset (on `-O3 -march=native`) | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 2.719, 2.714, 2.719 | 2.7172 | +0.41% | reject |
| `-mprefer-vector-width=256` | 2.699, 2.700, 2.696 | 2.6982 | -0.29% | reject |

No near-miss variant (no Phase 4 reject was CI-clear above baseline). The microarch multiplier was skipped because
the winning set already has `-march=native`.

## Knowledge table

The memory-bound rows this run changed:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 16 of 29, +21.16% | 17 of 30, +21.21% |
| `-flto` | 6 of 23, +2.51% | 7 of 24, +2.47% |
| `-fprofile-use` | 5 of 24, -3.82% | 5 of 25, -3.65% |
| `-fprefetch-loop-arrays` | 5 of 29, +1.68% | 5 of 30, +1.65% |
| `-fgraphite-identity` | 3 of 26, +1.43% | 3 of 27, +1.40% |
| `-mprefer-vector-width=256` | 2 of 20, -1.32% | 2 of 21, -1.27% |
| `-fno-math-errno` | 2 of 11, +0.54% | 2 of 12, +0.51% |

The `-flto` accept is probably drift (above), so its row now carries one accept it likely shouldn't.

## Compared with `chicago`

| | `chicago` (2026-11-10) | `niwot` |
|---|---|---|
| Baseline | 4.2796, ±0.14%, 84 W | 2.2061, ±0.52%, 42 W |
| `-march=native` | +14.53% | +22.66% |
| `-flto` alone | +0.00% | +1.70% (accepted; probably drift) |
| `-flto` on top of `-march=native` | not measured | +0.07% |
| PGO on top | +0.23% | +0.41% |
| Vector width on top | -0.09% | -0.29% |
| Total | +14.53% | +22.66% |
| Run | 27 trials, 2h12m | 37 trials, 11h20m |

The same winner and the same flat rest, but `niwot` gains half again as much from `-march=native`, the reverse of
marian_s and palm_s (#42). cactus is one of the higher-power fpspeed runs here (42-45 W, with nab_s, namd_s and
sph_exa_s, against 15-25 W on marian_s, neutron_s and pot3d_s), which fits #42's reading: where this host isn't held back by memory bandwidth,
its AVX-512 gain is as large as `chicago`'s or larger. On cactus_r the two hosts were +21.56% here and +16.51% there,
the same ordering.

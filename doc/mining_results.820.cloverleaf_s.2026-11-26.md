# `cfm mine` results: 820.cloverleaf_s on `niwot`, 2026-11-26

The eleventh fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `820.cloverleaf_s` is
CloverLeaf, a Fortran mini-app solving the compressible Euler equations on a structured 2-D grid, parallelized with
OpenMP. `chicago` mined it on 2026-11-11 ([write-up](mining_results.820.cloverleaf_s.2026-11-11.md)) and accepted
nothing. Its corpus shape is memory-bound at 88.2%, so the shape filter dropped 8 candidates, the same 8 as on
`chicago`. This mine was the queue's second attempt: the first (experiment 213) was cut off by the host's reboot on
2026-11-25 before its first trial.

## Headline result

**`-O3 -march=znver5`, +2.67% over plain `-O3`** (ratio 0.7429 → 0.7627), where `chicago` accepted nothing.

- **`-march=native` and `-march=znver5` built the same code** (`3de86b3d`, also `chicago`'s `-march=native` code),
  and the verdicts differ only by sampling. `-march=native` read +2.04% (0.761, 0.760, 0.753) and was rejected on CI
  overlap; `-march=znver5`, measured in Phase 6, read +2.67% with tighter reps (0.761-0.764) and was accepted. All six
  runs pooled read +2.36% on the calibration mean, +2.14% on all six `-O3` runs. On `chicago` the same code read
  +0.55% and +0.57%, under the 1% bar.
- **`-mprefer-vector-width=256` on top read +1.60%** (0.770, 0.776, 0.779; +4.30% on `-O3`) and was rejected on CI
  overlap with the `-march=znver5` step. It's the best-measured flagset of the run; see below.
- **`-fstack-arrays` +1.30% was rejected on CI overlap**, `-fgraphite-identity` +0.81% and `-flto` +0.82% under the
  bar, `-fprefetch-loop-arrays` +0.39%. `-frecursive` built the same code as `-O3` and was skipped.
- **PGO +0.07%** and `-mtune=znver5` +1.60% were rejected.
- **No throttling.** Unlike tealeaf_s, every run sat at 17.2-17.8 W, the bandwidth probe read 45.1-45.9 GB/s before
  every run, and no rerun rule fired.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 820.cloverleaf_s --settle-seconds 600` (uncapped, from the restarted fpspeed queue) |
| Code | `main` at `cac959a` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 214 |
| Started / finished | 2026-11-26T09:36:12Z / 2026-11-27T03:52:21Z (18h16m) |
| Final status | `converged` |
| Trials | 38 (2898-2935), no reruns, 1 skipped as unchanged code |
| Candidates screened / confirmed | 5 / 4 (plus `-march=native` fast-tracked; `-frecursive` skipped) |
| Excluded on shape (Phase 2) | 8: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (`-flto` kept under `SHAPE_EXEMPT_FLAGS`) |
| Fast-tracked (M4) | `-march=native` (accepted 17 of 30, mean +21.21%) |
| Accepted in Phase 4 | none |
| Winning flags | `["-O3", "-march=znver5"]`, +2.67% (microarch multiplier) |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before the first run only (45.1-45.9 GB/s); no reruns; baseline recheck not flagged (-0.87%) |
| Power | package power median 17.5-17.8 W on `-O3`-class code, 17.2-17.4 W on `-march=znver5` code |

A trial took about 28 minutes with the settle. `chicago` ran its 38 trials in 5h36m, at 84.9 W. Every timed run's
`.rsf` reads `valid: S` for cloverleaf.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 88.2%, `vectorization_density=high`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2898 | warm-up | 0.75039 |
| 2899 | warm-up | 0.75128 |
| 2900 | calibration | 0.74689 |
| 2901 | calibration | 0.73800 |
| 2902 | calibration | 0.74383 |
| 2923 | recheck | 0.73648 (-0.87%) |

Warm-up settled after the minimum 2 reps (3544 s). The calibration mean is 0.74291, 95% CI ±1.5%, wide for a run
this steady: six `-O3` runs of one binary (`c83c0a06`) spread 2.0% at a flat 17.5-17.7 W. That width decided most
verdicts below.

## Phase 3/4: screening and confirmation

All five screened candidates survived (0.748-0.761); `-frecursive` was skipped as unchanged code.

| Flag | Reps | Mean | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` (fast-tracked) | 0.761, 0.760, 0.753 | 0.7581 | +2.04% | reject (CI overlap) |
| `-fstack-arrays` | 0.753, 0.754, 0.751 | 0.7526 | +1.30% | reject (CI overlap) |
| `-flto` | 0.750, 0.749, 0.748 | 0.7490 | +0.82% | reject |
| `-fgraphite-identity` | 0.747, 0.750, 0.750 | 0.7489 | +0.81% | reject |
| `-fprefetch-loop-arrays` | 0.762, 0.733, 0.743 | 0.7458 | +0.39% | reject |

Both CI-overlap rejects were over the 1% bar but their CIs reached into the baseline's upper end (0.754), so neither
was a near-miss for PGO either (that needs a CI-clear reject).

## Phase 5: combination

Nothing was accepted, so Phase 5 ran no trials and Phase 6 layered on plain `-O3`.

## Phase 6: multipliers

| Flagset (on `-O3`) | Reps | Mean | Delta on the step before | Verdict |
|---|---|---|---|---|
| `-fprofile-use` | 0.741, 0.744, 0.745 | 0.7434 | +0.07% | reject |
| `-march=znver5` | 0.761, 0.763, 0.764 | 0.7627 | +2.67% | **accept** |
| `-mtune=znver5` | 0.752, 0.755, 0.758 | 0.7548 | +1.60% | reject |
| `-march=znver5 -mprefer-vector-width=256` | 0.770, 0.776, 0.779 | 0.7749 | +1.60% | reject (CI overlap) |

The three PGO builds had one fingerprint (`7cdcb224`). The microarch multiplier ran because nothing with an
`-march=` had been accepted, and its `-march=znver5` re-measured `-march=native`'s code (#37a); this time the extra runs
turned a reject into the run's only accept. That's the third fpspeed mine here, after nab_s and neutron_s, where
the microarch slice found the `-march` gain.

### `-mprefer-vector-width=256`

At 0.7749, the 256-bit build is 4.3% above `-O3` and 1.6% above the winner, with every rep above every
`-march=znver5` rep. Its reps rose in order (0.770, 0.776, 0.779), which widened its CI enough to overlap. With 512-bit
vectors, the winner may be fetching more than this bandwidth-bound loop nest can use; `chicago` never measured
`=256` here (no `-march=` was accepted there). A direct `cfm measure` of `-O3 -march=znver5` against
`-O3 -march=znver5 -mprefer-vector-width=256`, interleaved, would settle it (#43).

## Knowledge table

The memory-bound rows this run changed:

| Flag | Before | After |
|---|---|---|
| `-march=native` | 17 of 30, +21.21% | 17 of 31, +20.59% |
| `-march=znver5` | 4 of 13, +0.76% | 5 of 14, +0.89% |
| `-mtune=znver5` | 0 of 13, -0.29% | 0 of 14, -0.15% |
| `-mprefer-vector-width=256` | 2 of 21, -1.27% | 2 of 22, -1.14% |
| `-flto` | 7 of 24, +2.47% | 7 of 25, +2.41% |
| `-fprofile-use` | 5 of 25, -3.65% | 5 of 26, -3.51% |
| `-fstack-arrays` | 0 of 3, -1.39% | 0 of 4, -0.72% |
| `-fprefetch-loop-arrays` | 5 of 30, +1.65% | 5 of 31, +1.61% |
| `-fgraphite-identity` | 3 of 27, +1.40% | 3 of 28, +1.38% |

## Compared with `chicago`

| | `chicago` (2026-11-11) | `niwot` |
|---|---|---|
| Baseline | 1.8570, 84.9 W | 0.7429, ±1.5%, 17.6 W |
| `-march` code (`3de86b3d`) | +0.55% / +0.57% (under the bar) | +2.04% (CI overlap) / +2.67% (accepted) |
| `-march=znver5 -mprefer-vector-width=256` | not measured | +4.30% on `-O3` (rejected on CI overlap) |
| PGO | +0.33% | +0.07% |
| Other flags | all within ±0.11% | +0.39% to +1.30%, all rejected |
| Total | +0.00% | +2.67% |
| Run | 38 trials, 5h36m | 38 trials, 18h16m |

`chicago` reads 2.5 times this host's ratio, the same bandwidth-sized gap as tealeaf_s. The `-march` binary gains a
little more here, but both hosts agree that nothing changes this benchmark much; on `niwot` the baseline's own 2%
spread is about the size of every effect measured.

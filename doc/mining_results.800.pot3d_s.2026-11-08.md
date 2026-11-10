# `cfm mine` results: 800.pot3d_s on `chicago`, 2026-11-08

This is the first fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`800.pot3d_s` mine on any host. `800.pot3d_s` is POT3D, a Fortran potential-field solver for the solar corona,
whose loops are written as `DO CONCURRENT`. Its corpus shape is memory-bound at 52.0%, under the 55% shape margin,
so no candidate was excluded on shape.

**Superseded by the [2026-11-10 re-mine](mining_results.800.pot3d_s.2026-11-10.md)** with correct thread
placement: `-O3 -Ofast`, +28.25%, and `-fno-unswitch-loops` -31.8%.

## Headline result

**Not a usable result: every trial ran pinned to one CPU.** The reported winner, `-O3 -fno-unswitch-loops` at
+115.71% (ratio 0.3526 → 0.7606), was measured with all of the benchmark's threads confined to CPU 1, and doesn't
describe how pot3d runs on this host.

- **Why it was pinned.** pot3d's `@benchsets` are `fpspeed doconcurrent specspeed`, with no `openmp`. Its
  `DO CONCURRENT` loops are parallelized by the config's `-ftree-parallelize-loops=32` into libgomp parallel
  regions of 32 threads, but `benchmark_threading()` classed it `serial`, so `thread_placement()` added
  `submit = taskset -c 1 ${command}` to every trial (each trial's hypotheses row says "single-threaded, pinned to
  CPU 1"). It is the only `doconcurrent` benchmark in the suite; every other fpspeed benchmark is `openmp` or
  `cxxthreads` and is placed correctly. Fixed in [PR #70](https://github.com/mvermeulen/compiler-flag-miner/pull/70),
  which classes `doconcurrent` as OpenMP.
- **The symptoms were in the run.** Package power read 24.4-24.8 W on `-O3` trials, against 85.0 W on every
  fprate mine here, and a `-O3` trial took about 32 minutes.
- **`-fno-unswitch-loops` more than doubled the ratio in that setup** (all three reps 0.759-0.764, power up to
  31.5 W). It's a real, reproducible effect on the pinned binary, but which loops `-ftree-parallelize-loops` turns
  into parallel regions, and what 32 threads on one CPU cost per region, both enter into it. Whether any of it
  survives with the threads spread across the CPUs is for the re-mine to show.
- **Everything else was small.** `-march=native` alone read +2.76% (accepted); on top of `-fno-unswitch-loops` it
  read -2.89%. PGO read -0.36%. The other ten candidates were within ±0.8% of `-O3`.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 800.pot3d_s` (uncapped, defaults) |
| Code | `main` at `ace7358` (no code changes since `f31ba64`, only docs) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` (raised from 24 before this run, to match) |
| Experiment id | 15 |
| Started / finished | 2026-11-08T14:49:36Z / 2026-11-09T20:03:57Z (29h14m) |
| Final status | `converged` |
| Trials | 67 (661-727), 3 skipped as unchanged code, no reruns |
| Thread placement | `taskset -c 1` on every trial (the bug above) |
| Candidates screened / confirmed | 13 / 10 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | none (memory-bound 52.0%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 9 of 11, mean +23.85%) |
| Skipped as unchanged code | `-fno-stack-protector`, `-fcf-protection=none`, `-frecursive` (same code as `-O3`) |
| Reported winner | `["-O3", "-fno-unswitch-loops"]`, +115.71% (not usable, see above) |
| Guards | bandwidth gate waited 30 s before 19 of 64 runs; no reruns; baseline recheck not flagged (+0.12%) |
| Power | package power median 24.4-24.8 W on most trials, 31.0-31.7 W on `-fno-unswitch-loops` builds; CPU temperature 74-81°C |

A `-O3` trial took about 32 minutes, a `-fno-unswitch-loops` trial about 15.5, and a PGO trial about 20. Every
trial's `.rsf` reads `valid: S` for pot3d.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 52.0%, `vectorization_density=moderate`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 661 | warm-up | 0.35248 |
| 662 | warm-up | 0.35290 |
| 663 | calibration | 0.35193 |
| 664 | calibration | 0.35203 |
| 665 | calibration | 0.35382 |
| 712 | recheck | 0.35300 (+0.12%) |

The calibration mean is 0.352595, with a 95% CI of [0.349953, 0.355238] (±0.75%). Warm-up settled after the
minimum two reps (3,878 s). Every `-O3` build had the same code fingerprint (`f3eb5077`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 666-678 | screening | 13 candidates | 0.350-0.763 | | all survived (3 skipped as unchanged code) |
| 679-681 | confirmation | `-fprefetch-loop-arrays` | 0.34992 | -0.76% | reject |
| 682-684 | confirmation | `-fgraphite-identity` | 0.35171 | -0.25% | reject |
| 685-687 | confirmation | `-fstack-arrays` | 0.35118 | -0.40% | reject |
| 688-690 | confirmation | `-flto` | 0.35508 | +0.70% | reject |
| 691-693 | confirmation | `-fno-pie -no-pie` | 0.35359 | +0.28% | reject |
| 694-696 | confirmation | `-funroll-loops` | 0.35408 | +0.42% | reject |
| 697-699 | confirmation | `-Ofast` | 0.35198 | -0.18% | reject |
| 700-702 | confirmation | `-ffast-math` | 0.35318 | +0.16% | reject |
| 703-705 | confirmation | `-fno-ipa-cp-clone` | 0.35220 | -0.11% | reject |
| 706-708 | confirmation | `-fno-unswitch-loops` | 0.76058 | +115.71% | **accept** (pinned) |
| 709-711 | confirmation (fast-tracked) | `-march=native` | 0.36233 | +2.76% | **accept** |
| 713-715 | combination (greedy) | `-fno-unswitch-loops -march=native` | 0.739 | -2.89% | reject |
| 716-718 | combination (pair) | `-fno-unswitch-loops -march=native` | 0.741 | +110.21% | accept, didn't replace the winner |
| 719-721 | PGO | `-fno-unswitch-loops -fprofile-use` | 0.758 | -0.36% | reject |
| 722-724 | microarch | `-fno-unswitch-loops -march=znver5` | 0.739 | -2.77% | reject |
| 725-727 | microarch | `-fno-unswitch-loops -mtune=znver5` | 0.759 | -0.20% | reject |

The greedy-step delta is against the step before, the pair delta against `-O3`, and the Phase 6 deltas against
`-O3 -fno-unswitch-loops`. The greedy walk started from the Phase 4 `-fno-unswitch-loops` result rather than
re-measuring it. `-march=znver5` built the same code as `-march=native` (`d23c3a90`). The vector-width multiplier
was skipped because the winning set has no `-march=`.

## Observations

- **pot3d is left out of the fpspeed summary** until it's re-mined with PR #70's placement. This run's numbers
  stay in `cfm.db` (experiment 15); its knowledge-table rows, `-fno-unswitch-loops`'s +115.7% accept among them,
  were recorded under the memory-bound cluster like any other mine: `-fno-unswitch-loops` now reads accepted 1 of
  4 there (mean +29.2%), which doesn't fast-track it (open item 13 on the host page).
- **Low package power is the tell for a mis-placed speed benchmark**, as it was for `821.gcc_s` on niwot (16
  compiles on one CPU). At 24.6 W against the 85 W this host holds under any full load, most of the chip was idle.
- **The run took 29 hours**, mostly because each pinned `-O3` trial took 32 minutes. With the threads spread out,
  the re-mine should be far shorter.
- **The `-ftree-parallelize-loops=32` change did reach the build**: the SPEC build log shows `=32` on pot3d's
  compile lines.

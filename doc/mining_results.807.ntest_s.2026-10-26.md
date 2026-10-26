# `cfm mine` results: 807.ntest_s on `niwot`, 2026-10-26

The sixth SPECspeed benchmark mined on `niwot`. `807.ntest_s` is the speed version of `707.ntest_r` (the
ntest Othello engine). It uses OpenMP, so this is the first mine to run with PR #55's OpenMP placement
(`OMP_PLACES=threads OMP_PROC_BIND=close`, thread *i* on CPU *i*).

## Headline result

**`-O3 -march=native -flto -fprofile-use`, +19.21% over plain `-O3`** (ratio 0.9026 → 1.0760). That's the
same winning set as `707.ntest_r`'s re-mine (+30.95%), built in the same order:

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 0.9026 | — |
| `-O3 -march=native` | 1.0012 | +10.92% |
| `+ -flto` | 1.0377 | +3.64% |
| `+ -fprofile-use` | 1.0760 | +3.69% |

- **`-march=native` is the biggest single step, as in rate** (+10.9% here, +15.0% there).
- **LTO pays a little more here than in rate** (+3.6% on top of `-march=native`, against +2.3%). That's
  unlike ns3 and gem5, where speed got about half the rate LTO gain.
- **PGO pays a third of its rate gain** (+3.7% against +11.3%). See "PGO in the speed version" below.
- **OpenMP placement measured very steadily.** The baseline CI was ±0.33%, and every rejected flag's
  confirmation CI was ±0.4% or tighter. The baseline recheck read -0.03%.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 807.ntest_s` (uncapped, queued after the #27 abc_s check) |
| Code | `main` at `ef72829` (code as of `9e0d86e`; before PR #56, which would have changed nothing here, since no candidate was excluded on shape) |
| Experiment id | 178 |
| Started / finished | 2026-10-25T20:30:47Z / 2026-10-26T17:51:05Z (21h20m) |
| Final status | `converged` |
| Trials | 62 (995-1056) |
| Candidates screened / confirmed | 11 / 2 |
| Fast-tracked (M4) | none |
| Winning flags | `["-O3", "-march=native", "-flto", "-fprofile-use"]`, +19.21% |
| Thread placement | OpenMP, `OMP_PLACES=threads OMP_PROC_BIND=close`, 16 threads (confirmed in `speccmds.cmd`) |
| Guards | bandwidth gate 41.4-45.9 GB/s before every run, waited only before the first (30 s); no slow-rep reruns; no audit warnings; baseline recheck not flagged |
| Power profile | `balanced`; CPU temp 85.9-90.6°C, package power 21.0-23.1 W |

About 20 minutes per trial, set mostly by the timed run: `-O3` trials came 21 minutes apart, `-march=native`
ones 19.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 995 | warm-up (excluded from CI) | 0.9178 |
| 996 | warm-up (excluded from CI) | 0.9018 |
| 997 | calibration | 0.9040 |
| 998 | calibration | 0.9019 |
| 999 | calibration | 0.9020 |
| 1044 | recheck after Phase 4 | 0.9024 (-0.03%, not flagged) |

Calibration mean **0.9026**, 95% CI **[0.8997, 0.9056]** (±0.33%).

The first warm-up read 1.7% high. It came after about 90 seconds of idle (the queue's 60-second gap plus a
30-second bandwidth-gate wait), following the abc_s check. Every later `-O3` rep landed within 0.25% of 0.902. This is what the
warm-up reps are for.

**Shape: `memory-bound`, 41.9%**, `vectorization_density=low`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`). ntest_r's corpus entry read compute-bound 40.6%. Both are under the
55% gate, so nothing was excluded on `resource_dominance`. The low vectorization density excluded both
`-mprefer-vector-width=` candidates.

## Phase 2 and M4

Eleven candidates, all screened. Since minizinc_s, every memory-bound prior stood at 1 of 2 or worse, so
nothing was fast-tracked.

## Phase 3 screening (vs. most recent calibration rep, 0.9020)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 0.9915 | **+9.92%** |
| `-flto` | 0.9584 | **+6.25%** |
| `-fno-semantic-interposition` | 0.9042 | +0.25% |
| `-freorder-blocks-and-partition` | 0.9033 | +0.14% |
| `-freorder-functions` | 0.9031 | +0.12% |
| `-Ofast` | 0.9024 | +0.04% |
| `-ffast-math` | 0.9016 | -0.04% |
| `-fipa-pta` | 0.9016 | -0.04% |
| `-fprefetch-loop-arrays` | 0.9008 | -0.13% |
| `-fgraphite-identity` | 0.8998 | -0.24% |
| `-funroll-loops` | 0.8978 | -0.46% |

All eleven survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [0.8997, 0.9056])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | 1.0015, 1.0003, 1.0019 | 1.0012 | [0.9991, 1.0034] | **+10.93%** | **accept** |
| `-flto` | 0.9623, 0.9586, 0.9591 | 0.9600 | [0.9550, 0.9650] | **+6.36%** | **accept** |
| `-fipa-pta` | 0.9032, 0.9036, 0.9038 | 0.9036 | [0.9028, 0.9043] | +0.10% | reject |
| `-fno-semantic-interposition` | 0.9028, 0.9025, 0.9044 | 0.9032 | [0.9008, 0.9057] | +0.07% | reject |
| `-freorder-functions` | 0.9039, 0.9019, 0.9038 | 0.9032 | [0.9005, 0.9059] | +0.06% | reject |
| `-freorder-blocks-and-partition` | 0.9016, 0.9027, 0.9026 | 0.9023 | [0.9008, 0.9039] | -0.03% | reject |
| `-fgraphite-identity` | 0.9022, 0.9025, 0.9005 | 0.9017 | [0.8991, 0.9043] | -0.10% | reject |
| `-Ofast` | 0.9016, 0.9014, 0.9020 | 0.9017 | [0.9009, 0.9024] | -0.11% | reject |
| `-funroll-loops` | 0.8988, 0.9015, 0.9008 | 0.9004 | [0.8968, 0.9039] | -0.25% | reject |
| `-fprefetch-loop-arrays` | 0.9007, 0.8996, 0.9002 | 0.9001 | [0.8988, 0.9015] | -0.28% | reject |
| `-ffast-math` | 0.8997, 0.9000, 0.8994 | 0.8997 | [0.8989, 0.9005] | -0.32% | reject |

Two clear accepts and nine flat rejects, none within 0.4% of baseline. No reject was CI-clear above
baseline, so Phase 6 had no near-miss PGO variant to try.

## Phase 5 combination

| Step | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | 1.0025, 1.0020, 0.9992 | 1.0012 | [0.9969, 1.0056] | +10.92% vs baseline | accept |
| 2 | `+ -flto` | 1.0394, 1.0358, 1.0379 | 1.0377 | [1.0333, 1.0421] | +3.64% vs step 1 | accept |
| Pair | `-flto` + `-march=native` | 1.0403, 1.0362, 1.0370 | 1.0378 | [1.0326, 1.0431] | +14.98% vs baseline | accept, but doesn't replace the greedy winner |

The two flags compound almost fully. Alone they gave +10.93% and +6.36%, so a product of +17.98%; together
they give +14.96%. In rate, `-flto` alone was +3.6% and +2.3% on top.

## Phase 6 multipliers (on `-O3 -march=native -flto`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -march=native -flto -fprofile-use` | 1.0767, 1.0766, 1.0747 | 1.0760 | [1.0732, 1.0788] | **+3.69%** vs step 2 | **accept** |
| Microarch | — | | | | | skipped (`-march=native` already in the winning set) |
| Vector width | — | | | | | skipped (no deferred candidates) |

The audit confirmed `-O3 -fprofile-use` in the PGO binary. As always, `-march=native` and `-flto` can't be
checked from the recorded switches.

## PGO in the speed version

PGO paid +11.3% in `707.ntest_r` and +3.7% here, on the same code. Not investigated. Two plausible reasons:

- **The training run differs.** In speed, SPEC runs the train workload with 16 OpenMP threads and none of the
  placement the timed run gets: `thread_placement()` wraps only the timed run (the build directory's
  `speccmds.cmd` sets `OMP_NUM_THREADS 16` and no `OMP_PLACES`). Counters from a parallel
  search are merged across threads (`-fprofile-update=atomic`), and a parallel search visits a different mix
  of positions from 16 single-threaded copies.
- **The bottleneck differs.** 16 threads sharing one search tree add synchronization and shared-cache
  traffic, which PGO's layout and inlining don't help. ntest_s's corpus shape is memory-bound where ntest_r's
  is compute-bound.

A follow-up could build the PGO binary with a pinned or single-threaded training run, but at +3.7% against a
possible +11% it isn't obviously worth a slot in the queue.

## Compared with `707.ntest_r`

| | `707.ntest_r` (2026-10-22 re-mine) | `807.ntest_s` (this run) |
|---|---|---|
| Copies / threads | 16 copies | 16 OpenMP threads, placed |
| Shape | compute-bound 40.6% | memory-bound 41.9% |
| Winner | `-O3 -march=native -flto -fprofile-use`, +30.95% | the same, +19.21% |
| `-march=native` | +14.97% | +10.92% |
| `-flto` on top | +2.32% | +3.64% |
| `-fprofile-use` on top | +11.31% | +3.69% |
| Baseline CI | — | ±0.33% |

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-flto` | 3 | 2 | +7.45% |
| `-march=native` | 9 | 3 | +1.67% |
| `-fprofile-use` | 4 | 2 | +1.38% |

**`-flto` is back at a strict majority (2 of 3), so the next memory-bound mine fast-tracks it.** `801.xz_s`
starts straight after this run. The knowledge table still doesn't separate rate from speed records.

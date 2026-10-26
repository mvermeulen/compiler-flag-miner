# `cfm mine` results: 801.xz_s on `niwot`, 2026-10-26

The seventh SPECspeed benchmark mined on `niwot`. `801.xz_s` is xz/LZMA compression. It has no rate
counterpart in this suite, so this is its first mine on either host. It uses pthreads and runs unpinned.

## Headline result

**Nothing accepted: plain `-O3` stays the best (ratio 0.9457).** A clean reject. The best of the rest
was PGO at +0.70%, with CIs overlapping.

- **The first real mine with #28 (PR #56) in effect.** The corpus shape was memory-bound at 56.3%, just past
  the 55% gate, so Phase 2 excluded seven frontend-, compute- and backend-tagged candidates. `-flto` was
  kept anyway ("never excluded on shape"). It was flat, +0.08%, so here the exclusion would have been
  right, as it was for zstd. #28 cost three trials to find that out.
- **`-flto` was fast-tracked** on its 2-of-3 memory-bound prior from ntest_s. At 2 of 4 it no longer
  qualifies.
- **The baseline recheck was flagged** (-0.69%). It changes no verdict: nothing came within 0.3% of the
  1% bar.
- **Noisier than the pinned and OpenMP mines.** A few reps dropped about 2% (one `-march=znver5` rep read
  0.920), which widened those CIs to ±2-3%. None dropped far enough to trigger a slow-rep rerun.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 801.xz_s` (uncapped, queued after `807.ntest_s`) |
| Code | `main` at `daa45b8` (PR #56). PRs #57 and #58 were pulled mid-run; xz_s kept the code it started with |
| Experiment id | 179 |
| Started / finished | 2026-10-26T17:52:55Z / 2026-10-26T23:17:02Z (5h24m) |
| Final status | `converged` |
| Trials | 30 (1057-1086) |
| Candidates screened / confirmed | 3 / 0 (plus 1 fast-tracked, rejected) |
| Fast-tracked (M4) | `-flto` (rejected) |
| Winning flags | `["-O3"]`, 0.0% |
| Thread placement | pthread, not pinned |
| Guards | bandwidth gate 42.9-45.6 GB/s before every run, waited only before the first (30 s); no slow-rep reruns; no audit warnings; baseline recheck **flagged** (-0.69%) |
| Power profile | `balanced`; CPU temp 80.2-84.2°C, package power 21.1-23.1 W |

About 11 minutes per trial.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1057 | warm-up (excluded from CI) | 0.9408 |
| 1058 | warm-up (excluded from CI) | 0.9435 |
| 1059 | calibration | 0.9456 |
| 1060 | calibration | 0.9436 |
| 1061 | calibration | 0.9480 |
| 1077 | recheck after Phase 4 | 0.9392 (**-0.69%, flagged**) |

Calibration mean **0.9457**, 95% CI **[0.9402, 0.9512]** (±0.58%).

The six `-O3` measurements span 0.939-0.948, about 1%. The warm-ups and the recheck all sit below the
calibration mean, so the true `-O3` level is probably nearer 0.943. That would move every delta below up
by about 0.3%, and still leave nothing over the 1% bar.

**Shape: `memory-bound`, 56.3%**, `vectorization_density=moderate`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`).

## Phase 2: seven exclusions, one exemption

| Excluded | Tagged |
|---|---|
| `-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition` | frontend-bound |
| `-Ofast`, `-ffast-math` | compute-bound |
| `-funroll-loops` | compute- and backend-bound |
| `-fipa-pta` | backend-bound |

`-flto` (frontend-bound) was kept under #28 and fast-tracked. Both `-mprefer-vector-width=` settings were held
for Phase 6. That left `-fprefetch-loop-arrays`, `-fgraphite-identity` and `-march=native` to screen.

## Phases 3 and 4

| Flags | Screening (vs. 0.9480) | Confirmation ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| `-flto` (fast-tracked) | — | 0.9452, 0.9431, 0.9513 | 0.9465 | [0.9359, 0.9571] | +0.08% | reject |
| `-fgraphite-identity` | 0.9424 (-0.59%) | 0.9463, 0.9469, 0.9460 | 0.9464 | [0.9453, 0.9475] | +0.07% | reject |
| `-fprefetch-loop-arrays` | 0.9397 (-0.88%) | 0.9358, 0.9398, 0.9479 | 0.9412 | [0.9259, 0.9565] | -0.48% | reject |
| `-march=native` | 0.9348 (-1.40%) | 0.9463, 0.9346, 0.9288 | 0.9366 | [0.9144, 0.9588] | -0.97% | reject |

All flat. `-march=native`'s three reps fell steadily (0.946, 0.935, 0.929), so its -0.97% is as likely noise
as a real loss. `-march=znver5` (below) showed the same spread.

## Phase 6 multipliers (on `-O3`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -fprofile-use` | 0.9505, 0.9536, 0.9530 | 0.9524 | [0.9483, 0.9564] | +0.70% | reject (CIs overlap) |
| Microarch | `-O3 -march=znver5` | 0.9438, 0.9390, 0.9202 | 0.9343 | [0.9034, 0.9653] | -1.21% | reject |
| Microarch | `-O3 -mtune=znver5` | 0.9394, 0.9406, 0.9395 | 0.9398 | [0.9381, 0.9415] | -0.62% | reject |
| Vector width | — | | | | | skipped (no `-march=` in the winning set) |

- **PGO +0.70%** is the closest anything came. Against the flagged recheck's lower level it would be about
  +1.4%, but its CI still overlaps the baseline's, so it's a reject either way. It could be worth a direct
  interleaved check like #27's if xz's gains ever matter, but the effect is small.
- **No near-miss PGO variant:** no Phase 4 reject was CI-clear above baseline.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-flto` | 4 | 2 | +5.61% |
| `-fprofile-use` | 5 | 2 | +1.24% |
| `-march=native` | 10 | 3 | +1.41% |

`-flto` is back to half, so the next memory-bound mine screens it normally. Under #28 it's never excluded on
shape any more, so it still always gets measured.

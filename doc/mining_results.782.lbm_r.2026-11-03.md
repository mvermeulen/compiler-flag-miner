# `cfm mine` results: 782.lbm_r on `niwot`, 2026-11-03

The second `782.lbm_r` mine on `niwot`. The first (2026-10-23) was stopped when the same `-O3` binary measured
6.32, 3.02, 4.15 and 4.26: the memory-side throttle in the traps log and
[`lbm_swing_investigation.2026-10-23.md`](lbm_swing_investigation.2026-10-23.md). This re-mine asked one question:
does a long idle before every timed run (`--settle-seconds 600`, 10 minutes) keep the throttle away?

## Headline result

**No.** Nothing was accepted (0.0%, the winner is plain `-O3` at 5.738), and the settle didn't remove the noise.

- **One binary measured both 6.33 and 5.00.** `-march=native` and `-march=znver5` built identical code (fingerprint
  `f4a24b15`). `-march=native`'s four runs (one screening, three confirmation) read 6.316-6.335 between 09:33 and
  21:23. `-march=znver5`'s three read 4.970-5.032 between 01:14 and 02:35 the next night. That's 27% apart on the same
  code, after the same 10-minute settle and the same pre-run bandwidth reading (45.8-45.9 GB/s).
- **The ratios fall on discrete levels**, not a continuum: about 6.35, 5.9, 5.4 and 5.05, each step 7-9%. `-O3` hit all four in
  ten reps, every rerun flagset hit at least two, and `-mtune=znver5` hit three (6.375, 5.920, 5.074).
- **The pre-run bandwidth gate can't see it.** All 46 probes read 44.9-46.0 GB/s, and the gate never waited after
  the first trial. As in October, the throttle sets in during the timed run.
- **Package power tracks the level**: 17.09 W at the 6.35 level, 17.0 W at 5.9, about 16.0 W at 5.05-5.4, and 15.0 W
  at the slowest. Here low power means a slow run, the opposite of `854.graph500_s` (#36).
- **The `-O3` spread was 17%** (5.048-5.910 over ten reps), against about 2x in the first mine. That's milder, but
  still far too wide for a 1% accept bar. The baseline CI came out ±12.6%.

So for fprate on this host, a settle delay doesn't help. `709.cactus_r`, `749.fotonik3d_r` and `765.roms_r` stay held
back.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 782.lbm_r --settle-seconds 600` (uncapped, 10 min idle after `854.graph500_s`) |
| Code | `main` at `c7a46c9` (PR #68's low-power sibling check) |
| Experiment id | 188 |
| Started / finished | 2026-11-03T01:23:10Z / 2026-11-04T06:20:14Z (28h57m, 7.7 h of it settle) |
| Final status | `converged` |
| Trials | 46 (1516-1561), 14 of them slow-rep reruns |
| Candidates screened / confirmed | 4 / 0 |
| Fast-tracked (M4) | none (`-march=native` at 4 of 11 memory-bound doesn't qualify) |
| Excluded on shape | 11 (memory-bound 94.9%: all seven of PR #57's opt-outs, `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta`) |
| Skipped as unchanged code (#58) | none (but see `-march=znver5` below) |
| Winning flags | `["-O3"]`, 0.0% |
| Guards | 10-minute settle before every timed run; bandwidth gate 44.9-46.0 GB/s, waited only before the first run; 14 slow-rep reruns, no low-power reruns; baseline recheck not flagged (-0.26%) |
| Power | package power median 15.0-18.0 W per trial |

Each trial took about 35-41 minutes: a 16-copy SPECrate run of about 20-25 minutes plus the 10-minute settle.

## Baseline

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 1516 | warm-up | 5.854 | 17.0 W |
| 1517 | warm-up | 5.048 | 15.1 W |
| 1518 | warm-up | 5.065 | 16.0 W |
| 1519 | calibration | 5.910 | 17.0 W |
| 1520 | calibration | 5.903 | 17.0 W |
| 1521 | calibration, replaced (slow) | 5.100 | 16.0 W |
| 1522 | rerun, replaced (slow) | 5.384 | 16.1 W |
| 1523 | rerun, replaced (slow) | 5.120 | 16.0 W |
| 1524 | rerun, kept (three reruns used) | 5.402 | 16.1 W |
| 1548 | recheck after Phase 4 | 5.723 | 16.1 W (-0.26%, not flagged) |

Calibration mean **5.738**, 95% CI **[5.014, 6.462]** (±12.6%). Warm-up "settled" after 3 reps (7064 s), on two
adjacent slow-level reps (5.048, 5.065), the same false settle graph500_s had.

**Shape: `memory-bound`, 94.9%**, `vectorization_density=high`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`).

## Phase 3 screening (vs. most recent calibration rep, 5.4015)

| Flags | Ratio | Delta |
|---|---|---|
| `-fgraphite-identity` | 6.338 | +17.34% |
| `-march=native` | 6.316 | +16.93% |
| `-flto` | 5.957 | +10.28% |
| `-fprefetch-loop-arrays` | 5.391 | -0.20% |

All four survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [5.014, 6.462])

| Flags | Kept reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` | 6.330, 6.333, 6.335 | 6.333 | [6.326, 6.339] | +10.36% | reject (CI overlap) |
| `-flto` | 6.371, 6.367, 5.908 | 6.215 | [5.554, 6.877] | +8.32% | reject |
| `-fgraphite-identity` | 5.856, 5.929, 6.340 | 6.042 | [5.393, 6.690] | +5.29% | reject |
| `-fprefetch-loop-arrays` | 5.905, 5.100, 5.079 | 5.361 | [4.191, 6.531] | -6.57% | reject |

None of these deltas measures a flag. Each one says which throttle levels its reps happened to land on. `-march=native`'s
CI is tight because all three reps landed on the 6.33 level. The same code later read 5.00 (Phase 6).

## Phase 6 multipliers (on `-O3`)

| Stage | Flags | Kept reps | Mean | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 6.332, 5.743, 5.750 | 5.942 | +3.55% | reject |
| Microarch | `+ -march=znver5` | 4.970, 5.004, 5.032 | 5.002 | **-12.83%** | reject |
| Microarch | `+ -mtune=znver5` | 6.375, 6.375, 5.142 | 5.964 | +3.94% | reject |
| Vector width | — | | | | skipped (no `-march=` in the winning set) |

- **`-march=znver5` built the same code as `-march=native`** and read 21% lower. The no-code-change guard (#58) only
  compares a build against the flagset it layers on (here `-O3`), not against other flagsets already measured.
  So it spent three timed runs re-measuring a known binary, and they landed in a slow stretch.
- **Neither rerun rule fired on `-march=znver5`.** Its three reps agreed with each other (4.97-5.03), so the slow-rep
  rule had no fast sibling to compare against. All three drew 15.03 W, more than 8% below the 17.015 W baseline
  reference, but PR #68's sibling check only reruns a rep that is also 8% below its highest-power sibling. On
  `821.gcc_s` that check correctly kept PGO's uniformly low-power reps. Here it kept a flagset that ran its whole
  measurement in the throttled state (#37).

## Guards

- **14 slow-rep reruns** (3 on baseline calibration, 3 on `-fprefetch-loop-arrays`, 1 on `-fgraphite-identity`, 3 on
  `-flto`, 1 on PGO, 3 on `-mtune=znver5`). They behaved as designed, rerunning a rep that read below its siblings.
  But the replacement landed on another random level as often as not. `-flto`'s 5.952 was replaced by 4.982, then 4.980,
  then 5.908.
- **No low-power reruns** (see above).
- **No audit warnings.**

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 12 | 4 | +12.75% |
| `-flto` | 6 | 2 | +5.12% |
| `-fprofile-use` | 7 | 2 | +1.21% |
| `-fgraphite-identity` | 12 | 0 | +0.54% |
| `-mtune=znver5` | 8 | 0 | +0.53% |
| `-fprefetch-loop-arrays` | 13 | 2 | +0.26% |
| `-march=znver5` | 8 | 1 | -1.73% |

This run's rows are noise: `-march=native` +10.36% and `-march=znver5` -12.83% for the same binary. They're all
rejects, so no fast track changes, but they pull the means. Experiment 151's lbm rows had the same problem.
Deleting experiment 188's knowledge contributions would need the per-experiment history the table doesn't keep.

## What this means for fprate on `niwot`

The 10-minute settle cost 7.7 hours and changed nothing that matters. The throttle sets in during a run, in discrete
steps, and lasts for hours at a time. Neither an idle gap before the run nor a bandwidth probe can predict it. The
eight queued fprate mines continue as planned: astcenc, flightdm, nest, gmsh, ocio, marian, femflow and palm, all
less bandwidth-heavy than lbm. Each write-up will check the same signs (discrete levels, power tracking the ratio,
same-fingerprint flagsets disagreeing). Only an in-run signal could make lbm-class benchmarks minable here: per-trial
power, or a DRAM-fill counter read through wspy, used to reject a rep that ran throttled (#37).

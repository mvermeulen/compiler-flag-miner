# `cfm mine` results: 854.graph500_s on `niwot`, 2026-11-02

This is the thirteenth and last intspeed benchmark mined on `niwot`. `854.graph500_s` is Graph500: a BFS (scale 26) followed
by an all-pairs shortest path (APSP, Floyd-Warshall over a 16,000 × 16,000 matrix), both on OpenMP, placed with
`OMP_PLACES=threads OMP_PROC_BIND=close`. The first mine (experiment 185, 2026-10-30) was stopped and marked failed
because its `-O3` reps spread 24%. This re-mine is the first with PR #67's `--settle-seconds 180`: each trial idles
3 minutes between its build and its timed run.

## Headline result

**`-O3 -funroll-loops`, +15.85% over plain `-O3`** (ratio 0.8954 → 1.0374).

- **The gain is real, but its size depends on which `-O3` you compare against.** The `-O3` binary ran in a fast
  state or a slow state (below). The calibration mean, 0.8954, mixes both. `-funroll-loops`'s 13 reps read
  1.0334-1.0391, above every non-unrolled trial (the highest, a `-march=native` rep, was 0.9889; the highest without `-march=native` was 0.9581). Against the fast-state
  `-O3` runs (about 0.936-0.958) it's about +8-11%.
- **`-funroll-loops` removes the noise along with the slowness.** In SPEC's per-workload times, APSP took 275-277 s
  on all 12 unrolled reps that could be matched, with BFS at 312-315 s. Every non-unrolled flagset's APSP took 311-383 s. So the noise
  that stopped the first mine is in the non-unrolled code. It isn't an environment state that would hit every binary.
- **The settle delay halved the `-O3` spread but didn't remove it.** The `-O3` reps spread 8.1% (0.8658-0.9362, CV
  2.6%), against 24.4% (0.7675-0.9546, CV 5.1%) in experiment 185.
- **Low package power marks the *fast* state.** Across the 66 non-unrolled, non-`-march=native` trials, power and ratio
  correlate at r = -0.88. Trials under 21 W averaged 0.939, and trials at 25 W or more averaged 0.880. The
  low-power rerun rule assumes the opposite, so here it replaced fast reps with slow ones (see Guards).
- PGO, `-march=znver5` and `-mtune=znver5` on top of `-funroll-loops` were all rejected (-3.1%, -0.9%, -0.7%).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 854.graph500_s --settle-seconds 180` (uncapped, queued after `821.gcc_s`) |
| Code | `main` at `a72c066` (PR #67) |
| Experiment id | 187 (the stopped first mine was 185) |
| Started / finished | 2026-11-01T21:00:02Z / 2026-11-03T01:12:45Z (28h13m) |
| Final status | `converged` |
| Trials | 105 (1411-1515), 32 of them low-power or slow-rep reruns |
| Candidates screened / confirmed | 14 / 1 (plus `-flto` fast-tracked, rejected) |
| Fast-tracked (M4) | `-flto` (9 of 11 frontend-bound) |
| Skipped as unchanged code (#58) | `-fno-ipa-cp-clone` |
| Winning flags | `["-O3", "-funroll-loops"]`, +15.85% |
| Thread placement | OpenMP, `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Guards | 3-minute settle before every timed run; 29 low-power and 3 slow-rep reruns; baseline recheck not flagged (-0.08%) |
| Power | package power median 18.1-27.1 W per trial |

Each trial took about 15-16 minutes, including the 3-minute settle, and PGO trials about 21.

## Baseline

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 1411 | warm-up | 0.9317 | 23.0 W |
| 1412 | warm-up | 0.9017 | 20.0 W |
| 1413 | warm-up | 0.8658 | 27.0 W |
| 1414 | warm-up | 0.8710 | 27.0 W |
| 1415 | calibration, replaced (low power) | 0.9055 | 24.0 W |
| 1416 | calibration | 0.8692 | 27.0 W |
| 1417 | calibration, replaced (low power) | 0.8951 | 24.0 W |
| 1418 | rerun of 1415 | 0.8809 | 25.1 W |
| 1419 | rerun of 1417, replaced (low power) | 0.8963 | 24.1 W |
| 1420 | rerun of 1419 | 0.9362 | 19.0 W |
| 1491 | recheck after Phase 4 | 0.8947 | 24.0 W (-0.08%, not flagged) |

Calibration mean **0.89542**, 95% CI **[0.8065, 0.9843]** (±9.9%), by far the widest baseline on this host. Warm-up
settled after 4 reps (3925 s), on two adjacent slow reps (0.8658, 0.8710).

The power reference was taken from the slow warm-ups (27.0 W, later 25.1 W), so every faster, lower-power
rep looked "low". The last rerun, trial 1420, drew 19.0 W, but the rule had used up its three reruns, so 1420 stayed. It's the fastest
`-O3` rep and also Phase 3's reference.

**Shape: `frontend-bound`, 48.6%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). That's under the 55% gate, so nothing was excluded on `resource_dominance`. One
candidate was excluded on vectorization: `-mprefer-vector-width=256`.

## The noise

SPEC records each workload's elapsed time. Matching each run's `.rsf` ratio to its trial gave 78 of the 104 timed runs,
from trial 1438 onward:

| Flagset (on `-O3`) | Reps | BFS (s) | APSP (s) |
|---|---|---|---|
| `-funroll-loops` | 12 | 312-315 | **275-277** |
| `-funroll-loops -mtune=znver5` | 6 | 316-321 | 275-276 |
| `-funroll-loops -march=znver5` | 6 | 312-314 | 281-289 |
| `-funroll-loops -fprofile-use` | 6 | 322-330 | 281-290 |
| `-march=native` | 6 | 331-345 | 285-305 |
| `-ffast-math` | 5 | 329-332 | 311-362 |
| `-U_FORTIFY_SOURCE` | 5 | 329-333 | 320-383 |
| `-flto` | 6 | 329-333 | 341-373 |
| the other eight single flags and `-O3` | 3-4 each | 313-334 | 337-378 |

- **The variance is in APSP, as in experiment 185**, and BFS is steady to within about 2%.
- **Unrolled code runs APSP at the standalone speed.** Outside SPEC, the real binary's APSP ran 279-288 s and flat
  (the 2026-10-30 investigation). In the mine, `-funroll-loops` ran it in 275-277 s. Every non-unrolled flagset ran it
  20-40% slower, and a different amount each time. One caution: the binary used in the standalone runs was
  whatever the stopped mine had left in SPEC's run directory, probably the `-fno-unswitch-loops` screening build,
  not plain `-O3`. So "fast alone, slow in the mine" isn't yet shown for the same binary.
- **Slow APSP draws *more* power.** -O3 reps at 19-20 W were fast, and those at 25-27 W were slow. A memory-side throttle
  would stall the cores and lower power, so it doesn't explain this. Threads spinning at the 16,000 per-sweep barriers
  would explain it: libgomp spin-waits before sleeping, and a straggling thread keeps the other 15 spinning. The
  unrolled loop, which is shorter per sweep and evidently steadier, would leave less to wait for. That's a
  hypothesis; `OMP_WAIT_POLICY=passive` (or `GOMP_SPINCOUNT=0`) would test it (opportunity #36).
- **The 180 s settle** halved the `-O3` spread against experiment 185 (8.1% against 24.4%). But experiment 185 ran
  just after 26 hours of mining and this one ran after gcc_s's 43, so the settle isn't cleanly separated from
  other differences between the two runs.

## Phase 3 screening (vs. most recent calibration rep, 0.93619)

| Flags | Ratio | Delta |
|---|---|---|
| `-funroll-loops` | 1.0360 | **+10.66%** |
| `-fno-pie -no-pie` | 0.9581 | +2.34% |
| `-Ofast` | 0.9473 | +1.19% |
| `-fipa-pta` | 0.9399 | +0.40% |
| `-U_FORTIFY_SOURCE` | 0.9324 | -0.40% |
| `-fgraphite-identity` | 0.9276 | -0.92% |
| `-march=native` | 0.9170 | -2.05% |
| `-fno-unswitch-loops` | 0.9169 | -2.06% |
| `-fno-stack-protector` | 0.9165 | -2.10% |
| `-fcf-protection=none` | 0.9147 | -2.30% |
| `-ffast-math` | 0.9069 | -3.13% |
| `-fprefetch-loop-arrays` | 0.9065 | -3.17% |
| `-fno-math-errno` | 0.8776 | **-6.26%**, pruned |
| `-fno-ipa-cp-clone` | — | same code as `-O3`, skipped (#58) |

Phase 3's reference was the fastest `-O3` rep (trial 1420, 19.0 W), so nearly every candidate read negative against it.
`-fno-math-errno` was pruned on one slow-state reading (26.1 W), so it's the one flag this mine never confirmed.

## Phase 4 confirmation (3 reps each, vs. baseline CI [0.8065, 0.9843])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-funroll-loops` | 1.0380 | [1.0359, 1.0402] | **+15.93%** | **accept** |
| `-march=native` | 0.9749 | [0.9398, 1.0100] | +8.88% | reject (CI overlap) |
| `-fno-pie -no-pie` | 0.9110 | [0.8961, 0.9260] | +1.74% | reject |
| `-fno-stack-protector` | 0.8997 | [0.8696, 0.9298] | +0.48% | reject |
| `-fcf-protection=none` | 0.8956 | [0.8882, 0.9029] | +0.02% | reject |
| `-ffast-math` | 0.8945 | [0.8632, 0.9258] | -0.10% | reject |
| `-U_FORTIFY_SOURCE` | 0.8893 | [0.8808, 0.8978] | -0.69% | reject |
| `-fprefetch-loop-arrays` | 0.8880 | [0.8326, 0.9434] | -0.83% | reject |
| `-fipa-pta` | 0.8846 | [0.8708, 0.8984] | -1.21% | reject |
| `-fno-unswitch-loops` | 0.8838 | [0.8773, 0.8904] | -1.30% | reject |
| `-Ofast` | 0.8835 | [0.8381, 0.9289] | -1.34% | reject |
| `-fgraphite-identity` | 0.8818 | [0.8384, 0.9253] | -1.52% | reject |
| `-flto` (fast-tracked) | 0.8787 | [0.8513, 0.9061] | -1.87% | reject |

- **`-march=native` was probably a real win swallowed by the baseline's CI.** All six of its confirmation reps drew 18-19 W
  and ran APSP at 285-305 s, closer to the unrolled code than to `-O3`. Its CI's lower bound (0.9398) is above every
  `-O3` rep. Phase 6 later put `-march=znver5` (the same ISA) on top of `-funroll-loops` and lost 0.9%, so it doesn't add
  to unrolling. It looks like the same effect reached a different way.
- **`-flto` lost on frontend-bound code for the third time** (9 of 12 accepted before this). graph500 is two small
  kernels, so there's little cross-module inlining for LTO to do.
- The other reps mix fast-state and slow-state runs, so their ±1-2% deltas are noise.

## Phase 5 combination

Only `-funroll-loops` was accepted, so Phase 5 re-confirmed it alone: 1.0390, 1.0382, 1.0351 (after three low-power
reruns of reps that read 1.0334-1.0381), mean **1.0374**, CI [1.0323, 1.0425], +15.86%.

## Phase 6 multipliers (on `-O3 -funroll-loops`, 1.0374)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 1.0048 | [0.9893, 1.0203] | -3.14% | reject |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | `+ -march=znver5` | 1.0284 | [1.0243, 1.0326] | -0.87% | reject |
| Microarch | `+ -mtune=znver5` | 1.0305 | [1.0266, 1.0343] | -0.67% | reject |
| Vector width | — | | | | skipped (`=256` excluded in Phase 2) |

- **PGO's first frontend-bound loss on a speed benchmark.** PGO's own BFS was 7-18 s slower than the unrolled code's.
  The six PGO builds had three different code fingerprints (#32).
- **Every Phase 6 rep drew 19.0-19.1 W**, so with the pre-#68 rule (below) each flagset spent three low-power reruns
  re-measuring a steady reading.

## Guards

- **29 low-power reruns, about 8 hours.** 18 of them were on flagsets whose every rep drew 18-19 W (`-funroll-loops`
  in Phases 4 and 5, `-march=native`, all of Phase 6). That's #33, which PR #68 fixed after this mine started: this
  run's checkout was `a72c066`. The other 11 were reps of mixed flagsets that drew less than their siblings. On this
  benchmark low power means a fast run, so those reruns replaced fast reps with slower ones. Examples: `-U_FORTIFY_SOURCE` 0.9405 → 0.8562
  (then slow-rep rerun → 0.8865), and `-ffast-math` 0.9513 → 0.8806. PR #68's sibling check would still have rerun those (#36).
- **3 slow-rep reruns** (`-fno-pie -no-pie` twice, `-U_FORTIFY_SOURCE` once), all on slow-state reps.
- **No audit warnings**; the bandwidth gate never waited.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprofile-use` | 13 | 9 | +6.89% |
| `-flto` | 12 | 9 | +6.45% |
| `-funroll-loops` | 3 | 1 | +5.20% |
| `-march=native` | 13 | 2 | +4.16% |
| `-fno-pie -no-pie` | 4 | 1 | +1.34% |
| `-march=znver5` | 12 | 0 | +0.08% |
| `-mtune=znver5` | 12 | 0 | -0.01% |

`-funroll-loops` now has a +5.20% frontend-bound mean from one big win. At 1 of 3 it doesn't fast-track, which is
the right call: the prior comes from a two-kernel graph benchmark, not from typical frontend-bound code.

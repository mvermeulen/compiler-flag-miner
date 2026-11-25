# `cfm mine` results: 821.gcc_s on `chicago`, 2026-11-25

This is the fourth intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `821.gcc_s` is
GCC compiling a set of C sources. It isn't threaded: `$multiprocess = 'yes'` has specinvoke run its `cc1` compiles
many at a time, so it runs unpinned (CLAUDE.md trap, 2026-10-27). niwot's mine found `-O3 -fno-pie -no-pie -flto
-fno-stack-protector -fprofile-use` at +16.88%, with `-fno-stack-protector` entering as PGO's near-miss flag
([write-up](mining_results.821.gcc_s.2026-10-31.md)). This machine's `721.gcc_r` found `-O3 -flto -fno-pie -no-pie
-fprofile-use` at +12.68% ([write-up](mining_results.721.gcc_r.2026-11-21.md)). Its corpus shape is frontend-bound at
59.7%, over the 55% gate, so the shape filter excluded seven candidates.

## Headline result

**`-O3 -fno-pie -no-pie -flto -fprofile-use`, +16.66% over plain `-O3`** (ratio 2.6975 → 3.1470).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 2.6975 | — |
| `-O3 -fno-pie -no-pie` | 2.7677 | +2.60% |
| `+ -flto` | 2.8302 | +2.26% |
| `+ -fprofile-use` | 3.1470 | **+11.19%** |

- **niwot's steps reproduce**: non-PIE +2.60% against +2.54%, LTO +2.26% against +1.75%, PGO +11.19% against
  +10.83%. As on gcc_r, PGO is most of the gain.
- **`-fno-stack-protector` is the one difference, and it fell to the 1% bar.** It was fast-tracked and accepted alone
  (+1.44%), but on top of non-PIE and LTO it read +0.88%, CI-clear and under the bar, so the greedy step was
  rejected. On niwot it was a Phase 4 near-miss, so Phase 6 tried it with PGO, where it added +1.07%. Here it was a
  Phase 4 accept, so it wasn't on the near-miss list and never met PGO ([opportunity #22](host_chicago.md#open-items)).
- **The near-miss PGO variant (`+ -fcf-protection=none`) read 0.32% above plain PGO**, with overlapping CIs, so plain
  PGO stayed the winner. `-fcf-protection=none` had read +0.33% alone, CI-clear but under the bar.
- **`-march=native` lost 0.15%** (niwot -0.22%). On the winner, `-march=znver5` read +0.33% (CI overlap) and
  `-mtune=znver5` +0.49% (CI-clear, under the bar).

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 821.gcc_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `ae219ae` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` |
| Thread placement | multiprocess, not pinned |
| Experiment id | 46 |
| Started / finished | 2026-11-24T23:46:46Z / 2026-11-25T20:48:29Z (21h02m) |
| Final status | `converged` |
| Trials | 67 (2453-2519), none skipped, no reruns |
| Candidates screened / confirmed | 7 / 7 (plus `-flto` and `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-mprefer-vector-width=256`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 59.7%, over the gate) |
| Fast-tracked (M4) | `-flto` (accepted 5 of 8, mean +6.32%), `-fno-stack-protector` (accepted 6 of 8, mean +1.88%) |
| Accepted in Phase 4 | `-fno-pie -no-pie` +2.60%, `-flto` +2.08%, `-fno-stack-protector` +1.44% |
| Winning flags | `["-O3", "-fno-pie -no-pie", "-flto", "-fprofile-use"]`, +16.66% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 8 of 67 timed runs; no reruns; baseline recheck not flagged (-0.09%) |
| Power | package power median 84.98-85.00 W on every trial; CPU temperature 90.9-97.2°C |

A trial took about 17.5 minutes, a PGO trial about 24.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 59.7%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2453 | warm-up | 2.7135 |
| 2454 | warm-up | 2.6972 |
| 2455 | calibration | 2.6962 |
| 2456 | calibration | 2.6992 |
| 2457 | calibration | 2.6971 |
| 2492 | recheck | 2.6951 (-0.09%) |

The calibration mean is 2.6975, with a 95% CI of [2.6937, 2.7013] (±0.14%). Warm-up settled after the minimum two
reps (1800 s). Every `-O3` build had the same code fingerprint (`8730e580`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2458-2464 | screening | 7 candidates | 2.6923-2.7657 | | all survived |
| 2465-2467 | confirmation | `-fno-pie -no-pie` | 2.7677 | +2.60% | **accept** (the greedy start) |
| 2468-2470 | confirmation | `-fcf-protection=none` | 2.7065 | +0.33% | reject (CI-clear, under the 1% bar) |
| 2471-2473 | confirmation | `-U_FORTIFY_SOURCE` | 2.7041 | +0.24% | reject |
| 2474-2476 | confirmation | `-fno-ipa-cp-clone` | 2.6974 | -0.01% | reject |
| 2477-2479 | confirmation | `-fno-unswitch-loops` | 2.7006 | +0.11% | reject |
| 2480-2482 | confirmation | `-march=native` | 2.6934 | -0.15% | reject |
| 2483-2485 | confirmation | `-fno-math-errno` | 2.6974 | +0.00% | reject |
| 2486-2488 | confirmation (fast-tracked) | `-flto` | 2.7535 | +2.08% | **accept** |
| 2489-2491 | confirmation (fast-tracked) | `-fno-stack-protector` | 2.7364 | +1.44% | **accept** |
| 2492 | baseline recheck | `-O3` | 2.6951 | -0.09% | not flagged |
| 2493-2495 | combination (greedy) | `-fno-pie -no-pie -flto` | 2.8302 | +2.26% | **accept** |
| 2496-2498 | combination (greedy) | `+ -fno-stack-protector` | 2.8551 | +0.88% | reject (CI-clear, under the 1% bar) |
| 2499-2501 | combination (pair) | `-fno-pie -no-pie -fno-stack-protector` | 2.8014 | +3.85% | accept, not enough to replace the greedy winner |
| 2502-2504 | combination (pair) | `-flto -fno-stack-protector` | 2.7928 | +3.53% | accept, not enough to replace the greedy winner |
| 2505-2507 | combination (pair) | `-flto -fno-pie -no-pie` | 2.8313 | +4.96% | accept, same code as the greedy step, not enough to replace the winner |
| 2508-2510 | PGO | winner `+ -fprofile-use` | 3.1470 | +11.19% | **accept** |
| 2511-2513 | PGO (near-miss variant) | winner `+ -fcf-protection=none -fprofile-use` | 3.1569 | +11.54% | accept, CI overlaps plain PGO, not the winner |
| 2514-2516 | microarch | winner `+ -march=znver5` | 3.1575 | +0.33% | reject |
| 2517-2519 | microarch | winner `+ -mtune=znver5` | 3.1623 | +0.49% | reject (CI-clear, under the 1% bar) |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against the step before, PGO deltas against
`-O3 -fno-pie -no-pie -flto`, and microarch deltas against the PGO winner. The greedy walk started from the Phase 4
non-PIE result rather than re-measuring it. The vector-width multiplier had no candidate (the shape filter had
excluded `256`).

## Observations

- **A flag can miss PGO by being accepted first.** The PGO near-miss list is built from Phase 4 rejects that were
  CI-clear of baseline. `-fno-stack-protector` passed Phase 4, then failed the greedy step under the 1% bar with a
  clear CI ([2.8513, 2.8589] against [2.8264, 2.8340]), which is the same kind of near-miss, but greedy rejects aren't
  on the list. Its pairs with non-PIE (+3.85%, against +2.60% for non-PIE alone) and with LTO (+3.53%, against
  +2.08%) both point the same way. niwot's +1.07% on top of PGO suggests it might clear the bar there.
- **gcc_s is very repeatable here.** Every non-PGO flagset's three reps were within 0.15% of each other, and the six
  `-O3` runs read 2.6951-2.7135, the first warm-up the only one above 2.70.
- **PGO built different code on every rep** (all twelve PGO builds had distinct fingerprints), as expected on SPEC
  (CLAUDE.md, 2026-10-28). The reps still agreed within 0.5%.
- **No low-power reruns fired**, unlike niwot's mine, where all 12 PGO reps were re-run (niwot opportunity #33).
  Here every trial, PGO included, read 84.98-85.00 W, so the rule had nothing to see.
- **At 21h02m this is the longest int mine here**, ahead of ntest_s's 13h56m: 67 trials at about 17.5 minutes, PGO
  trials 24. The bandwidth gate waited before 8 of 67 timed runs, about 4 minutes in all.

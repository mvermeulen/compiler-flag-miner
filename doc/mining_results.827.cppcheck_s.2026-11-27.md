# `cfm mine` results: 827.cppcheck_s on `chicago`, 2026-11-27

This is the sixth intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)).
`827.cppcheck_s` is the speed version of `727.cppcheck_r` (the cppcheck C/C++ static analyzer), tagged `pthread`
and run unpinned. niwot's mine found `-O3 -fno-stack-protector -fprofile-use` at +12.00% (stack protector +2.83%, PGO
+8.91%; [write-up](mining_results.827.cppcheck_s.2026-10-29.md)), and this machine's `727.cppcheck_r` found the same
set at +8.76% (stack protector +3.6%, PGO +5.0%; [write-up](mining_results.727.cppcheck_r.2026-11-22.md)). Its corpus
shape is frontend-bound at 74.1%, over the 55% gate, so the shape filter excluded seven candidates.

## Headline result

**`-O3 -fno-stack-protector -fprofile-use`, +9.67% over plain `-O3`** (ratio 2.1307 → 2.3367).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 2.1307 | — |
| `-O3 -fno-stack-protector` | 2.1856 | **+2.58%** |
| `+ -fprofile-use` | 2.3367 | **+6.91%** |

- **The same winning set as niwot's and cppcheck_r's.** The stack-protector step (+2.58%) matches niwot's +2.83%;
  PGO (+6.91%) falls between cppcheck_r's +5.0% and niwot's +8.91%.
- **Three more flags were accepted alone and lost on top of the stack protector.** `-fno-unswitch-loops` (+1.72%),
  `-U_FORTIFY_SOURCE` (+1.31%) and `-fno-ipa-cp-clone` (+1.19%) each cleared the bar against `-O3`, but each read
  0.78-0.96% *below* `-O3 -fno-stack-protector` when added to it (CI overlap). On niwot `-fno-unswitch-loops` did
  the same (+1.65% alone, -0.58% on top).
- **`-flto` lost 1.32%**, CI-overlapping, as on niwot (-0.16%) and cppcheck_r here (+1.3%, rejected on overlap).
  Its fast-track prior (7 of 10 frontend-bound accepts) didn't carry over.
- **The near-miss PGO variant (`+ -fcf-protection=none`) read 0.85% below plain PGO.** `-fcf-protection=none` had
  read +1.00% alone, CI-clear but just under the 1% bar.
- **`-march=native` (+0.18%) and non-PIE (+0.42%) were flat.** On the winner, `-march=znver5` (+0.08%) and
  `-mtune=znver5` (-0.13%) were rejected on CI overlap.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 827.cppcheck_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `01a99dc` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` |
| Thread placement | pthread, not pinned |
| Experiment id | 48 |
| Started / finished | 2026-11-26T16:19:54Z / 2026-11-27T06:08:43Z (13h49m) |
| Final status | `converged` |
| Trials | 80 (2577-2656), none skipped, no reruns |
| Candidates screened / confirmed | 7 / 7 (plus `-flto` and `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-mprefer-vector-width=256`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 74.1%, over the gate) |
| Fast-tracked (M4) | `-flto` (accepted 7 of 10, mean +5.77%), `-fno-stack-protector` (accepted 8 of 10, mean +1.77%) |
| Accepted in Phase 4 | `-fno-stack-protector` +2.58%, `-fno-unswitch-loops` +1.72%, `-U_FORTIFY_SOURCE` +1.31%, `-fno-ipa-cp-clone` +1.19% |
| Winning flags | `["-O3", "-fno-stack-protector", "-fprofile-use"]`, +9.67% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 32 of 80 timed runs; no reruns; baseline recheck not flagged (+0.24%) |
| Power | package power median 84.98-85.00 W on every trial; CPU temperature 88.4-94.8°C |

A trial took about 10 minutes, an LTO trial about 12, and a PGO trial about 12.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 74.1%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2577 | warm-up | 2.1496 |
| 2578 | warm-up | 2.1216 |
| 2579 | warm-up | 2.1294 |
| 2580 | calibration | 2.1278 |
| 2581 | calibration | 2.1294 |
| 2582 | calibration | 2.1350 |
| 2617 | recheck | 2.1358 (+0.24%) |

The calibration mean is 2.1307, with a 95% CI of [2.1213, 2.1401] (±0.44%). Warm-up took three reps (1808 s): the
first read 2.1496, 1.3% above the second, so a third was needed before two agreed within 1%. Every `-O3` build had
the same code fingerprint (`c36c9cc6`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2583-2589 | screening | 7 candidates | 2.1298-2.1631 | | all survived |
| 2590-2592 | confirmation | `-fno-pie -no-pie` | 2.1397 | +0.42% | reject |
| 2593-2595 | confirmation | `-fcf-protection=none` | 2.1520 | +1.00% | reject (CI-clear, just under the 1% bar) |
| 2596-2598 | confirmation | `-U_FORTIFY_SOURCE` | 2.1588 | +1.31% | **accept** |
| 2599-2601 | confirmation | `-fno-ipa-cp-clone` | 2.1562 | +1.19% | **accept** |
| 2602-2604 | confirmation | `-fno-unswitch-loops` | 2.1673 | +1.72% | **accept** |
| 2605-2607 | confirmation | `-march=native` | 2.1346 | +0.18% | reject |
| 2608-2610 | confirmation | `-fno-math-errno` | 2.1360 | +0.25% | reject |
| 2611-2613 | confirmation (fast-tracked) | `-flto` | 2.1026 | -1.32% | reject |
| 2614-2616 | confirmation (fast-tracked) | `-fno-stack-protector` | 2.1856 | +2.58% | **accept** (the greedy start) |
| 2617 | baseline recheck | `-O3` | 2.1358 | +0.24% | not flagged |
| 2618-2620 | combination (greedy) | `-fno-stack-protector -fno-unswitch-loops` | 2.1685 | -0.78% | reject |
| 2621-2623 | combination (greedy) | `-fno-stack-protector -U_FORTIFY_SOURCE` | 2.1647 | -0.96% | reject |
| 2624-2626 | combination (greedy) | `-fno-stack-protector -fno-ipa-cp-clone` | 2.1673 | -0.84% | reject |
| 2627-2629 | combination (pair) | `-fno-stack-protector -fno-unswitch-loops` | 2.1672 | +1.71% | accept, same code as the greedy step, not enough to replace the winner |
| 2630-2632 | combination (pair) | `-U_FORTIFY_SOURCE -fno-stack-protector` | 2.1619 | +1.46% | accept, same code as the greedy step, not enough to replace the winner |
| 2633-2635 | combination (pair) | `-fno-ipa-cp-clone -fno-unswitch-loops` | 2.1326 | +0.09% | reject |
| 2636-2638 | combination (pair) | `-U_FORTIFY_SOURCE -fno-unswitch-loops` | 2.1378 | +0.33% | reject |
| 2639-2641 | combination (pair) | `-U_FORTIFY_SOURCE -fno-ipa-cp-clone` | 2.1548 | +1.13% | reject |
| 2642-2644 | combination (pair) | `-fno-ipa-cp-clone -fno-stack-protector` | 2.1678 | +1.74% | accept, same code as the greedy step, not enough to replace the winner |
| 2645-2647 | PGO | winner `+ -fprofile-use` | 2.3367 | +6.91% | **accept** |
| 2648-2650 | PGO (near-miss variant) | winner `+ -fcf-protection=none -fprofile-use` | 2.3168 | +6.00% | accept, CI overlaps plain PGO, not the winner |
| 2651-2653 | microarch | winner `+ -march=znver5` | 2.3386 | +0.08% | reject |
| 2654-2656 | microarch | winner `+ -mtune=znver5` | 2.3336 | -0.13% | reject |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against `-O3 -fno-stack-protector`, PGO deltas against
`-O3 -fno-stack-protector`, and microarch deltas against the PGO winner. The greedy walk started from the Phase 4
`-fno-stack-protector` result rather than re-measuring it. The vector-width multiplier had no candidate (the shape
filter had excluded `256`).

## Observations

- **The three smaller accepts don't combine with anything.** Alone they read +1.19% to +1.72% against `-O3`; with
  `-fno-stack-protector` each read below the stack protector alone, and their pairs with each other read +0.09% to
  +1.13%, under any of their single gains. One reading is that they share whatever cppcheck_s gets from a changed
  code layout, with no separate effect each; this run doesn't measure that.
- **The pair tournament re-measured all three greedy steps' code** (nine timed runs at about 10 minutes each, niwot
  opportunity #35). Every pair read within 0.15% of its greedy step.
- **cppcheck_s is noisier than gcc_s and llvm_s here.** The baseline CI is ±0.44% (gcc_s ±0.14%, llvm_s ±0.055%),
  `-march=native`'s reps spread 1.5% (2.1156-2.1472) and PGO's 0.9%. niwot's cppcheck_s was noisier still (±1.0%).
- **PGO built different code on every rep** (all twelve PGO-based builds had distinct fingerprints), as expected on
  SPEC (CLAUDE.md, 2026-10-28). Plain PGO read 2.3278-2.3498.
- **The bandwidth gate waited before 32 of 80 timed runs**, about 16 minutes in all. No rep was slow and no rerun
  fired.

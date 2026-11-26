# `cfm mine` results: 823.llvm_s on `chicago`, 2026-11-26

This is the fifth intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `823.llvm_s` is
the speed version of `723.llvm_r` (LLVM's `llc`). Its `object.pm` tags it `pthread` and sets `$multiprocess`, so it
runs unpinned. niwot's mine found `-O3 -flto -fprofile-use` at +19.96% (LTO +7.18%, PGO +11.92%;
[write-up](mining_results.823.llvm_s.2026-10-28.md)). This machine's `723.llvm_r` found `-O3 -fno-pie -no-pie
-fno-stack-protector -fprofile-use` at +16.95%, with `-flto` a 1.26% loss ([write-up](mining_results.723.llvm_r.2026-11-22.md)).
Its corpus shape is frontend-bound at 58.5%, over the 55% gate, so the shape filter excluded six candidates.

## Headline result

**`-O3 -flto -fno-stack-protector -fprofile-use`, +28.96% over plain `-O3`** (ratio 1.9593 → 2.5268).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.9593 | — |
| `-O3 -flto` | 2.0590 | **+5.09%** |
| `+ -fno-stack-protector` (pair tournament) | 2.0802 | +1.03% |
| `+ -fprofile-use` | 2.5268 | **+21.47%** |

- **PGO gained +21.47% on top of LTO**, against +11.92% on niwot and +10.3% (without LTO) on llvm_r here. It is the
  second-largest PGO step on this host's int mines, after cpython_r's +22.0%.
- **`-flto` gained +5.09%**, where it lost 1.26% on llvm_r here; niwot's llvm_s got +7.18%. With LTO and PGO
  together, llvm_s's total is well above llvm_r's, which bears on [opportunity #19](host_chicago.md#open-items).
- **`-fno-stack-protector` got in through the pair tournament.** It gained +1.22%
  alone, then +0.98% as a greedy step on top of `-flto`, CI-clear but 0.02 points under the 1% bar. The pair
  tournament then measured the same code at 2.0802 (+1.03% over LTO), CI-clear of the LTO winner, and a pair
  replaces the winner with no 1% bar ([opportunity #10](host_chicago.md#open-items)). Here the step is real either
  way: six runs of that code read 2.0783-2.0804, all above LTO's 2.0584-2.0593.
- **Non-PIE gained only +0.54%** (CI-clear, under the bar), against +4.6% on llvm_r here. As PGO's near-miss
  variant it read 0.19% above plain PGO, CI-overlapping.
- **`-march=native` was flat (+0.02%).** On the winner, `-march=znver5` (+0.45%) and `-mtune=znver5` (+0.17%) were
  rejected on CI overlap.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 823.llvm_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `defef1b` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` |
| Thread placement | pthread (and `$multiprocess`), not pinned |
| Experiment id | 47 |
| Started / finished | 2026-11-25T20:49:29Z / 2026-11-26T16:18:54Z (19h29m) |
| Final status | `converged` |
| Trials | 57 (2520-2576), none skipped, no reruns |
| Candidates screened / confirmed | 6 / 6 (plus `-flto`, `-fno-pie -no-pie` and `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 58.5%, over the gate) |
| Fast-tracked (M4) | `-flto` (accepted 6 of 9, mean +5.85%), `-fno-pie -no-pie` (5 of 9, +2.82%), `-fno-stack-protector` (7 of 9, +1.83%) |
| Accepted in Phase 4 | `-flto` +5.09%, `-fno-stack-protector` +1.22% |
| Winning flags | `["-O3", "-flto", "-fno-stack-protector", "-fprofile-use"]`, +28.96% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 17 of 57 timed runs; no reruns; baseline recheck not flagged (+0.08%) |
| Power | package power median 84.97-85.00 W on every trial; CPU temperature 86.5-94.5°C |

A trial took about 17 minutes, an LTO trial about 21.5, and an LTO+PGO trial about 30.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 58.5%, `vectorization_density=moderate`,
`allocation_pressure=high`.

| Trial | Role | Ratio |
|---|---|---|
| 2520 | warm-up | 1.9625 |
| 2521 | warm-up | 1.9592 |
| 2522 | calibration | 1.9598 |
| 2523 | calibration | 1.9590 |
| 2524 | calibration | 1.9591 |
| 2558 | recheck | 1.9608 (+0.08%) |

The calibration mean is 1.9593, with a 95% CI of [1.9582, 1.9604] (±0.055%). Warm-up settled after the minimum two
reps (2074 s). Every `-O3` build had the same code fingerprint (`2763e7a5`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2525-2530 | screening | 6 candidates | 1.9581-1.9664 | | all survived |
| 2531-2533 | confirmation | `-fcf-protection=none` | 1.9630 | +0.19% | reject |
| 2534-2536 | confirmation | `-U_FORTIFY_SOURCE` | 1.9659 | +0.33% | reject (CI-clear, under the 1% bar) |
| 2537-2539 | confirmation | `-fno-ipa-cp-clone` | 1.9639 | +0.23% | reject (CI-clear, under the 1% bar) |
| 2540-2542 | confirmation | `-fno-unswitch-loops` | 1.9663 | +0.36% | reject (CI-clear, under the 1% bar) |
| 2543-2545 | confirmation | `-march=native` | 1.9597 | +0.02% | reject |
| 2546-2548 | confirmation | `-fno-math-errno` | 1.9598 | +0.03% | reject |
| 2549-2551 | confirmation (fast-tracked) | `-flto` | 2.0590 | +5.09% | **accept** (the greedy start) |
| 2552-2554 | confirmation (fast-tracked) | `-fno-pie -no-pie` | 1.9698 | +0.54% | reject (CI-clear, under the 1% bar) |
| 2555-2557 | confirmation (fast-tracked) | `-fno-stack-protector` | 1.9831 | +1.22% | **accept** |
| 2558 | baseline recheck | `-O3` | 1.9608 | +0.08% | not flagged |
| 2559-2561 | combination (greedy) | `-flto -fno-stack-protector` | 2.0792 | +0.98% | reject (CI-clear, under the 1% bar) |
| 2562-2564 | combination (pair) | `-flto -fno-stack-protector` | 2.0802 | +6.17% | **accept**, same code as the greedy step; replaces the LTO winner |
| 2565-2567 | PGO | winner `+ -fprofile-use` | 2.5268 | +21.47% | **accept** |
| 2568-2570 | PGO (near-miss variant) | winner `+ -fno-pie -no-pie -fprofile-use` | 2.5315 | +21.70% | accept, CI overlaps plain PGO, not the winner |
| 2571-2573 | microarch | winner `+ -march=znver5` | 2.5383 | +0.45% | reject |
| 2574-2576 | microarch | winner `+ -mtune=znver5` | 2.5312 | +0.17% | reject |

Phase 4 and pair deltas are against `-O3`, the greedy-step delta against `-O3 -flto`, PGO deltas against
`-O3 -flto -fno-stack-protector`, and microarch deltas against the PGO winner. The greedy walk started from the
Phase 4 `-flto` result rather than re-measuring it. The PGO near-miss list was `-fno-pie -no-pie`,
`-fno-unswitch-loops`, `-U_FORTIFY_SOURCE` and `-fno-ipa-cp-clone`; only the first was tried. The vector-width
multiplier was skipped because the winning set has no `-march=`.

## Observations

- **LTO and PGO together are worth far more here than on llvm_r.** On llvm_r here, `-flto` lost 1.26% alone, so the
  winner had no LTO and PGO added +10.3%. Here `-flto` gained +5.09% and PGO +21.47% on top of it. Both earlier
  llvm_r mines got about +24% from PGO on top of `-flto`. This is the strongest evidence yet for open item #19's
  question, though it is the speed benchmark, not llvm_r itself.
- **The greedy step and the pair measured the same code** (`a4e36c61`), 2.0792 and 2.0802, three timed runs at
  about 21.5 minutes each (niwot opportunity #35). The two reads straddle the 1% bar, which is how the pair rule
  (#10) let the step in.
- **llvm_s is very repeatable here.** The baseline CI is ±0.055%, and every non-PGO flagset's reps were within 0.2%.
- **PGO built different code on every rep** (all fifteen PGO builds had distinct fingerprints), as on niwot and as
  CLAUDE.md's 2026-10-28 entry describes. Unlike niwot's mine, no rep was slow: plain PGO read 2.5218-2.5296, and
  every PGO-based rep 2.5218-2.5407.
- **The bandwidth gate waited before 17 of 57 timed runs**, about 8.5 minutes in all. No rep was slow and no rerun
  fired.

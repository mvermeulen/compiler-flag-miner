# `cfm mine` results: 829.abc_s on `chicago`, 2026-11-27

This is the seventh intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `829.abc_s` is
the speed version of `729.abc_r` (the ABC logic-synthesis and verification tool, C). Its `@benchsets` are just
`intspeed specspeed` and it doesn't set `$multiprocess`, so it's single-threaded and was pinned with `taskset -c 1`.
niwot's mine accepted nothing, since its shape filter had excluded `-flto` (PGO read -0.64%); a hand-measured
follow-up there found `-O3 -flto` at +2.32% ([write-up](mining_results.829.abc_s.2026-10-25.md), niwot opportunity
#27), which led to `-flto` being exempted from the filter (#28). This machine's `729.abc_r` found
`-O3 -flto` at +2.26%, with PGO -8.59% on top ([write-up](mining_results.729.abc_r.2026-11-22.md)). Its corpus shape
is memory-bound at 72.9%, over the 55% gate, so the shape filter excluded eleven candidates; `-flto` is exempt from
the filter now, so it was screened.

## Headline result

**`-O3 -flto`, +2.53% over plain `-O3`** (ratio 2.1917 → 2.2472).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 2.1917 | — |
| `-O3 -flto` | 2.2472 | **+2.53%** |

- **`-flto` gives the speed version about the same gain as abc_r** (+2.53% against +2.26% on abc_r here), and
  matches niwot's hand-measured +2.32% on abc_s. The mine found it on its own this time because of the #28 exemption,
  on a shape read (72.9%) that would otherwise have excluded it.
- **PGO on top of LTO read +0.41%, CI-overlapping**, against -8.59% on abc_r here and -0.64% (without LTO) on niwot's
  abc_s. As on niwot, the speed version's training run doesn't mislead PGO the way abc_r's does.
- **`-fno-math-errno` lost 1.43%**, CI-clear below baseline; the only clear loss in the run.
- **`-march=native` was fast-tracked and lost 0.40%** (CI-clear below; abc_r here read +0.80%). On the winner,
  `-march=znver5` (-0.64%) and `-mtune=znver5` (-0.36%) were rejected on CI overlap.
- **`-fprefetch-loop-arrays` (-0.14%) and `-fgraphite-identity` (-0.19%) were flat.** `-fgraphite-identity` was a
  single-flag accept on abc_r here (+1.43% alone, -0.12% on top of LTO).

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 829.abc_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `d1e8074` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` (unused: single-threaded) |
| Thread placement | single-threaded, pinned with `taskset -c 1` |
| Experiment id | 49 |
| Started / finished | 2026-11-27T06:09:43Z / 2026-11-27T10:52:27Z (4h43m) |
| Final status | `converged` |
| Trials | 34 (2657-2690), none skipped, no reruns |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (frontend-bound-tagged), `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta` (compute-/backend-bound-tagged), `-mprefer-vector-width=256` (`vectorization_density=low`) (memory-bound 72.9%, over the gate) |
| Fast-tracked (M4) | `-march=native` (accepted 22 of 34, mean +17.43%) |
| Accepted in Phase 4 | `-flto` +2.53% |
| Winning flags | `["-O3", "-flto"]`, +2.53% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 16 of 34 timed runs; no reruns; baseline recheck not flagged (+0.02%) |
| Power | package power median 19.3-20.0 W on every trial (one pinned core); CPU temperature 73.4-82.4°C |

A trial took about 7.5 minutes, an LTO trial about 9, and an LTO+PGO trial about 12.5.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 72.9%, `vectorization_density=low`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2657 | warm-up | 2.1882 |
| 2658 | warm-up | 2.1877 |
| 2659 | calibration | 2.1912 |
| 2660 | calibration | 2.1922 |
| 2661 | calibration | 2.1918 |
| 2681 | recheck | 2.1922 (+0.02%) |

The calibration mean is 2.1917, with a 95% CI of [2.1905, 2.1930] (±0.057%). Warm-up settled after the minimum two
reps (921 s). Every `-O3` build had the same code fingerprint (`f281576f`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2662-2665 | screening | 4 candidates | 2.1893-2.2298 | | all survived |
| 2666-2668 | confirmation | `-fprefetch-loop-arrays` | 2.1887 | -0.14% | reject |
| 2669-2671 | confirmation | `-fgraphite-identity` | 2.1876 | -0.19% | reject |
| 2672-2674 | confirmation | `-flto` | 2.2473 | +2.53% | **accept** (the greedy start) |
| 2675-2677 | confirmation | `-fno-math-errno` | 2.1604 | -1.43% | reject (CI-clear, below) |
| 2678-2680 | confirmation (fast-tracked) | `-march=native` | 2.1830 | -0.40% | reject (CI-clear, below) |
| 2681 | baseline recheck | `-O3` | 2.1922 | +0.02% | not flagged |
| 2682-2684 | PGO | winner `+ -fprofile-use` | 2.2565 | +0.41% | reject |
| 2685-2687 | microarch | winner `+ -march=znver5` | 2.2327 | -0.64% | reject |
| 2688-2690 | microarch | winner `+ -mtune=znver5` | 2.2390 | -0.36% | reject |

Phase 4 deltas are against `-O3`, and Phase 6 deltas against `-O3 -flto`. With one accept there was no greedy step
beyond the start and no pair tournament. The PGO near-miss list was empty, so only plain PGO was tried. The
vector-width multiplier had no candidate (the shape filter had excluded `256`).

## Observations

- **The shape filter costs abc_s little here.** It excluded eleven candidates on a 72.9% memory-bound read, against
  one on abc_r's 38.2%. Of the flags abc_r tried that abc_s didn't, only `-U_FORTIFY_SOURCE` was a single-flag
  accept there (+1.01% alone, 0.00% on top of LTO), and nothing on abc_r improved on LTO alone.
- **PGO built identical code on every rep** (`86a28a13`, 2.2522-2.2590), like ntest_s and unlike the other SPEC PGO
  mines here (CLAUDE.md, 2026-10-28). abc_s's training run is evidently deterministic.
- **Package power read about 19.6 W**, as expected for one pinned core, and the CPU ran cooler (73-82°C) than on any
  unpinned mine here.
- **abc_s is very repeatable.** The baseline CI is ±0.057%, the six `-O3` runs read 2.1877-2.1922, and every
  flagset's reps were within 0.6%.
- **The bandwidth gate waited before 16 of 34 timed runs**, about 8 minutes in all. No rep was slow and no rerun
  fired.

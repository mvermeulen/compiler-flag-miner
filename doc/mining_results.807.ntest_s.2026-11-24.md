# `cfm mine` results: 807.ntest_s on `chicago`, 2026-11-24

This is the second intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `807.ntest_s` is
the NTest Othello engine (C++, OpenMP; `@benchsets` `intspeed openmp specspeed`), run as one copy with
`threads = 32`. niwot's mine found `-O3 -march=native -flto -fprofile-use` at +19.21% (`-march=native` +10.92%,
LTO +3.64%, PGO +3.69%; [write-up](mining_results.807.ntest_s.2026-10-26.md)), without non-PIE in the catalog. This
machine's `707.ntest_r` found `-O3 -march=native -fno-pie -no-pie -fprofile-use` at +26.22%, with `-flto` rejected on
top ([write-up](mining_results.707.ntest_r.2026-11-19.md)). Its corpus shape is memory-bound at 41.9%, under the 55%
gate, so only `-mprefer-vector-width=256` was excluded (on `vectorization_density=low`).

## Headline result

**`-O3 -march=native -flto -fno-pie -no-pie -fprofile-use`, +25.53% over plain `-O3`** (ratio 1.9921 → 2.5006).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.9921 | — |
| `-O3 -march=native` | 2.2241 | **+11.65%** |
| `+ -flto` | 2.3187 | +4.25% |
| `+ -fno-pie -no-pie` | 2.3897 | +3.06% |
| `+ -fprofile-use` | 2.5006 | +4.64% |

- **niwot's three steps reproduce closely**: `-march=native` +11.65% against +10.92%, LTO +4.25% against +3.64%,
  PGO +4.64% against +3.69%. Non-PIE, new since niwot's mine, adds the other +3.06%.
- **`-flto` was accepted here but not on `707.ntest_r`**, where it read +0.96% on top of `-march=native -fno-pie
  -no-pie`. Here it gained +7.08% alone and +4.25% on top of `-march=native`.
- **Non-PIE gained +2.73% alone** and +3.06% on top of `-march=native -flto`, against +4.78% alone and +6.53% on
  top of `-march=native` on ntest_r.
- **The near-miss PGO variant (`+ -fno-stack-protector`) read 0.18% above plain PGO**, with overlapping CIs, so plain
  PGO stayed the winner. `-fno-stack-protector` had read +0.89% alone, CI-clear but under the 1% bar.
- **Nothing else moved**: the other eleven candidates read -0.53% to +0.18%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 807.ntest_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `1c41ead` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` |
| Thread placement | OpenMP (`OMP_PLACES`/`OMP_PROC_BIND`) |
| Experiment id | 44 |
| Started / finished | 2026-11-24T05:00:19Z / 2026-11-24T18:56:25Z (13h56m) |
| Final status | `converged` |
| Trials | 86 (2329-2414), none skipped, no reruns |
| Candidates screened / confirmed | 14 / 14 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-mprefer-vector-width=256` (`vectorization_density=low`); none on `resource_dominance` (41.9% is under the gate) |
| Fast-tracked (M4) | `-march=native` (accepted 20 of 32, mean +13.92%) |
| Accepted in Phase 4 | `-march=native` +11.65%, `-flto` +7.08%, `-fno-pie -no-pie` +2.73% |
| Winning flags | `["-O3", "-march=native", "-flto", "-fno-pie -no-pie", "-fprofile-use"]`, +25.53% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 42 of 86 timed runs; no reruns; baseline recheck not flagged (+0.13%) |
| Power | package power median 84.99 W on every trial; CPU temperature 89.2-95.6°C |

A trial took about 10 minutes, about 9 with `-march=native` or LTO.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 41.9%, `vectorization_density=low`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2329 | warm-up | 1.9928 |
| 2330 | warm-up | 1.9915 |
| 2331 | calibration | 1.9923 |
| 2332 | calibration | 1.9921 |
| 2333 | calibration | 1.9919 |
| 2393 | recheck | 1.9947 (+0.13%) |

The calibration mean is 1.9921, with a 95% CI of [1.9916, 1.9926] (±0.025%), the tightest of any int mine here
(abc_r's ±0.03% is next). Warm-up settled after the minimum two reps (1203 s). Every `-O3` build had the same code
fingerprint (`ef51a2be`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2334-2347 | screening | 14 candidates | 1.9844-2.1313 | | all survived |
| 2348-2350 | confirmation | `-fprefetch-loop-arrays` | 1.9869 | -0.26% | reject |
| 2351-2353 | confirmation | `-fgraphite-identity` | 1.9914 | -0.04% | reject |
| 2354-2356 | confirmation | `-flto` | 2.1330 | +7.08% | **accept** |
| 2357-2359 | confirmation | `-fno-pie -no-pie` | 2.0464 | +2.73% | **accept** |
| 2360-2362 | confirmation | `-fno-stack-protector` | 2.0098 | +0.89% | reject (CI-clear, under the 1% bar) |
| 2363-2365 | confirmation | `-fcf-protection=none` | 1.9946 | +0.13% | reject (CI-clear, under the 1% bar) |
| 2366-2368 | confirmation | `-U_FORTIFY_SOURCE` | 1.9908 | -0.07% | reject |
| 2369-2371 | confirmation | `-funroll-loops` | 1.9816 | -0.53% | reject |
| 2372-2374 | confirmation | `-Ofast` | 1.9855 | -0.33% | reject |
| 2375-2377 | confirmation | `-ffast-math` | 1.9885 | -0.18% | reject |
| 2378-2380 | confirmation | `-fno-math-errno` | 1.9955 | +0.17% | reject |
| 2381-2383 | confirmation | `-fno-ipa-cp-clone` | 1.9932 | +0.06% | reject |
| 2384-2386 | confirmation | `-fno-unswitch-loops` | 1.9947 | +0.13% | reject |
| 2387-2389 | confirmation | `-fipa-pta` | 1.9957 | +0.18% | reject |
| 2390-2392 | confirmation (fast-tracked) | `-march=native` | 2.2241 | +11.65% | **accept** (the greedy start) |
| 2393 | baseline recheck | `-O3` | 1.9947 | +0.13% | not flagged |
| 2394-2396 | combination (greedy) | `-march=native -flto` | 2.3187 | +4.25% | **accept** |
| 2397-2399 | combination (greedy) | `+ -fno-pie -no-pie` | 2.3897 | +3.06% | **accept** |
| 2400-2402 | combination (pair) | `-flto -march=native` | 2.3230 | +16.61% | accept, same code as the greedy step, not enough to replace the winner |
| 2403-2405 | combination (pair) | `-flto -fno-pie -no-pie` | 2.1776 | +9.31% | accept, not enough to replace the greedy winner |
| 2406-2408 | combination (pair) | `-fno-pie -no-pie -march=native` | 2.2819 | +14.55% | accept, not enough to replace the greedy winner |
| 2409-2411 | PGO | winner `+ -fprofile-use` | 2.5006 | +4.64% | **accept** |
| 2412-2414 | PGO (near-miss variant) | winner `+ -fno-stack-protector -fprofile-use` | 2.5052 | +4.83% | accept, CI overlaps plain PGO, not the winner |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against the step before, and Phase 6 deltas against
`-O3 -march=native -flto -fno-pie -no-pie`. The greedy walk started from the Phase 4 `-march=native` result rather
than re-measuring it. The PGO near-miss list was `-fno-stack-protector` and `-fcf-protection=none`; only the first
was tried. The microarch multiplier was skipped (`-march=native` in the set), and the vector-width multiplier had no
candidate (the shape filter had excluded `256`).

## Observations

- **ntest_s is very repeatable on this host.** Every flagset's three reps were within 1% of each other, and most
  within 0.3%; the six `-O3` runs read 1.9915-1.9947. With the baseline CI at ±0.025%, the 1% bar decided both
  hardening rejects, not CI overlap.
- **PGO built identical code on every rep** (`d5afa86c`, 2.4964-2.5031), and the near-miss variant's three reps did
  too (`78192cc7`). On `823.llvm_s` every SPEC PGO build differed (CLAUDE.md, 2026-10-28); ntest_s's training run
  evidently isn't affected the same way.
- **The pair tournament re-measured the greedy step's code** (`18d668b4`: 2.3230 against 2.3187), three timed runs
  at about 9 minutes each (niwot opportunity #35).
- **The bandwidth gate waited before 42 of 86 timed runs**, about 21 minutes in all. No rep was slow and no rerun
  fired.
- **At 13h56m this is the longest int mine here so far**: 14 screened candidates, all confirmed, at about
  10 minutes a trial.

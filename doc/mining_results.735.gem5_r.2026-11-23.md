# `cfm mine` results: 735.gem5_r on `chicago`, 2026-11-23

This is the eleventh intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `735.gem5_r` is
the gem5 architecture simulator (C++). Both earlier mines found `-O3 -flto` and rejected PGO as a regression: this
machine in August at +13.62%, with PGO -6.7% on top ([write-up](mining_results.735.gem5_r.2026-08-27.md)), and
niwot at +11.01%, with PGO -10.59% on top ([write-up](mining_results.735.gem5_r.2026-10-20.md)). Its corpus shape is
frontend-bound at 60.3%, over the 55% gate, so the shape filter excluded six candidates.

## Headline result

**`-O3 -flto -fno-pie -no-pie -fno-stack-protector -march=znver5`, +13.05% over plain `-O3`** (ratio 75.832 →
85.729).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 75.832 | — |
| `-O3 -flto` | 80.879 | **+6.65%** |
| `+ -fno-pie -no-pie` | 83.173 | +2.84% |
| `+ -fno-stack-protector` | 84.322 | +1.38% |
| `+ -march=znver5` | 85.729 | +1.67% |

- **PGO lost 9.40% again**, against -6.7% in August and -10.59% on niwot. gem5 is the third benchmark in this
  intrate run where PGO lost, after stockfish (-1.14%) and abc (-8.59%). niwot's `-fprofile-partial-training`
  check removed gem5's regression without a clear gain (niwot opportunity #21).
- **`-flto` gave +6.65%**, about half of August's +13.62% and niwot's +11.01%. On this machine's August run the
  hardening opt-outs weren't in the catalog; here non-PIE and `-fno-stack-protector` added +4.3% on top of LTO,
  so the total (+13.05%) is about August's.
- **`-march=znver5` was accepted on top of the Phase 5 set (+1.67%)**, the second microarch accept here, after
  cpython's `-mtune=znver5`. `-march=native` alone read +0.78%, CI-clear but under the 1% bar, and as the PGO
  near-miss variant it lost 2.4 points less than plain PGO (-6.74% against -9.40%). `-mtune=znver5` read +0.29%, so
  the gain is from the instruction sets, not the tuning.
- **`-mprefer-vector-width=256` on top of `-march=znver5` was flat (+0.10%).** The shape filter had deferred it
  to the vector-width multiplier, as on stockfish (-8.25% there).
- **`-fno-stack-protector` was fast-tracked** (accepted 4 of 6 in the frontend-bound cluster) and accepted at
  +2.13% alone. Non-PIE is in six of the eleven intrate winning sets here.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 735.gem5_r` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `651d740` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 39 |
| Started / finished | 2026-11-23T00:45:25Z / 2026-11-23T11:10:57Z (10h26m) |
| Final status | `converged` |
| Trials | 71 (2101-2171), none skipped, no reruns |
| Candidates screened / confirmed | 8 / 8 (plus `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 60.3%, over the gate); `-mprefer-vector-width=256` deferred to Phase 6 |
| Fast-tracked (M4) | `-fno-stack-protector` (accepted 4 of 6, mean +1.67%) |
| Accepted in Phase 4 | `-flto` +6.65%, `-fno-pie -no-pie` +3.43%, `-fno-stack-protector` +2.13% |
| Winning flags | `["-O3", "-flto", "-fno-pie -no-pie", "-fno-stack-protector", "-march=znver5"]`, +13.05% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 1 of 71 timed runs; no reruns; baseline recheck not flagged (+0.02%) |
| Power | package power median 84.99 W on every trial; CPU temperature 86.4-96.0°C |

A trial took about 8 minutes, an LTO trial about 8.5, and a PGO trial about 17.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 60.3%, `vectorization_density=moderate`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2101 | warm-up | 75.656 |
| 2102 | warm-up | 75.904 |
| 2103 | calibration | 75.976 |
| 2104 | calibration | 75.742 |
| 2105 | calibration | 75.778 |
| 2141 | recheck | 75.848 (+0.02%) |

The calibration mean is 75.832, with a 95% CI of [75.519, 76.145] (±0.41%). Warm-up settled after the minimum two
reps (973 s). Every gem5 build had a different code fingerprint, `-O3` included (see Observations).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2106-2113 | screening | 8 candidates | 75.20-80.61 | | all survived |
| 2114-2116 | confirmation | `-flto` | 80.879 | +6.65% | **accept** (the greedy start) |
| 2117-2119 | confirmation | `-fno-pie -no-pie` | 78.430 | +3.43% | **accept** |
| 2120-2122 | confirmation | `-fcf-protection=none` | 76.191 | +0.47% | reject |
| 2123-2125 | confirmation | `-U_FORTIFY_SOURCE` | 75.612 | -0.29% | reject |
| 2126-2128 | confirmation | `-fno-ipa-cp-clone` | 75.585 | -0.33% | reject |
| 2129-2131 | confirmation | `-fno-unswitch-loops` | 75.801 | -0.04% | reject |
| 2132-2134 | confirmation | `-march=native` | 76.427 | +0.78% | reject (CI-clear, under the 1% bar) |
| 2135-2137 | confirmation | `-fno-math-errno` | 75.802 | -0.04% | reject |
| 2138-2140 | confirmation (fast-tracked) | `-fno-stack-protector` | 77.447 | +2.13% | **accept** |
| 2141 | baseline recheck | `-O3` | 75.848 | +0.02% | not flagged |
| 2142-2144 | combination (greedy) | `-flto -fno-pie -no-pie` | 83.173 | +2.84% | **accept** |
| 2145-2147 | combination (greedy) | `+ -fno-stack-protector` | 84.322 | +1.38% | **accept** |
| 2148-2150 | combination (pair) | `-flto -fno-pie -no-pie` | 82.877 | +9.29% | accept, not enough to replace the greedy winner |
| 2151-2153 | combination (pair) | `-fno-pie -no-pie -fno-stack-protector` | 80.400 | +6.02% | accept, not enough to replace the greedy winner |
| 2154-2156 | combination (pair) | `-flto -fno-stack-protector` | 82.167 | +8.35% | accept, not enough to replace the greedy winner |
| 2157-2159 | PGO | winner `+ -fprofile-use` | 76.394 | -9.40% | reject (CI-clear, below) |
| 2160-2162 | PGO (near-miss variant) | winner `+ -march=native -fprofile-use` | 78.636 | -6.74% | reject (CI-clear, below) |
| 2163-2165 | microarch | winner `+ -march=znver5` | 85.729 | +1.67% | **accept** |
| 2166-2168 | microarch | winner `+ -mtune=znver5` | 84.562 | +0.29% | reject |
| 2169-2171 | vector width | winner `+ -march=znver5 -mprefer-vector-width=256` | 85.817 | +0.10% | reject |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against the step before, and Phase 6 deltas against
the set they were layered on. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it.

## Observations

- **Every gem5 build is a different binary.** All six `-O3` builds had different code fingerprints, as did every
  rep of every other flagset, so the no-code-change guard can't fire on gem5 and the pair tournament's
  re-measure of `-flto -fno-pie -no-pie` (82.88 against the greedy step's 83.17) can't be checked by fingerprint.
  That's the same symptom as `709.cactus_r`'s embedded build time (CLAUDE.md, 2026-11-05); the run doesn't show
  what gem5 embeds. It doesn't make a result wrong, and the `-O3` reps still read within 0.4% of each other.
- **PGO's loss is consistent and large**: three reps at 76.29-76.51, giving back almost all of the Phase 5 gain
  (76.39 against `-O3`'s 75.83). With every build different, the PGO reps can't be checked for identical code.
- **`-march=znver5` gained more on top of the Phase 5 set than `-march=native` did on plain `-O3`** (+1.67%
  against +0.78%), and `-march=native` also narrowed PGO's loss by 2.4 points. Both CIs were clear of what they
  were layered on. One possibility is that the wider instruction sets pay off more once LTO has inlined across
  files; the run doesn't test that directly.
- **The CPU reached 96.0°C**, with package power at 84.99 W throughout.

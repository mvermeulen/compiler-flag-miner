# `cfm mine` results: 753.ns3_r on `chicago`, 2026-11-23

This is the thirteenth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `753.ns3_r`
is the ns-3 discrete-event network simulator (C++). Both earlier mines found `-O3 -flto -fprofile-use`: this machine
in August at +37.99% (LTO +23.3%, PGO +11.9% on top; [write-up](mining_results.753.ns3_r.2026-08-27.md)), and niwot
at +26.66% (LTO +21.4%, PGO +4.3%; [write-up](mining_results.753.ns3_r.2026-10-21.md)). Neither had non-PIE or
`-fno-stack-protector` in the catalog. Its corpus shape is frontend-bound at 60.7%, over the 55% gate, so the shape
filter excluded six candidates.

## Headline result

**`-O3 -flto -fno-pie -no-pie -fno-stack-protector -fprofile-use`, +32.13% over plain `-O3`** (ratio 85.800 →
113.367).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 85.800 | — |
| `-O3 -flto` | 100.339 | **+16.95%** |
| `+ -fno-pie -no-pie` | 107.110 | **+6.75%** |
| `+ -fno-stack-protector` | 110.317 | +2.99% |
| `+ -fprofile-use` | 113.367 | +2.76% |

- **Non-PIE gained +11.68% alone**, by far the largest non-PIE gain on this host (ntest's +4.78% is next), and
  +6.75% on top of `-flto`. It is now in seven of the thirteen intrate winning sets here.
- **`-flto` gained +16.95%**, less than August's +23.07% and niwot's +21.4%. It was fast-tracked (accepted 4 of 7
  in the frontend-bound cluster), as was `-fno-stack-protector` (5 of 7), which gained +2.89% alone.
- **PGO added only +2.76%** on top of the Phase 5 set, against +11.94% on top of `-flto` in August and +4.3% on
  niwot. One possibility is that non-PIE and the stack protector take some of what PGO gave on top of LTO alone;
  this run didn't measure `-flto -fprofile-use` to check.
- **The total (+32.13%) is under August's +37.99%**, but against a much faster `-O3`: August's baseline read 70.88
  and its LTO+PGO winner 97.81, against 85.80 and 113.37 here. The two machine states differ too much (August ran
  at far lower package power) to compare ratios directly.
- **`-march=native` was flat (-0.05%)**, and on top of the winner `-march=znver5` (-0.62%) and `-mtune=znver5`
  (-0.79%) were rejected on CI overlap, as in August.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 753.ns3_r` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `d02c3f8` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 41 |
| Started / finished | 2026-11-23T14:23:42Z / 2026-11-23T21:47:02Z (7h23m) |
| Final status | `converged` |
| Trials | 64 (2206-2269), none skipped, no reruns |
| Candidates screened / confirmed | 7 / 7 (plus `-flto` and `-fno-stack-protector` fast-tracked) |
| Excluded on shape (Phase 2) | `-funroll-loops`, `-fprefetch-loop-arrays`, `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` (frontend-bound 60.7%, over the gate) |
| Fast-tracked (M4) | `-flto` (accepted 4 of 7, mean +4.80%), `-fno-stack-protector` (accepted 5 of 7, mean +1.73%) |
| Accepted in Phase 4 | `-flto` +16.95%, `-fno-pie -no-pie` +11.68%, `-fno-stack-protector` +2.89% |
| Winning flags | `["-O3", "-flto", "-fno-pie -no-pie", "-fno-stack-protector", "-fprofile-use"]`, +32.13% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 5 of 64 timed runs; no reruns; baseline recheck not flagged (+0.52%) |
| Power | package power median 84.99 W on every trial; CPU temperature 91.4-97.0°C |

A trial took about 5.5 minutes, an LTO trial about 7, and an LTO+PGO trial about 13.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 60.7%, `vectorization_density=moderate`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2206 | warm-up | 86.100 |
| 2207 | warm-up | 85.951 |
| 2208 | calibration | 85.758 |
| 2209 | calibration | 85.631 |
| 2210 | calibration | 86.010 |
| 2245 | recheck | 86.243 (+0.52%) |

The calibration mean is 85.800, with a 95% CI of [85.320, 86.279] (±0.56%). Warm-up settled after the minimum two
reps (703 s). Every `-O3` build had the same code fingerprint (`9b9250a3`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2211-2217 | screening | 7 candidates | 85.62-95.65 | | all survived |
| 2218-2220 | confirmation | `-fno-pie -no-pie` | 95.822 | +11.68% | **accept** |
| 2221-2223 | confirmation | `-fcf-protection=none` | 86.384 | +0.68% | reject |
| 2224-2226 | confirmation | `-U_FORTIFY_SOURCE` | 86.302 | +0.59% | reject |
| 2227-2229 | confirmation | `-fno-ipa-cp-clone` | 86.008 | +0.24% | reject |
| 2230-2232 | confirmation | `-fno-unswitch-loops` | 85.998 | +0.23% | reject |
| 2233-2235 | confirmation | `-march=native` | 85.754 | -0.05% | reject |
| 2236-2238 | confirmation | `-fno-math-errno` | 86.027 | +0.26% | reject |
| 2239-2241 | confirmation (fast-tracked) | `-flto` | 100.339 | +16.95% | **accept** (the greedy start) |
| 2242-2244 | confirmation (fast-tracked) | `-fno-stack-protector` | 88.276 | +2.89% | **accept** |
| 2245 | baseline recheck | `-O3` | 86.243 | +0.52% | not flagged |
| 2246-2248 | combination (greedy) | `-flto -fno-pie -no-pie` | 107.110 | +6.75% | **accept** |
| 2249-2251 | combination (greedy) | `+ -fno-stack-protector` | 110.317 | +2.99% | **accept** |
| 2252-2254 | combination (pair) | `-flto -fno-stack-protector` | 103.575 | +20.72% | accept, not enough to replace the greedy winner |
| 2255-2257 | combination (pair) | `-flto -fno-pie -no-pie` | 106.777 | +24.45% | accept, same code as the greedy step, not enough to replace the winner |
| 2258-2260 | combination (pair) | `-fno-pie -no-pie -fno-stack-protector` | 98.176 | +14.42% | accept, not enough to replace the greedy winner |
| 2261-2263 | PGO | winner `+ -fprofile-use` | 113.367 | +2.76% | **accept** |
| 2264-2266 | microarch | winner `+ -march=znver5` | 112.666 | -0.62% | reject |
| 2267-2269 | microarch | winner `+ -mtune=znver5` | 112.467 | -0.79% | reject |

Phase 4 and pair deltas are against `-O3`, greedy-step deltas against the step before, and Phase 6 deltas against
the set they were layered on. The greedy walk started from the Phase 4 `-flto` result rather than re-measuring it.
The PGO near-miss list was empty (no Phase 4 reject was CI-clear of baseline), so only plain PGO was tried. The
vector-width multiplier was skipped: the shape filter hadn't deferred a width candidate, and the winning set has no
`-march=`.

## Observations

- **The three accepted flags mostly add up.** Alone they gained +16.95%, +11.68% and +2.89%; their product would be
  +34.4%, and the greedy walk reached +28.57%. Two of the three pairs read below their members' product (non-PIE
  with `-flto` +24.45% against +30.6%; non-PIE with the stack protector +14.42% against +14.91%), while `-flto` with
  the stack protector matched it (+20.72% against +20.33%). The overlap is mostly between LTO and non-PIE.
- **The pair tournament re-measured the greedy step's code** (`8000b4e9`: 106.78 against 107.11), three timed
  runs at about 7 minutes each (niwot opportunity #35).
- **PGO built identical code on every rep** (`00bd5f43`, 113.17-113.55), so ns3's training run is deterministic.
- **The `-fno-stack-protector` greedy step had the widest CI of the run** (±0.96%; reps 109.84-110.64), but its
  low end (109.26) still cleared the previous step's high end (107.45).
- **The CPU reached 97.0°C**, with package power at 84.99 W throughout.

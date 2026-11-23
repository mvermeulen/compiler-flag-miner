# `cfm mine` results: 750.sealcrypto_r on `chicago`, 2026-11-23

This is the twelfth intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)).
`750.sealcrypto_r` is Microsoft SEAL, a homomorphic encryption library (C++). This machine mined it twice in
August, both times finding `-O3 -march=native` (+14.17% in [`2026-08-24`](mining_results.750.sealcrypto_r.2026-08-24.md),
+15.63% in [`2026-08-24b`](mining_results.750.sealcrypto_r.2026-08-24b.md)), with PGO skipped on shape. niwot's mine
found `-O3 -march=native` at +20.49%, and its hand-measured follow-up added PGO for +32.32% with `-flto` a 3.3% loss
([write-up](mining_results.750.sealcrypto_r.2026-10-18.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-23)).
Its corpus shape is compute-bound at 55.1%, 0.1 points over the 55% gate, so the shape filter excluded nine
candidates.

## Headline result

**`-O3 -march=native -fprofile-use`, +34.93% over plain `-O3`** (ratio 60.902 → 82.178).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 60.902 | — |
| `-O3 -march=native` | 75.362 | **+23.74%** |
| `+ -fprofile-use` | 82.178 | **+9.04%** |

- **The mine now finds niwot's hand-measured answer on its own.** PGO added +9.04% on top of `-march=native`,
  against +10.36% on niwot; August's runs skipped PGO on shape, which the mine no longer does.
- **`-march=native` gained +23.74%**, against +14.17% and +15.63% here in August and +20.49% on niwot. It was
  fast-tracked on ntest's accept. August's baselines were still settling (50.7-56.2) at much lower package power
  (about 26 W on the 2026-08-24 `cfm measure` check, against 85 W here), so the two machine states aren't
  comparable enough to say why the gain grew.
- **`-flto` lost 1.84%** (CI clear, below), as on niwot (-3.29% on top of `-march=native`). It was fast-tracked
  on ntest's +3.49% accept. sealcrypto is the second benchmark in this intrate run where LTO lost alone, after
  stockfish.
- **`-mprefer-vector-width=256` on top of the winner lost 1.04%** (CI clear, below), as it lost 8.25% on
  stockfish. The microarch multiplier was skipped because `-march=native` was already in the set.
- **Nothing else moved**: `-funroll-loops` +0.32%, `-fno-math-errno` +0.30%, `-Ofast` and `-ffast-math` +0.06%,
  all CI-overlapping. In the August re-mine `-Ofast`, `-ffast-math` and `-funroll-loops` read about -5.5%,
  against a settling baseline.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 750.sealcrypto_r` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `651d740` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 40 |
| Started / finished | 2026-11-23T11:11:57Z / 2026-11-23T14:22:42Z (3h11m) |
| Final status | `converged` |
| Trials | 34 (2172-2205), none skipped, no reruns |
| Candidates screened / confirmed | 4 / 4 (plus `-march=native` and `-flto` fast-tracked) |
| Excluded on shape (Phase 2) | `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (frontend-bound-tagged), `-fprefetch-loop-arrays`, `-fipa-pta`, `-fgraphite-identity` (compute-bound 55.1%, over the gate); `-mprefer-vector-width=256` deferred to Phase 6 |
| Fast-tracked (M4) | `-march=native` (accepted 1 of 1, mean +14.79%), `-flto` (accepted 1 of 1, mean +3.49%), both from ntest |
| Accepted in Phase 4 | `-march=native` +23.74% |
| Winning flags | `["-O3", "-march=native", "-fprofile-use"]`, +34.93% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 11 of 34 timed runs; no reruns; baseline recheck not flagged (-0.16%) |
| Power | package power median 84.99 W on every trial; CPU temperature 90.6-96.0°C |

A trial took about 5 minutes, a `-march=native` trial about 4.5, and a PGO trial about 8.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): compute-bound 55.1%, `vectorization_density=moderate`,
`allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 2172 | warm-up | 60.929 |
| 2173 | warm-up | 60.937 |
| 2174 | calibration | 60.808 |
| 2175 | calibration | 60.916 |
| 2176 | calibration | 60.983 |
| 2199 | recheck | 60.803 (-0.16%) |

The calibration mean is 60.902, with a 95% CI of [60.683, 61.122] (±0.36%). Warm-up settled after the minimum two
reps (627 s). Every `-O3` build had the same code fingerprint (`51c75fe8`). Unlike August, the baseline didn't
settle downward: all six `-O3` runs read 60.80-60.94.

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2177-2180 | screening | 4 candidates | 60.81-61.06 | | all survived |
| 2181-2183 | confirmation | `-funroll-loops` | 61.097 | +0.32% | reject |
| 2184-2186 | confirmation | `-Ofast` | 60.938 | +0.06% | reject |
| 2187-2189 | confirmation | `-ffast-math` | 60.937 | +0.06% | reject |
| 2190-2192 | confirmation | `-fno-math-errno` | 61.082 | +0.30% | reject |
| 2193-2195 | confirmation (fast-tracked) | `-march=native` | 75.362 | +23.74% | **accept** (the greedy start) |
| 2196-2198 | confirmation (fast-tracked) | `-flto` | 59.781 | -1.84% | reject (CI-clear, below) |
| 2199 | baseline recheck | `-O3` | 60.803 | -0.16% | not flagged |
| 2200-2202 | PGO | winner `+ -fprofile-use` | 82.178 | +9.04% | **accept** |
| 2203-2205 | vector width | winner `+ -mprefer-vector-width=256` | 81.326 | -1.04% | reject (CI-clear, below) |

Phase 4 deltas are against `-O3`, and Phase 6 deltas against the set they were layered on. With one Phase 4 accept,
Phase 5 had nothing to combine and ran no trials. The PGO near-miss list was empty (no Phase 4 reject was CI-clear
above baseline), so only plain PGO was tried.

## Observations

- **The shape gate may have cost a non-PIE gain.** At 55.1% compute-bound, 0.1 points over the gate, nine flags
  were excluded, among them `-fno-pie -no-pie`. On ntest, the other compute-bound benchmark here, it gained +4.78%
  alone and +6.53% on top of `-march=native`, and it is in six of the eleven earlier intrate winning sets here.
  niwot's mine ran before non-PIE was in the catalog, so it has never been measured on sealcrypto. A
  `--no-shape-filter` re-mine or a hand-measured check would settle it ([opportunity #20](host_chicago.md#open-items)).
- **PGO built identical code on every rep** (`6b0859f6`, 82.11-82.25), so sealcrypto's training run is
  deterministic, as abc's, cppcheck's and omnetpp's are.
- **The bandwidth gate waited more often than on any other intrate mine here** (11 of 34 runs, against 1 of 71
  on gem5 and 5 of 92 on abc); recorded probes read 88-106 GB/s against a session best of 101-106. No rep was
  slow and no rerun fired, so it cost about 5.5 minutes and nothing else.
- **The baseline held steady**: six `-O3` runs within 0.30% of each other, against August's 56.2 → 50.7 settling, which motivated PR #38's screening fix and PR #41's warm-up reps.

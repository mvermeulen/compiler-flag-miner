# `cfm mine` results: 777.zstd_r on `chicago`, 2026-11-24

This is the fourteenth and last intrate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)).
`777.zstd_r` is the Zstandard compressor (C). This machine's August mine accepted nothing, with `-march=native` about
+0.7%, under the 1% bar ([write-up](mining_results.777.zstd_r.2026-08-25.md)). niwot's mine accepted `-O3
-march=native` at +1.72%, and its follow-up found `-flto` flat (+0.24%) and PGO a 1.7% loss
([write-up](mining_results.777.zstd_r.2026-10-22.md)). Its corpus shape is memory-bound at 64.0%, over the 55% gate,
so the shape filter excluded ten candidates.

## Headline result

**`-O3 -march=native`, +1.18% over plain `-O3`** (ratio 41.682 → 42.172).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 41.682 | — |
| `-O3 -march=native` | 42.172 | +1.18% |

- **`-march=native` cleared the 1% bar by 0.18 points**, between August's +0.7% here and niwot's +1.72%. It was
  fast-tracked (accepted 19 of 30 in the memory-bound cluster, mean +14.82%).
- **PGO lost 3.25%** (CI clear, below), against -1.7% in niwot's follow-up. All three reps built identical code
  (`b3c1e172`) and read 40.77-40.86. zstd is the fourth intrate benchmark here where PGO lost, after stockfish,
  abc and gem5.
- **`-flto` was flat (-0.21%)**, as on niwot (+0.24%). `-fprefetch-loop-arrays` (+0.05%) and
  `-fgraphite-identity` (+0.19%) were flat too; `-fno-math-errno` built the same code as `-O3` and was skipped.
- **`-mprefer-vector-width=256` on top of `-march=native` was flat (-0.19%).** The microarch multiplier was
  skipped because `-march=native` was already in the set.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 777.zstd_r` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `5ca9463` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `copies = 32` |
| Experiment id | 42 |
| Started / finished | 2026-11-23T21:48:02Z / 2026-11-24T01:53:24Z (4h05m) |
| Final status | `converged` |
| Trials | 28 (2270-2297), one skipped as unchanged code (`-fno-math-errno`), no reruns |
| Candidates screened / confirmed | 4 / 3 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (frontend-bound-tagged), `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta` (memory-bound 64.0%, over the gate); `-mprefer-vector-width=256` deferred to Phase 6 |
| Fast-tracked (M4) | `-march=native` (accepted 19 of 30, mean +14.82%) |
| Accepted in Phase 4 | `-march=native` +1.18% |
| Winning flags | `["-O3", "-march=native"]`, +1.18% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 17 of 27 timed runs; no reruns; baseline recheck not flagged (+0.18%) |
| Power | package power median 84.98-85.00 W on every trial; CPU temperature 93.6-97.0°C |

A trial took about 9 minutes, an LTO trial about 8.5, and a PGO trial about 11.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 64.0%, `vectorization_density=moderate`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2270 | warm-up | 41.709 |
| 2271 | warm-up | 41.823 |
| 2272 | calibration | 41.731 |
| 2273 | calibration | 41.741 |
| 2274 | calibration | 41.575 |
| 2291 | recheck | 41.757 (+0.18%) |

The calibration mean is 41.682, with a 95% CI of [41.451, 41.914] (±0.55%). Warm-up settled after the minimum two
reps (1079 s). Every `-O3` build had the same code fingerprint (`8dda3760`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2275-2278 | screening | 4 candidates | 41.66-41.75 | | 3 survived; `-fno-math-errno` skipped (same code as `-O3`) |
| 2279-2281 | confirmation | `-fprefetch-loop-arrays` | 41.703 | +0.05% | reject |
| 2282-2284 | confirmation | `-fgraphite-identity` | 41.762 | +0.19% | reject |
| 2285-2287 | confirmation | `-flto` | 41.593 | -0.21% | reject |
| 2288-2290 | confirmation (fast-tracked) | `-march=native` | 42.172 | +1.18% | **accept** |
| 2291 | baseline recheck | `-O3` | 41.757 | +0.18% | not flagged |
| 2292-2294 | PGO | winner `+ -fprofile-use` | 40.803 | -3.25% | reject (CI-clear, below) |
| 2295-2297 | vector width | winner `+ -mprefer-vector-width=256` | 42.094 | -0.19% | reject |

Phase 4 deltas are against `-O3`, and Phase 6 deltas against `-O3 -march=native`. With one Phase 4 accept, Phase 5
had nothing to combine and ran no trials. The PGO near-miss list was empty, so only plain PGO was tried.

## Observations

- **`-march=native`'s accept is narrow but clean**: its CI [42.107, 42.238] is clear of the baseline's
  [41.451, 41.914], and all six `-O3` runs read 41.58-41.82, under every `-march=native` rep (42.14-42.19).
- **Ten of fourteen candidates were excluded on shape**, non-PIE and `-fno-stack-protector` among them. Both are
  tagged frontend-bound only, and neither has been measured on zstd on either host. On the memory-bound
  benchmarks under the gate here, non-PIE gained +2.46% on stockfish and +1.71% on gcc.
- **The bandwidth gate waited before 17 of 27 timed runs**, the most of any intrate mine here (sealcrypto 11 of
  34). Every probe that waited then read 97.7-106.2 GB/s, no rep was slow, and no rerun fired; it cost about
  8.5 minutes.
- **Every flagset's three reps were within 0.8% of each other**; the widest was `-flto` (41.39-41.72).

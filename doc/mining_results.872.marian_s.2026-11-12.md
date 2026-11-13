# `cfm mine` results: 872.marian_s on `chicago`, 2026-11-12

This is the twelfth fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`872.marian_s` mine on any host. `872.marian_s` is the SPECspeed version of Marian, a C++ neural machine-translation
decoder, parallelized with OpenMP; its rate counterpart was
[mined here on 2026-11-08](mining_results.772.marian_r.2026-11-08.md) (+72.43%, `-O3 -march=native`). Its corpus shape
is memory-bound at 86.9%.

## Headline result

**`-O3 -march=native`, +56.38% over plain `-O3`** (ratio 4.4193 → 6.9108), the largest fpspeed gain on this host.

- **`-march=native` is almost the whole win**, as on marian_r (+72.43%). Its CI [6.828, 6.994] is far clear of
  baseline's [4.369, 4.469]. It was fast-tracked on the memory-bound prior (accepted 16 of 23).
- **`-mprefer-vector-width=256` cost 15.07%** on top of `-march=native` (5.869), against -6.30% on marian_r. Marian's
  matrix kernels depend on 512-bit AVX-512 vectors more as a speed benchmark than as a rate one.
- **`-fprefetch-loop-arrays` probably adds about 1.8% on top, but was rejected twice on CI overlap**, the same as on
  marian_r. The greedy step read +1.63% (CI low 6.979 against `-march=native`'s high 6.994) and the pair tournament
  built the same code (`56f8b760`) and read 7.044 (CI low 6.985). Pooled, those six runs average 7.033, +1.77% over
  `-march=native`, with a CI of [7.010, 7.056] that's clear of it.
- **Alone on `-O3`, `-fprefetch-loop-arrays` gained +4.78% and `-fno-math-errno` +3.24%**, both accepted. On marian_r
  prefetching gained +15.2%. `-fno-math-errno` was a candidate only because PR #71 exempts it from the shape filter;
  on top of `-march=native` it read +0.28%.
- **PGO lost 1.0%**, and each PGO trial took about 1h42m. `-fgraphite-identity` lost 2.64% (on marian_r it gained
  +10.5% alone). `-flto` screened at -15.0% and was pruned.
- **The shape filter dropped 10 candidates** on the 86.9% memory-bound read, `-Ofast` and `-ffast-math` among them.
  niwot's `--no-shape-filter` re-mine of marian_r found that none of those adds anything on top of `-march=native`.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 872.marian_s` (uncapped, defaults) |
| Code | `main` at `1cd3a35` (no code changes since `c933ee2`, PR #71) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 27 |
| Started / finished | 2026-11-12T16:20:56Z / 2026-11-13T01:31:38Z (9h11m) |
| Final status | `converged` |
| Trials | 43 (1210-1252), none skipped, no reruns |
| Candidates screened / confirmed | 4 / 3 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 10 (`-flto` and `-fno-math-errno` kept, exempt) |
| Pruned in screening | `-flto` (3.760, -15.0%) |
| Fast-tracked (M4) | `-march=native` (accepted 16 of 23, mean +14.45%) |
| Accepted in Phase 4 | `-march=native` +56.38%, `-fprefetch-loop-arrays` +4.78%, `-fno-math-errno` +3.24% |
| Winning flags | `["-O3", "-march=native"]`, +56.38% |
| Guards | bandwidth gate waited 30 s before 33 of 43 timed runs; no reruns; baseline recheck not flagged (-0.58%) |
| Power | package power median 84.78-84.92 W on every trial; CPU temperature 81.2-84.8°C |

A plain trial took about 6.5 minutes, a `-march=native` trial about 5, and a PGO trial about 1h42m: the three PGO
trials took 5.1 of the run's 9.2 hours. Every timed run's `.rsf` reads `valid: S` for marian.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 86.9%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 1210 | warm-up | 4.42157 |
| 1211 | warm-up | 4.43057 |
| 1212 | calibration | 4.43646 |
| 1213 | calibration | 4.39717 |
| 1214 | calibration | 4.42425 |
| 1231 | recheck | 4.39346 (-0.58%) |

The calibration mean is 4.419293, with a 95% CI of [4.36934, 4.46925] (±1.13%). Warm-up settled after the minimum
two reps (820 s). Every `-O3` build had the same code fingerprint (`30a0fb47`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 1215-1218 | screening | 4 candidates | 3.760-4.629 | | `-flto` pruned (-15.0%) |
| 1219-1221 | confirmation | `-fprefetch-loop-arrays` | 4.6307 | +4.78% | **accept** |
| 1222-1224 | confirmation | `-fgraphite-identity` | 4.3025 | -2.64% | reject (CI clear below) |
| 1225-1227 | confirmation | `-fno-math-errno` | 4.5626 | +3.24% | **accept** |
| 1228-1230 | confirmation (fast-tracked) | `-march=native` | 6.9108 | +56.38% | **accept** (the greedy start) |
| 1232-1234 | combination (greedy) | `-march=native -fprefetch-loop-arrays` | 7.0231 | +1.63% | reject (CI overlap) |
| 1235-1237 | combination (greedy) | `-march=native -fno-math-errno` | 6.9298 | +0.28% | reject |
| 1238-1240 | combination (pair) | `-fprefetch-loop-arrays -march=native` | 7.0437 | +59.38% | accept, didn't replace the winner (CI overlap) |
| 1241-1243 | combination (pair) | `-fno-math-errno -march=native` | 6.9165 | +56.51% | accept, didn't replace the winner |
| 1244-1246 | combination (pair) | `-fno-math-errno -fprefetch-loop-arrays` | 4.6276 | +4.71% | accept, didn't replace the winner |
| 1247-1249 | PGO | `-march=native -fprofile-use` | 6.842 | -1.00% | reject |
| 1250-1252 | vector width | `-march=native -mprefer-vector-width=256` | 5.869 | -15.07% | reject |

Greedy-step deltas are against `-O3 -march=native`, pair deltas against `-O3`, and Phase 6 deltas against
`-O3 -march=native`. The microarch multiplier was skipped because the winning set already had `-march=native`. No
Phase 4 reject was CI-clear above baseline, so PGO had no near-miss variant.

## Observations

- **`-fprefetch-loop-arrays` on top of `-march=native` has now been rejected on CI overlap in both marian mines
  here**, at +1.68% on marian_r and +1.63% on marian_s, with the pair tournament measuring the same code higher each
  time. Three reps a side can't separate a 1.7% step from `-march=native`'s own ±1.2% CI. Open item 17 proposes
  measuring it directly.
- **The PGO builds had three different code fingerprints** (as on marian_r) and read 6.80-6.89, all below every
  `-march=native` rep. At 1h42m a trial, PGO is the most expensive step mined on this host so far.
- **CPU temperature ran 81-85°C on every trial, `-O3` included**, about 5°C cooler than the other fpspeed mines
  here at the same 85 W. Nothing in the run says why.
- **niwot hasn't mined marian_s yet.**

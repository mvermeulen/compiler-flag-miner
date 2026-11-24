# `cfm mine` results: 801.xz_s on `chicago`, 2026-11-24

This is the first intspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)). `801.xz_s` is
the xz/LZMA compressor (C, pthreads; `@benchsets` `cxxthreads intspeed pthread specspeed`), run unpinned as one copy
with `threads = 32`. It has no intrate counterpart. niwot's mine accepted nothing: PGO came closest at +0.70% with
CIs overlapping ([write-up](mining_results.801.xz_s.2026-10-26.md)). Its corpus shape is memory-bound at 56.3%, just
over the 55% gate, so the shape filter excluded ten candidates.

## Headline result

**`-O3 -fprofile-use`, +1.10% over plain `-O3`** (ratio 1.8575 → 1.8779).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 1.8575 | — |
| `-O3 -fprofile-use` | 1.8779 | +1.10% |

- **PGO cleared the 1% bar by 0.10 points**, CI-clear of baseline ([1.8728, 1.8829] against [1.8528, 1.8621]).
  niwot's +0.70% was rejected on CI overlap with a noisier baseline (its reps spread about 2%; here every flagset's
  reps were within 0.6%).
- **`-march=znver5` on top of PGO read +0.82%**, CI-clear of PGO but under the 1% bar, so it was rejected. The set
  `-O3 -fprofile-use -march=znver5` read 1.8932, +1.92% over `-O3`, the highest mean of the run. `-march=native`
  alone read -0.20% and `-mtune=znver5` on top of PGO -0.62%.
- **Every Phase 4 candidate was flat**: `-fprefetch-loop-arrays` +0.01%, `-flto` +0.02%, `-fgraphite-identity`
  +0.13%, `-march=native` -0.20%, all CI-overlapping. `-fno-math-errno` built the same code as `-O3` and was
  skipped.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance`, kernel 7.0.0-43 |
| Command | `python3 -m cfm.cli mine 801.xz_s` (uncapped, defaults; started by `~/cfm-logs/queue/run_queue.sh`) |
| Code | `main` at `c1abe54` (no code changes since `3b15833`, PR #72) |
| SPEC config | `gcc_O3.cfg`, `threads = 32` |
| Thread placement | pthread, not pinned |
| Experiment id | 43 |
| Started / finished | 2026-11-24T01:54:24Z / 2026-11-24T04:59:19Z (3h05m) |
| Final status | `converged` |
| Trials | 31 (2298-2328), one skipped as unchanged code (`-fno-math-errno`), no reruns |
| Candidates screened / confirmed | 4 / 3 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | `-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops` (frontend-bound-tagged), `-funroll-loops`, `-Ofast`, `-ffast-math`, `-fipa-pta` (memory-bound 56.3%, over the gate); `-mprefer-vector-width=256` deferred to Phase 6 |
| Fast-tracked (M4) | `-march=native` (accepted 20 of 31, mean +14.38%) |
| Accepted | PGO +1.10% (nothing in Phase 4) |
| Winning flags | `["-O3", "-fprofile-use"]`, +1.10% |
| Guards | throttle stop not triggered; bandwidth gate waited 30 s before 23 of 30 timed runs; no reruns; baseline recheck not flagged (+0.10%) |
| Power | package power median 84.99 W on every trial; CPU temperature 90.5-95.0°C |

A trial took about 6 minutes, a PGO trial about 6.5.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 56.3%, `vectorization_density=moderate`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 2298 | warm-up | 1.8587 |
| 2299 | warm-up | 1.8578 |
| 2300 | calibration | 1.8555 |
| 2301 | calibration | 1.8592 |
| 2302 | calibration | 1.8577 |
| 2319 | recheck | 1.8594 (+0.10%) |

The calibration mean is 1.8575, with a 95% CI of [1.8528, 1.8621] (±0.25%). Warm-up settled after the minimum two
reps (725 s). Every `-O3` build had the same code fingerprint (`f79b62f1`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 2303-2306 | screening | 4 candidates | 1.8541-1.8613 | | 3 survived; `-fno-math-errno` skipped (same code as `-O3`) |
| 2307-2309 | confirmation | `-fprefetch-loop-arrays` | 1.8576 | +0.01% | reject |
| 2310-2312 | confirmation | `-fgraphite-identity` | 1.8599 | +0.13% | reject |
| 2313-2315 | confirmation | `-flto` | 1.8579 | +0.02% | reject |
| 2316-2318 | confirmation (fast-tracked) | `-march=native` | 1.8538 | -0.20% | reject |
| 2319 | baseline recheck | `-O3` | 1.8594 | +0.10% | not flagged |
| 2320-2322 | PGO | `-O3 -fprofile-use` | 1.8779 | +1.10% | **accept** |
| 2323-2325 | microarch | winner `+ -march=znver5` | 1.8932 | +0.82% | reject (CI-clear, under the 1% bar) |
| 2326-2328 | microarch | winner `+ -mtune=znver5` | 1.8662 | -0.62% | reject |

Phase 4 and PGO deltas are against `-O3`, and microarch deltas against `-O3 -fprofile-use`. With nothing accepted
in Phase 4, Phase 5 had nothing to combine and PGO was layered on plain `-O3`. The PGO near-miss list was empty. The
vector-width multiplier was skipped because the winning set has no `-march=`.

## Observations

- **`-march=znver5` may be worth about +1.9% with PGO.** It was CI-clear of PGO by a wide margin (its low end,
  1.8891, sits above PGO's high end, 1.8829) and failed only the 1% bar. Layered rejects aren't carried forward, so
  the reported winner is PGO alone. Odd next to `-march=native`'s -0.20% alone; the run doesn't measure
  `-march=znver5` without PGO.
- **PGO builds differed between reps**, as expected on SPEC (CLAUDE.md, 2026-10-28): the first PGO rep built
  `bd3e31b7` and the other two `6c68cf80`, and the three `-mtune=znver5` reps three different binaries. The reps
  still agreed (PGO 1.8766-1.8802), so the verdicts don't hinge on one build.
- **The bandwidth gate waited before 23 of 30 timed runs**, more than on any intrate mine here (zstd 17 of 27).
  No rep was slow and no rerun fired; it cost about 11.5 minutes.
- **Package power read 84.99 W on every trial**, the same as the 32-copy intrate mines. The pinned `800.pot3d_s`
  run read 24.6 W (CLAUDE.md, 2026-11-09), so this is consistent with the unpinned threads loading the whole chip.

# `cfm mine` results: 772.marian_r on `chicago`, 2026-11-08

This is the twelfth and last fprate benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the
first `772.marian_r` mine on any host. `772.marian_r` is the Marian neural machine-translation decoder (C++),
translating with a transformer model on the CPU. Its corpus shape is memory-bound at 63.1%.

## Headline result

**`-O3 -march=native`, +72.43% over plain `-O3`** (ratio 121.729 → 209.894). It's the second-largest gain on this
host, after femflow's +132%.

- **`-march=native` gave +72.43%**, with all three reps (208.79-210.98) far above every `-O3` rep (121.06-122.79). It
  was fast-tracked on the memory-bound prior (accepted 8 of 10).
- **Like femflow, this is AVX-512 autovectorization.** Marian's hand-written AVX/AVX-512 paths in
  `tensors/cpu/tensor_operators.cpp` are compiled out under `#ifndef SPEC`, so its matrix products and element-wise
  kernels are plain loops for GCC to vectorize, and `-march=native` lets it use 512-bit vectors and FMA.
  `-mprefer-vector-width=256` on top cost **-6.30%** (196.661).
- **`-fprefetch-loop-arrays` (+15.23%) and `-fgraphite-identity` (+10.50%) were both accepted alone**, the first
  accepts for either flag on this host. Both add nothing on top of `-march=native`:
  - The greedy step `-march=native -fprefetch-loop-arrays` read +1.68% (213.414), but its CI [210.21, 216.62]
    overlaps `-march=native`'s [207.18, 212.61], so it was rejected. The pair with the same code (`f577b531`) read
    +75.77% against `-O3` but with an even wider CI, so it didn't replace the winner.
  - `-march=native -fgraphite-identity` read -1.49% and was rejected.
  - Together without `-march=native` they read +6.52%, less than prefetching alone.

  Both look like ways to recover some of the scalar build's memory stalls, and the vectorized build doesn't have
  those to recover.
- **PGO lost 4.06%**, and each PGO trial took about an hour (the training run is long). Its three builds had
  three different code fingerprints, the first time on this host that PGO builds didn't reproduce.
- **`-flto` read +1.29% and was rejected on CI overlap** with a baseline CI of ±1.23%.
- **The shape filter dropped 11 candidates** on the 63.1% memory-bound read, among them `-Ofast`, `-ffast-math` and
  `-funroll-loops`. A neural-network decoder is the kind of code fast-math can help, so this is another case for a
  `--no-shape-filter` re-mine.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 772.marian_r` (uncapped, defaults) |
| Code | `main` at `60baf31` (no code changes since `f31ba64`, only docs) |
| Experiment id | 14 |
| Started / finished | 2026-11-08T07:04:34Z / 2026-11-08T14:49:21Z (7h45m) |
| Final status | `converged` |
| Trials | 42 (619-660), no reruns, none skipped |
| Candidates screened / confirmed | 3 / 3 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 11 |
| Fast-tracked (M4) | `-march=native` (accepted 8 of 10, mean +18.99%) |
| Winning flags | `["-O3", "-march=native"]`, +72.43% |
| Guards | bandwidth gate waited 30 s before 16 of 42 runs; no reruns; baseline recheck not flagged (-0.38%) |
| Power | package power median 84.96-85.03 W on every trial; CPU temperature 91.4-96.0°C |

A `-O3` trial took about 8 minutes, a `-march=native` trial about 6, and a PGO trial about 64.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 63.1%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 619 | warm-up | 122.788 |
| 620 | warm-up | 121.628 |
| 621 | calibration | 121.919 |
| 622 | calibration | 122.212 |
| 623 | calibration | 121.056 |
| 639 | recheck | 121.268 (-0.38%) |

The calibration mean is 121.729, with a 95% CI of [120.236, 123.222] (±1.23%), the widest on this host. Warm-up
settled after the minimum two reps (1,016 s). Every `-O3` build had the same code fingerprint (`9cd2c3c3`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 624-626 | screening | 3 candidates | 123.59-141.18 | | all survived |
| 627-629 | confirmation | `-fprefetch-loop-arrays` | 140.267 | +15.23% | **accept** |
| 630-632 | confirmation | `-fgraphite-identity` | 134.512 | +10.50% | **accept** |
| 633-635 | confirmation | `-flto` | 123.298 | +1.29% | reject (CI overlap) |
| 636-638 | confirmation (fast-tracked) | `-march=native` | 209.894 | +72.43% | **accept** (also the greedy start) |
| 640-642 | combination (greedy) | `-march=native -fprefetch-loop-arrays` | 213.414 | +1.68% | reject (CI overlap) |
| 643-645 | combination (greedy) | `-march=native -fgraphite-identity` | 206.776 | -1.49% | reject |
| 646-648 | combination (pair) | `-fprefetch-loop-arrays -march=native` | 213.958 | +75.77% | accept, didn't replace the winner (CI overlap) |
| 649-651 | combination (pair) | `-fgraphite-identity -fprefetch-loop-arrays` | 129.667 | +6.52% | accept, didn't replace the winner |
| 652-654 | combination (pair) | `-fgraphite-identity -march=native` | 208.696 | +71.44% | accept, didn't replace the winner |
| 655-657 | PGO | `-march=native -fprofile-use` | 201.367 | -4.06% | reject |
| 658-660 | vector width | `-march=native -mprefer-vector-width=256` | 196.661 | -6.30% | reject |

The greedy-step deltas are against the step before, the pair deltas against `-O3`, and the Phase 6 deltas against
`-O3 -march=native`. The greedy walk started from the Phase 4 `-march=native` result rather than re-measuring it. The
microarch multiplier was skipped because the winning set already had `-march=native`.

## Observations

- **fprate on this host is now fully mined**, and the two deal.II/Marian-style codes dominate it: femflow (2.32×) and
  marian (1.72×) together lift the suite geomean from about +9.6% to +23.1%. In both, SPEC's portability settings
  compile out hand-written SIMD, which leaves the vector width to the compiler and makes `-march=native` worth far more
  than on a typical code.
- **The `-march=native` rejections (gmsh, flightdm, nest) were all on codes with little vector work.** The flag's
  record here is now 9 of 12, with every reject under ±1%.
- **The pair tournament did nothing here.** `-march=native -fprefetch-loop-arrays` measured 1.7-1.9% above
  `-march=native` twice (greedy step and pair), but each time with a CI too wide to separate it. Six reps of the same
  code averaging +1.8% is the best case yet for open item 5 (more calibration reps on wide-CI benchmarks).
- **Package power read 85.0 W on every trial**, for the twelfth mine in a row.

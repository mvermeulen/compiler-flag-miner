# `cfm mine` results: 737.gmsh_r on `chicago`, 2026-11-07

This is the eighth benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first `737.gmsh_r`
mine on any host. `737.gmsh_r` is Gmsh, a C++ finite-element mesh generator: geometry kernels, Delaunay
refinement and pointer-heavy mesh data structures. Its corpus shape is memory-bound at 42.7%, under the shape
filter's 55% confidence margin, so no candidate was excluded on shape.

## Headline result

**`-O3 -flto`, +2.40% over plain `-O3`** (ratio 59.371 → 60.796).

- **`-march=native` was rejected, -0.42%. It's the first `-march=native` reject on this host** after 7 accepts
  (+3.5% to +20.5%). It was fast-tracked on that prior, built different code from `-O3` (`52569fe7` against
  `e3e8440c`), and all three reps (59.06-59.24) sat in the low half of the `-O3` range (59.22-59.62).
- **`-flto` gave +2.15% in Phase 4 and +2.40% in Phase 5**, the largest LTO gain on this host so far (ocio's was
  +1.17% alone). All six of its reps (60.49-60.90) beat every `-O3` rep. Both phases built the same code
  (`af7dfc6a`).
- **PGO read +0.68% on top of `-flto` and was rejected on the 1% bar.** Its CI [61.06, 61.36] is clear of the
  winner's [60.56, 61.03], so the gain is real but small. All three PGO reps built the same code (`be3774a9`).
- **The microarch multiplier ran for the first time on this host**, since the winning set had no `-march=`:
  `-march=znver5` read -0.23% and `-mtune=znver5` +0.06%, both rejected. That agrees with `-march=native`'s reject.
  The vector-width multiplier was skipped (no `-march=` in the winner).
- **Every other candidate was within ±0.8% of `-O3`.** `-fipa-pta` (-0.78%) was the only CI-clear loss. The
  security-hardening flags all read slightly positive (`-fno-stack-protector` +0.76%, `-fno-pie -no-pie` +0.59%,
  `-fcf-protection=none` +0.47%, `-U_FORTIFY_SOURCE` +0.26%), all inside the baseline CI.
- **`-ffast-math` and `-fno-math-errno` built code identical to `-O3`**, so their timed runs were skipped. The SPEC
  config gives gmsh `PORTABILITY = -fno-fast-math`, which lands after `OPTIMIZE` and cancels both (niwot's
  [flightdm write-up](mining_results.748.flightdm_r.2026-11-05.md) found the same). `-Ofast` did change the code
  (`3439d7b7`), since its non-fast-math parts survive, and read +0.14%.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 737.gmsh_r` (uncapped, defaults) |
| Code | `main` at `d8b3270` (no code changes since `f31ba64`, only docs) |
| Experiment id | 10 |
| Started / finished | 2026-11-07T04:03:46Z / 2026-11-07T10:39:17Z (6h36m) |
| Final status | `converged` |
| Trials | 71 (365-435), 2 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 14 / 11 (plus `-march=native` fast-tracked, rejected) |
| Excluded on shape (Phase 2) | none (memory-bound 42.7%, under the 55% margin) |
| Fast-tracked (M4) | `-march=native` (accepted 7 of 7, mean +8.49%) |
| Skipped as unchanged code | `-ffast-math`, `-fno-math-errno` (same code as `-O3`) |
| Winning flags | `["-O3", "-flto"]`, +2.40% |
| Guards | bandwidth gate waited three times (30 s, trials 365, 424 and 426); no reruns; baseline recheck not flagged (+0.79%) |
| Power | package power median 84.98-85.00 W on every trial; CPU temperature 94.5-98.1°C |

Each trial took about 5.5 minutes, and each PGO trial about 8.5.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 42.7%, `vectorization_density=high`,
`allocation_pressure=high`.

| Trial | Role | Ratio |
|---|---|---|
| 365 | warm-up | 59.346 |
| 366 | warm-up | 59.400 |
| 367 | calibration | 59.619 |
| 368 | calibration | 59.219 |
| 369 | calibration | 59.275 |
| 423 | recheck | 59.840 (+0.79%) |

The calibration mean is 59.371, with a 95% CI of [58.833, 59.909] (±0.91%), the widest baseline CI on this host so
far. Rep 367 read 0.6% above its siblings. Warm-up settled after the minimum two reps (674 s). Every `-O3` build
had the same code fingerprint (`e3e8440c`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 370-383 | screening | 14 candidates | 59.04-60.77 | | all survived (2 skipped as unchanged code) |
| 384-386 | confirmation | `-fprefetch-loop-arrays` | 59.548 | +0.30% | reject |
| 387-389 | confirmation | `-fgraphite-identity` | 59.516 | +0.24% | reject |
| 390-392 | confirmation | `-flto` | 60.647 | +2.15% | **accept** |
| 393-395 | confirmation | `-fno-pie -no-pie` | 59.721 | +0.59% | reject |
| 396-398 | confirmation | `-fno-stack-protector` | 59.822 | +0.76% | reject |
| 399-401 | confirmation | `-fcf-protection=none` | 59.649 | +0.47% | reject |
| 402-404 | confirmation | `-U_FORTIFY_SOURCE` | 59.524 | +0.26% | reject |
| 405-407 | confirmation | `-funroll-loops` | 59.106 | -0.45% | reject |
| 408-410 | confirmation | `-Ofast` | 59.453 | +0.14% | reject |
| 411-413 | confirmation | `-fno-ipa-cp-clone` | 59.443 | +0.12% | reject |
| 414-416 | confirmation | `-fno-unswitch-loops` | 59.603 | +0.39% | reject |
| 417-419 | confirmation | `-fipa-pta` | 58.908 | -0.78% | reject (CI clear below baseline) |
| 420-422 | confirmation (fast-tracked) | `-march=native` | 59.124 | -0.42% | reject |
| 424-426 | combination (greedy) | `-flto` | 60.796 | +2.40% | **accept** |
| 427-429 | PGO | `-flto -fprofile-use` | 61.211 | +0.68% | reject (CI-clear, under the 1% bar) |
| 430-432 | microarch | `-flto -march=znver5` | 60.655 | -0.23% | reject |
| 433-435 | microarch | `-flto -mtune=znver5` | 60.830 | +0.06% | reject |

Phase 6 deltas are against `-O3 -flto`. With only one accepted flag there was nothing to pair, so the pair
tournament ran no trials.

## Observations

- **`-march=native`'s record here is now 7 of 8.** On every earlier fprate benchmark the vectorizer had dense
  floating-point loops to widen. A mesh generator spends its time chasing pointers through adjacency structures,
  where AVX-512 has little to work on. The `-march=znver5` multiplier, an independent measurement of nearly the
  same target, also read flat.
- **The fast-track cost nothing here**: the prior sent `-march=native` straight to confirmation, and confirmation
  rejected it on its own merits. The cluster's prior mean drops accordingly.
- **LTO is the only win, as on niwot's frontend-bound intrate codes.** gmsh is a large C++ code base with many
  small functions across translation units, the shape where cross-module inlining pays.
- **PGO's +0.68% is a measured gain left on the table by the 1% bar**, like ocio's vector-width read. A combined
  `-flto -fprofile-use` would be about +3.1% over `-O3`.
- **The baseline CI (±0.91%) was the widest yet** and kept the security flags' +0.5-0.8% reads inside it. Each
  of those is under the 1% bar anyway.
- **Package power read 85.0 W on every trial**, for the eighth mine in a row. The CPU reached 98.1°C, a new high
  for this host.

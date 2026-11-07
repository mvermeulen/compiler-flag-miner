# `cfm mine` results: 731.astcenc_r on `chicago`, 2026-11-06

This is the sixth benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first one here that
`niwot` has also mined ([2026-11-04](mining_results.731.astcenc_r.2026-11-04.md)). `731.astcenc_r` is ARM's ASTC
texture compressor, a SIMD-heavy floating-point C++ code. It is also the first benchmark here outside the
memory-bound cluster: its corpus shape reads frontend-bound at 44.3%.

## Headline result

**`-O3 -march=native -Ofast`, +29.49% over plain `-O3`** (ratio 77.592 → 100.477). This is the same winner niwot
found, at almost the same gain (+29.64%).

| Step | Mean | Gain on the step before |
|---|---|---|
| `-O3` | 77.592 | — |
| `-O3 -march=native` | 93.372 | +20.34% |
| `+ -Ofast` | 100.477 | +7.61% |

- **`-march=native` gave +20.42% alone** in Phase 4. This was the first time it was screened on this host rather
  than fast-tracked: there are no priors yet in the frontend-bound cluster here. Its screening rep read +20.25%.
- **`-Ofast` (+5.24%) and `-ffast-math` (+5.22%) were both accepted alone**, and both passed SPEC validation.
  - On top of `-march=native`, `-Ofast` gained +7.61%, more than it gave alone. Niwot measured the identical
    step, +7.61%.
  - `-ffast-math` on top of `-march=native -Ofast` built the same code as `-march=native -Ofast` (`-Ofast` already
    includes it), so its timed run was skipped.
- **The pair tournament didn't change the winner.** The pair `-ffast-math -march=native` read 100.592 (+29.64%), but
  it built different code from the winner (`3a3b0b79` against `095e23b9`), and it didn't beat the greedy winner
  by enough to replace it.
- **PGO lost 1.51%** on top of `-march=native -Ofast`. Niwot's PGO loss was 2.45%.
  - The near-miss variant added `-fno-math-errno` and read -1.45%. It built the same code (`d39e6069`), since
    `-Ofast` already implies `-fno-math-errno`.
  - `-mprefer-vector-width=256` was flat (-0.23%).
- **Every other candidate was within ±0.4% of `-O3`, except `-funroll-loops` at -1.09%.** The losing candidates
  included `-flto` (-0.30%), `-fno-pie -no-pie` (+0.30%) and `-fno-math-errno` (+0.49%, which was CI-clear of
  baseline but under the 1% bar).
- **No candidate was excluded on shape.** The frontend-bound read of 44.3% is under the 55% confidence margin, so
  all 15 candidates were screened.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 731.astcenc_r` (uncapped, defaults) |
| Code | `main` at `df1c29d` (no code changes since `f31ba64`, only docs) |
| Experiment id | 8 |
| Started / finished | 2026-11-06T15:38:06Z / 2026-11-07T00:21:21Z (8h43m) |
| Final status | `converged` |
| Trials | 91 (238-328), 1 skipped as unchanged code, no reruns |
| Candidates screened / confirmed | 15 / 3 (`-march=native`, `-Ofast`, `-ffast-math`) |
| Excluded on shape (Phase 2) | none (frontend-bound 44.3%, under the 55% margin) |
| Fast-tracked (M4) | none (no frontend-bound priors on this host yet) |
| Skipped as unchanged code | `-march=native -Ofast -ffast-math` (same code as `-march=native -Ofast`) |
| Winning flags | `["-O3", "-march=native", "-Ofast"]`, +29.49% |
| Guards | bandwidth gate waited twice (30 s, trials 238 and 317); no reruns; baseline recheck not flagged (+0.07%) |
| Power | package power median 84.99 W on every trial; CPU temperature 91.5-97.4°C |

Each trial took about 6 minutes.

## Baseline

The shape comes from the reference-matrix corpus (`amd-370-64gb`): frontend-bound 44.3%,
`vectorization_density=high`, `allocation_pressure=low`.

| Trial | Role | Ratio |
|---|---|---|
| 238 | warm-up | 77.536 |
| 239 | warm-up | 77.462 |
| 240 | calibration | 77.531 |
| 241 | calibration | 77.595 |
| 242 | calibration | 77.651 |
| 303 | recheck | 77.650 (+0.07%) |

The calibration mean is 77.592, with a 95% CI of [77.442, 77.743] (±0.19%). Warm-up settled after the minimum two
reps (758 s). Every `-O3` build had the same code fingerprint (`f98bd13f`).

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 243-257 | screening | 15 candidates | 76.73-93.38 | | all survived |
| 258-260 | confirmation | `-flto` | 77.362 | -0.30% | reject |
| 261-263 | confirmation | `-fno-pie -no-pie` | 77.824 | +0.30% | reject |
| 264-266 | confirmation | `-fno-stack-protector` | 77.282 | -0.40% | reject |
| 267-269 | confirmation | `-fcf-protection=none` | 77.608 | +0.02% | reject |
| 270-272 | confirmation | `-U_FORTIFY_SOURCE` | 77.581 | -0.01% | reject |
| 273-275 | confirmation | `-fno-ipa-cp-clone` | 77.580 | -0.02% | reject |
| 276-278 | confirmation | `-fno-unswitch-loops` | 77.511 | -0.11% | reject |
| 279-281 | confirmation | `-funroll-loops` | 76.743 | -1.09% | reject (CI clear below baseline) |
| 282-284 | confirmation | `-fprefetch-loop-arrays` | 77.377 | -0.28% | reject |
| 285-287 | confirmation | `-march=native` | 93.435 | +20.42% | **accept** |
| 288-290 | confirmation | `-Ofast` | 81.660 | +5.24% | **accept** |
| 291-293 | confirmation | `-ffast-math` | 81.642 | +5.22% | **accept** |
| 294-296 | confirmation | `-fno-math-errno` | 77.972 | +0.49% | reject (CI-clear, under the 1% bar) |
| 297-299 | confirmation | `-fipa-pta` | 77.504 | -0.11% | reject |
| 300-302 | confirmation | `-fgraphite-identity` | 77.545 | -0.06% | reject |
| 304-306 | combination (greedy) | `-march=native` | 93.372 | +20.34% | **accept** |
| 307-309 | combination (greedy) | `-march=native -Ofast` | 100.477 | +7.61% | **accept** |
| 310 | combination (greedy) | `-march=native -Ofast -ffast-math` | | | skipped (same code) |
| 311-313 | combination (pair) | `-Ofast -march=native` | 100.492 | +29.51% | accept (same code as the greedy winner) |
| 314-316 | combination (pair) | `-Ofast -ffast-math` | 81.670 | +5.26% | accept (same code as `-Ofast`) |
| 317-319 | combination (pair) | `-ffast-math -march=native` | 100.592 | +29.64% | accept, didn't replace the greedy winner |
| 320-322 | PGO | `-march=native -Ofast -fprofile-use` | 98.963 | -1.51% | reject |
| 323-325 | PGO near-miss | `+ -fno-math-errno` | 99.017 | -1.45% | reject (same code as PGO) |
| 326-328 | vector width | `-march=native -Ofast -mprefer-vector-width=256` | 100.244 | -0.23% | reject |

The greedy-step deltas are measured against the step before. The pair deltas are measured against `-O3`, and the
Phase 6 deltas against `-O3 -march=native -Ofast`. The microarch multiplier was skipped because the winning set
already had `-march=native`.

## Observations

- **niwot and chicago built the same code.** Both run GCC 15.2.0, and `-march=native` resolves to `znver5` on both
  hosts, so equal fingerprints mean byte-identical code:
  - `-O3 -Ofast` built `eb9a7597` on both hosts.
  - `-O3 -march=native -Ofast` built `095e23b9` on both hosts.
  - PGO built `d39e6069` on both hosts, because both trained on the same SPEC train workload.

  Every relative gain also lines up between the hosts: +29.49% against +29.64% overall, +7.61% against +7.61% for
  `-Ofast` on top of `-march=native`, and a PGO loss on both. The hosts differ in core count, memory bandwidth and
  power limit (85 W against about 50 W), and those differences moved none of the gains. For a compute-heavy code,
  a flag result from one host carries over to the other.
- **Two pair trials re-measured code the mine had already timed**, as on niwot. `-Ofast -march=native` built the
  greedy winner's code, and `-Ofast -ffast-math` built `-Ofast`'s. The no-code-change guard only compares a build
  against the flagset it layers on, so it didn't skip them. Each re-measurement cost about 15 minutes here.
- **The baseline CI was ±0.19%**, and the bandwidth gate waited only twice. Package power read 85.0 W on every
  trial again (the sixth mine in a row), and the CPU reached 97.4°C, the highest on this host so far.
- **The fast-math flags paid here and not on the memory-bound benchmarks.** On lbm (with the shape filter off),
  `-Ofast` read +1.03% and was rejected. The shape filter excluded both fast-math flags on cactus, fotonik3d, roms
  and palm, so they were never measured there. Open item 6 (cactus with `--no-shape-filter`) would test whether
  that exclusion hides a win on a stencil code.

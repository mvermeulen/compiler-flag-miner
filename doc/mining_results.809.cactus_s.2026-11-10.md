# `cfm mine` results: 809.cactus_s on `chicago`, 2026-11-10

This is the third fpspeed benchmark mined on `chicago` (see [`host_chicago.md`](host_chicago.md)), and the first
`809.cactus_s` mine on any host. `809.cactus_s` is the SPECspeed version of Cactus/BSSN (numerical relativity),
parallelized with OpenMP; its rate counterpart was [mined here on 2026-11-05](mining_results.709.cactus_r.2026-11-05.md)
(+16.51% with `-march=native`). Its corpus shape is memory-bound at 70.9%.

## Headline result

**`-O3 -march=native`, +14.53% over plain `-O3`** (ratio 4.2796 → 4.9012), close to cactus_r's +16.51% on 32 copies.

- **`-march=native` gave +14.53%**, with all three reps (4.896-4.910) far above every `-O3` rep (4.271-4.282). It
  was fast-tracked on the memory-bound prior (accepted 11 of 13).
- **Nothing else moved.** `-flto` +0.00%, `-fprefetch-loop-arrays` +0.16% and `-fgraphite-identity` -0.04% were
  all rejected, as were PGO on top of `-march=native` (+0.23%) and `-mprefer-vector-width=256` (-0.09%).
- **The shape filter dropped 11 candidates** on the 70.9% memory-bound read, as on cactus_r (open item 6 covers a
  `--no-shape-filter` re-mine of that one).
- **Thread placement was right**: OpenMP placement across all 32 CPUs, package power 83.7-85.0 W.

## Run metadata

| | |
|---|---|
| Host | `chicago`: AMD Ryzen AI MAX+ 395 (16 Zen5 cores, 32 threads), 91 GB RAM, power profile `performance` |
| Command | `python3 -m cfm.cli mine 809.cactus_s` (uncapped, defaults) |
| Code | `main` at `fc725b9` (no code changes since `f31ba64`, only docs) |
| SPEC config | `threads = 32`; `-ftree-parallelize-loops=32` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 17 |
| Started / finished | 2026-11-09T23:24:28Z / 2026-11-10T01:36:31Z (2h12m) |
| Final status | `converged` |
| Trials | 27 (756-782), no reruns, none skipped |
| Candidates screened / confirmed | 3 / 3 (plus `-march=native` fast-tracked) |
| Excluded on shape (Phase 2) | 11 |
| Fast-tracked (M4) | `-march=native` (accepted 11 of 13, mean +21.09%) |
| Winning flags | `["-O3", "-march=native"]`, +14.53% |
| Guards | bandwidth gate waited 30 s before 13 of 27 runs; no reruns; baseline recheck not flagged (-0.18%) |
| Power | package power median 83.7-85.0 W on every trial; CPU temperature 86.2-90.1°C |

Each trial took about 5 minutes. Every trial's `.rsf` reads `valid: S` for cactus.

## Baseline

Shape from the reference-matrix corpus (`amd-370-64gb`): memory-bound 70.9%, `vectorization_density=high`,
`allocation_pressure=moderate`.

| Trial | Role | Ratio |
|---|---|---|
| 756 | warm-up | 4.27150 |
| 757 | warm-up | 4.28188 |
| 758 | calibration | 4.27908 |
| 759 | calibration | 4.27738 |
| 760 | calibration | 4.28229 |
| 776 | recheck | 4.27182 (-0.18%) |

The calibration mean is 4.279584, with a 95% CI of [4.27339, 4.28577] (±0.14%). Warm-up settled after the minimum
two reps (632 s). As on cactus_r, every build had a different code fingerprint, since Cactus compiles
`__DATE__`/`__TIME__` into the binary (CLAUDE.md's 2026-11-05 trap), so the no-code-change guard couldn't skip
anything.

## Trials

| Trials | Phase | Flags (on `-O3`) | Mean ratio | Delta | Verdict |
|---|---|---|---|---|---|
| 761-763 | screening | 3 candidates | 4.215-4.296 | | all survived |
| 764-766 | confirmation | `-fprefetch-loop-arrays` | 4.2864 | +0.16% | reject |
| 767-769 | confirmation | `-fgraphite-identity` | 4.2780 | -0.04% | reject |
| 770-772 | confirmation | `-flto` | 4.2796 | +0.00% | reject |
| 773-775 | confirmation (fast-tracked) | `-march=native` | 4.9012 | +14.53% | **accept** |
| 777-779 | PGO | `-march=native -fprofile-use` | 4.913 | +0.23% | reject |
| 780-782 | vector width | `-march=native -mprefer-vector-width=256` | 4.897 | -0.09% | reject |

Phase 6 deltas are against `-O3 -march=native`. With one accepted flag, Phase 5 had nothing to combine and ran no
trials. The microarch multiplier was skipped because the winning set already had `-march=native`.

## Observations

- **cactus behaves the same as a speed and a rate benchmark here**: `-march=native` is the only win (+14.5% on 32
  threads, +16.5% on 32 copies), and LTO and PGO add nothing.
- **The fastest mine on this host so far** (2h12m), with 5-minute trials and only 3 candidates surviving the
  shape filter.
- **niwot hasn't mined cactus_s yet.**

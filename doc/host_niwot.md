# Mining host: `niwot`

Index of `cfm mine` results for this host. Every `doc/mining_results.*.md` dated before 2026-10 came from a
different machine (a Strix Halo host, 91 GB RAM, 32 copies). Those results, and that host's `cfm.db`
knowledge priors, don't carry over here.

## Host

| | |
|---|---|
| CPU | AMD Ryzen AI 7 350 w/ Radeon 860M (family 1a model 60): 4 Zen5 + 4 Zen5c cores, 16 threads |
| Memory | 60 GB |
| Chassis | mini PC (DMI chassis type 35) |
| OS / compiler | Linux 7.0.0-38-generic, GCC 15.2.0 (Ubuntu 15.2.0-16ubuntu1) |
| SPEC | CPU2026 1.0.1 at `/home/mev/cpu2026` |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg` (label `gcc_O3`, `copies = 16`) |
| Power | amd-pstate `active`, governor `powersave`, EPP `balance_performance`, profile `balanced` |
| Microarch detection | `-march=znver5` / `-mtune=znver5` (needs PR #46, the hybrid Zen5/Zen5c fix) |
| Sensors | `k10temp` (CPU temp), `amdgpu` `power1_average` (package power, ~5 W idle, ~20 W under SPECrate load) |

## Running here

This SPEC install has no `gcc_O3.cfg` (cfm's default), so every invocation needs:

```
CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg .venv/bin/cfm mine <benchmark>
```

`cfm.db` on this host started empty on 2026-10-16.

## Results

| Date | Benchmark | Shape (source) | Winning flags | Gain vs `-O3` | Write-up |
|---|---|---|---|---|---|
| 2026-10-17 | `706.stockfish_r` | frontend-bound 40.6% (local) | `-O3 -march=native` | **+48.42%** | [link](mining_results.706.stockfish_r.2026-10-17.md) |
| 2026-10-17 | `714.cpython_r` | frontend-bound 63.9% (local) | `-O3 -flto -fprofile-use` | **+36.49%** | [link](mining_results.714.cpython_r.2026-10-17.md) |
| 2026-10-17 | `708.sqlite_r` | memory-bound 39.7% (corpus, low conf.) | `-O3 -fprefetch-loop-arrays -fprofile-use` (follow-up; the mine found `-O3 -fprefetch-loop-arrays`, +1.76%) | **+10.48%** | [link](mining_results.708.sqlite_r.2026-10-17.md) |
| 2026-10-17 | `729.abc_r` | memory-bound 38.2% (corpus, low conf.) | `-O3 -flto` (follow-up; the mine accepted nothing) | **+2.49%** | [link](mining_results.729.abc_r.2026-10-17.md) |
| 2026-10-18 | `707.ntest_r` | compute-bound 40.6% (corpus) | `-O3 -march=native` | **+14.27%** | [link](mining_results.707.ntest_r.2026-10-18.md) |
| 2026-10-19 | `750.sealcrypto_r` | compute-bound 55.1% (corpus) | `-O3 -march=native -fprofile-use` (follow-up; the mine found `-O3 -march=native`, +20.49%) | **+32.32%** | [link](mining_results.750.sealcrypto_r.2026-10-18.md) |
| 2026-10-19 | `710.omnetpp_r` | frontend-bound 45.9% (corpus) | `-O3 -flto -fprofile-use` | **+29.94%** | [link](mining_results.710.omnetpp_r.2026-10-19.md) |
| 2026-10-19 | `723.llvm_r` | frontend-bound 61.6% (corpus) | `-O3 -flto -fprofile-use` | **+24.83%** | [link](mining_results.723.llvm_r.2026-10-19.md) |
| 2026-10-20 | `727.cppcheck_r` | frontend-bound 71.0% (corpus) | `-O3 -flto -fprofile-use` (follow-up; the mine found `-O3 -fprofile-use`, +7.78%) | **+10.33%** | [link](mining_results.727.cppcheck_r.2026-10-19.md) |
| 2026-10-20 | `734.vpr_r` | memory-bound 45.4% (corpus) | `-O3 -march=native -flto -fprofile-use` (follow-up; the mine found `-O3 -march=native`, +1.31%) | **+15.77%** | [link](mining_results.734.vpr_r.2026-10-20.md) |
| 2026-10-20 | `721.gcc_r` | memory-bound 45.2% (corpus) | `-O3 -flto -fprofile-use` (follow-up; the mine accepted nothing) | **+10.71%** | [link](mining_results.721.gcc_r.2026-10-20.md) |
| 2026-10-21 | `735.gem5_r` | frontend-bound 60.3% (corpus) | `-O3 -flto` | **+11.01%** | [link](mining_results.735.gem5_r.2026-10-20.md) |
| 2026-10-22 | `753.ns3_r` | frontend-bound 60.7% (corpus) | `-O3 -flto -fprofile-use` | **+26.66%** | [link](mining_results.753.ns3_r.2026-10-21.md) |
| 2026-10-22 | `707.ntest_r` (re-mine) | compute-bound 40.6% (corpus, under the 55% gate) | `-O3 -march=native -flto -fprofile-use` | **+30.95%** | [link](mining_results.707.ntest_r.2026-10-22.md) |
| 2026-10-22 | `777.zstd_r` | memory-bound 64.0% (corpus) | `-O3 -march=native` (LTO/PGO follow-up: no gain) | **+1.72%** | [link](mining_results.777.zstd_r.2026-10-22.md) |
| 2026-10-24 | `834.vpr_s` | memory-bound 35.9% (corpus, under the 55% gate) | `-O3 -flto -fprofile-use -march=znver5` | **+25.17%** | [link](mining_results.834.vpr_s.2026-10-24.md) |
| 2026-10-24 | `853.ns3_s` | frontend-bound 39.4% (corpus, under the 55% gate) | `-O3 -flto -fprofile-use` | **+16.46%** | [link](mining_results.853.ns3_s.2026-10-24.md) |
| 2026-10-24 | `846.minizinc_s` | memory-bound 36.9% (corpus, under the 55% gate) | `-O3` (nothing accepted; `-flto` -1.66%, PGO -2.42%) | 0.0% | [link](mining_results.846.minizinc_s.2026-10-24.md) |
| 2026-10-25 | `835.gem5_s` | frontend-bound 40.4% (corpus, under the 55% gate) | `-O3 -flto` (PGO -8.63%) | **+5.35%** | [link](mining_results.835.gem5_s.2026-10-24.md) |
| 2026-10-25 | `829.abc_s` | memory-bound 72.9% (corpus) | `-O3 -flto` (follow-up #27; the mine accepted nothing, `-flto` excluded on shape) | **+2.32%** | [link](mining_results.829.abc_s.2026-10-25.md) |
| 2026-10-26 | `807.ntest_s` | memory-bound 41.9% (corpus, under the 55% gate) | `-O3 -march=native -flto -fprofile-use` | **+19.21%** | [link](mining_results.807.ntest_s.2026-10-26.md) |
| 2026-10-26 | `801.xz_s` | memory-bound 56.3% (corpus) | `-O3` (nothing accepted; `-flto` kept under #28, +0.08%; PGO +0.70%) | 0.0% | [link](mining_results.801.xz_s.2026-10-26.md) |
| 2026-10-27 | `817.flac_s` | memory-bound 65.1% (corpus) | `-O3 -fprefetch-loop-arrays -march=native -mprefer-vector-width=256` (`-march=native` alone +128.6%) | **+148.16%** | [link](mining_results.817.flac_s.2026-10-27.md) |
| 2026-10-28 | `823.llvm_s` | frontend-bound 58.5% (corpus) | `-O3 -flto -fprofile-use` (LTO +7.2%, PGO +11.9% on top) | **+19.96%** | [link](mining_results.823.llvm_s.2026-10-28.md) |
| 2026-10-29 | `827.cppcheck_s` | frontend-bound 74.1% (corpus) | `-O3 -fno-stack-protector -fprofile-use` (first PR #57 flag accepted; `-flto` -0.16%) | **+12.00%** | [link](mining_results.827.cppcheck_s.2026-10-29.md) |
| 2026-10-30 | `838.diamond_s` | compute-bound 45.4% (corpus, under the 55% gate) | `-O3 -flto -funroll-loops -march=znver5` (`-march=znver5` +30.7% in Phase 6; `-march=native` -6.2% alone in Phase 4) | **+34.49%** | [link](mining_results.838.diamond_s.2026-10-30.md) |
| 2026-11-01 | `821.gcc_s` | frontend-bound 59.7% (corpus) | `-O3 -fno-pie -no-pie -flto -fno-stack-protector -fprofile-use` (PGO +10.8%; first near-miss variant to win) | **+16.88%** | [link](mining_results.821.gcc_s.2026-10-31.md) |

## Summary by suite

Per benchmark: the latest converged `cfm mine` experiment on this host. *Base* is the plain `-O3` calibration
mean, *best* is the winning flag set's confirmed mean, and *gain* is best / base. Ratios come from
single-iteration `--action=validate` runs (rate: 16 copies; speed: 16 threads), not reportable SPEC scores.

Each suite has two geomean rows:

- **Suite geomean gain (progression)** is the geomean of the per-benchmark gain factors over **every**
  benchmark in the suite, counting each unmined benchmark as 1.00× (no gain yet). It only rises as
  mining finds wins, so it tracks overall progress, and it becomes the real suite-level gain once every
  row is mined. Base and best ratios don't exist for unmined rows, so this row shows the gain only.
- **Mined-only geomean** covers just the benchmarks mined so far: base and best ratio geomeans, plus their
  gain (geomean(best) / geomean(base) over the same rows). It shows the typical win per mined benchmark,
  not a suite score.

### intrate (14 of 14 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `706.stockfish_r` | 50.69 | 75.23 | `-O3 -march=native` | **+48.42%** | [2026-10-17](mining_results.706.stockfish_r.2026-10-17.md) |
| `707.ntest_r` | 28.36 | 37.13 | `-O3 -march=native -flto -fprofile-use` | **+30.95%** | [2026-10-22](mining_results.707.ntest_r.2026-10-22.md) |
| `708.sqlite_r` | 24.27 | 26.81 | `-O3 -fprefetch-loop-arrays -fprofile-use` ¹ | **+10.48%** | [2026-10-17](mining_results.708.sqlite_r.2026-10-17.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-21) |
| `710.omnetpp_r` | 24.06 | 31.27 | `-O3 -flto -fprofile-use` | **+29.94%** | [2026-10-19](mining_results.710.omnetpp_r.2026-10-19.md) |
| `714.cpython_r` | 37.53 | 51.23 | `-O3 -flto -fprofile-use` | **+36.49%** | [2026-10-17](mining_results.714.cpython_r.2026-10-17.md) |
| `721.gcc_r` | 22.99 | 25.45 | `-O3 -flto -fprofile-use` ¹ | **+10.71%** | [2026-10-20](mining_results.721.gcc_r.2026-10-20.md#follow-up-lto-and-pgo-2026-10-21) |
| `723.llvm_r` | 25.83 | 32.24 | `-O3 -flto -fprofile-use` | **+24.83%** | [2026-10-19](mining_results.723.llvm_r.2026-10-19.md) |
| `727.cppcheck_r` | 24.85 | 27.42 | `-O3 -flto -fprofile-use` ² | **+10.33%** | [2026-10-19](mining_results.727.cppcheck_r.2026-10-19.md#follow-up-lto-and-pgo-together-2026-10-22) |
| `729.abc_r` | 27.43 | 28.11 | `-O3 -flto` ¹ | **+2.49%** | [2026-10-17](mining_results.729.abc_r.2026-10-17.md#follow-up-lto-and-pgo-2026-10-21) |
| `734.vpr_r` | 21.20 | 24.55 | `-O3 -march=native -flto -fprofile-use` ¹ | **+15.77%** | [2026-10-20](mining_results.734.vpr_r.2026-10-20.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-20) |
| `735.gem5_r` | 34.06 | 37.81 | `-O3 -flto` | **+11.01%** | [2026-10-20](mining_results.735.gem5_r.2026-10-20.md) |
| `750.sealcrypto_r` | 27.91 | 36.93 | `-O3 -march=native -fprofile-use` ¹ | **+32.32%** | [2026-10-18](mining_results.750.sealcrypto_r.2026-10-18.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-23) |
| `753.ns3_r` | 36.48 | 46.21 | `-O3 -flto -fprofile-use` | **+26.66%** | [2026-10-21](mining_results.753.ns3_r.2026-10-21.md) |
| `777.zstd_r` | 17.15 | 17.44 | `-O3 -march=native` | **+1.72%** | [2026-10-22](mining_results.777.zstd_r.2026-10-22.md) |
| **Suite geomean gain (14, unmined = 1.00×)** | | | | **+20.13%** | |
| Mined-only geomean (14 of 14) | 27.75 | 33.34 | | +20.13% | |

¹ From an interleaved LTO/PGO follow-up (`cfm measure`, 3 rounds), not from the mine itself, whose shape filter
excluded both. The mines' own winners were `-O3 -fprefetch-loop-arrays` at 24.70 (sqlite, +1.76%),
`-O3` (abc and gcc, nothing accepted), `-O3 -march=native` at 21.48 (vpr, +1.31%) and `-O3 -march=native` at
33.63 (sealcrypto, +20.49%).

² From an interleaved follow-up (`cfm measure`, 3 rounds). The mine rejected `-flto` alone (+0.96%, under the 1% bar)
and ran PGO on plain `-O3` (26.79, +7.78%), so it never measured the two together.

### fprate (12 of 12 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `709.cactus_r` | 44.056 | 53.553 | `-O3 -march=native` (fast-tracked; nothing else within 1%; no throttle) | **+21.56%** | [2026-11-14](mining_results.709.cactus_r.2026-11-14.md) |
| `722.palm_r` | 35.326 | 38.672 | `-O3 -march=znver5 -mprefer-vector-width=256` (same code as `-march=native`, rejected in Phase 4; bimodal `-O3`) | **+9.47%** | [2026-11-09](mining_results.722.palm_r.2026-11-09.md) |
| `731.astcenc_r` | 36.591 | 47.438 | `-O3 -march=native -Ofast` | **+29.64%** | [2026-11-04](mining_results.731.astcenc_r.2026-11-04.md) |
| `736.ocio_r` | 38.325 | 48.370 | `-O3 -march=native -fno-math-errno` (`--no-shape-filter` re-mine; the shape-filtered mine got `-O3 -march=native`, +22.35%) | **+26.21%** | [2026-11-10](mining_results.736.ocio_r.2026-11-10.md), [2026-11-07](mining_results.736.ocio_r.2026-11-07b.md) |
| `737.gmsh_r` | 27.829 | 27.829 | `-O3` (`-flto` +1.69% accepted in Phase 4, rejected by the greedy re-measure, #39) | 0.0% | [2026-11-06](mining_results.737.gmsh_r.2026-11-06.md) |
| `748.flightdm_r` | 47.765 | 60.094 | `-O3 -flto -fprofile-use` | **+25.81%** | [2026-11-05](mining_results.748.flightdm_r.2026-11-05.md) |
| `749.fotonik3d_r` | 14.078 | 14.078 | `-O3` (the mine reported `-O3 -mtune=znver5` +9.92%, a throttle-level mismatch: `-O3` read 15.87 on the same 17 W level; recheck +12.76% flagged; `-march=native` rejected twice on CI overlap) | 0.0% | [2026-11-14](mining_results.749.fotonik3d_r.2026-11-14.md) |
| `765.roms_r` | 14.283 | 14.283 | `-O3` (nothing accepted; throttled, baseline CI ±18%; `-march=native` rejected twice on CI overlap, +7.19% on `chicago`) | 0.0% | [2026-11-15](mining_results.765.roms_r.2026-11-15.md) |
| `766.femflow_r` | 43.082 | 89.001 | `-O3 -march=native` (`-flto` +15% alone, nothing on top; PGO -27.18%; the `--no-shape-filter` re-mine picked the same, +108.68%, PGO -30.07% on the same binary) | **+106.58%** | [2026-11-09](mining_results.766.femflow_r.2026-11-09.md), [2026-11-14](mining_results.766.femflow_r.2026-11-14.md) |
| `767.nest_r` | 42.970 | 43.532 | `-O3 -march=native` (PGO -6.36%) | **+1.31%** | [2026-11-05](mining_results.767.nest_r.2026-11-05.md) |
| `772.marian_r` | 57.103 | 93.307 | `-O3 -march=native` (prefetch +19%, graphite +16% alone, nothing on top; the `--no-shape-filter` re-mine picked the same, +64.13%, fast-math -2.5% on top) | **+63.40%** | [2026-11-08](mining_results.772.marian_r.2026-11-08b.md), [2026-11-12](mining_results.772.marian_r.2026-11-12.md) |
| `782.lbm_r` | 5.738 | 5.738 | `-O3` (nothing accepted; throttle noise, ±12.6% baseline) | 0.0% | [2026-11-03](mining_results.782.lbm_r.2026-11-03.md) |
| **Suite geomean gain (12, unmined = 1.00×)** | | | | +20.50% | |
| Mined-only geomean (12 of 12) | 29.000 | 34.943 | | +20.50% | |

### intspeed (13 of 13 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `801.xz_s` | 0.9457 | 0.9457 | `-O3` (nothing accepted) | 0.0% | [2026-10-26](mining_results.801.xz_s.2026-10-26.md) |
| `807.ntest_s` | 0.9026 | 1.0760 | `-O3 -march=native -flto -fprofile-use` | **+19.21%** | [2026-10-26](mining_results.807.ntest_s.2026-10-26.md) |
| `817.flac_s` | 2.387 | 5.923 | `-O3 -fprefetch-loop-arrays -march=native -mprefer-vector-width=256` | **+148.16%** | [2026-10-27](mining_results.817.flac_s.2026-10-27.md) |
| `821.gcc_s` | 1.1018 | 1.2877 | `-O3 -fno-pie -no-pie -flto -fno-stack-protector -fprofile-use` | **+16.88%** | [2026-10-31](mining_results.821.gcc_s.2026-10-31.md) |
| `823.llvm_s` | 0.9252 | 1.1099 | `-O3 -flto -fprofile-use` | **+19.96%** | [2026-10-28](mining_results.823.llvm_s.2026-10-28.md) |
| `827.cppcheck_s` | 1.0595 | 1.1866 | `-O3 -fno-stack-protector -fprofile-use` | **+12.00%** | [2026-10-29](mining_results.827.cppcheck_s.2026-10-29.md) |
| `829.abc_s` | 2.754 | 2.818 | `-O3 -flto` (follow-up) | **+2.32%** | [2026-10-25](mining_results.829.abc_s.2026-10-25.md#follow-up--o3-against--o3--flto-27-2026-10-25) |
| `834.vpr_s` | 4.111 | 5.145 | `-O3 -flto -fprofile-use -march=znver5` | **+25.17%** | [2026-10-24](mining_results.834.vpr_s.2026-10-24.md) |
| `835.gem5_s` | 5.260 | 5.542 | `-O3 -flto` | **+5.35%** | [2026-10-24](mining_results.835.gem5_s.2026-10-24.md) |
| `838.diamond_s` | 0.9384 | 1.2620 | `-O3 -flto -funroll-loops -march=znver5` | **+34.49%** | [2026-10-30](mining_results.838.diamond_s.2026-10-30.md) |
| `846.minizinc_s` | 4.659 | 4.659 | `-O3` (nothing accepted) | 0.0% | [2026-10-24](mining_results.846.minizinc_s.2026-10-24.md) |
| `853.ns3_s` | 6.527 | 7.602 | `-O3 -flto -fprofile-use` | **+16.46%** | [2026-10-24](mining_results.853.ns3_s.2026-10-24.md) |
| `854.graph500_s` | 0.8954 | 1.0374 | `-O3 -funroll-loops` | **+15.85%** | [2026-11-02](mining_results.854.graph500_s.2026-11-02.md) |
| **Suite geomean gain (13, unmined = 1.00×)** | | | | +20.56% | |
| Mined-only geomean (13 of 13) | 1.867 | 2.251 | | +20.56% | |

### fpspeed (9 of 13 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `800.pot3d_s` | 0.7936 | 0.9582 | `-O3 -Ofast` (+28.25% on `chicago`; `-ffast-math` +18.05%; fast-math code runs in two modes about 4% apart, +19.47% over all nine `-Ofast` runs; nothing on top) | **+20.73%** | [2026-11-23](mining_results.800.pot3d_s.2026-11-23.md) |
| `803.sph_exa_s` | 1.4990 | 1.6920 | `-O3 -march=native -fprofile-use` (`-march=native` +9.04%, two of five reps in a 3.8%-slower mode; PGO +3.51% on top) | **+12.88%** | [2026-11-19](mining_results.803.sph_exa_s.2026-11-19.md) |
| `809.cactus_s` | 2.2061 | 2.7060 | `-O3 -march=native` (+14.53% on `chicago`; `-flto` +1.70% alone but +0.07% on top, probably drift, recheck flagged +1.48%; PGO and vector width flat) | **+22.66%** | [2026-11-24](mining_results.809.cactus_s.2026-11-24.md) |
| `811.tealeaf_s` | — | — | not mined yet | — | |
| `816.nab_s` | 1.6230 | 1.8744 | `-O3 -Ofast -fprofile-use -march=znver5` (`-march=native` +0.26% alone, `-march=znver5` +7.04% on top of fast-math and PGO) | **+15.49%** | [2026-11-17](mining_results.816.nab_s.2026-11-17.md) |
| `820.cloverleaf_s` | — | — | not mined yet | — | |
| `822.palm_s` | 1.6908 | 1.9431 | `-O3 -march=native -fprofile-use` (`-march=native` +10.26% against +19.22% on `chicago`; PGO +4.22%; `-flto` +1.34%, CI overlap on both hosts) | **+14.92%** | [2026-11-22](mining_results.822.palm_s.2026-11-22.md) |
| `849.fotonik3d_s` | — | — | not mined yet | — | |
| `857.namd_s` | 1.2139 | 1.4648 | `-O3 -march=native` (fast-math -2.7%; PGO, near-miss and vector width +0.5-0.65% on top, under the bar) | **+20.67%** | [2026-11-18](mining_results.857.namd_s.2026-11-18.md) |
| `865.roms_s` | — | — | not mined yet | — | |
| `867.nest_s` | 1.0029 | 1.0029 | `-O3` (nothing accepted, as on `chicago`; `-O3` runs spread 3.8%, recheck flagged -2.03%; `-march` code +0.6% pooled; PGO -4.4%) | +0.00% | [2026-11-22](mining_results.867.nest_s.2026-11-22.md) |
| `872.marian_s` | 2.2856 | 2.6896 | `-O3 -march=native` (+56.38% on `chicago`; prefetch +9.7% and graphite +6.2% alone, nothing on top; `=256` -6.66%) | **+17.68%** | [2026-11-20](mining_results.872.marian_s.2026-11-20.md) |
| `881.neutron_s` | 1.1209 | 1.2230 | `-O3 -flto -march=znver5` (the same code as `chicago`'s `-flto -march=native`; `-march=native` -1.05% alone, `-march=znver5` +3.28% on top of `-flto`; PGO -29.1%) | **+9.11%** | [2026-11-21](mining_results.881.neutron_s.2026-11-21.md) |
| **Suite geomean gain (13, unmined = 1.00×)** | | | | +9.96% | |
| Mined-only geomean (9 of 13) | 1.4131 | 1.6208 | | +14.70% | |

### Suite geomean progression

Suite geomean gain over every benchmark in the suite, unmined = 1.00×, recorded after each mine.

| After | intrate (14) | fprate (12) | intspeed (13) | fpspeed (13) |
|---|---|---|---|---|
| `706.stockfish_r` | +2.86% | +0.00% | +0.00% | +0.00% |
| `714.cpython_r` | +5.17% | +0.00% | +0.00% | +0.00% |
| `708.sqlite_r` | +5.30% | +0.00% | +0.00% | +0.00% |
| `729.abc_r` | +5.30% | +0.00% | +0.00% | +0.00% |
| `707.ntest_r` | +6.31% | +0.00% | +0.00% | +0.00% |
| `750.sealcrypto_r` | +7.74% | +0.00% | +0.00% | +0.00% |
| `710.omnetpp_r` | +9.77% | +0.00% | +0.00% | +0.00% |
| `723.llvm_r` | +11.52% | +0.00% | +0.00% | +0.00% |
| `727.cppcheck_r` | +12.12% | +0.00% | +0.00% | +0.00% |
| `734.vpr_r` | +12.23% | +0.00% | +0.00% | +0.00% |
| `734.vpr_r` LTO/PGO follow-up | +13.30% | +0.00% | +0.00% | +0.00% |
| `721.gcc_r` | +13.30% | +0.00% | +0.00% | +0.00% |
| `735.gem5_r` | +14.15% | +0.00% | +0.00% | +0.00% |
| `708.sqlite_r` LTO/PGO follow-up | +14.82% | +0.00% | +0.00% | +0.00% |
| `729.abc_r` LTO/PGO follow-up | +15.02% | +0.00% | +0.00% | +0.00% |
| `721.gcc_r` LTO/PGO follow-up | +15.86% | +0.00% | +0.00% | +0.00% |
| `753.ns3_r` | +17.84% | +0.00% | +0.00% | +0.00% |
| `777.zstd_r` | +17.98% | +0.00% | +0.00% | +0.00% |
| `727.cppcheck_r` LTO/PGO follow-up | +18.18% | +0.00% | +0.00% | +0.00% |
| `707.ntest_r` re-mine | +19.33% | +0.00% | +0.00% | +0.00% |
| `750.sealcrypto_r` LTO/PGO follow-up | +20.13% | +0.00% | +0.00% | +0.00% |
| `834.vpr_s` | +20.13% | +0.00% | +1.74% | +0.00% |
| `853.ns3_s` | +20.13% | +0.00% | +2.94% | +0.00% |
| `846.minizinc_s` | +20.13% | +0.00% | +2.94% | +0.00% |
| `835.gem5_s` | +20.13% | +0.00% | +3.36% | +0.00% |
| `829.abc_s` | +20.13% | +0.00% | +3.36% | +0.00% |
| `829.abc_s` LTO follow-up | +20.13% | +0.00% | +3.54% | +0.00% |
| `807.ntest_s` | +20.13% | +0.00% | +4.95% | +0.00% |
| `801.xz_s` | +20.13% | +0.00% | +4.95% | +0.00% |
| `817.flac_s` | +20.13% | +0.00% | +12.55% | +0.00% |
| `823.llvm_s` | +20.13% | +0.00% | +14.13% | +0.00% |
| `827.cppcheck_s` | +20.13% | +0.00% | +15.13% | +0.00% |
| `838.diamond_s` | +20.13% | +0.00% | +17.79% | +0.00% |
| `821.gcc_s` | +20.13% | +0.00% | +19.21% | +0.00% |
| `854.graph500_s` | +20.13% | +0.00% | +20.56% | +0.00% |
| `782.lbm_r` (600 s settle) | +20.13% | +0.00% | +20.56% | +0.00% |
| `731.astcenc_r` | +20.13% | +2.19% | +20.56% | +0.00% |
| `748.flightdm_r` | +20.13% | +4.16% | +20.56% | +0.00% |
| `767.nest_r` | +20.13% | +4.27% | +20.56% | +0.00% |
| `737.gmsh_r` | +20.13% | +4.27% | +20.56% | +0.00% |
| `736.ocio_r` | +20.13% | +6.04% | +20.56% | +0.00% |
| `772.marian_r` | +20.13% | +10.47% | +20.56% | +0.00% |
| `766.femflow_r` | +20.13% | +17.36% | +20.56% | +0.00% |
| `722.palm_r` | +20.13% | +18.24% | +20.56% | +0.00% |
| `736.ocio_r` `--no-shape-filter` re-mine | +20.13% | +18.55% | +20.56% | +0.00% |
| `772.marian_r` `--no-shape-filter` re-mine (same winner, row kept) | +20.13% | +18.55% | +20.56% | +0.00% |
| `766.femflow_r` `--no-shape-filter` re-mine (same winner, row kept) | +20.13% | +18.55% | +20.56% | +0.00% |
| `709.cactus_r` (held back, mined clean) | +20.13% | +20.50% | +20.56% | +0.00% |
| `749.fotonik3d_r` (held back, throttled; recorded 0.0%) | +20.13% | +20.50% | +20.56% | +0.00% |
| `765.roms_r` (held back, throttled; nothing accepted) | +20.13% | +20.50% | +20.56% | +0.00% |
| `816.nab_s` | +20.13% | +20.50% | +20.56% | +1.11% |
| `857.namd_s` | +20.13% | +20.50% | +20.56% | +2.59% |
| `803.sph_exa_s` | +20.13% | +20.50% | +20.56% | +3.55% |
| `872.marian_s` | +20.13% | +20.50% | +20.56% | +4.85% |
| `881.neutron_s` | +20.13% | +20.50% | +20.56% | +5.56% |
| `822.palm_s` | +20.13% | +20.50% | +20.56% | +6.69% |
| `867.nest_s` | +20.13% | +20.50% | +20.56% | +6.69% |
| `800.pot3d_s` | +20.13% | +20.50% | +20.56% | +8.25% |
| `809.cactus_s` | +20.13% | +20.50% | +20.56% | +9.96% |

SPECspeed mining started on 2026-10-24 with `834.vpr_s`, the first `_s` benchmark cfm has mined on
either host. Speed ratios come from one 16-thread process (`threads = 16`), not 16 copies. Before fpspeed (2026-11-17), the config's `-ftree-parallelize-loops`, which auto-parallelizes `800.pot3d_s`'s `DO CONCURRENT` loops (the only `doconcurrent` benchmark), was lowered from 24 to 16 to match, as `chicago` raised its to 32. Since PR #55,
single-threaded speed benchmarks are pinned with `taskset` to a Zen5 CPU, and OpenMP ones bind thread
*i* to CPU *i*. pthread benchmarks (vpr_s among them) can't be pinned from outside and run unpinned.
`853.ns3_s` was the first pinned mine (CPU 2); its baseline CI was ±0.23%, against ±0.6% for vpr_s and ±0.5% for ns3_r.
`829.abc_s`, also pinned, was ±0.21%. `807.ntest_s`, the first OpenMP-placed mine, was ±0.33%. In speed, LTO paid about half its rate gain on ns3 (+10.3% vs +21.4%)
and gem5 (+5.4% vs +11.0%), but more on vpr (+17.7% vs +11.4%), ntest (+3.6% vs +2.3% on top of `-march=native`) and llvm (+7.2% vs +1.4%). PGO on top paid about a third to a half of its rate gain: ntest +3.7% vs +11.3%, llvm +11.9% vs +23.1%.
fprate mining moved to [`chicago`](host_chicago.md) after `782.lbm_r` hit this host's memory-bandwidth throttle
([note](lbm_swing_investigation.2026-10-23.md)). A 2026-11-03 re-mine with a 10-minute settle before every run didn't help: the same binary read 6.33 and 5.00, on
discrete throttle levels that set in mid-run ([write-up](mining_results.782.lbm_r.2026-11-03.md)). The less
bandwidth-heavy fprate benchmarks are being mined here anyway. Of the three held back, cactus was mined on 2026-11-14
with no throttle sign at all (no reruns, recheck +0.35%). fotonik3d (2026-11-14) throttled like lbm: the same `-O3` binary read on three levels tracking 15/16/17 W, 15 slow-rep reruns, and the one accept (`-mtune=znver5`, +9.92%) was a level mismatch, so it is recorded as 0.0% ([write-up](mining_results.749.fotonik3d_r.2026-11-14.md)). roms (2026-11-15) throttled too (17-20 W, 22 reruns, baseline CI ±18%) and accepted nothing ([write-up](mining_results.765.roms_r.2026-11-15.md)). With that fprate is complete here, but fotonik3d, roms and lbm read 0.0% only because `niwot` can't measure them; use `chicago`'s results for those three.

## Cross-host comparison

| Benchmark | Old host | `niwot` |
|---|---|---|
| `706.stockfish_r` | `-march=native` +48.75% | `-march=native` +48.42% |
| `714.cpython_r` | `-flto` + PGO +41.65% | `-flto` + PGO +36.49% |
| `714.cpython_r`, `-march=native` | -5.32% (screening only) | -4.77% (confirmed) |
| `708.sqlite_r` | not mined | `-fprefetch-loop-arrays` +1.76% (re-check: +1.68%; prefetch-latency sweep: no better setting); follow-up `-fprefetch-loop-arrays -fprofile-use` +10.48% (`-flto` -0.7%) |
| `729.abc_r` | not mined | nothing accepted (0.0%; re-measure: `-march=znver5` +0.55%); follow-up `-flto` +2.49% (PGO about -4%) |
| `707.ntest_r` | `-march=native` +14.83% | `-march=native` +14.27%; re-mine with the margin gate: `-march=native -flto -fprofile-use` +30.95% (LTO +2.3%, PGO +11.3% on top) |
| `750.sealcrypto_r` | `-march=native` +14.17% / +15.63% | `-march=native` +20.49%; follow-up `-march=native -fprofile-use` +32.32% (PGO +10.4% on top, `-flto` -3.3%) |
| `710.omnetpp_r` | `-flto` + PGO +39.90% (LTO +13.3%, PGO +23.5%) | `-flto` + PGO +29.94% (LTO +13.1%, PGO +14.9%) |
| `723.llvm_r` | `-flto` + PGO +32.23% (LTO +5.9%, PGO +24.9%) | `-flto` + PGO +24.83% (LTO +1.4%, PGO +23.1%) |
| `727.cppcheck_r` | PGO +10.79% (`-flto` +4.20% rejected) | PGO +7.78% (`-flto` +0.96% rejected); follow-up `-flto -fprofile-use` +10.33% |
| `734.vpr_r` | `-march=native` +1.04% (fast-tracked) | `-march=native` +1.31% (screened; `-fprefetch-loop-arrays` fast-tracked, +0.42% rejected); follow-up `-march=native -flto -fprofile-use` +15.77% |
| `721.gcc_r` | nothing accepted (`-march=native` -0.15%) | nothing accepted (`-march=native` -0.27%); follow-up `-flto -fprofile-use` +10.71% |
| `735.gem5_r` | `-flto` +13.62% (PGO -6.7% rejected) | `-flto` +11.01% (PGO -10.6% rejected; with `-fprofile-partial-training`, +1.3% over `-flto`, CIs overlap) |
| `753.ns3_r` | `-flto` + PGO +37.99% (LTO +23.3%, PGO +11.9%) | `-flto` + PGO +26.66% (LTO +21.4%, PGO +4.3%) |
| `777.zstd_r` | nothing accepted (`-march=native` about +0.7%, under the 1% bar) | `-march=native` +1.72%; follow-up `-flto` +0.24%, PGO -1.7% |

## Open items

Follow-up experiments and pipeline ideas are tracked in
[`opportunities_niwot.md`](opportunities_niwot.md) (prefetch-distance sweep for sqlite, abc re-measure,
local-shape cross-checks, the stockfish LTO regression, and others). Standing facts about this host:

- ~~Reference-matrix lookup never matches on this host~~: fixed in PR #47 (merged 2026-10-17). It first
  matched for real on `708.sqlite_r`. Runs before that (`706.stockfish_r`, `714.cpython_r`) used local shapes.
- `706.stockfish_r`: `-flto` is a confirmed **-16.6%** regression (3 reps), and about -24% on top of
  `-march=native`. It's stockfish-specific: `714.cpython_r` gained +7.94% from `-flto` here.
- The microarch multiplier has run for real here (cpython, sqlite, abc; every candidate rejected), so PR #46's
  detection fix is verified end to end.

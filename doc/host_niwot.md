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

### fprate (0 of 12 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `709.cactus_r` | — | — | not mined yet | — | |
| `722.palm_r` | — | — | not mined yet | — | |
| `731.astcenc_r` | — | — | not mined yet | — | |
| `736.ocio_r` | — | — | not mined yet | — | |
| `737.gmsh_r` | — | — | not mined yet | — | |
| `748.flightdm_r` | — | — | not mined yet | — | |
| `749.fotonik3d_r` | — | — | not mined yet | — | |
| `765.roms_r` | — | — | not mined yet | — | |
| `766.femflow_r` | — | — | not mined yet | — | |
| `767.nest_r` | — | — | not mined yet | — | |
| `772.marian_r` | — | — | not mined yet | — | |
| `782.lbm_r` | — | — | not mined yet | — | |
| **Suite geomean gain (12, unmined = 1.00×)** | | | | +0.00% | |
| Mined-only geomean (0 of 12) | — | — | | — | |

### intspeed (11 of 13 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `801.xz_s` | 0.9457 | 0.9457 | `-O3` (nothing accepted) | 0.0% | [2026-10-26](mining_results.801.xz_s.2026-10-26.md) |
| `807.ntest_s` | 0.9026 | 1.0760 | `-O3 -march=native -flto -fprofile-use` | **+19.21%** | [2026-10-26](mining_results.807.ntest_s.2026-10-26.md) |
| `817.flac_s` | 2.387 | 5.923 | `-O3 -fprefetch-loop-arrays -march=native -mprefer-vector-width=256` | **+148.16%** | [2026-10-27](mining_results.817.flac_s.2026-10-27.md) |
| `821.gcc_s` | — | — | not mined yet | — | |
| `823.llvm_s` | 0.9252 | 1.1099 | `-O3 -flto -fprofile-use` | **+19.96%** | [2026-10-28](mining_results.823.llvm_s.2026-10-28.md) |
| `827.cppcheck_s` | 1.0595 | 1.1866 | `-O3 -fno-stack-protector -fprofile-use` | **+12.00%** | [2026-10-29](mining_results.827.cppcheck_s.2026-10-29.md) |
| `829.abc_s` | 2.754 | 2.818 | `-O3 -flto` (follow-up) | **+2.32%** | [2026-10-25](mining_results.829.abc_s.2026-10-25.md#follow-up--o3-against--o3--flto-27-2026-10-25) |
| `834.vpr_s` | 4.111 | 5.145 | `-O3 -flto -fprofile-use -march=znver5` | **+25.17%** | [2026-10-24](mining_results.834.vpr_s.2026-10-24.md) |
| `835.gem5_s` | 5.260 | 5.542 | `-O3 -flto` | **+5.35%** | [2026-10-24](mining_results.835.gem5_s.2026-10-24.md) |
| `838.diamond_s` | 0.9384 | 1.2620 | `-O3 -flto -funroll-loops -march=znver5` | **+34.49%** | [2026-10-30](mining_results.838.diamond_s.2026-10-30.md) |
| `846.minizinc_s` | 4.659 | 4.659 | `-O3` (nothing accepted) | 0.0% | [2026-10-24](mining_results.846.minizinc_s.2026-10-24.md) |
| `853.ns3_s` | 6.527 | 7.602 | `-O3 -flto -fprofile-use` | **+16.46%** | [2026-10-24](mining_results.853.ns3_s.2026-10-24.md) |
| `854.graph500_s` | — | — | not mined yet | — | |
| **Suite geomean gain (13, unmined = 1.00×)** | | | | +17.79% | |
| Mined-only geomean (11 of 13) | 2.094 | 2.541 | | +21.35% | |

### fpspeed (0 of 13 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `800.pot3d_s` | — | — | not mined yet | — | |
| `803.sph_exa_s` | — | — | not mined yet | — | |
| `809.cactus_s` | — | — | not mined yet | — | |
| `811.tealeaf_s` | — | — | not mined yet | — | |
| `816.nab_s` | — | — | not mined yet | — | |
| `820.cloverleaf_s` | — | — | not mined yet | — | |
| `822.palm_s` | — | — | not mined yet | — | |
| `849.fotonik3d_s` | — | — | not mined yet | — | |
| `857.namd_s` | — | — | not mined yet | — | |
| `865.roms_s` | — | — | not mined yet | — | |
| `867.nest_s` | — | — | not mined yet | — | |
| `872.marian_s` | — | — | not mined yet | — | |
| `881.neutron_s` | — | — | not mined yet | — | |
| **Suite geomean gain (13, unmined = 1.00×)** | | | | +0.00% | |
| Mined-only geomean (0 of 13) | — | — | | — | |

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

SPECspeed mining started on 2026-10-24 with `834.vpr_s`, the first `_s` benchmark cfm has mined on
either host. Speed ratios come from one 16-thread process (`threads = 16`), not 16 copies. Since PR #55,
single-threaded speed benchmarks are pinned with `taskset` to a Zen5 CPU, and OpenMP ones bind thread
*i* to CPU *i*. pthread benchmarks (vpr_s among them) can't be pinned from outside and run unpinned.
`853.ns3_s` was the first pinned mine (CPU 2); its baseline CI was ±0.23%, against ±0.6% for vpr_s and ±0.5% for ns3_r.
`829.abc_s`, also pinned, was ±0.21%. `807.ntest_s`, the first OpenMP-placed mine, was ±0.33%. In speed, LTO paid about half its rate gain on ns3 (+10.3% vs +21.4%)
and gem5 (+5.4% vs +11.0%), but more on vpr (+17.7% vs +11.4%), ntest (+3.6% vs +2.3% on top of `-march=native`) and llvm (+7.2% vs +1.4%). PGO on top paid about a third to a half of its rate gain: ntest +3.7% vs +11.3%, llvm +11.9% vs +23.1%.
fprate mining moved to another host after `782.lbm_r` hit this host's memory-bandwidth throttle
([note](lbm_swing_investigation.2026-10-23.md)).

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

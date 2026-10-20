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
| 2026-10-17 | `708.sqlite_r` | memory-bound 39.7% (corpus, low conf.) | `-O3 -fprefetch-loop-arrays` | **+1.76%** | [link](mining_results.708.sqlite_r.2026-10-17.md) |
| 2026-10-17 | `729.abc_r` | memory-bound 38.2% (corpus, low conf.) | `-O3` (nothing accepted) | 0.00% | [link](mining_results.729.abc_r.2026-10-17.md) |
| 2026-10-18 | `707.ntest_r` | compute-bound 40.6% (corpus) | `-O3 -march=native` | **+14.27%** | [link](mining_results.707.ntest_r.2026-10-18.md) |
| 2026-10-19 | `750.sealcrypto_r` | compute-bound 55.1% (corpus) | `-O3 -march=native` | **+20.49%** | [link](mining_results.750.sealcrypto_r.2026-10-18.md) |
| 2026-10-19 | `710.omnetpp_r` | frontend-bound 45.9% (corpus) | `-O3 -flto -fprofile-use` | **+29.94%** | [link](mining_results.710.omnetpp_r.2026-10-19.md) |
| 2026-10-19 | `723.llvm_r` | frontend-bound 61.6% (corpus) | `-O3 -flto -fprofile-use` | **+24.83%** | [link](mining_results.723.llvm_r.2026-10-19.md) |
| 2026-10-20 | `727.cppcheck_r` | frontend-bound 71.0% (corpus) | `-O3 -fprofile-use` | **+7.78%** | [link](mining_results.727.cppcheck_r.2026-10-19.md) |
| 2026-10-20 | `734.vpr_r` | memory-bound 45.4% (corpus) | `-O3 -march=native -flto -fprofile-use` (follow-up; the mine found `-O3 -march=native`, +1.31%) | **+15.77%** | [link](mining_results.734.vpr_r.2026-10-20.md) |
| 2026-10-20 | `721.gcc_r` | memory-bound 45.2% (corpus) | `-O3` (nothing accepted; LTO/PGO check queued) | 0.00% | [link](mining_results.721.gcc_r.2026-10-20.md) |

## Summary by suite

Per benchmark: the latest converged `cfm mine` experiment on this host. *Base* is the plain `-O3` calibration
mean, *best* is the winning flag set's confirmed mean, and *gain* is best / base. Ratios are SPECrate ratios
from single-iteration `--action=validate` runs (16 copies), not reportable SPEC scores.

Each suite has two geomean rows:

- **Suite geomean gain (progression)** is the geomean of the per-benchmark gain factors over **every**
  benchmark in the suite, counting each unmined benchmark as 1.00× (no gain yet). It only rises as
  mining finds wins, so it tracks overall progress, and it becomes the real suite-level gain once every
  row is mined. Base and best ratios don't exist for unmined rows, so this row shows the gain only.
- **Mined-only geomean** covers just the benchmarks mined so far: base and best ratio geomeans, plus their
  gain (geomean(best) / geomean(base) over the same rows). It shows the typical win per mined benchmark,
  not a suite score.

### intrate (11 of 14 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `706.stockfish_r` | 50.69 | 75.23 | `-O3 -march=native` | **+48.42%** | [2026-10-17](mining_results.706.stockfish_r.2026-10-17.md) |
| `707.ntest_r` | 28.61 | 32.69 | `-O3 -march=native` | **+14.27%** | [2026-10-18](mining_results.707.ntest_r.2026-10-18.md) |
| `708.sqlite_r` | 24.27 | 24.70 | `-O3 -fprefetch-loop-arrays` | **+1.76%** | [2026-10-17](mining_results.708.sqlite_r.2026-10-17.md) |
| `710.omnetpp_r` | 24.06 | 31.27 | `-O3 -flto -fprofile-use` | **+29.94%** | [2026-10-19](mining_results.710.omnetpp_r.2026-10-19.md) |
| `714.cpython_r` | 37.53 | 51.23 | `-O3 -flto -fprofile-use` | **+36.49%** | [2026-10-17](mining_results.714.cpython_r.2026-10-17.md) |
| `721.gcc_r` | 22.99 | 22.99 | `-O3` (nothing accepted) | 0.00% | [2026-10-20](mining_results.721.gcc_r.2026-10-20.md) |
| `723.llvm_r` | 25.83 | 32.24 | `-O3 -flto -fprofile-use` | **+24.83%** | [2026-10-19](mining_results.723.llvm_r.2026-10-19.md) |
| `727.cppcheck_r` | 24.85 | 26.79 | `-O3 -fprofile-use` | **+7.78%** | [2026-10-19](mining_results.727.cppcheck_r.2026-10-19.md) |
| `729.abc_r` | 27.43 | 27.43 | `-O3` (nothing accepted) | 0.00% | [2026-10-17](mining_results.729.abc_r.2026-10-17.md) |
| `734.vpr_r` | 21.20 | 24.55 | `-O3 -march=native -flto -fprofile-use` ¹ | **+15.77%** | [2026-10-20](mining_results.734.vpr_r.2026-10-20.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-20) |
| `735.gem5_r` | — | — | not mined yet | — | |
| `750.sealcrypto_r` | 27.91 | 33.63 | `-O3 -march=native` | **+20.49%** | [2026-10-18](mining_results.750.sealcrypto_r.2026-10-18.md) |
| `753.ns3_r` | — | — | not mined yet | — | |
| `777.zstd_r` | — | — | not mined yet | — | |
| **Suite geomean gain (14, unmined = 1.00×)** | | | | **+13.30%** | |
| Mined-only geomean (11 of 14) | 27.78 | 32.57 | | +17.23% | |

¹ From the interleaved LTO/PGO follow-up (`cfm measure`, 3 rounds), not from the mine itself, whose shape filter
excluded both. The mine's own winner was `-O3 -march=native` at 21.48 (+1.31%).

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

### intspeed (0 of 13 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `801.xz_s` | — | — | not mined yet | — | |
| `807.ntest_s` | — | — | not mined yet | — | |
| `817.flac_s` | — | — | not mined yet | — | |
| `821.gcc_s` | — | — | not mined yet | — | |
| `823.llvm_s` | — | — | not mined yet | — | |
| `827.cppcheck_s` | — | — | not mined yet | — | |
| `829.abc_s` | — | — | not mined yet | — | |
| `834.vpr_s` | — | — | not mined yet | — | |
| `835.gem5_s` | — | — | not mined yet | — | |
| `838.diamond_s` | — | — | not mined yet | — | |
| `846.minizinc_s` | — | — | not mined yet | — | |
| `853.ns3_s` | — | — | not mined yet | — | |
| `854.graph500_s` | — | — | not mined yet | — | |
| **Suite geomean gain (13, unmined = 1.00×)** | | | | +0.00% | |
| Mined-only geomean (0 of 13) | — | — | | — | |

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

cfm has only mined `_r` (SPECrate) benchmarks so far, on either host. The `_s` speed suites are listed
for completeness. Whether `cfm mine` handles a speed benchmark correctly (threads rather than copies) hasn't
been checked.

## Cross-host comparison

| Benchmark | Old host | `niwot` |
|---|---|---|
| `706.stockfish_r` | `-march=native` +48.75% | `-march=native` +48.42% |
| `714.cpython_r` | `-flto` + PGO +41.65% | `-flto` + PGO +36.49% |
| `714.cpython_r`, `-march=native` | -5.32% (screening only) | -4.77% (confirmed) |
| `708.sqlite_r` | not mined | `-fprefetch-loop-arrays` +1.76% (re-check: +1.68%; prefetch-latency sweep: no better setting) |
| `729.abc_r` | not mined | nothing accepted (0.0%; re-measure: `-march=znver5` +0.55%) |
| `707.ntest_r` | `-march=native` +14.83% | `-march=native` +14.27% |
| `750.sealcrypto_r` | `-march=native` +14.17% / +15.63% | `-march=native` +20.49% |
| `710.omnetpp_r` | `-flto` + PGO +39.90% (LTO +13.3%, PGO +23.5%) | `-flto` + PGO +29.94% (LTO +13.1%, PGO +14.9%) |
| `723.llvm_r` | `-flto` + PGO +32.23% (LTO +5.9%, PGO +24.9%) | `-flto` + PGO +24.83% (LTO +1.4%, PGO +23.1%) |
| `727.cppcheck_r` | PGO +10.79% (`-flto` +4.20% rejected) | PGO +7.78% (`-flto` +0.96% rejected) |
| `734.vpr_r` | `-march=native` +1.04% (fast-tracked) | `-march=native` +1.31% (screened; `-fprefetch-loop-arrays` fast-tracked, +0.42% rejected); follow-up `-march=native -flto -fprofile-use` +15.77% |
| `721.gcc_r` | nothing accepted (`-march=native` -0.15%) | nothing accepted (`-march=native` -0.27%); LTO/PGO check queued |

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

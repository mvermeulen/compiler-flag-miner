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
| in progress | `729.abc_r` | memory-bound 38.2% (corpus, low conf.) | | | |

## Summary by suite

Per benchmark: the latest converged `cfm mine` experiment on this host. *Base* is the plain `-O3` calibration
mean, *best* is the winning flag set's confirmed mean, and *gain* is best / base. Ratios are SPECrate ratios
from single-iteration `--action=validate` runs (16 copies), not reportable SPEC scores.

Geomean rows cover **only the benchmarks mined so far**, so they aren't a suite score until every row is
filled in. The geomean gain is the geomean of the per-benchmark gain factors (equal to geomean(best) /
geomean(base) over the same rows).

### intrate (3 of 14 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `706.stockfish_r` | 50.69 | 75.23 | `-O3 -march=native` | **+48.42%** | [2026-10-17](mining_results.706.stockfish_r.2026-10-17.md) |
| `707.ntest_r` | — | — | not mined yet | — | |
| `708.sqlite_r` | 24.27 | 24.70 | `-O3 -fprefetch-loop-arrays` | **+1.76%** | [2026-10-17](mining_results.708.sqlite_r.2026-10-17.md) |
| `710.omnetpp_r` | — | — | not mined yet | — | |
| `714.cpython_r` | 37.53 | 51.23 | `-O3 -flto -fprofile-use` | **+36.49%** | [2026-10-17](mining_results.714.cpython_r.2026-10-17.md) |
| `721.gcc_r` | — | — | not mined yet | — | |
| `723.llvm_r` | — | — | not mined yet | — | |
| `727.cppcheck_r` | — | — | not mined yet | — | |
| `729.abc_r` | — | — | not mined yet | — | |
| `734.vpr_r` | — | — | not mined yet | — | |
| `735.gem5_r` | — | — | not mined yet | — | |
| `750.sealcrypto_r` | — | — | not mined yet | — | |
| `753.ns3_r` | — | — | not mined yet | — | |
| `777.zstd_r` | — | — | not mined yet | — | |
| **Geomean (3 of 14 mined)** | **35.88** | **45.66** | | **+27.27%** | |

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
| **Geomean** | — | — | | — (nothing mined yet) | |

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
| **Geomean** | — | — | | — (nothing mined yet) | |

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
| **Geomean** | — | — | | — (nothing mined yet) | |

cfm has only mined `_r` (SPECrate) benchmarks so far, on either host. The `_s` speed suites are listed
for completeness. Whether `cfm mine` handles a speed benchmark correctly (threads rather than copies) hasn't
been checked.

## Cross-host comparison

| Benchmark | Old host | `niwot` |
|---|---|---|
| `706.stockfish_r` | `-march=native` +48.75% | `-march=native` +48.42% |
| `714.cpython_r` | `-flto` + PGO +41.65% | `-flto` + PGO +36.49% |
| `714.cpython_r`, `-march=native` | -5.32% (screening only) | -4.77% (confirmed) |
| `708.sqlite_r` | not mined | `-fprefetch-loop-arrays` +1.76% |

## Open items

- ~~Reference-matrix lookup never matches on this host~~: fixed in PR #47 (merged 2026-10-17). It first
  matched for real on `708.sqlite_r`. Runs before that (`706.stockfish_r`, `714.cpython_r`) used local shapes.
- `706.stockfish_r`: `-flto` is a confirmed **-16.6%** regression (3 reps), and about -24% on top of
  `-march=native`. It's stockfish-specific: `714.cpython_r` gained +7.94% from `-flto` here.
- `708.sqlite_r`: try `--param prefetch-latency=N` (200/300/400) on top of the accepted
  `-fprefetch-loop-arrays`. The catalog entry is a placeholder that every run skips.
- Corpus shapes for `708.sqlite_r`/`729.abc_r` are low-confidence memory-bound, which excludes LTO and PGO
  untried. A local cross-check (a `deep-cpu` trial or a direct `-flto` measure) would show whether that's
  right.
- `714.cpython_r`: `-march=native` regresses -4.77% at plain `-O3` on both hosts. The cause is still open.
- The microarch multiplier has run for real here (cpython, sqlite; all four candidates rejected), so PR #46's
  detection fix is verified end to end.

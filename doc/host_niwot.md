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

## Cross-host comparison

| Benchmark | Old host | `niwot` |
|---|---|---|
| `706.stockfish_r` | `-march=native` +48.75% | `-march=native` +48.42% |
| `714.cpython_r` | `-flto` + PGO +41.65% | `-flto` + PGO +36.49% |
| `714.cpython_r`, `-march=native` | -5.32% (screening only) | -4.77% (confirmed) |

## Open items

- **Reference-matrix lookup never matches on this host.** `_slugify_test_point()` turns
  `ryzen350_64gb.gcc_O3.cfg` into `ryzen350_64gb.gcc_o3-base`, not the published `gcc_o3-base`, so every run
  falls back to a local `deep-cpu` characterization trial. Harmless (this host's own shape), but not the
  designed first choice. Not fixed yet.
- `706.stockfish_r`: `-O3 -flto` screened at **-16.9%** (single trial, never confirmed). `714.cpython_r`'s
  `-flto` was +7.94% on the same host, so this is stockfish-specific. Worth re-measuring.
- `714.cpython_r`: `-march=native` regresses -4.77% at plain `-O3` on both hosts. The cause is still open.
- The microarch multiplier has run for real here (cpython, both candidates rejected), so PR #46's detection
  fix is verified end to end.

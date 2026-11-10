# Mining host: `chicago`

Index of `cfm mine` results for this host. `chicago` is a Strix Halo mini PC with about twice the cores and
memory bandwidth of [`niwot`](host_niwot.md) and [`erie`](host_erie.md). It's where fprate mining moved after
`782.lbm_r` hit niwot's memory-bandwidth throttle ([note](lbm_swing_investigation.2026-10-23.md)).
Neither of those hosts' results or `cfm.db` knowledge priors carry over: this host's `cfm.db` started empty on
2026-11-03.

The `doc/mining_results.*.md` write-ups dated 2026-08 came from this machine (then described as "a Strix Halo
host, 91 GB RAM, 32 copies"). They predate `cfm`'s warm-up, bandwidth-gate and rerun guards, so treat
them as history, not as this host's baselines.

## Host

| | |
|---|---|
| CPU | AMD Ryzen AI MAX+ 395 w/ Radeon 8060S (family 1a model 70): 16 Zen5 cores, 32 threads, 2 x 32 MB L3 |
| Clocks | every CPU max 5.19 GHz (no Zen5c cores, so `fastest_cpus()` returns all 32) |
| Memory | 91 GB, 8 GB swap |
| Chassis | mini PC: GMKtec NucBox EVO-X2 (DMI chassis type 35) |
| OS / compiler | Ubuntu 26.04.1 LTS, Linux 7.0.0-42-generic, GCC 15.2.0 (Ubuntu 15.2.0-16ubuntu1) |
| SPEC | CPU2026 1.0.1 at `/home/mev/cpu2026`, `gcc_O3.cfg` (label `gcc_O3`, `copies = 32`, `threads = 32`) |
| Phoronix Test Suite | `~/.phoronix-test-suite`, 35 tests installed (coremark and c-ray among them); none mined here yet |
| Power | **profile `performance` since 2026-11-03** (`powerprofilesctl set performance`; governor and EPP follow to `performance`). amd-pstate `active`. It shipped in `balanced` (governor `powersave`, EPP `balance_performance`) |
| Microarch detection | `-march=znver5` / `-mtune=znver5` (every core reports `Zen5`) |
| Sensors | `k10temp` (CPU temp), `amdgpu` `power1_average` (package power; ~8 W idle, 84.99 W median on every 32-copy lbm trial) |
| Memory bandwidth | 101.8-103.2 GB/s on `cfm/bandwidth.py`'s 32-thread triad (three probes from idle under `balanced`, 101.5 under `performance`, 2026-11-03), against about 45 GB/s (fast state) on niwot |

## Running here

`cfm`'s defaults fit this host: `gcc_O3.cfg` exists, so no `CFM_SPEC_CONFIG` is needed. There's no `.venv`, so
run the package from the repo directly:

```
python3 -m cfm.cli mine 782.lbm_r
python3 -m pytest -q
```

## Results

| Date | Benchmark | Shape (source) | Winning flags | Gain vs `-O3` | Write-up |
|---|---|---|---|---|---|
| 2026-11-03 | `782.lbm_r` | memory-bound 94.9% (corpus) | `-O3 -march=native` | **+2.92%** | [link](mining_results.782.lbm_r.2026-11-03b.md) |
| 2026-11-04 | `782.lbm_r` (`--no-shape-filter`) | memory-bound 94.9% (corpus) | `-O3 -march=native` | **+3.52%** | [link](mining_results.782.lbm_r.2026-11-04.md) (`-Ofast` +1.03%, rejected on CI overlap) |
| 2026-11-05 | `709.cactus_r` | memory-bound 71.6% (corpus) | `-O3 -march=native` | **+16.51%** | [link](mining_results.709.cactus_r.2026-11-05.md) (11 of 15 candidates excluded on shape) |
| 2026-11-05 | `749.fotonik3d_r` | memory-bound 97.3% (corpus) | `-O3 -march=native -mprefer-vector-width=256` | **+7.04%** | [link](mining_results.749.fotonik3d_r.2026-11-05.md) (PGO -4.5%, LTO -2.4%) |
| 2026-11-05 | `765.roms_r` | memory-bound 95.0% (corpus) | `-O3 -march=native` | **+7.19%** | [link](mining_results.765.roms_r.2026-11-05.md) (`-mprefer-vector-width=256` -4.0%, PGO +0.8% rejected) |
| 2026-11-06 | `722.palm_r` | memory-bound 69.2% (corpus) | `-O3 -march=native -fprofile-use` | **+5.20%** | [link](mining_results.722.palm_r.2026-11-06.md) (first PGO accept here, +1.03%; `-flto` +1.04% rejected on CI overlap) |
| 2026-11-06 | `731.astcenc_r` | frontend-bound 44.3% (corpus, under the 55% gate) | `-O3 -march=native -Ofast` | **+29.49%** | [link](mining_results.731.astcenc_r.2026-11-06.md) (same winner, gain and code fingerprints as niwot's +29.64%) |
| 2026-11-07 | `736.ocio_r` | memory-bound 58.5% (corpus) | `-O3 -march=native -flto` | **+22.04%** | [link](mining_results.736.ocio_r.2026-11-07.md) (first LTO accept here; PGO -5.1%; 11 of 14 excluded on shape) |
| 2026-11-07 | `737.gmsh_r` | memory-bound 42.7% (corpus, under the 55% gate) | `-O3 -flto` | **+2.40%** | [link](mining_results.737.gmsh_r.2026-11-07.md) (first `-march=native` reject here, -0.42%; PGO +0.68% under the 1% bar) |
| 2026-11-07 | `748.flightdm_r` | frontend-bound 42.0% (corpus, under the 55% gate) | `-O3 -flto -fno-stack-protector -fprofile-use` | **+26.48%** | [link](mining_results.748.flightdm_r.2026-11-07.md) (LTO +10.7%, PGO +12.6%, both as on niwot; first hardening-flag accept here) |
| 2026-11-07 | `766.femflow_r` | memory-bound 69.4% (corpus) | `-O3 -flto -march=native` | **+132.01%** | [link](mining_results.766.femflow_r.2026-11-07.md) (`-march=native` alone +130.5%, AVX-512 autovectorization; `-mprefer-vector-width=256` -15.7%) |
| 2026-11-08 | `767.nest_r` | memory-bound 47.9% (corpus, under the 55% gate) | `-O3 -fno-stack-protector` | **+1.34%** | [link](mining_results.767.nest_r.2026-11-08.md) (`-march=native` +0.43% rejected; PGO -6.1% as on niwot) |
| 2026-11-08 | `772.marian_r` | memory-bound 63.1% (corpus) | `-O3 -march=native` | **+72.43%** | [link](mining_results.772.marian_r.2026-11-08.md) (AVX-512 autovectorization; `-fprefetch-loop-arrays` +15.2% alone, nothing on top; 11 of 14 excluded on shape) |
| 2026-11-08 | `800.pot3d_s` | memory-bound 52.0% (corpus, under the 55% gate) | (`-O3 -fno-unswitch-loops`) | (+115.71%) | [link](mining_results.800.pot3d_s.2026-11-08.md) (**not usable**: every trial pinned to one CPU, `doconcurrent` classed single-threaded; fixed in PR #70, re-mine pending) |
| 2026-11-09 | `803.sph_exa_s` | memory-bound 67.4% (corpus) | `-O3 -march=native -fprofile-use` | **+12.73%** | [link](mining_results.803.sph_exa_s.2026-11-09.md) (`-march=native` +9.1%, PGO +3.4% on top; 11 of 14 excluded on shape) |
| 2026-11-10 | `809.cactus_s` | memory-bound 70.9% (corpus) | `-O3 -march=native` | **+14.53%** | [link](mining_results.809.cactus_s.2026-11-10.md) (as cactus_r's +16.5%; LTO, PGO flat; 11 of 14 excluded on shape) |
| 2026-11-10 | `811.tealeaf_s` | memory-bound 70.7% (corpus) | `-O3` | 0.00% | [link](mining_results.811.tealeaf_s.2026-11-10.md) (clean reject: every candidate within ±0.16%, `-march=native` +0.02%; PGO trials 88 min each) |
| 2026-11-10 | `800.pot3d_s` (re-mine) | memory-bound 52.0% (corpus, under the 55% gate) | `-O3 -Ofast` | **+28.25%** | [link](mining_results.800.pot3d_s.2026-11-10.md) (OpenMP placement; baseline 4.1× the pinned run's; `-ffast-math` +27.8%, likely more parallelized reductions; `-fno-unswitch-loops` now -31.8%) |
| 2026-11-10 | `816.nab_s` | | | | in progress |

## Summary by suite

The method is the same as [niwot's](host_niwot.md#summary-by-suite). Each row is the latest converged `cfm mine`
experiment on this host for that benchmark. *Base* is the plain `-O3` calibration mean, *best* is the winning
flag set's confirmed mean, and *gain* is best / base. Ratios come from single-iteration `--action=validate` runs
with 32 copies, so they aren't reportable SPEC scores and can't be compared with niwot's 16-copy ratios.

- **Suite geomean gain** is the geomean of every benchmark's gain, with each unmined benchmark counted as 1.00×.
  It rises as mining finds wins, and once every row is mined it is the suite-level gain.
- **Mined-only geomean** covers only the benchmarks mined so far. Its gain is geomean(best) / geomean(base), the
  typical win per mined benchmark, not a suite score.

### fprate (12 of 12 mined)

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `709.cactus_r` | 91.446 | 106.547 | `-O3 -march=native` | **+16.51%** | [2026-11-05](mining_results.709.cactus_r.2026-11-05.md) |
| `722.palm_r` | 76.561 | 80.540 | `-O3 -march=native -fprofile-use` | **+5.20%** | [2026-11-06](mining_results.722.palm_r.2026-11-06.md) |
| `731.astcenc_r` | 77.592 | 100.477 | `-O3 -march=native -Ofast` | **+29.49%** | [2026-11-06](mining_results.731.astcenc_r.2026-11-06.md) |
| `736.ocio_r` | 83.802 | 102.273 | `-O3 -march=native -flto` | **+22.04%** | [2026-11-07](mining_results.736.ocio_r.2026-11-07.md) |
| `737.gmsh_r` | 59.371 | 60.796 | `-O3 -flto` | **+2.40%** | [2026-11-07](mining_results.737.gmsh_r.2026-11-07.md) |
| `748.flightdm_r` | 96.219 | 121.701 | `-O3 -flto -fno-stack-protector -fprofile-use` | **+26.48%** | [2026-11-07](mining_results.748.flightdm_r.2026-11-07.md) |
| `749.fotonik3d_r` | 38.726 | 41.452 | `-O3 -march=native -mprefer-vector-width=256` | **+7.04%** | [2026-11-05](mining_results.749.fotonik3d_r.2026-11-05.md) |
| `765.roms_r` | 36.618 | 39.250 | `-O3 -march=native` | **+7.19%** | [2026-11-05](mining_results.765.roms_r.2026-11-05.md) |
| `766.femflow_r` | 89.074 | 206.665 | `-O3 -flto -march=native` | **+132.01%** | [2026-11-07](mining_results.766.femflow_r.2026-11-07.md) |
| `767.nest_r` | 89.606 | 90.811 | `-O3 -fno-stack-protector` | **+1.34%** | [2026-11-08](mining_results.767.nest_r.2026-11-08.md) |
| `772.marian_r` | 121.729 | 209.894 | `-O3 -march=native` | **+72.43%** | [2026-11-08](mining_results.772.marian_r.2026-11-08.md) |
| `782.lbm_r` | 16.033 | 16.598 | `-O3 -march=native` | **+3.52%** | [2026-11-04](mining_results.782.lbm_r.2026-11-04.md) (`--no-shape-filter`) |
| **Suite geomean gain (12, unmined = 1.00×)** | | | | +23.08% | |
| Mined-only geomean (12 of 12) | 65.054 | 80.066 | | +23.08% | |

### fpspeed (4 of 13 mined)

SPECspeed runs one copy with `threads = 32`. The config's `-ftree-parallelize-loops`, which auto-parallelizes Fortran
loops in every fpspeed build, was raised from 24 to 32 on 2026-11-06 to match, before the first fpspeed mine.

| Benchmark | Base (`-O3`) | Best | Winning flags | Gain | Write-up |
|---|---|---|---|---|---|
| `800.pot3d_s` | 1.4446 | 1.8526 | `-O3 -Ofast` | **+28.25%** | [2026-11-10](mining_results.800.pot3d_s.2026-11-10.md) (the [2026-11-08](mining_results.800.pot3d_s.2026-11-08.md) mine ran pinned to one CPU and isn't counted) |
| `803.sph_exa_s` | 3.3481 | 3.7743 | `-O3 -march=native -fprofile-use` | **+12.73%** | [2026-11-09](mining_results.803.sph_exa_s.2026-11-09.md) |
| `809.cactus_s` | 4.2796 | 4.9012 | `-O3 -march=native` | **+14.53%** | [2026-11-10](mining_results.809.cactus_s.2026-11-10.md) |
| `811.tealeaf_s` | 1.4308 | 1.4308 | `-O3` | 0.00% | [2026-11-10](mining_results.811.tealeaf_s.2026-11-10.md) |
| **Suite geomean gain (13, unmined = 1.00×)** | | | | +3.95% | |
| Mined-only geomean (4 of 13) | 2.333 | 2.646 | | +13.43% | |

### Suite geomean progression

Suite geomean gain (unmined = 1.00×), recorded after each mine: fprate over 12 benchmarks, fpspeed over 13.

| After | fprate (12) | fpspeed (13) |
|---|---|---|
| `782.lbm_r` | +0.24% | — |
| `782.lbm_r` `--no-shape-filter` re-mine | +0.29% | — |
| `709.cactus_r` | +1.57% | — |
| `749.fotonik3d_r` | +2.15% | — |
| `765.roms_r` | +2.74% | — |
| `722.palm_r` | +3.18% | — |
| `731.astcenc_r` | +5.43% | — |
| `736.ocio_r` | +7.19% | — |
| `737.gmsh_r` | +7.40% | — |
| `748.flightdm_r` | +9.53% | — |
| `766.femflow_r` | +17.48% | — |
| `767.nest_r` | +17.61% | — |
| `772.marian_r` | +23.08% | — |
| `803.sph_exa_s` | +23.08% | +0.93% |
| `809.cactus_s` | +23.08% | +1.98% |
| `811.tealeaf_s` | +23.08% | +1.98% |
| `800.pot3d_s` re-mine | +23.08% | +3.95% |

## Standing facts about this host

- **Experiment 1 (`782.lbm_r`, 2026-11-03) was stopped during its first warm-up rep** to switch the power
  profile to `performance`, and marked failed. Experiment 2 is the real mine.
- **SPECrate runs 32 copies here**, twice niwot's and erie's 16, so ratios aren't comparable across hosts.
- **No memory-bandwidth throttle seen under lbm.** Over 34 trials (11 hours), the pre-run probe read 89-99 GB/s and
  the gate never waited after the first trial. lbm's `-O3` reps spread 0.08% (CI ±0.11%), against 17% (CI ±12.6%) on
  niwot the same night ([write-up](mining_results.782.lbm_r.2026-11-03.md)).
- **Under 32 copies of lbm, package power sits at about 85 W** for the whole run, and the CPU at 91-95°C.
- **A SPECrate trial of lbm takes about 19 minutes**, so a full mine is about 11 hours (21 with `--no-shape-filter`).
- **Package power sits at 85.0 W under every 32-copy fprate mine so far** (lbm, cactus, fotonik3d, roms, palm, astcenc, ocio, gmsh, flightdm, femflow, nest, marian): the sustained package limit.
- **SPECspeed runs use 32 threads**, and `-ftree-parallelize-loops=32` (raised from 24 on 2026-11-06).
- **A speed benchmark drawing far under 85 W is mis-placed**: pot3d_s, pinned to one CPU, drew 24.6 W.
- **The bandwidth gate sometimes catches the tail of the previous run.** In experiment 3 it waited 30 s before
  10 of 66 runs, and each re-probe read the session best (~105 GB/s).

## Open items

| # | Pri | Opportunity | How | What would change |
|---|---|---|---|---|
| 1 | ~~H~~ | ~~**Does fprate mine cleanly here?**~~ niwot's memory side halved its bandwidth for minutes at a time under lbm. | Mine `782.lbm_r` with the bandwidth gate on. | **Done 2026-11-04:** yes. No reruns, the gate waited once (30 s, first trial), baseline CI ±0.11%. |
| 2 | ~~M~~ | ~~**lbm without the shape filter.**~~ | Re-mine with `--no-shape-filter`. | **Done 2026-11-05:** nothing new accepted. `-Ofast` (+1.03%) and `-ffast-math` (same code) came closest; every other flag was within ±0.55%. |
| 3 | H | **The rest of fprate.** | Mine the other fprate benchmarks here, starting with the three niwot holds back (cactus, fotonik3d, roms). | fprate coverage, which niwot couldn't give. |
| 4 | L | **`-march=native -Ofast` on lbm.** Phase 5 never combined them because `-Ofast` was rejected alone, on a CI widened by one low baseline rep. | `cfm measure` both, interleaved with `-O3 -march=native`. | Whether fast-math adds ~1% on top of AVX-512 here. |
| 5 | M | **A 0.7%-low calibration rep widened lbm's CI ninefold** (experiment 3, trial 39). Too small for either rerun rule. | Five calibration reps, or rerun a rep outside its siblings' spread by a smaller factor when the spread is tiny. | Tighter verdicts on ~1% effects. |
| 6 | M | **cactus without the shape filter.** The 71.6% memory-bound read excluded `-Ofast`, `-ffast-math` and `-funroll-loops`. | Re-mine with `--no-shape-filter` (about 6 hours). | Whether fast-math adds to `-march=native`'s +16.5%. |
| 7 | M | **`-flto` on palm.** It read +1.04% alone but was rejected on CI overlap (baseline ±0.73%), so it was never tried with `-march=native -fprofile-use`, which won (+5.20%). | `cfm measure` `-O3 -march=native -flto -fprofile-use`, interleaved with the winner (3 rounds). | Whether LTO adds ~1% on top of PGO here, as it did for intrate on niwot. |
| 8 | M | **ocio without the shape filter.** Its 58.5% memory-bound read, just over the 55% gate, excluded 11 of 14 candidates, `-Ofast` and `-ffast-math` among them; on astcenc (under the gate) `-Ofast` added +7.6% on top of `-march=native`. | Re-mine with `--no-shape-filter` (about 8 hours). | Whether fast-math adds to `-march=native -flto`'s +22.0%. |
| 9 | L | **PGO on gmsh.** `-flto -fprofile-use` read +0.68% on top of `-flto`, CI-clear of it, and was rejected only on the 1% bar. | Nothing unless the bar changes; the measurement stands. | About +3.1% over `-O3` instead of +2.4%. |
| 10 | L | **The pair tournament skips the 1% bar for its marginal flag.** A pair replaces the greedy winner on a clear CI and a higher mean alone (`greedy_combine()`), so on femflow it added `-flto` on +0.5% over `-march=native`, which the greedy step had just rejected under the bar; on flightdm it recovered a step a single low rep had sunk. | Apply `MIN_PRACTICAL_SIGNIFICANCE_PCT` to a replacing pair's gain over the greedy winner too. | Winning sets carry only flags the evidence supports. |
| 11 | M | **marian without the shape filter.** Its 63.1% memory-bound read excluded 11 of 14 candidates, `-Ofast` and `-ffast-math` among them, on a neural-network decoder that `-march=native` sped up 72%. | Re-mine with `--no-shape-filter` (about 10 hours; PGO trials alone take an hour each). | Whether fast-math adds to the +72%. |
| 12 | ~~H~~ | ~~**Re-mine `800.pot3d_s` with correct thread placement**~~ (PR #70 merged 2026-11-10). Experiment 15 pinned all 32 auto-parallel threads to CPU 1 (`doconcurrent` was classed single-threaded). | Merge PR #70, then re-mine. | **Done 2026-11-10:** +28.25% with `-Ofast`; `-fno-unswitch-loops` reads -31.8% with correct placement. |
| 13 | L | **Experiment 15's knowledge rows came from the pinned run.** `-fno-unswitch-loops` now reads accepted 1 of 4, mean +29.2%, in the memory-bound cluster; `-march=native` gained a +2.8% accept. | Leave them (one accept of four doesn't fast-track) or remove experiment 15's contributions after the re-mine. | Cleaner memory-bound priors. |
| 14 | M | **Fast-math on the shape-filtered fpspeed benchmarks.** On pot3d_s (52.0%, under the gate) `-Ofast` gained +28.3%, probably by letting GCC parallelize floating-point reductions. sph_exa_s, cactus_s and tealeaf_s (67-71% memory-bound) never measured it. | Re-mine them with `--no-shape-filter`, or `cfm measure` `-Ofast` on top of each winner. | Whether the fpspeed geomean is missing large fast-math wins. |

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
| 2026-11-08 | `772.marian_r` | | | | in progress |

## Summary by suite

The method is the same as [niwot's](host_niwot.md#summary-by-suite). Each row is the latest converged `cfm mine`
experiment on this host for that benchmark. *Base* is the plain `-O3` calibration mean, *best* is the winning
flag set's confirmed mean, and *gain* is best / base. Ratios come from single-iteration `--action=validate` runs
with 32 copies, so they aren't reportable SPEC scores and can't be compared with niwot's 16-copy ratios.

- **Suite geomean gain** is the geomean of every benchmark's gain, with each unmined benchmark counted as 1.00×.
  It rises as mining finds wins, and once every row is mined it is the suite-level gain.
- **Mined-only geomean** covers only the benchmarks mined so far. Its gain is geomean(best) / geomean(base), the
  typical win per mined benchmark, not a suite score.

### fprate (11 of 12 mined)

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
| `772.marian_r` | — | — | in progress | — | |
| `782.lbm_r` | 16.033 | 16.598 | `-O3 -march=native` | **+3.52%** | [2026-11-04](mining_results.782.lbm_r.2026-11-04.md) (`--no-shape-filter`) |
| **Suite geomean gain (12, unmined = 1.00×)** | | | | +17.61% | |
| Mined-only geomean (11 of 12) | 61.452 | 73.350 | | +19.36% | |

### Suite geomean progression

fprate suite geomean gain (12 benchmarks, unmined = 1.00×), recorded after each mine.

| After | fprate (12) |
|---|---|
| `782.lbm_r` | +0.24% |
| `782.lbm_r` `--no-shape-filter` re-mine | +0.29% |
| `709.cactus_r` | +1.57% |
| `749.fotonik3d_r` | +2.15% |
| `765.roms_r` | +2.74% |
| `722.palm_r` | +3.18% |
| `731.astcenc_r` | +5.43% |
| `736.ocio_r` | +7.19% |
| `737.gmsh_r` | +7.40% |
| `748.flightdm_r` | +9.53% |
| `766.femflow_r` | +17.48% |
| `767.nest_r` | +17.61% |

## Standing facts about this host

- **Experiment 1 (`782.lbm_r`, 2026-11-03) was stopped during its first warm-up rep** to switch the power
  profile to `performance`, and marked failed. Experiment 2 is the real mine.
- **SPECrate runs 32 copies here**, twice niwot's and erie's 16, so ratios aren't comparable across hosts.
- **No memory-bandwidth throttle seen under lbm.** Over 34 trials (11 hours), the pre-run probe read 89-99 GB/s and
  the gate never waited after the first trial. lbm's `-O3` reps spread 0.08% (CI ±0.11%), against 17% (CI ±12.6%) on
  niwot the same night ([write-up](mining_results.782.lbm_r.2026-11-03.md)).
- **Under 32 copies of lbm, package power sits at about 85 W** for the whole run, and the CPU at 91-95°C.
- **A SPECrate trial of lbm takes about 19 minutes**, so a full mine is about 11 hours (21 with `--no-shape-filter`).
- **Package power sits at 85.0 W under every 32-copy fprate mine so far** (lbm, cactus, fotonik3d, roms, palm, astcenc, ocio, gmsh, flightdm, femflow, nest): the sustained package limit.
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
| 10 | L | **The pair tournament skips the 1% bar for its marginal flag.** A pair is compared against `-O3`, so on femflow it added `-flto` on +0.5% over `-march=native`, which the greedy step had just rejected; on flightdm it recovered a step a single low rep had sunk. | Compare a replacing pair against the greedy winner as well, with the same bar. | Winning sets carry only flags the evidence supports. |

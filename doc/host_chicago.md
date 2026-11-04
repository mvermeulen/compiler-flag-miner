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

## Standing facts about this host

- **Experiment 1 (`782.lbm_r`, 2026-11-03) was stopped during its first warm-up rep** to switch the power
  profile to `performance`, and marked failed. Experiment 2 is the real mine.
- **SPECrate runs 32 copies here**, twice niwot's and erie's 16, so ratios aren't comparable across hosts.
- **No memory-bandwidth throttle seen under lbm.** Over 34 trials (11 hours), the pre-run probe read 89-99 GB/s and
  the gate never waited after the first trial. lbm's `-O3` reps spread 0.08% (CI ±0.11%), against 17% (CI ±12.6%) on
  niwot the same night ([write-up](mining_results.782.lbm_r.2026-11-03.md)).
- **Under 32 copies of lbm, package power sits at about 85 W** for the whole run, and the CPU at 91-95°C.
- **A SPECrate trial of lbm takes about 19 minutes**, so a full mine is about 11 hours.

## Open items

| # | Pri | Opportunity | How | What would change |
|---|---|---|---|---|
| 1 | ~~H~~ | ~~**Does fprate mine cleanly here?**~~ niwot's memory side halved its bandwidth for minutes at a time under lbm. | Mine `782.lbm_r` with the bandwidth gate on. | **Done 2026-11-04:** yes. No reruns, the gate waited once (30 s, first trial), baseline CI ±0.11%. |
| 2 | M | **lbm without the shape filter.** The 94.9% memory-bound read excluded 11 of 15 candidates, `-funroll-loops` and `-Ofast` among them. | Re-mine with `--no-shape-filter` (about 11 hours more). | Whether anything beyond `-march=native` helps lbm. |
| 3 | H | **The rest of fprate.** | Mine the other fprate benchmarks here. | fprate coverage, which niwot couldn't give. |

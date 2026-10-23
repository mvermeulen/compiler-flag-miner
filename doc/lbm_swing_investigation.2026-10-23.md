# `782.lbm_r` ratio swings on `niwot` (2026-10-23)

Opportunity #26 on the [opportunity list](opportunities_niwot.md). The first `niwot` mine of `782.lbm_r`
(experiment 151, trials 661-671, code at `989561a`) measured ratios that swung 2x between trials. It was stopped
after 11 trials, and this note collects what the data already in hand says. No new SPEC runs were made for it.

## The swings

| Trial | Flags | Ratio | Elapsed (s) | Instructions | Cycles | IPC | CPU temp | Package power |
|---|---|---|---|---|---|---|---|---|
| 661 | `-O3` (warm-up) | 6.32 | 1457 | 35.8T | 67.5T | 0.53 | 92.0°C | 21.1 W |
| 662 | `-O3` (warm-up) | 3.02 | 3037 | 35.9T | 144T | 0.25 | 82.8°C | 22.0 W |
| 663 | `-O3` | 4.15 | 2215 | 35.8T | 104T | 0.34 | 82.2°C | 21.1 W |
| 664 | `-O3` | 4.24 | 2167 | 35.8T | 102T | 0.35 | 84.4°C | 23.1 W |
| 665 | `-O3` | 4.26 | 2160 | 35.8T | 102T | 0.35 | 83.5°C | 22.0 W |
| 666 | `-fprefetch-loop-arrays` | 4.27 | 2152 | 36.3T | 101T | 0.36 | 83.1°C | 22.0 W |
| 667 | `-fgraphite-identity` | 4.63 | 1985 | 35.8T | 93.1T | 0.39 | 84.4°C | 22.1 W |
| 668 | `-march=native` | 6.33 | 1455 | 26.2T | 67.5T | 0.39 | 88.6°C | 22.0 W |
| 669 | `-fprefetch-loop-arrays` | 3.04 | 3018 | 36.4T | 143T | 0.25 | 80.4°C | 22.1 W |
| 670 | `-fprefetch-loop-arrays` | 4.75 | 1936 | 36.2T | 90.4T | 0.40 | 83.8°C | 22.1 W |
| 671 | `-fprefetch-loop-arrays` | 5.46 | 1686 | 36.2T | 78.5T | 0.46 | 85.5°C | 22.0 W |

Instructions, cycles and IPC come from each trial's own wspy `quick`-profile `run.txt` (all 16 copies); temperature
and power are the per-trial `hypotheses` rows.

## What the data rules in and out

- **The cores ran at the same speed in every trial.** Cycles track elapsed time almost exactly (about 46-47 G
  cycles/s across 16 threads, roughly 2.9 GHz each, in both the fastest and slowest trials), and every `-O3`
  build retired the same 35.8T instructions. What changed is IPC, from 0.25 to 0.53: the cores spent up to twice as
  long stalled. lbm is a streaming stencil limited by DRAM bandwidth, so **the memory side ran at different speeds
  in different trials**.
- **It's system-wide and lasts a whole trial.** In each run all 16 copies' elapsed times sit within a few percent
  of each other (SPEC logs `CPU2026.1352`-`1362`), and the state held for 25-50 minutes before changing.
- **Not power or thermal limits on the cores.** Package power was flat at 21-23 W throughout. Temperature followed
  the ratio (hot when fast) rather than leading it, as you'd expect when stalled cores do less work.
- **Not huge pages.** THP is `madvise`-only here and lbm doesn't madvise, so every trial ran on 4K pages
  (`AnonHugePages: 0`, `thp_fault_fallback 0`).
- **Nothing else was running.** `sar` shows 99.8% user CPU and under 0.6% system time for the whole window.
- **Not visible at idle.** A 16-thread triad probe run afterwards measured a steady 40.8 GB/s over two minutes,
  with no jumps between levels.

## The first guess (superseded below)

*Superseded by the follow-up measurements below: the `performance` profile didn't change anything, so this
isn't the profile's clock policy.*


The memory clock (MCLK: 1000/2400/2800 MHz) and fabric clock (FCLK: 500-1600 MHz) on this APU are under the SMU's
automatic power management (`power_dpm_force_performance_level=auto`), with the host on the `balanced` power
profile. With package power pinned near 22 W, an SMU picking a different FCLK/MCLK level for each long trial would
produce exactly this: the same core clock, the same instructions, and memory throughput in two or three discrete
steps (trials cluster at about 1455 s, 2160 s and 3030 s). The driver doesn't mark the active FCLK/MCLK level, and
this kernel exposes no data-fabric or memory-controller PMU (`amd_df`/`amd_umc`), so this isn't confirmed.

Earlier memory-bound runs show smaller versions of the same thing: `777.zstd_r` trial 542 (uniformly 29% slow at
low temperature and power) and the old host's 7.8-hour `782.lbm_r` drift
([`mining_results.782.lbm_r.2026-08-21.md`](mining_results.782.lbm_r.2026-08-21.md)). lbm, the most
bandwidth-bound benchmark in the suite, shows it most.

## Consequences for the stopped mine

- **`-march=native`'s screening 6.33 was the fast memory state, not the flag.** It took the same cycles as the fast
  `-O3` warm-up (67.5T each); it only retired fewer instructions.
- **The baseline CI ([4.15, 4.26] reps) was tight only because all three reps fell in the middle state.** Any
  verdict against it is a coin toss on which state a candidate's reps landed in.
- No knowledge rows from experiment 151 should be trusted. Only `-fprefetch-loop-arrays` reached a verdict
  (reject), so the `memory-bound` row for that flag picked up one bad sample.

## Follow-up measurements (2026-10-23)

Code at `93a3482`. Twelve single-iteration `cfm measure 782.lbm_r --flags=-O3` runs, experiments 152-163,
11:22Z-18:14Z: six under `balanced`, then six under `performance`. Each run was bracketed by a 30-second,
16-thread triad probe (fresh 1.6 GB allocation), with a 30-second sampler logging package power, CPU temperature
and average core clock (`results/logs/lbmswing.782.lbm_r.2026-10-23.*`). The script restored `balanced` at the
end. Every run exited 0.

| Profile | Rep | Probe before (GB/s) | lbm ratio | Minutes | Probe after (GB/s) | Package power (W) | CPU temp mean / max (°C) | Core clock (MHz) |
|---|---|---|---|---|---|---|---|---|
| balanced | 1 | 40.8 | **6.33** | 24 | 22.5 | 17.8 | 60.9 / 70.8 | 2956 |
| balanced | 2 | 22.5 | **6.34** | 24 | 22.5 | 18.0 | 63.4 / 72.4 | 2923 |
| balanced | 3 | 22.5 | 4.24 | 36 | 40.5 | 14.9 | 57.6 / 72.5 | 3004 |
| balanced | 4 | 36.2 | 5.49 | 28 | 23.0 | 16.5 | 60.2 / 78.1 | 2985 |
| balanced | 5 | 32.3 | **6.34** | 24 | 22.5 | 17.8 | 62.5 / 64.5 | 2993 |
| balanced | 6 | 22.5 | 4.16 | 36 | 45.4 | 14.8 | 57.7 / 59.9 | 2982 |
| performance | 1 | 45.5 | **6.33** | 24 | 22.5 | 40.6 | 90.3 / 92.6 | 4167 |
| performance | 2 | 22.5 | 3.03 | 50 | 45.5 | 34.7 | 80.2 / 96.9 | 4188 |
| performance | 3 | 45.5 | **6.33** | 24 | 22.4 | 39.3 | 89.9 / 92.1 | 4128 |
| performance | 4 | 22.5 | 3.02 | 50 | 45.5 | 34.5 | 80.6 / 96.5 | 4175 |
| performance | 5 | 45.4 | 3.46 | 44 | 30.9 | 35.4 | 82.2 / 83.6 | 4185 |
| performance | 6 | 29.7 | **6.30** | 24 | 22.5 | 39.9 | 91.0 / 97.2 | 4182 |

- **lbm's ceiling is 6.33, and it's very repeatable.** Half the runs (6 of 12) landed at 6.30-6.34. The rest were
  slower by up to 2.1x (3.02), with values in between (3.46, 4.16, 4.24, 5.49).
- **The power profile doesn't matter.** `performance` raised the core clock from about 2.95 to 4.18 GHz and
  package power from about 17 to 38 W, and left the ceiling and the slow levels where they were. lbm is limited
  by memory alone.
- **Memory bandwidth comes in two states, about 45 and about 22.5 GB/s,** with a few probes in between. The state
  usually flips between consecutive runs: after a fast lbm run the next probe reads 22.5, and after a slow run it
  reads about 45. Under `performance`, runs 1-4 alternated exactly, fast, slow, fast, slow. The state also held
  through the roughly one-minute gap between the "after" probe and the next "before" probe.
- **The probe before a run predicts it only loosely.** Three of the four runs starting at 40 GB/s or more were fast;
  the fourth (`performance` 5, 45.4 GB/s) read 3.46. A run starting at 22.5 was slow four times out of five (`balanced` 2 was
  fast).

### Page placement ruled out

After reading the SMBIOS memory map (`dmidecode` is setuid here), page placement looked like the best
explanation. The host has two matched 32 GB DDR5-5600 SO-DIMMs (Samsung M425R4GA3EB0-CWMOL, dual-rank), one per
channel, and SMBIOS maps channel A to 0-32 GB and channel B to 32-64 GB, with interleave "Unknown". That suggested
a buffer on one channel would get half the bandwidth. Three in-process tests, run on an idle host after the lbm
runs:

1. **16 separate 1 GB buffers, measured back to back.** Right after the last lbm run, all 16 read 19.8-21.2 GB/s;
   a few minutes later, a fresh run of the same program read 40.0-44.9 for all 16. Each time the buffers agreed
   with each other, so they didn't fall into fast and slow groups.
2. **12 buffers, every pair run at once** (8 threads each). Every single buffer reached 39-46 GB/s alone, and
   pairs didn't add up (29.8-43.7 combined). So about 45 GB/s is the whole system's ceiling, and any one buffer
   can reach it. That doesn't fit a layout where a buffer lives on one channel.
3. **A long-lived buffer against fresh ones, under load.** One 1 GB buffer kept the same pages for 10 minutes and
   was measured every 18 seconds: 6 minutes of a 16-thread triad load on a separate 6 GB working set, then
   5 minutes idle, each time next to a freshly allocated 1 GB buffer. The load's own bandwidth sagged from 42 to
   about 33 GB/s within a minute. The long-lived buffer moved with it, 25-39 GB/s during the load, and came back
   to 36-45 when idle, in step with the fresh buffers. Its pages never changed, so **the slow state is
   system-wide and time-dependent**, not tied to which pages a buffer got. The SMBIOS split by channel is most
   likely just how this BIOS reports the layout.

### What it is, so far

A system-wide memory throttle with two main levels, about 45 and about 22.5 GB/s, independent of the core power
profile. It often flips around run boundaries, and sustained bandwidth load brings it on partly. That fits a
memory-side thermal or power limit, such as DIMM or memory-controller thermal throttling in a small enclosure
(ASUS PN54, BIOS KRKPNSTD.0021, 2025-03-20). But a 24-minute run staying at the exact ceiling and flipping right
at its end isn't an obvious thermal shape, so this is a lead, not a conclusion. The DIMMs' own temperature sensors
would test it. The `spd5118` driver is installed but not loaded, and loading it needs root.

### What this means for mining

- Memory-bound fprate results on this host aren't trustworthy yet. With a tight baseline CI, any rep that lands in
  the slow state reads as a big regression, and a fast rep against a slow baseline reads as a big win.
- Compute-bound benchmarks are probably safe. The intrate mines mostly showed run-to-run noise within about 1%;
  `777.zstd_r` trial 542 (uniformly 29% slow) may have been this.
- **A cheap guard while the cause is open:** run the 30-second triad probe before each trial and wait until it
  reads above, say, 40 GB/s. That won't catch a flip partway through a run, but here a fast start meant a fast run
  in three of four cases.

## Module temperatures and recovery time (2026-10-23)

**DIMM temperatures can't be read on this board.** With `spd5118` loaded, the SPD hubs were instantiated by
hand at every SPD address (0x50-0x57) on all three PIIX4 SMBus ports (`i2c-2`/`3`/`4`), and the driver bound
to none of them. On AMD mobile platforms the SMU typically owns the SPD bus after boot. The only temperatures
the OS sees are CPU Tctl, the ACPI zone and the GPU edge sensor, so the two temperature-logged lbm runs weren't
possible.

**Recovery time.** One single-iteration `-O3` run (experiment 164, 18:44Z-19:13Z, ratio 5.29, so partly slow),
then a short 50-rep probe (a few seconds of load) right after the run and every 30 seconds:

| Time after the run | Probe | Tctl |
|---|---|---|
| +4 s | 22.6 GB/s | 66.1°C |
| +32 s | 45.4 GB/s | 53.8°C |
| +64 s | 45.7 GB/s | 50.6°C |
| +96 s | 45.6 GB/s | 49.2°C |

- **Bandwidth comes back within half a minute of idling.** So the slow state needs ongoing load to persist.
- **That explains the earlier "flips between runs" pattern.** In the 12-run check, each 30-second "after" probe
  ran straight into the next 30-second "before" probe and then the next build, with no idle gap in between. Those
  probes were measuring the tail of the previous run's slow state, not a separate state that only changes at run
  boundaries. The one run with 60 seconds of idle before it (`balanced` 1) started fast.
- **But the state also changes during a run.** This run's 5.29, and the earlier 3.46-5.49 values, are a mix
  of fast and slow time within one 24-50 minute run. Idling before a trial only fixes the start.

So the throttle comes on under sustained memory load, at an unpredictable point (sometimes not for a whole
24-minute run, sometimes within a minute), and lets go within about 30 seconds of idle. That fits a
memory-side thermal or power limit with a fast cool-down better than anything else seen so far. It's still
unconfirmed, since the module temperatures can't be read.

## Next steps

1. ~~**DIMM temperatures**~~: not readable on this board (above).
2. ~~**BIOS memory settings**~~: the PN54's BIOS only offers memory frequency, with no power-down, thermal
   throttling or interleaving options (checked 2026-10-23).
4. **Airflow test:** a desk fan blowing on the case (or across the SO-DIMM side), then a few
   single-iteration lbm runs with probes. If every run lands at about 6.33, the throttle is thermal.
   This is the cheapest direct test left, and needs no reboot.
5. **Lower memory frequency** (BIOS, DDR5-5600 → 4800): less heat and power in the memory subsystem. If
   that stops the throttle, the ceiling drops by up to about 14% but becomes repeatable; measure a few lbm
   runs at each setting before deciding.
6. **Pipeline workaround, whatever the cause:** for memory-bound benchmarks, idle 60 seconds and probe
   bandwidth before each trial, record the probe with the trial, and re-run any trial whose ratio sits far
   below its siblings (the fast state is repeatable to within 1%, so slow reps stand out). That makes
   measurements usable without fixing the host, at the cost of extra trials.
3. ~~**Recovery time**~~: done above, under 30 seconds of idle.

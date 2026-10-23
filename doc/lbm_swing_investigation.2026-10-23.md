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

## The likely cause

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

## Next step

A monitored check: interleave `cfm measure 782.lbm_r --flags="-O3 ..."` runs with a 30-second triad probe just
before and after each, under `balanced` and then under the `performance` profile. If the probe's bandwidth
predicts each lbm ratio, the memory clock is confirmed; if `performance` pins it, that's the fix for mining
fprate here.

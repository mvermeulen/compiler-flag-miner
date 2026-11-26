# `cfm mine` results: 811.tealeaf_s on `niwot`, 2026-11-25

The tenth fpspeed benchmark mined on `niwot` (see [`host_niwot.md`](host_niwot.md)). `811.tealeaf_s` is TeaLeaf, a C
mini-app that solves the linear heat-conduction equation with an iterative sparse solver, parallelized with OpenMP.
`chicago` mined it on 2026-11-10 ([write-up](mining_results.811.tealeaf_s.2026-11-10.md)) and accepted nothing. Its
corpus shape is memory-bound at 70.7%.

## Headline result

**The throttle stop fired after Phase 1; no candidate was measured.** Recorded as 0.0%, matching `chicago`'s clean
reject (every candidate within ±0.16% of `-O3` there).

- **The same `-O3` binary ran on three levels, and package power tracked them exactly.** Nine reps of one build
  (code fingerprint `02845cc0`) read about 0.46-0.47 at 17 W, 0.49-0.50 at 17-18 W, and 0.55 at 19 W, a 20% spread.
  This is the memory throttle (#26) that lbm_r, fotonik3d_r and roms_r showed here, and the first fpspeed mine to hit it.
- **The bandwidth gate saw nothing.** Its probe read 43.6-46.0 GB/s before every run, the slow ones included, so the
  throttle set in during the timed runs, after the probe.
- **The rerun rules couldn't settle it.** Three reruns (two slow-rep, one spread-rule) replaced slow reps, and two of
  the three replacements landed slow again. Four of nine reps read more than 10% below the fastest, so the throttle
  stop (PR #72) ended the mine with no knowledge rows written, as designed.
- **Nothing here is lost.** `chicago` found every flag flat on this benchmark, which fits a sparse solver that
  streams matrix data through memory. A clean `niwot` measurement would need the throttle fixed or worked around
  (#26, #37c), not another mine.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c cores, 16 threads), 64 GB RAM |
| Command | `cfm mine 811.tealeaf_s --settle-seconds 600` (uncapped, from the fpspeed queue) |
| Code | `main` at `3cc23bf` (no code changes since PR #72) |
| SPEC config | `ryzen350_64gb.gcc_O3.cfg`: `threads = 16` |
| Thread placement | OpenMP: `OMP_PLACES=threads OMP_PROC_BIND=close` |
| Experiment id | 212 |
| Started / finished | 2026-11-25T08:59:32Z / 2026-11-25T13:20:24Z (4h21m) |
| Final status | `failed` (throttle stop) |
| Trials | 9 (2889-2897), all `-O3`: 3 warm-up, 3 calibration, 3 reruns |
| Excluded on shape (Phase 2) | not reached |
| Winning flags | `["-O3"]`, recorded 0.0% |
| Guards | **throttle stop** (4 of 9 reps more than 10% below the fastest); bandwidth gate waited 30 s before the first run only (43.6-46.0 GB/s); two slow-rep reruns and one spread-rule rerun |
| Power | package power median 17.0-19.0 W, tracking the ratio |

A timed run took about 17 minutes at 0.55 and 20 minutes at 0.46, plus the 600-second settle. Every timed run's
`.rsf` reads `valid: S` for tealeaf.

## Baseline

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 2889 | warm-up | 0.46651 | 17.1 W |
| 2890 | warm-up | 0.50002 | 18.0 W |
| 2891 | warm-up | 0.50064 | 18.0 W |
| 2892 | calibration | 0.49985 | 18.0 W (replaced by 2896, spread rule) |
| 2893 | calibration | 0.45880 | 17.0 W (replaced by 2895, slow-rep) |
| 2894 | calibration | 0.55208 | 19.0 W |
| 2895 | rerun | 0.55095 | 19.0 W |
| 2896 | rerun | 0.46761 | 17.1 W (replaced by 2897, slow-rep) |
| 2897 | rerun | 0.49157 | 17.1 W |

Warm-up settled after 3 reps (5294 s), on the 18 W level. The calibration reps then moved to 17 W and 19 W, and the
spread rule replaced the 18 W rep because the other two (2894, 2895, both at 19 W) agreed within 0.21%. The three reps
the mine ended with (0.552, 0.551, 0.492) average 0.5315; that's the base recorded in `host_niwot.md`, though it
mixes two levels.

## Compared with `chicago`

| | `chicago` (2026-11-10) | `niwot` |
|---|---|---|
| Baseline | 1.4308, 85 W | 0.46-0.55 on three levels, 17-19 W |
| Result | nothing accepted, every flag within ±0.16% | throttle stop after Phase 1 |
| Run | 31 trials, 7h39m | 9 trials, 4h21m |

`chicago` reads 2.6-3.1 times this host's ratio here, against about 1.9 times on the compute-heavier fpspeed
benchmarks (cactus_s 1.94). That's about its bandwidth advantage (about 102 GB/s against
45 GB/s), as expected for a code that does little but stream memory. Use `chicago`'s result for tealeaf_s.

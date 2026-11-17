# `cfm mine` results: 765.roms_r on `niwot`, 2026-11-15

`765.roms_r` is the Regional Ocean Modeling System, a Fortran ocean-circulation code, 16 copies under SPECrate. It is
the last of the three fprate benchmarks held back on `niwot` after `782.lbm_r` hit this host's memory-side throttle
(#26), mined on the user's request after `709.cactus_r` (clean) and `749.fotonik3d_r` (throttled). It ran with
`--settle-seconds 600` and the shape filter on. `chicago` mined it on 2026-11-05
([write-up](mining_results.765.roms_r.2026-11-05.md)).

## Headline result

**`-O3`, nothing accepted (0.0%).** The throttle hit roms like fotonik3d, and the mine could resolve nothing smaller
than its own ±18% baseline CI.

- **One `-O3` binary (`211dae19`, 9 runs) read on three levels that track package power:** about 12.2 at 18 W, 13.06
  at 19 W, 14.89 at 20 W, plus 11.81 on the recheck. Every pre-run bandwidth probe passed (43.7-45.8 GB/s), as on
  lbm and fotonik3d.
- **The baseline's kept reps straddle two levels** (13.07, 14.89, 14.89), so its 95% CI is [11.67, 16.89], ±18%.
  Every flagset's CI overlapped it; no verdict could have been an accept short of a 20% gain.
- **The recheck read 11.81, -17.3%, and was not flagged**, because 11.81 is inside that CI. On fotonik3d (±3%) the
  same check caught a +12.8% offset. A wide enough baseline blinds the recheck too.
- **`-march=native` probably helps, by a few percent, but the mine couldn't show it.** `-march=native` and
  `-march=znver5` built the same code (`978059ad`) and got +1.01% and +4.67%, both rejected on CI overlap. That binary's
  top level (14.96-15.74) is above `-O3`'s (14.89), and it drew about 1 W less than `-O3` on each level. `chicago` measured +7.19%,
  every rep clear.
- **No false accept this time.** `-mtune=znver5`, fotonik3d's false accept, read 14.85-14.89 at 20 W, level with
  `-O3`'s 14.89, and its kept reps spread across levels, so it was rejected (+0.62%).
- **22 reruns in 57 trials**, the 3-per-flagset cap hit on 7 of 9 flagsets. 39h44m, the longest mine on record here.
- **`-march=native`'s memory-bound record is now 12 of 24**, exactly half, so it no longer fast-tracks (M4 needs a
  strict majority). Two of the 24 are this run's and fotonik3d's throttled rejects.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 765.roms_r --settle-seconds 600` (uncapped, 10 min idle after fotonik3d) |
| Code | `main` at `748e519` |
| Experiment id | 202 |
| Started / finished | 2026-11-15T08:32:15Z / 2026-11-17T00:16:35Z (39h44m, about 9.3 h of it settle) |
| Final status | `converged` |
| Trials | 57 (2387-2443), 1 skipped as unchanged code, 22 reruns (21 slow-rep, 1 low-power) |
| Candidates screened / confirmed | 5 / 4 (none accepted), plus `-march=native` fast-tracked (rejected) |
| Fast-tracked (M4) | `-march=native` (12 of 23 accepted in the memory-bound cluster, mean +24.95%) |
| Excluded on shape | 8: `-Ofast`, `-ffast-math`, `-funroll-loops`, and five frontend-tagged flags (`-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops`), on a 95.0% memory-bound read |
| Kept despite shape | `-flto`. `-fno-math-errno` isn't a Fortran candidate |
| Skipped as unchanged code (#58) | `-frecursive` (same code as `-O3`, as on `chicago`) |
| Winning flags | `["-O3"]`, 0.0% |
| Guards | bandwidth gate waited once (30 s, trial 2387); 21 slow-rep reruns and 1 low-power rerun (trial 2414, 18.10 W against 20.07 W); baseline recheck -17.34%, **not flagged** (inside the ±18% CI) |
| Power / temperature | package power median 17.05-20.09 W, on levels about 1 W apart; CPU 90.0-97.1 °C; bandwidth probes 43.7-45.8 GB/s |
| Audit | clean |

Each trial took 37-52 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 2387 | warm-up | 12.174 | 18.05 W |
| 2388 | warm-up | 12.188 | 18.05 W |
| 2389 | calibration (slow, rerun) | 13.046 | 19.02 W |
| 2390 | calibration | 13.071 | 19.02 W |
| 2391 | calibration (spread rule, rerun) | 12.195 | 18.05 W |
| 2392 | rerun of 2391 (spread rule, rerun) | 12.235 | 18.05 W |
| 2393 | rerun of 2392 | 14.886 | 20.07 W |
| 2394 | rerun of 2389 | 14.893 | 20.07 W |
| 2428 | recheck after Phase 4 | 11.807 (-17.34%, not flagged) | 18.02 W |

Warm-up settled after the minimum 2 reps (5,434 s), only because both landed on the 18 W level. The spread rule
replaced the 18 W reps against the two 19 W ones; then the slow-rep rule replaced a 19 W rep against the new 20 W
one, leaving one 19 W rep and two 20 W reps. Calibration mean **14.283**, 95% CI **[11.674, 16.893]** (±18.3%).

**Shape: `memory-bound`, 95.0%**, `vectorization_density=high`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`), the same read as `chicago`'s.

## Phase 3 screening (vs. most recent calibration rep, 14.886)

| Flags | Ratio | Power | Delta | Result |
|---|---|---|---|---|
| `-fprefetch-loop-arrays` | 14.620 | 20.06 W | -1.79% | survived |
| `-fgraphite-identity` | 14.734 | 20.05 W | -1.02% | survived |
| `-fstack-arrays` | 14.648 | 20.06 W | -1.60% | survived |
| `-flto` | 14.622 | 20.04 W | -1.77% | survived |
| `-frecursive` | — | — | — | skipped, same code as `-O3` |

All four screening runs happened to land on the 20 W level, the same as the reference rep, so this is the one
level-matched comparison the mine made, and it agrees with `chicago`: nothing within 2% of `-O3` either way.

## Phase 4 confirmation (vs. baseline CI [11.674, 16.893])

Every run in order, replaced ones struck.

| Flags | Runs (power) | Kept mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-fprefetch-loop-arrays` | ~~12.980~~, 14.424 (20 W), ~~11.958~~, ~~11.905~~, 13.003 (19 W), 14.943 (20 W) | 14.123 | [11.628, 16.618] | -1.12% | reject |
| `-fgraphite-identity` | 14.244 (20 W), ~~12.723~~, ~~12.729~~, ~~12.860~~, 14.877 (20 W), 14.205 (20 W) | 14.442 | [13.505, 15.379] | +1.11% | reject |
| `-fstack-arrays` | 12.751 (19 W), 13.946 (20 W), ~~12.624~~ (low power), 12.839 (19 W) | 13.179 | [11.524, 14.833] | -7.73% | reject |
| `-flto` | 14.170 (20 W), ~~11.946~~, ~~12.065~~, ~~12.718~~, 14.561 (20 W), 12.781 (18 W) | 13.837 | [11.513, 16.161] | -3.12% | reject |
| `-march=native` (fast-tracked) | 14.962 (18 W), 13.306 (17 W), ~~12.744~~, ~~12.764~~, ~~12.752~~, 15.014 (18 W) | 14.427 | [12.014, 16.841] | +1.01% | reject |

`-fgraphite-identity`'s kept reps all sit on the 20 W level, so its +1.11% compares one level against a two-level
baseline; at 20 W it read 14.21-14.88 against `-O3`'s 14.89, no gain. Nothing was accepted, so Phase 5 kept `-O3`.

## Phase 6 multipliers (on `-O3`, 14.283)

| Stage | Flags | Runs (power) | Kept mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 14.434 (20 W), ~~12.794~~, 13.636 (19 W), ~~11.527~~, ~~11.213~~, 13.833 (19 W) | 13.968 | [12.935, 15.000] | -2.21% | reject |
| PGO near-miss | — | | | | | none |
| Microarch | `+ -march=znver5` | 14.706 (18 W), 15.738 (19 W), 14.409 (18 W) | 14.951 | [13.218, 16.684] | +4.67% | reject |
| Microarch | `+ -mtune=znver5` | 14.891 (20 W), ~~13.545~~, ~~11.452~~, 14.848 (20 W), ~~13.443~~, 13.377 (19 W) | 14.372 | [12.231, 16.513] | +0.62% | reject |
| Vector width | — | | | | | skipped: no `-march=` in the winning set |

The six PGO builds shared one fingerprint (`4f656d62`), so their 11.21-14.43 spread is the throttle (#32).
`-march=znver5` ran no reruns: its three runs happened to sit within 9% of each other.

## Reading the runs by level

Package power sorts one binary's runs cleanly, but different code draws different power on the same throttle level
(`-march=native`'s binary draws about 1 W less than `-O3`'s), so comparing across binaries by power is only rough.

| Binary | 17 W | 18 W | 19 W | 20 W |
|---|---|---|---|---|
| `-O3` (`211dae19`, 9 runs) | — | 11.81-12.24 (5) | 13.05, 13.07 | 14.89, 14.89 |
| `-march=native` = `-march=znver5` (`978059ad`, 9 runs) | 12.74-13.31 (4) | 14.41-15.01 (4) | 15.74 | — |
| `-fprefetch-loop-arrays` (7) | — | 11.90, 11.96 | 12.98, 13.00 | 14.42-14.94 (3) |
| `-fgraphite-identity` (7) | — | 12.72, 12.73 | 12.86 | 14.21-14.88 (4) |
| `-fstack-arrays` (5) | — | 12.62 | 12.75, 12.84 | 13.95, 14.65 |
| `-flto` (7) | — | 11.95-12.78 (4) | — | 14.17-14.62 (3) |
| PGO (6) | 11.21, 11.53 | 12.79 | 13.64, 13.83 | 14.43 |
| `-mtune=znver5` (6) | — | 11.45 | 13.38-13.55 (3) | 14.85, 14.89 |

At 20 W, the level where most flagsets have runs, every flag sits at or below `-O3`'s 14.89: `-mtune=znver5` level,
prefetch about -1.5%, graphite about -2.5%, `-flto` and PGO about -3%, `-fstack-arrays` about -4%. Those match `chicago`'s
picture (all within ±0.7% except a PGO-on-`-march=native` that was +0.77%) in sign, roughly. The `-march=native`
binary's top two levels (14.41-15.74) sit above `-O3`'s top level, which fits `chicago`'s +7.19% in direction.

## Comparison with `chicago`

| | `chicago` (2026-11-05) | `niwot` |
|---|---|---|
| `-O3` ratio | 36.618 | 14.283 (two-level mean; 11.8-14.9 overall) |
| Winning flags | `-O3 -march=native` | `-O3` |
| Gain | +7.19% | 0.0% |
| `-march=native` | +7.19% (fast-tracked, accepted) | +1.01% (fast-tracked, rejected); same code as `-march=znver5`, +4.67%, rejected |
| `-fprefetch-loop-arrays` / `-flto` / `-fgraphite-identity` / `-fstack-arrays` | +0.63% / +0.09% / -0.19% / -0.31% | -1.12% / -3.12% / +1.11% / -7.73%, all rejected |
| PGO | +0.77% on top of `-march=native`, rejected | -2.21% on `-O3`, rejected |
| `=256` | -4.04% on top of `-march=native` | not tried |
| Baseline CI / recheck | ±0.27% / +0.16% | ±18.3% / -17.34% (not flagged) |
| Reruns | none | 22 |
| Power | 85 W every trial | 17-20 W on four levels |
| Wall-clock | 13h23m (no settle) | 39h44m (10-minute settle) |

`chicago`'s `-O3` ratio is 2.46× `niwot`'s 20 W level.

## What this means

The held-back split is now settled across all three: cactus (45-50 W) mined clean, fotonik3d (15-17 W) and roms
(17-20 W) throttled like lbm. A low package power on a 16-copy fprate run is the sign a benchmark spends the run
waiting on memory, and on `niwot` those benchmarks throttle mid-run whatever the settle or the pre-run probe show.
Both throttled mines gave the wrong answer about `-march=native`, a real +5-7% win on `chicago`: rejected twice each.
fotonik3d also produced a false accept. These three should be mined on `chicago` only; `niwot`'s numbers for them
are recorded as 0.0%.

Two additions for #37: the baseline recheck can't flag an offset when the baseline CI is itself as wide as the
offset (here ±18%), and the knowledge table now carries two throttled `-march=native` rejects (and two `-march=znver5` ones, same code) from
these two benchmarks, enough to drop `-march=native` below the fast-track majority for the memory-bound cluster.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprefetch-loop-arrays` | 25 | 4 | +1.79% |
| `-march=native` | 24 | 12 | +23.95% |
| `-fgraphite-identity` | 20 | 2 | +1.98% |
| `-fprofile-use` | 19 | 2 | -3.68% |
| `-flto` | 17 | 5 | +3.54% |
| `-march=znver5` | 12 | 2 | +0.54% |
| `-mtune=znver5` | 12 | 1 | +1.24% |
| `-fstack-arrays` | 2 | 0 | -5.12% |

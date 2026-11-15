# `cfm mine` results: 749.fotonik3d_r on `niwot`, 2026-11-14

`749.fotonik3d_r` is a finite-difference time-domain electromagnetics code (Fortran), 16 copies under SPECrate. It is
the second of the three fprate benchmarks held back on `niwot` after `782.lbm_r` hit this host's memory-side throttle
(#26), mined anyway on the user's request after `709.cactus_r` ran clean. It ran with `--settle-seconds 600` and the
shape filter on. `chicago` mined it on 2026-11-05 ([write-up](mining_results.749.fotonik3d_r.2026-11-05.md)).

## Headline result

**The mine reported `-O3 -mtune=znver5`, +9.92% over plain `-O3` (14.078 → 15.475). That accept is almost certainly
false: the throttle, not the flag.**

- **The throttle hit fotonik3d the way it hit lbm.** The same `-O3` binary (one fingerprint, `c7909d50`, all 12 runs)
  read on three levels that track package power: about 12.0-12.6 at 15 W, 14.0-14.3 at 16 W, 15.87 at 17 W. Every
  pre-run bandwidth probe passed (43.6-45.6 GB/s); the throttle sets in during the run, as on lbm.
- **`-mtune=znver5` was accepted because its kept reps landed on the fast level and the baseline's on the middle
  one.** Three of its four runs drew 17 W and read 15.19-15.84; the baseline's three kept calibration reps drew 16 W
  and read 13.96-14.27. At 17 W, `-O3` itself read 15.875 and 15.874 (trials 2343 and 2370), above every
  `-mtune=znver5` rep. The baseline recheck after Phase 4 (trial 2370) read +12.76% and was flagged, which is the
  mine's own warning that its deltas were offset. This is #37 (b): no rerun rule fires when a flagset's reps all sit
  on one level.
- **`-march=native` probably helps a little, but the mine couldn't show it.** `-march=native` and `-march=znver5` built
  the same code (`e4096f14`, 12 runs between them). That binary read 13.27-13.92 at 15 W, where `-O3` read
  11.97-12.58, and its best runs (16.38, 16.11) beat every `-O3` run. Over all 12 runs each, its median is 3.9% above
  `-O3`'s. Both were rejected on CI overlap (+5.55% and +11.40%). `chicago` measured +5.43% for it, every rep clear.
- **Three of five screened candidates were pruned on throttled runs.** `-fgraphite-identity`, `-fstack-arrays` and
  `-flto` each got one screening run at 15-16 W reading 12.58-12.66, about 10% below the last calibration rep, past
  the 5% prune bar. Those reads are inside `-O3`'s own slow level, so they say nothing about the flags. `chicago` had
  all three within 0.4% of `-O3` except `-flto` (-2.38%).
- **PGO lost about 2.5%** (13.730, rejected), in line with `chicago`'s -4.53%; its runs spread over the same levels.
- **Recorded in [`host_niwot.md`](host_niwot.md) as 0.0%, not +9.92%**, like lbm: the reported winner isn't
  trustworthy, and the knowledge table now carries `-mtune=znver5`'s false accept (1 of 11).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 749.fotonik3d_r --settle-seconds 600` (uncapped, 10 min idle after cactus) |
| Code | `main` at `758c9a6` |
| Experiment id | 201 |
| Started / finished | 2026-11-14T08:26:13Z / 2026-11-15T08:22:15Z (23h56m, about 7.3 h of it settle) |
| Final status | `converged` |
| Trials | 45 (2342-2386), 1 skipped as unchanged code, 15 slow-rep reruns |
| Candidates screened / confirmed | 5 / 1 (`-fprefetch-loop-arrays`), plus `-march=native` fast-tracked |
| Fast-tracked (M4) | `-march=native` (12 of 22 accepted in the memory-bound cluster, mean +25.83%) |
| Excluded on shape | 8: `-Ofast`, `-ffast-math`, `-funroll-loops`, and five frontend-tagged flags (`-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops`), on a 97.3% memory-bound read |
| Kept despite shape | `-flto` (`SHAPE_EXEMPT_FLAGS`). `-fno-math-errno` isn't a candidate for Fortran, so PR #71's exemption didn't apply |
| Skipped as unchanged code (#58) | `-frecursive` (same code as `-O3`, as on `chicago`) |
| Winning flags (reported) | `["-O3", "-mtune=znver5"]`, +9.92%; not trusted, see above |
| Guards | bandwidth gate waited once (30 s, trial 2342); 15 slow-rep reruns, the 3-per-flagset cap hit on 4 flagsets; no spread or low-power reruns; baseline recheck **flagged** (+12.76%) |
| Power / temperature | package power median 15.05-17.08 W on three levels (15, 16, 17 W), whatever the flags; CPU 88.4-94.8 °C; bandwidth probes 43.6-45.6 GB/s |
| Audit | clean |

Each trial took 30-36 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio | Power |
|---|---|---|---|
| 2342 | warm-up | 11.966 | 15.06 W |
| 2343 | warm-up | 15.875 | 17.08 W |
| 2344 | warm-up | 14.008 | 16.06 W |
| 2345 | warm-up | 12.062 | 15.06 W |
| 2346 | warm-up | 14.078 | 16.07 W |
| 2347 | warm-up | 14.088 | 16.07 W |
| 2348 | calibration (slow, rerun) | 12.032 | 15.06 W |
| 2349 | calibration | 14.274 | 16.08 W |
| 2350 | calibration | 13.997 | 16.06 W |
| 2351 | rerun of 2348 (slow, rerun) | 12.577 | 15.08 W |
| 2352 | rerun of 2351 | 13.962 | 16.06 W |
| 2370 | recheck after Phase 4 | 15.874 (+12.76%, **flagged**) | 17.07 W |

Warm-up settled after 6 reps (11,933 s), only because two runs in a row landed on the 16 W level. Calibration mean
**14.078**, 95% CI **[13.653, 14.503]** (±3.0%), all three kept reps on the 16 W level. The slow-rep rule did its job
here, twice replacing a 15 W rep, but that also means the CI describes one level, not the benchmark.

**Shape: `memory-bound`, 97.3%**, `vectorization_density=high`, `allocation_pressure=low`, from the corpus
(`reference-matrix:amd-370-64gb`), the same read as `chicago`'s and the most memory-bound on record.

## Phase 3 screening (vs. most recent calibration rep, 13.997)

| Flags | Ratio | Power | Delta | Result |
|---|---|---|---|---|
| `-fprefetch-loop-arrays` | 14.540 | 17.01 W | +3.88% | survived |
| `-fgraphite-identity` | 12.578 | 15.09 W | -10.14% | pruned |
| `-fstack-arrays` | 12.664 | 15.10 W | -9.53% | pruned |
| `-flto` | 12.637 | 16.02 W | -9.72% | pruned |
| `-frecursive` | — | — | — | skipped, same code as `-O3` |

A screening run is one run, so whichever level it lands on decides it. Two of the three prunes drew 15 W, `-O3`'s
slow level.

## Phase 4 confirmation (vs. baseline CI [13.653, 14.503])

Kept reps after the slow-rep rule; every run listed in order, with the replaced ones struck.

| Flags | Runs (power) | Kept mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` (fast-tracked) | 15.555 (16 W), ~~13.265~~, ~~13.920~~, ~~13.348~~, 15.606 (16 W), 13.417 (15 W) | 14.860 | [11.756, 17.963] | +5.55% | reject (CI overlap) |
| `-fprefetch-loop-arrays` | ~~12.591~~, 15.822 (17 W), 13.181 (16 W), ~~13.161~~, ~~12.524~~, 15.818 (17 W) | 14.940 | [11.155, 18.725] | +6.13% | reject (CI overlap) |

Both hit the three-rerun cap with one slow rep still kept. `-fprefetch-loop-arrays`'s two fast reps are both at 17 W,
where `-O3` reads 15.87, so it shows nothing over `-O3` at the fast level either. Nothing was accepted, so Phase 5
kept `-O3`.

## Phase 6 multipliers (on `-O3`, 14.078)

| Stage | Flags | Runs (power) | Kept mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | ~~13.167~~, ~~12.645~~, 14.798 (17 W), ~~12.799~~, 13.506 (16 W), 12.886 (16 W) | 13.730 | [11.306, 16.154] | -2.47% | reject |
| PGO near-miss | — | | | | | none |
| Microarch | `+ -march=znver5` | 16.380 (16 W), ~~14.525~~, ~~13.892~~, ~~14.628~~, 16.110 (16 W), 14.560 (16 W) | 15.683 | [13.244, 18.123] | +11.40% | reject (CI overlap) |
| Microarch | `+ -mtune=znver5` | 15.390 (17 W), 15.192 (17 W), ~~13.778~~ (16 W), 15.842 (17 W) | 15.475 | [14.647, 16.302] | **+9.92%** | **accept** |
| Vector width | — | | | | | skipped: no `-march=` in the winning set |

`-march=znver5` is the same code as `-march=native` (`e4096f14`), so the mine measured that binary twice, 12 runs,
with verdicts of +5.55% and +11.40%, both rejected, while `-mtune=znver5`, a scheduling-only change, was accepted at
+9.92% on runs that happened to land on the 17 W level. The PGO builds all shared one fingerprint (`6dd7c381`), so
its spread is the throttle, not different training runs (#32).

## Reading the runs by level

Package power stands in for the throttle level. It isn't a clean control (different code can draw different power at
the same level), but within one binary it sorts the runs cleanly.

| Binary | 15 W | 16 W | 17 W | All runs, median |
|---|---|---|---|---|
| `-O3` (`c7909d50`, 12 runs) | 11.97, 12.06, 12.03, 12.58 | 13.96-14.27 (6) | 15.875, 15.874 | 14.003 |
| `-march=native` = `-march=znver5` (`e4096f14`, 12 runs) | 13.27, 13.35, 13.42, 13.89, 13.92 | 14.53-16.38 (7) | — | 14.543 (+3.9%) |
| `-mtune=znver5` (`7d8106ba`, 4 runs) | — | 13.78 | 15.19, 15.39, 15.84 | 15.291 |
| `-fprefetch-loop-arrays` (`003a891a`, 7 runs) | 12.52 | 12.59, 13.16, 13.18 | 14.54, 15.82, 15.82 | 13.181 |
| PGO (`6dd7c381`, 6 runs) | — | 12.65-13.51 (5) | 14.80 | 13.026 |

At 17 W, `-mtune=znver5` (mean 15.47) is 2.5% below `-O3` (15.87); at 16 W its one run (13.78) is 1.6% below `-O3`'s
level. Nothing here supports a gain. `-march=native` is above `-O3` on both levels it shares, by about 10% at 15 W,
which fits `chicago`'s +5.43% in direction if not in size.

## Comparison with `chicago`

| | `chicago` (2026-11-05) | `niwot` |
|---|---|---|
| `-O3` ratio | 38.726 | 14.078 (16 W level; 12.0-15.9 overall) |
| Winning flags | `-O3 -march=native -mprefer-vector-width=256` | reported `-O3 -mtune=znver5`; trusted: `-O3` |
| Gain | +7.04% | +9.92% reported, 0.0% recorded |
| `-march=native` | +5.43% (fast-tracked, accepted) | +5.55% (fast-tracked, rejected on CI overlap) |
| `-fprefetch-loop-arrays` / `-fstack-arrays` / `-fgraphite-identity` / `-flto` | -0.53% / -0.36% / -0.31% / -2.38% | +6.13% (rejected) / pruned / pruned / pruned, all on throttled runs |
| PGO | -4.53% on top of `-march=native` | -2.47% on `-O3` |
| Baseline CI / recheck | ±0.34% / -0.26% | ±3.0% / +12.76% (flagged) |
| Reruns | none | 15 |
| Power | 85 W every trial | 15-17 W on three levels |
| Wall-clock | 9h08m (no settle) | 23h56m (10-minute settle) |

`chicago`'s `-O3` ratio is 2.75× `niwot`'s 16 W level, against 2.08× on cactus. fotonik3d on `niwot` draws a third of
cactus's 45-50 W, the same pattern as lbm: the cores spend the run waiting on memory.

## What this means

fotonik3d is lbm-class on `niwot`: the 10-minute settle and the bandwidth gate don't stop a mid-run throttle, and the
rerun rules can't tell a flagset whose kept reps all sit on a higher level from a real gain. The one accept is that
case, and the one plausible real gain (`-march=native`) was rejected twice. cactus, at 45-50 W, never throttled;
whether a benchmark throttles here looks like a property of how bandwidth-bound it is, and roms, next, is the last
test of that.

Two things this run adds to #37: the level mismatch produces false *accepts*, not only false rejects (lbm's
`-march=znver5`), and #37 (a) would have pooled `-march=native` and `-march=znver5` into 12 runs of one binary
instead of two noisy verdicts. A power-matched comparison like the table above is what (b) or (c) would have to
automate; package power separates the levels cleanly for one binary here.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 23 | 12 | +24.95% |
| `-fprefetch-loop-arrays` | 24 | 4 | +1.91% |
| `-flto` | 16 | 5 | +3.96% |
| `-fgraphite-identity` | 19 | 2 | +2.02% |
| `-fprofile-use` | 18 | 2 | -3.76% |
| `-march=znver5` | 11 | 2 | +0.16% |
| `-mtune=znver5` | 11 | 1 (this run's, likely false) | +1.30% |

Screening prunes don't upsert the knowledge table, so `-flto`, `-fgraphite-identity` and `-fstack-arrays` are
unchanged.

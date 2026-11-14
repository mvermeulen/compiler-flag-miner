# `cfm mine` results: 709.cactus_r on `niwot`, 2026-11-14

`709.cactus_r` is a numerical-relativity code (the Cactus framework with the Einstein Toolkit's BSSN evolution), 16
copies under SPECrate. It was held back on `niwot` as one of the three most bandwidth-heavy fprate benchmarks, after
`782.lbm_r` hit this host's memory-side throttle; the user asked for it anyway after the `--no-shape-filter`
re-mines. It ran first of the three held-back mines, with `--settle-seconds 600` and the shape filter on (PR #71's
`-fno-math-errno` exemption in effect). `chicago` mined it on 2026-11-05
([write-up](mining_results.709.cactus_r.2026-11-05.md)).

## Headline result

**`-O3 -march=native`, +21.56% over plain `-O3`** (ratio 44.056 → 53.553).

- **No throttle.** Every rep of every flagset sat within 0.8% of its siblings, no rerun of any kind fired, the
  recheck read +0.35%, and every pre-run bandwidth probe passed (44.0-45.6 GB/s). The worry that held cactus back
  didn't show up.
- **`-march=native` is the whole story, as on `chicago`** (+16.51% there). It was fast-tracked on `niwot`'s own
  memory-bound record (11 of 21 accepted after the femflow re-mine), the first fast-track of it here since the
  strict-majority rule (2026-10-22). Its three reps (53.52-53.60)
  are 21% above every `-O3` rep.
- **Nothing else helped.** `-fprefetch-loop-arrays` +0.51%, `-flto` +0.29%, `-fgraphite-identity` +0.10%, all
  rejected. On top of `-march=native`, PGO was +0.45% and `-mprefer-vector-width=256` +0.07%, both rejected.
  `chicago` measured the same set within half a point of each.
- **`-fno-math-errno`, newly exempt from the shape filter, lost 1.43%** with a CI clear of baseline (three reps
  within 0.1 of each other, all below every `-O3` rep). This is the first real cost of PR #71's exemption: one
  screening run and three confirmation runs, about an hour, for a reject.
- **The shape filter excluded 10 of 15 candidates** on the corpus's 71.6% memory-bound read, fast-math and
  `-funroll-loops` among them. The three re-mines without the filter (#30) suggest those wouldn't add on top of
  `-march=native`, but cactus wasn't re-mined to check.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 709.cactus_r --settle-seconds 600` (uncapped, 10 min idle after the femflow re-mine) |
| Code | `main` at `b882964` (includes PR #71) |
| Experiment id | 200 |
| Started / finished | 2026-11-14T00:14:54Z / 2026-11-14T08:16:13Z (8h01m, about 5.2 h of it settle) |
| Final status | `converged` |
| Trials | 31 (2311-2341) |
| Candidates screened / confirmed | 4 / 4, plus `-march=native` fast-tracked |
| Fast-tracked (M4) | `-march=native` (11 of 21 accepted in the memory-bound cluster, mean +26.04%) |
| Excluded on shape | 10: `-Ofast`, `-ffast-math`, `-funroll-loops`, `-fipa-pta`, and the six frontend-tagged flags (`-fno-pie -no-pie`, `-fno-stack-protector`, `-fcf-protection=none`, `-U_FORTIFY_SOURCE`, `-fno-ipa-cp-clone`, `-fno-unswitch-loops`) |
| Kept despite shape | `-flto` and `-fno-math-errno` (`SHAPE_EXEMPT_FLAGS`) |
| Skipped as unchanged code (#58) | none possible: cactus stamps `__DATE__`/`__TIME__`, so every build has its own fingerprint |
| Winning flags | `["-O3", "-march=native"]`, +21.56% |
| Guards | bandwidth gate waited once (30 s, trial 2311); no slow-rep, spread or low-power reruns; baseline recheck not flagged (+0.35%) |
| Power / temperature | package power median 45-50 W, rising slowly through the run (45 W at the start, 50 W at the end) whatever the flags; CPU 98-100 °C; bandwidth probes 44.0-45.6 GB/s |
| Audit | clean |

Each trial took about 15-16 minutes, 10 of them the settle.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 2311 | warm-up | 44.123 |
| 2312 | warm-up | 43.839 |
| 2313 | calibration | 44.106 |
| 2314 | calibration | 43.932 |
| 2315 | calibration | 44.130 |
| 2335 | recheck after Phase 4 | 44.211 (+0.35%, not flagged) |

Calibration mean **44.056**, 95% CI **[43.788, 44.324]** (±0.61%). Warm-up settled after 2 reps (1913 s).

**Shape: `memory-bound`, 71.6%**, `vectorization_density=high`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`), the same read as `chicago`'s. `-mprefer-vector-width=256` was deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 44.130)

| Flags | Ratio | Delta |
|---|---|---|
| `-fprefetch-loop-arrays` | 44.386 | +0.58% |
| `-flto` | 43.863 | -0.61% |
| `-fgraphite-identity` | 43.664 | -1.05% |
| `-fno-math-errno` | 43.567 | -1.28% |

All four survived. `-march=native` skipped screening (fast-tracked).

## Phase 4 confirmation (3 reps each, vs. baseline CI [43.788, 44.324])

| Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` (fast-tracked) | 53.516, 53.544, 53.598 | 53.553 | [53.449, 53.657] | **+21.56%** | **accept** |
| `-fprefetch-loop-arrays` | 44.189, 44.515, 44.141 | 44.282 | [43.776, 44.787] | +0.51% | reject |
| `-flto` | 44.089, 44.083, 44.382 | 44.185 | [43.760, 44.610] | +0.29% | reject |
| `-fgraphite-identity` | 44.147, 44.012, 44.138 | 44.099 | [43.912, 44.286] | +0.10% | reject |
| `-fno-math-errno` | 43.381, 43.421, 43.478 | 43.427 | [43.306, 43.547] | **-1.43%** | reject (CI clear, below) |

## Phase 5 combination

Only `-march=native` was accepted, so Phase 5 kept `-O3 -march=native` (step 1 reused from Phase 4, no pairs).

## Phase 6 multipliers (on `-O3 -march=native`, 53.553)

| Stage | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 54.449, 53.311, 53.619 | 53.793 | [52.331, 55.255] | +0.45% | reject |
| PGO near-miss | — | | | | | none (no CI-clear Phase 4 reject above baseline) |
| Microarch | — | | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 53.503, 53.615, 53.657 | 53.592 | [53.394, 53.789] | +0.07% | reject |

PGO's reps spread 2.1% (53.31-54.45) against 0.15% for `-march=native`'s; with cactus's date stamp, fingerprints
can't show whether the three PGO builds were the same code (#32).

## Comparison with `chicago`

| | `chicago` (2026-11-05) | `niwot` |
|---|---|---|
| `-O3` ratio | 91.446 | 44.056 |
| Winning flags | `-O3 -march=native` | `-O3 -march=native` |
| Gain | +16.51% | +21.56% |
| Fast-tracked on | `782.lbm_r`'s prior (2 of 2) | `niwot`'s memory-bound record (11 of 21) |
| `-fprefetch-loop-arrays` / `-flto` / `-fgraphite-identity` | -0.15% / -0.08% / -0.44% | +0.51% / +0.29% / +0.10% |
| `-fno-math-errno` | excluded on shape | -1.43% (exempt since PR #71) |
| PGO / `=256` on the winner | +0.42% / +0.02% | +0.45% / +0.07% |
| Baseline CI / recheck | ±0.65% / -0.83% (flagged) | ±0.61% / +0.35% |
| Wall-clock | 2h38m (no settle) | 8h01m (10-minute settle) |

The two hosts agree on every flag to within half a point, except `-march=native`, which gains five points more here.
`chicago`'s `-O3` ratio is 2.08× `niwot`'s, in line with its 32 threads and about 2.2× the memory bandwidth
(about 102 GB/s against 45 GB/s).

## What this means

The first held-back fprate benchmark mined cleanly: in eight hours at 45-50 W, with a 10-minute settle between
runs, nothing tipped `niwot`'s memory side into the throttle that lbm hit. Why cactus stays clear of it hasn't been
checked (its bandwidth draw wasn't measured). fotonik3d and roms, next, are the heavier two.

Two firsts: `-march=native`'s first fast-track under the strict-majority rule worked as intended (no screening run,
accepted), and PR #71's `-fno-math-errno` exemption paid its first cost, an hour for a clear reject, against ocio's
two points.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 22 | 12 | +25.83% |
| `-flto` | 16 | 5 | +3.96% |
| `-fgraphite-identity` | 19 | 2 | +2.02% |
| `-fprefetch-loop-arrays` | 23 | 4 | +1.73% |
| `-fno-math-errno` | 5 | 2 | +1.34% |
| `-mprefer-vector-width=256` | 14 | 2 | -1.54% |
| `-fprofile-use` | 17 | 2 | -3.84% |

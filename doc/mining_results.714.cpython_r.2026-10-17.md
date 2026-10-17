# `cfm mine` results: 714.cpython_r on `niwot`, 2026-10-17

The second mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the first one here to use
cross-benchmark knowledge transfer (M4): `-march=native` was fast-tracked on `706.stockfish_r`'s accepted
prior from the same night. Picked because cpython had the largest verified win on the old host (`-flto` then
PGO, +41.65%, `mining_results.714.cpython_r.2026-08-23.md`), and because the microarch multiplier would
probably get its first real run here once `-march=native` stayed out of the winning set.

## Headline result

**`-O3 -flto -fprofile-use`, +36.49% over plain `-O3`** (ratio 37.53 → 51.23). The old host's winning set
is reproduced, with a somewhat smaller total gain (+41.65% there). LTO's share is almost identical: +7.94%
alone and +9.35% in Phase 5 here, against +8.00% there. PGO's added gain is smaller: +24.82% on top of
`-flto` here, against +31.16% there.

Two other first-time results for this host:

- **`-march=native` hurts cpython: -4.77%, confirmed over 3 reps.** The old host showed the same direction
  (-5.32%), but only from a single screening trial that was never confirmed (that write-up's loose thread).
  It now holds across two hosts, with a CI clearly below baseline.
- **The microarch multiplier ran for real on this host** for the first time, using PR #46's hybrid Zen5/Zen5c
  detection (`-march=znver5`/`-mtune=znver5`). Both were rejected.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 714.cpython_r` (uncapped) |
| Code | `main` at `602ffdd` |
| Experiment id | 2 |
| Started / finished | 2026-10-17T02:44:35Z / 2026-10-17T06:32:10Z (3h48m) |
| Final status | `converged` |
| Trials | 45 (38-82) |
| Candidates screened / confirmed | 6 / 1 (`-flto`) |
| Fast-tracked (M4) | `-march=native` (rejected) |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +36.49% |
| Power profile | `balanced`, unchanged; CPU temp 88.5-92.9°C, package power 18.1-20.1 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 38 | local `deep-cpu` characterization (shape only) | 37.32 |
| 39 | warm-up (excluded from CI) | 37.67 |
| 40 | warm-up (excluded from CI) | 38.15 |
| 41 | calibration | 37.24 |
| 42 | calibration | 37.85 |
| 43 | calibration | 37.52 |

Calibration mean **37.534**, 95% CI **[36.78, 38.29]**. The reps spread 2.4%, wider than stockfish's 0.9%,
but they're scattered, not drifting in one direction, so there's still no sign of the old host's settling
pattern.

**Shape: `frontend-bound`, 63.9%**, `vectorization_density=moderate`, `allocation_pressure=moderate`, from a
local `deep-cpu` trial. The corpus (`amd-370-64gb`) agrees: `frontend-bound` at 65.8%.

**Why the corpus wasn't used (a real bug, found during this write-up):** the stockfish write-up guessed its
corpus miss was a temporary network problem. That guess was wrong. `reference_matrix._slugify_test_point()`
builds the corpus page slug from `cfg.spec_config`. With this host's config it produces
`ryzen350_64gb.gcc_o3-base` instead of the published `gcc_o3-base`, so `fetch_shape()` returns `None` on
every run here. Reproduced directly with `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg`. My earlier
"it works" checks hadn't set that variable. No result is wrong because of this: the local-trial fallback is
the designed behavior, and it measures this host's own shape. The only cost is one extra trial (~4 min).
Not fixed yet; see Follow-ups.

## Phase 2 filtering

Six candidates were excluded as implausible for a frontend-bound shape: `-funroll-loops`,
`-fprefetch-loop-arrays`, `-Ofast`, `-ffast-math`, `-fipa-pta`, and `-fgraphite-identity`.
`-march=native` was pulled into the M4 fast track. Six candidates went on to screening.

## Phase 3 screening (vs. most recent calibration rep, 37.52)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 44 | `-O3 -flto` | 40.48 | +7.9% | survived |
| 45 | `-O3 -freorder-blocks-and-partition` | 37.48 | -0.1% | survived |
| 46 | `-O3 -freorder-functions` | 37.20 | -0.9% | survived |
| 47 | `-O3 -fno-semantic-interposition` | 37.70 | +0.5% | survived |
| 48 | `-O3 -mprefer-vector-width=256` | 37.40 | -0.3% | survived |
| 49 | `-O3 -mprefer-vector-width=512` | 37.72 | +0.5% | survived |

Here `-flto` screened **positive**, unlike stockfish's -16.9% on the same host the night before. LTO's
effect on this host depends on the benchmark; stockfish's regression isn't a general LTO problem here.

## Phase 4 confirmation (3 reps each, vs. baseline CI [36.78, 38.29])

| Flags | Mean | Delta | Verdict |
|---|---|---|---|
| `-flto` | 40.51 (CI [40.00, 41.03]) | **+7.94%** | **accept** |
| `-freorder-blocks-and-partition` | | +0.55% | reject |
| `-freorder-functions` | | +0.41% | reject |
| `-mprefer-vector-width=256` | | +0.37% | reject |
| `-mprefer-vector-width=512` | 37.52 | -0.03% | reject |
| `-fno-semantic-interposition` | | -0.22% | reject |
| `-march=native` (fast-tracked) | 35.74 (CI [35.35, 36.14]) | **-4.77%** | reject |

M4 worked as designed. `-march=native` skipped screening on its +48.31% prior from `706.stockfish_r`, then was
judged on cpython's own data and rejected. Its CI sits entirely below the baseline's, so this is a measured
regression, not a borderline no-effect result. Its knowledge-table mean for this cluster drops from +48.31%
(n=1) to about +21.8% (n=2, 1 accepted).

## Phase 5 combination

`-O3 -flto` re-confirmed at **41.04** (+9.35%, CI [40.74, 41.35]). That's somewhat above its Phase 4 mean,
with both inside run-to-run noise of each other.

## Phase 6 multipliers

- **PGO: accepted, +24.82%** on top of `-flto` (51.23, CI [51.00, 51.46], against 41.04, CI [40.74, 41.35]).
  The CIs don't overlap at all. The audit shows `-fprofile-use` compiled into all three trials. Each PGO trial
  took about 6 minutes, much less than stockfish's ~23-minute PGO trials, because cpython's training run is
  short.
- **Microarch: attempted, both rejected.** This is the first real run of the multiplier on this host, and
  the first since PR #46's detection fix.

  | Flags (on top of `-O3 -flto -fprofile-use`) | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|
  | `-march=znver5` | 51.59 | [50.45, 52.73] | +0.70% | reject |
  | `-mtune=znver5` | 52.34 | [51.19, 53.50] | +2.17% | reject |

  `-mtune=znver5`'s +2.17% is a nominal positive delta, but its wide CI overlaps the PGO winner's, so it is
  correctly rejected. It's the same pattern as `710.omnetpp_r`'s `-march=znver5` on the old host. The audit
  confirms both flags were literally compiled in.

  The +0.70% for `-march=znver5` doesn't contradict `-march=native`'s -4.77%, even though the two are
  nearly the same flag on this host. `gcc -Q --help=target` shows they differ only in `-mprefetchi`,
  `-mrdseed` and `-mshstk`, and none of those is a vector extension. They were measured on different bases:
  `-march=native` on plain `-O3`, `-march=znver5` on `-O3 -flto -fprofile-use`. One plausible reading is that
  PGO's profile-guided layout and inlining remove whatever `-march=native` costs cpython at plain `-O3`. This
  run doesn't isolate that.

## Knowledge table after this run (`frontend-bound`, `niwot`)

Every flag from Phase 4/6 was upserted. Notable entries: `-flto` (new, accepted, +7.94%, n=1),
`-fprofile-use` (now 1 accept out of 2: stockfish's -0.10% plus cpython's +24.82%), and `-march=native`
(1 accept out of 2, mean about +21.8%). `-march=znver5`/`-mtune=znver5` are recorded for the first time on
this host.

## Cross-host comparison

| | Old host (2026-08-23) | `niwot` |
|---|---|---|
| `-flto` | +8.00% (Phase 5) | +9.35% (Phase 5) |
| PGO on top of `-flto` | +31.16% | +24.82% |
| Overall | **+41.65%** | **+36.49%** |
| `-march=native` | -5.32% (screening only) | -4.77% (confirmed, 3 reps) |

## Follow-ups

1. **Fix `_slugify_test_point()`** so a host-prefixed config name (`<host>.gcc_O3.cfg`) maps to the published
   `gcc_o3-base` slug, for example by keying on the SPEC config's label or the part after the last `.`. Until
   then, every `niwot` run characterizes locally. That's harmless, but it isn't the designed first choice.
2. `706.stockfish_r`'s `-flto` regression (-16.9%) is now clearly specific to stockfish on this host, and it's
   still worth a dedicated repeat measurement.
3. Why `-march=native` hurts cpython on both hosts is still open. Since `-march=native` is effectively
   `-march=znver5` on this host (no vector-ISA difference), the regression comes from targeting znver5
   itself (AVX-512 code generation and znver5 tuning), not from a stray extension. A direct test: measure
   `-O3 -mtune=znver5` and `-O3 -march=x86-64-v4` separately on plain `-O3`, to separate tuning from ISA.

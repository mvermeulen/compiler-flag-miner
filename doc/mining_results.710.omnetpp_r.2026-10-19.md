# `cfm mine` results: 710.omnetpp_r on `niwot`, 2026-10-19

The seventh mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the third `frontend-bound` one,
after `706.stockfish_r` and `714.cpython_r`. `710.omnetpp_r` (OMNeT++ discrete-event network simulation) was
mined once on the old host ([`mining_results.710.omnetpp_r.2026-08-28.md`](mining_results.710.omnetpp_r.2026-08-28.md)),
where `-flto` plus PGO won by +39.90%.

## Headline result

**`-O3 -flto -fprofile-use`, +29.94% over plain `-O3`** (ratio 24.06 → 31.27). This is the same winning set
as on the old host, built up the same way:

- `-flto` was accepted at Phase 4/5: +13.14%, almost identical to the old host's +13.25%.
- Two-pass PGO was accepted on top at Phase 6: +14.85%, against the old host's +23.46%.

That PGO shortfall accounts for the whole gap to the old host's +39.90%. `714.cpython_r` showed the same
pattern, with smaller PGO gains here (+24.8% on top of LTO vs +31.2%).

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 710.omnetpp_r` (uncapped, queued after the `708.sqlite_r` re-check) |
| Code | `main` at `b087f8c` |
| Experiment id | 40 |
| Started / finished | 2026-10-19T09:57:27Z / 2026-10-19T13:49:53Z (3h52m) |
| Final status | `converged` |
| Trials | 35 (227-261) |
| Candidates screened / confirmed | 3 / 1 (plus 2 fast-tracked) |
| Fast-tracked (M4) | `-march=native` (rejected), `-flto` (accepted) |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, +29.94% |
| Power profile | `balanced`, unchanged; CPU temp 92.1-97.9°C, package power 19.1-27.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 227 | warm-up (excluded from CI) | 24.10 |
| 228 | warm-up (excluded from CI) | 24.22 |
| 229 | calibration | 24.04 |
| 230 | calibration | 24.24 |
| 231 | calibration | 23.91 |

Calibration mean **24.062**, 95% CI **[23.66, 24.46]** (±1.7%). That's a wide band for this host. There was no
settling trend, just run-to-run scatter. It didn't decide anything: every rejected candidate was within +0.5%,
and both winners cleared it by more than 10%.

**Shape: `frontend-bound`, 45.9%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`). No local characterization trial was run.

## Phase 2 filtering and M4

The frontend-bound, low-vectorization shape excluded eight candidates:

- compute-bound-tagged: `-funroll-loops`, `-Ofast`, `-ffast-math`
- memory-bound-tagged: `-fprefetch-loop-arrays`
- vectorization-high-tagged: both `-mprefer-vector-width` settings
- backend-bound-tagged: `-fipa-pta`, `-fgraphite-identity`

**This is the first run on this host where M4 had several frontend-bound priors to use.** It fast-tracked two
flags with accepted track records:

- `-march=native`: +21.77% mean, n=2. The mean is pulled up by stockfish; cpython rejected it.
- `-flto`: +7.94%, n=1, from cpython.

`-fprofile-use`'s prior isn't eligible for fast-tracking, because it always runs through Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 23.91)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 232 | `-O3 -freorder-blocks-and-partition` | 23.92 | +0.04% | survived |
| 233 | `-O3 -freorder-functions` | 24.17 | +1.09% | survived |
| 234 | `-O3 -fno-semantic-interposition` | 24.19 | +1.17% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [23.66, 24.46])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-flto` (fast-tracked) | 27.25, 27.19, 27.42 | 27.29 | [26.99, 27.58] | **+13.39%** | **accept** |
| `-freorder-blocks-and-partition` | 23.86, 24.46, 24.22 | 24.18 | [23.43, 24.93] | +0.49% | reject (CIs overlap) |
| `-fno-semantic-interposition` | 23.99, 24.36, 24.14 | 24.16 | [23.70, 24.63] | +0.43% | reject |
| `-march=native` (fast-tracked) | 24.18, 24.20, 24.06 | 24.15 | [23.96, 24.33] | +0.35% | reject |
| `-freorder-functions` | 24.15, 23.98, 24.30 | 24.14 | [23.75, 24.54] | +0.34% | reject |

- **`-flto` was fast-tracked and accepted.** It's the second accepted `-flto` on this host, after cpython.
- **`-march=native` was fast-tracked and rejected, flat.** That's the third distinct outcome for it in this
  host's frontend-bound cluster: +48% (stockfish), -4.8% (cpython), +0.35% (omnetpp). Its prior mean drops
  accordingly (below).

## Phase 5 combination

There's only one accepted flag, so the combination is `-O3 -flto` re-confirmed: **27.22** (27.17, 27.19, 27.32;
CI [27.02, 27.43]), +13.14%.

## Phase 6 multipliers

- **PGO: accepted, +14.85% on top of `-O3 -flto`** (31.37, 31.26, 31.17; mean 31.27, CI [31.02, 31.51]), and
  +29.94% overall. The CI is far clear of the LTO-only winner's. Each PGO trial took about 8 minutes, against
  about 6 for a plain `-flto` trial.
- **Microarch: attempted on `-O3 -flto -fprofile-use`, both rejected.**

  | Added flag | Ratios | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|---|
  | `-march=znver5` | 30.65, 30.97, 31.33 | 30.98 | [30.15, 31.82] | -0.90% | reject |
  | `-mtune=znver5` | 31.20, 31.52, 31.23 | 31.32 | [30.87, 31.76] | +0.16% | reject |

  On the old host, `-march=znver5` read a nominal +2.68% here and was still rejected because its CI overlapped.
  On this host it reads -0.90%, so microarch targeting adds nothing to the PGO winner on either host.

Every audit is clean. `-O3` and `-fprofile-use` were confirmed compiled in. `-flto` and `-march=native` are
reported as "not independently checkable", as expected.

## Knowledge table after this run (`frontend-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 3 | 1 | +14.63% |
| `-fprofile-use` | 3 | 2 | +13.19% |
| `-flto` | 2 | 2 | +10.67% |
| `-mtune=znver5` | 2 | 0 | +1.16% |
| `-freorder-blocks-and-partition` | 3 | 0 | +0.37% |
| `-freorder-functions` | 3 | 0 | +0.36% |
| `-fno-semantic-interposition` | 3 | 0 | +0.14% |
| `-mprefer-vector-width=256` | 2 | 0 | +0.12% |
| `-mprefer-vector-width=512` | 2 | 0 | +0.08% |
| `-march=znver5` | 2 | 0 | -0.10% |

`-march=native` still has an accepted record (1 of 3), so it will keep being fast-tracked for frontend-bound
benchmarks. Each fast-track costs 3 confirmation trials instead of 1 screening trial, which is a waste when it's
rejected, as it was here and on cpython. Its mean (+14.63%) is really one large outlier plus two near-zero
results.

## Follow-ups

1. **Why is PGO's gain on top of LTO smaller on this host?** omnetpp got +14.9% vs +23.5% on the old host, and
   cpython +24.8% vs +31.2%. One untested reading is that the old Strix Halo part's much larger L3 (64 MB vs this part's 16 + 8 MB) leaves less of a frontend penalty for PGO's code layout to remove. Another is that the hybrid Zen5c cores
   behave differently. Added to the [opportunity list](opportunities_niwot.md).
2. **M4 fast-track rule.** A fast-tracked flag with a 1-of-3 record and a mean dominated by one outlier is a
   weak prior. Requiring a majority-accepted record, or using a median, would have sent `-march=native` through
   screening here and saved 2 trials. Added to the opportunity list.

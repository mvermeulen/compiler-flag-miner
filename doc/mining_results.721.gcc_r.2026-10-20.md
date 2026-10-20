# `cfm mine` results: 721.gcc_r on `niwot`, 2026-10-20

The eleventh mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the fourth `memory-bound` one.
`721.gcc_r` (the GCC compiler) was mined once on the old host
([`mining_results.721.gcc_r.2026-08-28.md`](mining_results.721.gcc_r.2026-08-28.md)), where nothing was
accepted.

## Headline result

**Nothing accepted: `-O3` stays, 0.00%.** Same as on the old host. All five candidates the mine tried read
between -0.54% and -0.05%, with every CI overlapping the baseline's.

The catch is what it didn't try. The memory-bound shape (45.2%, nearly identical to vpr's 45.4%) excluded
`-flto` at Phase 2 and skipped PGO at Phase 6. On vpr, that same exclusion hid +14.7%
([#20](mining_results.734.vpr_r.2026-10-20.md#follow-up-lto-and-pgo-on-top-of-the-winner-2026-10-20)). An
interleaved LTO/PGO check on gcc is already queued (after `735.gem5_r`, alongside sqlite and abc), so this
result is provisional.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 721.gcc_r` (uncapped, queued after the vpr LTO/PGO check) |
| Code | `main` at `11e7c78` (later commits are doc-only) |
| Experiment id | 56 |
| Started / finished | 2026-10-20T15:03:29Z / 2026-10-20T18:28:55Z (3h25m) |
| Final status | `converged` |
| Trials | 21 (368-388) |
| Candidates screened / confirmed | 1 / 0 (plus 2 fast-tracked, both rejected) |
| Fast-tracked (M4) | `-fprefetch-loop-arrays` (rejected), `-march=native` (rejected) |
| Winning flags | `["-O3"]`, 0.00% |
| Power profile | `balanced`, unchanged; CPU temp 89.2-92.4°C, package power 18.1-19.1 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 368 | warm-up (excluded from CI) | 22.93 |
| 369 | warm-up (excluded from CI) | 22.95 |
| 370 | calibration | 22.98 |
| 371 | calibration | 22.99 |
| 372 | calibration | 23.00 |

Calibration mean **22.991**, 95% CI **[22.96, 23.02]** (±0.1%), the tightest baseline on this host so far.

**Shape: `memory-bound`, 45.2%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the
corpus (`reference-matrix:amd-370-64gb`).

## Phase 2 filtering and M4

Low vectorization added both `-mprefer-vector-width` settings to vpr's eight exclusions, for ten in all. That
left only `-fgraphite-identity` for screening.

M4 fast-tracked two flags, each on a 1-of-3 record: `-fprefetch-loop-arrays` (sqlite's accept) and
`-march=native` (vpr's accept).

## Phase 3 screening (vs. most recent calibration rep, 23.00)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 373 | `-O3 -fgraphite-identity` | 22.89 | -0.50% | survived |

## Phase 4 confirmation (3 reps each, vs. baseline CI [22.96, 23.02])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-fgraphite-identity` | 23.02, 22.97, 22.94 | 22.97 | [22.88, 23.07] | -0.07% | reject |
| `-march=native` (fast-tracked) | 22.95, 22.89, 22.95 | 22.93 | [22.84, 23.02] | -0.27% | reject |
| `-fprefetch-loop-arrays` (fast-tracked) | 22.95, 22.82, 22.84 | 22.87 | [22.70, 23.04] | -0.54% | reject |

- **Both fast-tracks missed**, adding two more cases to opportunity #15. Each spent 3 confirmation trials
  where 1 screening trial would have pruned it.
- **`-march=native` does nothing for GCC.** The old host found the same (-0.15%). A compiler's hot paths are
  pointer-heavy tree and RTL walks with little to vectorize.

## Phase 5 combination

Nothing was accepted at Phase 4, so the Phase 5 winner is plain `-O3`.

## Phase 6 multipliers

- **PGO: skipped**, because the memory-bound shape contradicts both of `-fprofile-use`'s `topdown_signals`.
- **Microarch: attempted on `-O3`, both rejected.**

  | Added flag | Ratios | Mean | 95% CI | Delta | Verdict |
  |---|---|---|---|---|---|
  | `-march=znver5` | 22.92, 22.88, 22.95 | 22.91 | [22.82, 23.01] | -0.33% | reject |
  | `-mtune=znver5` | 23.02, 23.05, 22.87 | 22.98 | [22.75, 23.21] | -0.05% | reject |

None of the trials logged an audit warning.

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-fprefetch-loop-arrays` | 4 | 1 | +0.71% |
| `-fgraphite-identity` | 4 | 0 | +0.49% |
| `-march=native` | 4 | 1 | +0.40% |
| `-mprefer-vector-width=256` | 2 | 0 | +0.35% |
| `-mtune=znver5` | 3 | 0 | +0.20% |
| `-mprefer-vector-width=512` | 2 | 0 | -0.07% |
| `-march=znver5` | 3 | 0 | -0.33% |

## Follow-ups

1. **The LTO/PGO check (queued).** Interleaved `cfm measure` of `-O3` against `-O3 -flto`,
   `-O3 -fprofile-use` and `-O3 -flto -fprofile-use`, 3 rounds. GCC is a large C codebase with a big
   instruction footprint, the kind of program LTO and PGO usually help, so a real gain is likely.

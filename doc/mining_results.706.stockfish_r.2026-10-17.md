# `cfm mine` results: 706.stockfish_r on `niwot`, 2026-10-17

The first mining run on a new host, `niwot` (see [`host_niwot.md`](host_niwot.md)). Every earlier
`doc/mining_results.*.md` came from a different machine. This run started from an empty `cfm.db`, so no
candidate was fast-tracked on a prior from another benchmark. `706.stockfish_r` was picked first because the
old host had a large, well-understood `-march=native` win on it (+48.75%,
`mining_results.706.stockfish_r.2026-08-23.md`), which made it a clear check that the pipeline works on this
host.

## Headline result

**`-O3 -march=native`, +48.42% over plain `-O3`** (ratio 50.69 → 75.23). Almost exactly the old host's
+48.75%. Before the run I expected a smaller win here: this mobile Zen5 part is, as I understand it, a
256-bit-datapath implementation of AVX-512, where Strix Halo has a full 512-bit datapath. That expectation
was wrong. On both hosts, stockfish's `-march=native` win doesn't appear to depend on datapath width.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 706.stockfish_r` (uncapped) |
| Code | `main` at PR #46 (hybrid Zen5/Zen5c microarch detection) |
| Experiment id | 1 (`niwot`'s own `cfm.db`) |
| Started / finished | 2026-10-16T20:50:10Z / 2026-10-17T02:40:17Z (5h50m) |
| Final status | `converged` |
| Trials | 37 |
| Candidates screened / confirmed | 7 / 1 |
| Fast-tracked (M4) | none (empty knowledge table) |
| Winning flags | `["-O3", "-march=native"]`, +48.42% |
| Power profile | `balanced` (governor `powersave`, EPP `balance_performance`), unchanged for the whole run |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1 | local `deep-cpu` characterization (shape only) | 50.58 |
| 2 | warm-up (excluded from CI) | 50.98 |
| 3 | warm-up (excluded from CI) | 50.94 |
| 4 | calibration | 50.52 |
| 5 | calibration | 50.72 |
| 6 | calibration | 50.82 |

Calibration mean **50.687**, 95% CI **[50.30, 51.07]**. Unlike the old host, there was **no settling drift**:
all six runs fall within 50.52-50.98, a 0.9% spread, and the warm-ups weren't higher than the calibration
reps. That's one benchmark's worth of evidence, but it's a good early sign that this host measures stably.
Measured CPU temperature stayed at 89.1-95.0°C and package power at 19.1-22.0 W across all trials.

**Shape: `frontend-bound`, 40.6%** (narrow margin), `vectorization_density=high`,
`allocation_pressure=moderate`. It came from a local `deep-cpu` trial, not the reference-matrix corpus. The
corpus lookup returned nothing during this run. *Correction:* I first put this down to a temporary network
problem. The real cause is a slug bug, found during the `714.cpython_r` write-up: a host-prefixed
`CFM_SPEC_CONFIG` never matches a published corpus page (see
[`mining_results.714.cpython_r.2026-10-17.md`](mining_results.714.cpython_r.2026-10-17.md)). The
corpus's entry for this benchmark (`amd-370-64gb`) reads `memory-bound` at 45.3%, with `frontend-bound` as
the 35.3% alternative. Both machines put stockfish near the boundary between those two classes. Because this
run used its own host's shape, its Phase 2 filtering differs from the old host's (next section).

## Phase 2 filtering

The frontend-bound shape excluded four candidates as implausible: `-Ofast` and `-ffast-math`
(compute-bound-tagged), `-fipa-pta` (backend-bound), and `-fgraphite-identity`
(backend-bound/memory-bound-corroborated). Seven candidates went on to screening.

## Phase 3 screening (vs. most recent calibration rep, 50.82)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 7 | `-O3 -flto` | 42.22 | **-16.93%** | pruned |
| 8 | `-O3 -freorder-blocks-and-partition` | 50.66 | -0.3% | survived |
| 9 | `-O3 -freorder-functions` | 50.92 | +0.2% | survived |
| 10 | `-O3 -fno-semantic-interposition` | 50.78 | -0.1% | survived |
| 11 | `-O3 -mprefer-vector-width=256` | 50.94 | +0.2% | survived |
| 12 | `-O3 -mprefer-vector-width=512` | 50.64 | -0.4% | survived |
| 13 | `-O3 -march=native` | 75.31 | +48.18% | survived |

**`-flto` at -16.9% is the notable result here.** It's a large regression from a single screening trial,
which the audit confirms was a real build (`-O3` compiled in, `-flto` expected to be absent from the audit
text, per the 2026-08-23 traps entry). LTO was a real win on several frontend-bound benchmarks on the old
host, so this is worth a dedicated repeat measurement (`cfm measure 706.stockfish_r --flags "-O3 -flto"`).
That measurement should check whether the regression is stable, and whether `-march=native -flto` behaves
differently. Under the current pipeline, a flag pruned at Phase 3 is never tried again in combination.

## Phase 4 confirmation (3 reps each, vs. baseline CI [50.30, 51.07])

| Flags | Mean delta | Verdict |
|---|---|---|
| `-march=native` | **+48.31%** (CI [74.55, 75.80]) | **accept** |
| `-freorder-functions` | +0.33% | reject |
| `-fno-semantic-interposition` | +0.20% | reject |
| `-mprefer-vector-width=512` | +0.19% | reject |
| `-freorder-blocks-and-partition` | +0.06% | reject |
| `-mprefer-vector-width=256` | -0.14% | reject |

All five rejects are flat, inside the baseline's own noise. Neither `-mprefer-vector-width` setting changes
anything at plain `-O3`, which is expected: without `-march=native`, the compiler isn't targeting AVX-512
anyway.

## Phase 5 combination

Only one flag was accepted, so the greedy walk has a single step: `-O3 -march=native` re-confirmed at
**75.23** (+48.42%, CI [74.78, 75.68]).

## Phase 6 multipliers

- **PGO: attempted, rejected (-0.10%).** It ran here only because the local shape was frontend-bound. The
  old host's memory-bound shape would have skipped it. `-O3 -march=native` plus real two-pass PGO gave a mean
  of 75.15 (CI [74.41, 75.89]), against 75.23 without it. The audit confirms `-fprofile-use` was compiled
  into all three trials, so this is a real, clean reject. Each PGO trial took about 23 minutes, against
  about 5 minutes for a plain `-O3 -march=native` trial (and about 7 for plain `-O3`).
- **Microarch: skipped**, because the winning set already contains `-march=native`, so the conflict guard
  fired. PR #46's hybrid Zen5/Zen5c detection fix (now returning `-march=znver5`/`-mtune=znver5` on this
  host) therefore still hasn't been exercised inside a real run. That needs a benchmark where
  `-march=native` doesn't win.

## Knowledge table after this run

All entries are under `cluster_key = frontend-bound`, with `n_trials = 1` each. This is `niwot`'s own
`cfm.db`, independent of the old host's.

| Flag | Mean delta | Accepted |
|---|---|---|
| `-march=native` | +48.31% | 1/1 |
| `-freorder-functions` | +0.33% | 0/1 |
| `-fno-semantic-interposition` | +0.20% | 0/1 |
| `-mprefer-vector-width=512` | +0.19% | 0/1 |
| `-freorder-blocks-and-partition` | +0.06% | 0/1 |
| `-fprofile-use` | -0.10% | 0/1 |
| `-mprefer-vector-width=256` | -0.14% | 0/1 |

`-flto` has no entry. Screening-phase prunes don't write to the knowledge table.

## Follow-up re-measure: `-flto` (2026-10-17)

Three interleaved rounds of standalone `cfm measure` trials (experiments 3-11, 07:56-11:04Z). Each round ran
`-O3`, then `-O3 -flto`, then `-O3 -march=native -flto`, so slow drift would hit all three sets equally.
All 9 built and validated.

| Flags | Ratios | Mean | vs `-O3` |
|---|---|---|---|
| `-O3` | 50.89, 50.70, 50.71 | 50.77 | — |
| `-O3 -flto` | 42.17, 42.38, 42.40 | 42.32 | **-16.6%** |
| `-O3 -march=native -flto` | 56.88, 57.09, 56.99 | 56.99 | +12.3% |

**Confirmed: LTO is a large, stable regression for stockfish on this host.** The `-O3` control matches the
mining run's baseline (50.69), and `-O3 -flto` matches its single screening trial (-16.9%). The ratios within
each set span at most 0.5%. LTO also hurts on top of `-march=native`: 56.99 against 75.23 without it, about
-24%. That means the mine's winning set `-O3 -march=native` would have stood even if `-flto` had reached
Phase 5. Why is open. The likely suspect is LTO's cross-unit inlining or code layout changing stockfish's hot
evaluation and search code. `714.cpython_r`'s +7.94% from `-flto` on the same host rules out a general LTO
problem on `niwot`.

(These standalone `cfm measure` trials go into `cfm.db` as their own experiments, but they don't update the
knowledge table. Only `cfm mine`'s Phase 4+ trials do.)

## Follow-ups

1. ~~Re-measure `-O3 -flto`~~: done, see above. Confirmed -16.6%.
2. ~~Exercise the microarch multiplier~~: done on `714.cpython_r` and `708.sqlite_r` (both rejected).
3. The `-march=native` prior in this host's `frontend-bound` cluster fast-tracked that flag on
   `714.cpython_r`, where it was rejected at -4.77%.

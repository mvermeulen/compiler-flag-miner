# `cfm mine` results: 750.sealcrypto_r on `niwot`, 2026-10-18

The sixth mining run on `niwot` (see [`host_niwot.md`](host_niwot.md)), and the second `compute-bound` one,
following `707.ntest_r` earlier the same evening. `750.sealcrypto_r` (Microsoft SEAL homomorphic encryption)
was mined twice on the old host
([`2026-08-24`](mining_results.750.sealcrypto_r.2026-08-24.md),
[`2026-08-24b`](mining_results.750.sealcrypto_r.2026-08-24b.md)), and `-march=native` won both times
(+14.17%, +15.63%).

## Headline result

**`-O3 -march=native`, +20.49% over plain `-O3`** (ratio 27.91 → 33.63). That's this host's second-largest
`-march=native` win after `706.stockfish_r`. It's also about 5 points larger than on the old host, where every
other `-march=native` result so far has come out about the same on both machines. Every other candidate was
flat and rejected.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 750.sealcrypto_r` (uncapped, queued after the `708.sqlite_r` prefetch sweep) |
| Code | `main` at `efcdcb1` |
| Experiment id | 33 |
| Started / finished | 2026-10-19T03:05:05Z / 2026-10-19T05:46:38Z (2h42m) |
| Final status | `converged` |
| Trials | 31 (190-220) |
| Candidates screened / confirmed | 5 / 1 |
| Fast-tracked (M4) | `-march=native` (accepted) |
| Winning flags | `["-O3", "-march=native"]`, +20.49% |
| Power profile | `balanced`, unchanged; CPU temp 92.2-94.6°C, package power 19.0-20.1 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 190 | warm-up (excluded from CI) | 28.45 |
| 191 | warm-up (excluded from CI) | 28.06 |
| 192 | calibration | 28.07 |
| 193 | calibration | 27.93 |
| 194 | calibration | 27.73 |

Calibration mean **27.910**, 95% CI **[27.49, 28.33]** (±1.5%).

- **The baseline was still settling downward.** All five reps fell steadily from 28.45 to 27.73 (-2.5%), the
  same pattern sealcrypto showed on the old host.
- **Settling made the CI wide, but no verdict depended on it.** Every non-`-march` candidate measured
  28.04-28.13, inside the baseline CI and about 1% above the last calibration rep. Against a settled `-O3` near
  28.0, those candidates read roughly flat. `-march=native`'s gain is far too large for a ±1.5% band to matter.

**Shape: `compute-bound`, 55.1%**, `vectorization_density=moderate`, `allocation_pressure=low`, from the
corpus (`reference-matrix:amd-370-64gb`). No local characterization trial was run.

## Phase 2 filtering and M4

The compute-bound shape excluded seven candidates as implausible:

- frontend-bound-tagged: `-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`,
  `-fno-semantic-interposition`
- memory-bound-tagged: `-fprefetch-loop-arrays`
- backend-bound-tagged: `-fipa-pta`, `-fgraphite-identity`

`vectorization_density=moderate` kept both `-mprefer-vector-width` settings in, unlike ntest.

**M4 fast-tracked `-march=native`** on `707.ntest_r`'s accepted prior (+14.43%). This is the first real
`compute-bound` fast-track on this host. The other three ntest priors (`-Ofast`, `-ffast-math`,
`-funroll-loops`) were rejects, so they went through screening as normal.

## Phase 3 screening (vs. most recent calibration rep, 27.73)

| Trial | Flags | Ratio | Delta | Result |
|---|---|---|---|---|
| 195 | `-O3 -funroll-loops` | 28.18 | +1.61% | survived |
| 196 | `-O3 -Ofast` | 28.05 | +1.14% | survived |
| 197 | `-O3 -ffast-math` | 28.07 | +1.21% | survived |
| 198 | `-O3 -mprefer-vector-width=256` | 28.07 | +1.20% | survived |
| 199 | `-O3 -mprefer-vector-width=512` | 28.05 | +1.12% | survived |

The uniform +1.1-1.6% spread across five unrelated flags reflects the low last calibration rep, not the flags.
That's the settling pattern described above.

## Phase 4 confirmation (3 reps each, vs. baseline CI [27.49, 28.33])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-march=native` (fast-tracked) | 33.65, 33.65, 33.67 | 33.65 | [33.63, 33.68] | **+20.58%** | **accept** |
| `-funroll-loops` | 28.15, 28.10, 28.13 | 28.13 | [28.07, 28.18] | +0.77% | reject (CIs overlap) |
| `-Ofast` | 28.07, 28.08, 28.06 | 28.07 | [28.05, 28.10] | +0.58% | reject |
| `-ffast-math` | 28.05, 28.10, 28.05 | 28.07 | [27.99, 28.15] | +0.57% | reject |
| `-mprefer-vector-width=256` | 28.09, 28.08, 27.94 | 28.04 | [27.83, 28.24] | +0.45% | reject |
| `-mprefer-vector-width=512` | 28.09, 27.63, 28.11 | 27.94 | [27.28, 28.61] | +0.12% | reject |

- **`-Ofast` and `-ffast-math` do nothing for SEAL.** That fits: SEAL's hot loops are modular integer
  arithmetic (NTT, polynomial multiply), not floating point. It's the same result as on the old host.
- **`-mprefer-vector-width` doesn't matter at plain `-O3`.** The baseline targets generic x86-64 without
  AVX-512, so there's no 512-bit code for the preference to choose. The wider-vector effect is part of what
  `-march=native` brings.

## Phase 5 combination

There's only one accepted flag, so the combination is `-O3 -march=native` re-confirmed: **33.63**
(33.59, 33.61, 33.69; CI [33.49, 33.77]), +20.49%.

## Phase 6 multipliers

- **PGO: skipped**, because the compute-bound shape contradicts both of `-fprofile-use`'s `topdown_signals`.
- **Microarch: skipped**, because the winning set already contains `-march=native`.

None of the trials logged an audit warning. `-O3` and every literal flag were confirmed compiled in.
`-march=native` is reported as "not independently checkable", as expected.

## Knowledge table after this run (`compute-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 2 | 2 | +17.51% |
| `-mprefer-vector-width=256` | 1 | 0 | +0.45% |
| `-Ofast` | 2 | 0 | +0.41% |
| `-ffast-math` | 2 | 0 | +0.35% |
| `-mprefer-vector-width=512` | 1 | 0 | +0.12% |
| `-funroll-loops` | 2 | 0 | -0.07% |

The flat rejects are probably about half a point optimistic because of the settling baseline.

## Follow-ups

1. **Why is the `-march=native` win bigger here than on the old host (+20.5% vs +14-16%)?** For stockfish and
   ntest the two hosts agree within a point, and cpython's `-march=native` regression is similar on both. One test is to measure `-march=znver5` with
   `-mprefer-vector-width=256` vs `=512` on top of `-O3`. That would show whether niwot's AVX-512 code
   generation, or something else in znver5 targeting, accounts for the difference.
2. **PGO and LTO were never tried** on sealcrypto on either host. The shape here (55.1% compute-bound) is a
   clearer margin than ntest's, so this is lower priority than ntest's equivalent item.

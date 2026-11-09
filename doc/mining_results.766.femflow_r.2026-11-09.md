# `cfm mine` results: 766.femflow_r on `niwot`, 2026-11-09

`766.femflow_r` is a C++ finite-element flow solver built on deal.II, 16 copies under SPECrate. It ran ninth in the
unattended queue, with `--settle-seconds 600`. `chicago` mined it on 2026-11-07
([write-up](mining_results.766.femflow_r.2026-11-07.md)).

## Headline result

**`-O3 -march=native`, +106.58% over plain `-O3`** (ratio 43.082 → 89.001): the largest gain cfm has found on `niwot`,
in any suite.

- **`-march=native` more than doubles the ratio.** It screened at +107.6% and confirmed at +106.58% (CI [88.62, 89.39],
  ±0.43%). Every one of its three reps (88.83-89.12) was more than twice every `-O3` rep (42.66-43.17). This is AVX-512
  autovectorization of deal.II's kernels, as on `chicago` (+130.46% for the flag alone there).
- **`-flto` gave +15.13% alone, but nothing on top of `-march=native`** (+0.03% as the greedy step, rejected).
  `chicago` measured +16.76% and +0.53%, and kept `-flto` through the pair tournament (#29).
- **PGO lost 27.18%** on top of `-march=native` (`chicago`: -2.01% on top of `-flto -march=native`), and
  `-mprefer-vector-width=256` lost 10.92% (`chicago`: -15.68%).
- **`-fgraphite-identity` was pruned at screening** (-6.36%), as on `chicago` (-5.9%).
- **PR #69's step 1 reuse fired a second time**, saving three timed runs.
- **The baseline recheck was flagged** (42.664, -0.97% against the calibration mean, 0.16% below the CI). That is far
  too small to matter for either accept.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 766.femflow_r --settle-seconds 600` (uncapped, 10 min idle after `772.marian_r`) |
| Code | `main` at `2663e47` (includes PR #69) |
| Experiment id | 195 |
| Started / finished | 2026-11-08T15:10:38Z / 2026-11-09T04:28:49Z (13h18m, about 5.2 h of it settle) |
| Final status | `converged` |
| Trials | 31 (1943-1973) |
| Candidates screened / confirmed | 4 / 3 (`-fgraphite-identity` pruned) |
| Fast-tracked (M4) | none (`-march=native` at 7 of 16 memory-bound doesn't qualify) |
| Excluded on shape | 11, the same as ocio's and marian's: `-Ofast`, `-ffast-math`, `-fno-math-errno`, `-funroll-loops`, `-fipa-pta` and the six frontend-tagged flags |
| Skipped as unchanged code (#58) | none |
| Winning flags | `["-O3", "-march=native"]`, +106.58% |
| Guards | bandwidth gate waited once (30 s, trial 1943); no slow-rep, spread or low-power reruns; **baseline recheck flagged (-0.97%)** |
| Power / temperature | package power median 48-50 W for `-O3`-class builds and PGO, 34-35 W for `-march=native`, 41 W for `=256`; CPU 95-99 °C; bandwidth probes 44.7-46.1 GB/s |
| Audit | clean |

An `-O3` trial took about 27 minutes, a `-march=native` trial about 19 and a PGO trial about 46, 10 minutes of each
the settle.

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 1943 | warm-up | 42.951 |
| 1944 | warm-up | 43.126 |
| 1945 | calibration | 43.167 |
| 1946 | calibration | 43.159 |
| 1947 | calibration | 42.920 |
| 1961 | recheck after Phase 4 | 42.664 (-0.97%, **flagged**) |

Calibration mean **43.082**, 95% CI **[42.733, 43.431]** (±0.81%). Warm-up settled after 2 reps (3239 s). All six
`-O3` builds had the same fingerprint (`4302cdf0`), and the six reps span only 1.2% (42.66-43.17), so the flag is the
0.5% warning threshold catching ordinary rep-to-rep spread rather than a real offset.

**Shape: `memory-bound`, 69.4%**, `vectorization_density=high`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). Well over the 55% gate, so only four candidates were left (`-flto` is exempt), and
`-mprefer-vector-width=256` was deferred to Phase 6.

## Phase 3 screening (vs. most recent calibration rep, 42.920)

| Flags | Ratio | Delta |
|---|---|---|
| `-march=native` | 89.106 | **+107.61%** |
| `-flto` | 49.654 | **+15.69%** |
| `-fprefetch-loop-arrays` | 42.652 | -0.63% |
| `-fgraphite-identity` | 40.189 | **-6.36%, pruned** |

## Phase 4 confirmation (3 reps each, vs. baseline CI [42.733, 43.431])

| Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|
| `-march=native` | 89.001 | [88.616, 89.386] | **+106.58%** | **accept** |
| `-flto` | 49.602 | [49.351, 49.852] | **+15.13%** | **accept** |
| `-fprefetch-loop-arrays` | 42.478 | [42.024, 42.933] | -1.40% | reject |

`-march=native` drew 34-35 W against the baseline's 49 W reference. As on marian, PR #68's sibling check kept the reps
(all three drew the same), and no rerun was spent.

## Phase 5 combination

| Step | Flags | Reps | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| 1 | `-O3 -march=native` | (reused from Phase 4) | 89.001 | [88.616, 89.386] | +106.58% vs baseline | accept |
| 2 | `+ -flto` | 89.095, 89.166, 88.809 | 89.023 | [88.553, 89.493] | +0.03% vs step 1 | reject |

**Pair tournament:** the only pair, `-flto` + `-march=native`, built the same code as step 2 (fingerprint `5673a072`)
and measured 88.997 [88.687, 89.308], +106.58% vs baseline but below the greedy winner, so it didn't replace it. Three
more timed runs on already-measured code (#35).

On `chicago` the same pair read +0.53% over the greedy winner and replaced it on a higher mean and clear CI, though
the greedy step had rejected the same code for missing the 1% bar (#29). Here the pair was lower, so the two rules
agreed.

## Phase 6 multipliers (on `-O3 -march=native`, 89.001)

| Stage | Flags | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| PGO | `+ -fprofile-use` | 64.808 | [64.553, 65.064] | **-27.18%** | reject |
| PGO near-miss | — | | | | none (no CI-clear Phase 4 reject) |
| Microarch | — | | | | skipped (`-march=native` already in the set) |
| Vector width | `+ -mprefer-vector-width=256` | 79.285 | [78.770, 79.799] | **-10.92%** | reject |

- **PGO's loss is real, not noise**: its three builds shared one fingerprint
  (`b72ab998`, so SPECrate PGO reproduced here, unlike ocio and marian), agreed within 0.3%, and drew 49 W, like
  `-O3` rather than like `-march=native` (34-35 W). That pattern fits a profile that marks the vectorized kernels cold
  or otherwise changes how they are vectorized, but the cause hasn't been checked. `chicago`'s PGO, on top of
  `-flto -march=native`, lost only 2.01%, so the two hosts disagree by 25 points; the different base (`-flto` there)
  is the obvious first difference to test.
- **`=256` cost 10.92%**: femflow's kernels want the full 512-bit width, as on `chicago`.

## Comparison with `chicago`

| | `chicago` | `niwot` |
|---|---|---|
| Winning flags | `-O3 -flto -march=native` | `-O3 -march=native` |
| Gain | +132.01% | +106.58% |
| `-march=native` alone | +130.46% (fast-tracked) | +106.58% |
| `-flto` alone / on top | +16.76% / +0.53% | +15.13% / +0.03% |
| PGO on the winner | -2.01% | **-27.18%** |
| `-mprefer-vector-width=256` | -15.68% | -10.92% |
| `-fgraphite-identity` | pruned, -5.9% | pruned, -6.36% |

## What this means

femflow, like marian, is a vectorization benchmark, and `-march=native` is nearly the whole story on both hosts. The
open question is PGO: a 27% loss that reproduces across three identical builds is real, and it is 25 points worse
than `chicago`'s. A follow-up `cfm measure` of `-O3 -march=native -flto -fprofile-use` here would show whether `-flto`
is the difference. As with ocio and marian, the shape filter dropped the fast-math and unrolling flags (#30).

## Knowledge table after this run (`memory-bound`, `niwot`)

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-march=native` | 17 | 8 | +20.43% |
| `-flto` | 11 | 4 | +4.16% |
| `-fgraphite-identity` | 15 | 1 | +1.49% |
| `-fprefetch-loop-arrays` | 18 | 3 | +1.05% |

`-march=native` is now 8 of 17 accepted in the memory-bound cluster, just short of a strict majority: an accept on palm
(9 of 18) would still fall short, and two more would make it fast-track.

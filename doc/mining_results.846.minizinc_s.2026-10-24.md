# `cfm mine` results: 846.minizinc_s on `niwot`, 2026-10-24

The third SPECspeed benchmark mined on `niwot`. `846.minizinc_s` (the MiniZinc constraint solver) has
no rate counterpart, so this is its first mine on either host. It uses pthreads and runs unpinned.

## Headline result

**Nothing accepted: plain `-O3` stays the best (ratio 4.659).** A clean reject, not a measurement problem.

- **LTO and PGO both hurt.** `-flto` measured -1.66% and PGO -2.42%, and both CIs sit entirely below
  baseline's.
- **M4 fast-tracked `-flto`, `-Ofast` and `-ffast-math` on vpr_s's 1-of-1 memory-bound records**, as
  [the vpr_s write-up](mining_results.834.vpr_s.2026-10-24.md) predicted. All three were rejected. The
  fast track skips only the screening trial, so it cost nothing here, but the priors didn't transfer.
- No candidate came within the 1% bar. The best was `-freorder-functions` at +0.59%, CIs overlapping.

## Run metadata

| | |
|---|---|
| Host | `niwot`: AMD Ryzen AI 7 350 (4 Zen5 + 4 Zen5c, 16 threads), 60 GB RAM |
| Command | `CFM_SPEC_CONFIG=ryzen350_64gb.gcc_O3.cfg cfm mine 846.minizinc_s` (uncapped, queued after `853.ns3_s`) |
| Code | `main` at `9e0d86e` (later commits are doc-only) |
| Experiment id | 169 |
| Started / finished | 2026-10-24T17:30:55Z / 2026-10-24T21:30:16Z (4h00m) |
| Final status | `converged` |
| Trials | 56 (839-894) |
| Candidates screened / confirmed | 8 / 0 (plus 3 fast-tracked, none accepted) |
| Fast-tracked (M4) | `-flto`, `-Ofast`, `-ffast-math` (all rejected) |
| Winning flags | `["-O3"]`, 0.0% |
| Thread placement | pthread, not pinned |
| Guards | bandwidth gate 43.8-45.8 GB/s before every run, waited only before the first; no slow-rep reruns; no audit warnings |
| Power profile | `balanced`; CPU temp 86.6-92.8°C, package power 21.0-23.0 W |

## Baseline

| Trial | Role | Ratio |
|---|---|---|
| 839 | warm-up (excluded from CI) | 4.655 |
| 840 | warm-up (excluded from CI) | 4.654 |
| 841 | calibration | 4.642 |
| 842 | calibration | 4.665 |
| 843 | calibration | 4.669 |
| 885 | recheck after Phase 4 | 4.686 (+0.58%, not flagged) |

Calibration mean **4.6589**, 95% CI **[4.623, 4.695]** (±0.77%).

**Shape: `memory-bound`, 36.9%**, `vectorization_density=low`, `allocation_pressure=moderate`, from the corpus
(`reference-matrix:amd-370-64gb`). Below the 55% gate, so nothing was excluded on `resource_dominance`.
The low vectorization density excluded both `-mprefer-vector-width=` candidates.

## Phase 3 screening (vs. most recent calibration rep, 4.6694)

| Flags | Ratio | Delta |
|---|---|---|
| `-fprefetch-loop-arrays` | 4.691 | +0.46% |
| `-fgraphite-identity` | 4.634 | -0.76% |
| `-freorder-blocks-and-partition` | 4.651 | -0.40% |
| `-freorder-functions` | 4.663 | -0.14% |
| `-fno-semantic-interposition` | 4.706 | +0.78% |
| `-funroll-loops` | 4.608 | -1.32% |
| `-march=native` | 4.643 | -0.57% |
| `-fipa-pta` | 4.614 | -1.19% |

All eight survived.

## Phase 4 confirmation (3 reps each, vs. baseline CI [4.623, 4.695])

| Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|
| `-freorder-functions` | 4.663, 4.694, 4.703 | 4.687 | [4.634, 4.739] | +0.59% | reject |
| `-freorder-blocks-and-partition` | 4.657, 4.679, 4.698 | 4.678 | [4.628, 4.729] | +0.41% | reject |
| `-Ofast` (fast-tracked) | 4.692, 4.688, 4.641 | 4.674 | [4.604, 4.744] | +0.32% | reject |
| `-ffast-math` (fast-tracked) | 4.664, 4.688, 4.662 | 4.672 | [4.635, 4.708] | +0.27% | reject |
| `-fno-semantic-interposition` | 4.666, 4.658, 4.687 | 4.670 | [4.634, 4.707] | +0.25% | reject |
| `-fgraphite-identity` | 4.669, 4.650, 4.635 | 4.651 | [4.609, 4.693] | -0.16% | reject |
| `-fprefetch-loop-arrays` | 4.659, 4.641, 4.634 | 4.645 | [4.611, 4.678] | -0.31% | reject |
| `-march=native` | 4.639, 4.654, 4.636 | 4.643 | [4.619, 4.667] | -0.34% | reject |
| `-fipa-pta` | 4.639, 4.616, 4.600 | 4.618 | [4.569, 4.667] | -0.87% | reject |
| `-funroll-loops` | 4.599, 4.629, 4.609 | 4.612 | [4.574, 4.650] | -1.00% | reject |
| `-flto` (fast-tracked) | 4.568, 4.581, 4.596 | 4.582 | [4.547, 4.616] | **-1.66%** | reject (CI-clear below) |

Nothing was accepted, so Phase 5 had nothing to combine and the winning set stayed `-O3`.

## Phase 6 multipliers (on `-O3`)

| Stage | Flags | Ratios | Mean | 95% CI | Delta | Verdict |
|---|---|---|---|---|---|---|
| PGO | `-O3 -fprofile-use` | 4.547, 4.540, 4.552 | 4.546 | [4.531, 4.561] | **-2.42%** | reject (CI-clear below) |
| Microarch | `-O3 -march=znver5` | 4.661, 4.653, 4.630 | 4.648 | [4.608, 4.688] | -0.24% | reject |
| Microarch | `-O3 -mtune=znver5` | 4.683, 4.660, 4.655 | 4.666 | [4.630, 4.702] | +0.15% | reject |
| Vector width | — | | | | | skipped (no deferred candidates) |

No near-miss PGO variant: no Phase 4 reject was CI-clear above baseline.

## Why LTO and PGO lose here

Not investigated. Both regressions are about 2%, small next to the +10-25% gains elsewhere. A constraint
solver's hot path depends heavily on the model it's solving, so PGO's training input may not represent
the reference models. That's the same reading as gem5 and abc (opportunity #21), where
`-fprofile-partial-training` recovered some or all of the loss. LTO's -1.66% may be inlining growth in a
search loop. Neither is worth a follow-up at this size.

## Knowledge table after this run (`memory-bound`, `niwot`)

The fast-tracked flags now have a second record each:

| Flag | n | Accepted | Mean delta |
|---|---|---|---|
| `-flto` | 2 | 1 | +8.00% |
| `-fprofile-use` | 2 | 1 | +1.22% |
| `-Ofast` | 2 | 1 | +0.98% |
| `-ffast-math` | 2 | 1 | +0.88% |

At 1 of 2 none of them qualifies for the fast track any more (it needs a strict majority), so the next
memory-bound mine screens them normally.

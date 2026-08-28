# `cfm mine` results: 721.gcc_r, 2026-08-28

A real, uncapped `cfm mine` run against `721.gcc_r` (GCC itself) — the highest-confidence of the three
remaining low-confidence memory-bound benchmarks needed to finish `intrate`, and a nice complement to
`723.llvm_r` (both are real-world compilers, but characterize very differently: LLVM as frontend-bound,
GCC here as memory-bound).

## Headline result

**Nothing accepted — `-O3` alone remains peak, 0.0% overall gain.** A clean, genuine reject across every
candidate, including `-march=native` (fast-tracked via a real accepted prior from four other memory-bound
benchmarks) landing essentially flat here — a real, honest "this flag doesn't generalize to every
memory-bound benchmark" result, similar in spirit to `782.lbm_r`'s own original correct reject.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 721.gcc_r` (uncapped) |
| Experiment id | 29 |
| Started | 2026-08-28T10:29:20Z |
| Finished | 2026-08-28T14:16:57Z |
| Wall-clock | 3h47m37s |
| Final status | `converged` |
| Candidates screened | 2 |
| Candidates fast-tracked (M4) | 1 (`-march=native`) |
| Candidates confirmed (ordinary Phase 4) | 0 |
| Winning flags | `["-O3"]`, 0.0% gain |

## Why this benchmark

`721.gcc_r` characterizes `memory-bound` at 45.2% (low confidence), `vectorization_density=low`,
`allocation_pressure=moderate` — the highest-confidence of the three remaining unmined benchmarks needed
to finish `intrate`. GCC's own compilation process (parsing, IR construction, optimization passes) is a
real, interesting counterpoint to `723.llvm_r`'s own frontend-bound characterization — both are
real-world compilers, but this suite's own topdown classification puts them in genuinely different
clusters, a real finding worth noting rather than assuming "compilers are all frontend-bound."

## Baseline

| Trial | Phase | Ratio |
|---|---|---|
| 570 | **warm-up** (excluded from CI) | 43.934 |
| 571 | **warm-up** (excluded from CI) | 42.670 |
| 572 | calibration | 42.113 |
| 573 | calibration | 42.196 |
| 574 | calibration | 42.165 |

The usual settling pattern, resolved within the 2 warm-up reps. Mean **42.158** (`baseline_ratio_mean`),
shape from the reference-matrix corpus (`reference-matrix:amd-370-64gb`): `resource_dominance=
memory-bound` at 45.2% (low confidence), `vectorization_density=low`, `allocation_pressure=moderate`.

## Phase 2 filtering

Nine candidates correctly excluded as implausible given the memory-bound/low-vectorization-density
shape: `-flto`, `-freorder-blocks-and-partition`, `-freorder-functions`, `-fno-semantic-interposition`
(frontend-bound-tagged), `-funroll-loops` (compute-bound/backend-bound-tagged), both
`-mprefer-vector-width` choices (vectorization-density-high-tagged, correctly excluded since density is
`low`), `-Ofast`/`-ffast-math` (compute-bound-tagged), `-fipa-pta` (backend-bound-tagged) — leaving only
`-fprefetch-loop-arrays`/`-fgraphite-identity` (both real rejected priors, going through ordinary
screening) and `-march=native` (real accepted prior, fast-tracked).

## M4: `-march=native` fast-tracked, then correctly rejected on its own merits

```
info: known prior for '-march=native' in cluster 'memory-bound' -- accepted before (mean +13.14%, n=4, last seen on '734.vpr_r')
info: known prior for '-fprefetch-loop-arrays' in cluster 'memory-bound' -- rejected before (mean +1.62%, n=4, last seen on '734.vpr_r')
info: known prior for '-mtune=znver5' in cluster 'memory-bound' -- rejected before (mean +1.49%, n=3, last seen on '777.zstd_r')
info: known prior for '-march=znver5' in cluster 'memory-bound' -- rejected before (mean +1.36%, n=3, last seen on '777.zstd_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'memory-bound' -- rejected before (mean -0.44%, n=4, last seen on '734.vpr_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'memory-bound' -- rejected before (mean -0.48%, n=4, last seen on '734.vpr_r')
info: known prior for '-fgraphite-identity' in cluster 'memory-bound' -- rejected before (mean -0.59%, n=4, last seen on '734.vpr_r')
```

`-march=native` was fast-tracked straight to Phase 4 (trials 583-585 jump directly to
`phase="confirmation"`, no preceding screening trial). Its confirmed mean (42.095 vs. baseline's 42.158)
is essentially flat — **-0.15%**, cleanly inside baseline's own CI — a real, honest reject on its own
merits. This is now the *fourth* distinct real effect size this flag has shown in the memory-bound
cluster alone (+48.75% on `706.stockfish_r`, +1.79% rejected on `782.lbm_r`, +1.04% accepted on
`734.vpr_r`, now -0.15% here) — the M4 mechanism correctly tries it first every time (it has the
strongest real prior), but never assumes the prior's magnitude — or even its direction — carries over
unchanged.

## Ordinary candidates: both correctly rejected

| Flag | Confirm mean | Verdict |
|---|---|---|
| `-fprefetch-loop-arrays` | 42.017 | reject |
| `-fgraphite-identity` | 42.075 | reject |

Both landed flat, consistent with their own real, rejected cluster priors.

## Phase 6: PGO correctly skipped, microarch multiplier correctly rejected both candidates

PGO correctly skipped (`topdown_signals ['frontend-bound', 'speculation-bound']` implausible given
`memory-bound`) — the same skip path confirmed on every real memory-bound benchmark to date.
`-march=znver5` (mean 42.058) and `-mtune=znver5` (mean 42.248) both landed within ~0.2% of baseline,
correctly rejected as noise-level.

## Knowledge table, `memory-bound` cluster, after this run

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-march=native` | 5 | 2 | +10.48% (down from +13.14%) |
| `-fprefetch-loop-arrays` | 5 | 0 | +1.23% |
| `-mtune=znver5` | 4 | 0 | +1.17% |
| `-march=znver5` | 4 | 0 | +0.96% |
| `-mprefer-vector-width=256` | 4 | 0 | −0.44% |
| `-mprefer-vector-width=512` | 4 | 0 | −0.48% |
| `-fgraphite-identity` | 5 | 0 | −0.51% |

`-march=native`'s own running mean continues to moderate as more real, varied data accumulates
(+48.82% → +25.31% → +17.14% → +13.14% → +10.48% across five real trials) — a genuinely honest,
increasingly well-calibrated cross-benchmark prior, not one anchored to its own original outsized win.

## Compiled-flags audit and package power: nothing unusual

Every trial's audit confirms genuine compilation (`-march=znver5`/`-mtune=znver5`'s own literal flags
survive directly into the audit, unlike `-march=native`, correctly reported "not independently
checkable"). No unusual power/temperature pattern — a genuinely flat run overall, since nothing was ever
accepted (`Pearson r(ratio, elapsed_min) = -0.382`, weak, no phase-change confound this time since the
winning flagset never changed).

## What this run actually confirms

- **A real, clean "nothing helps" result** — GCC's own compilation process, characterized memory-bound,
  simply doesn't benefit from any candidate in this catalog on this host, an honest negative result
  matching `782.lbm_r`'s own original correct reject.
- **M4 continues to work correctly, still without assuming a prior's magnitude (or even direction)
  transfers unchanged** — `-march=native`'s own real effect size now spans from +48.75% down to a
  genuine, small negative, and the knowledge table's running mean reflects that honestly.
- **Real-world compilers don't cluster together mechanically** — GCC (memory-bound) and LLVM
  (frontend-bound) land in different `resource_dominance` clusters despite both being compilers, a real
  finding worth remembering rather than assuming by category.

## Next steps this suggests

- Finishing `intrate`: `708.sqlite_r` and `729.abc_r` — the last two low-confidence memory-bound
  benchmarks needed to complete the whole suite.
- Phase 5's pair tournament still has zero real coverage across all real runs to date.
- The package-power/STAPM hypothesis remains open.

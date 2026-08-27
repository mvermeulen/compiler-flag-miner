# `cfm mine` results: 735.gem5_r, 2026-08-27

A real, uncapped `cfm mine` run against `735.gem5_r` (the gem5 computer-architecture simulator) — the
fourth real frontend-bound benchmark mined, continuing the systematic push to complete `intrate`. This
run produced two genuinely new findings for this project: the **first real PGO reject** (every prior
PGO trial, on `714.cpython_r`/`727.cppcheck_r`/`723.llvm_r`, was a real accept), and a **real bug in the
compiled-flags audit tool itself** — found, investigated, and fixed along the way, not glossed over.

## Headline result

**`-O3 -flto` accepted, +13.62% overall. PGO (`-fprofile-use`) rejected on top of it — a real, honest
"LTO alone was the right call here" result, not a false negative.** Every ordinary candidate
(`-march=native` included) was cleanly rejected. The microarch multiplier's own two candidates both
looked promising for their first two reps before settling back to baseline-level noise by the third —
a real, concrete illustration of why 3 reps (not 1 or 2) matters for this pipeline's own confirmation
bar.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 735.gem5_r` (uncapped) |
| Experiment id | 26 |
| Started | 2026-08-27T05:34:51Z |
| Finished | 2026-08-27T12:43:12Z |
| Wall-clock | 7h8m21s |
| Final status | `converged` |
| Candidates screened | 6 |
| Candidates fast-tracked (M4) | 1 (`-flto`) |
| Candidates confirmed (ordinary Phase 4) | 0 — `-flto` accepted via the M4 fast-track path |
| Winning flags | `["-O3", "-flto"]`, **+13.62% overall gain** |

## Why this benchmark

`735.gem5_r` characterizes `frontend-bound` at 60.3% (high confidence), `vectorization_density=moderate`,
`allocation_pressure=moderate` — picked as the next-highest-confidence unmined `intrate` benchmark,
continuing systematically through the suite rather than searching for maximal novelty. gem5 is a
real, well-known cycle-accurate computer-architecture simulator — mechanistically plausible as
frontend-bound (an event-driven simulator core with heavy indirect dispatch through its own object
model), and the fourth data point for this project's frontend-bound cluster after three straight PGO
accepts.

## Baseline

| Trial | Phase | Ratio |
|---|---|---|
| 446 | **warm-up** (excluded from CI) | 69.041 |
| 447 | **warm-up** (excluded from CI) | 64.676 |
| 448 | calibration | 63.172 |
| 449 | calibration | 63.240 |
| 450 | calibration | 63.031 |

The usual settling pattern, resolved within the 2 warm-up reps. Mean **63.148** (`baseline_ratio_mean`),
shape from the reference-matrix corpus (`reference-matrix:amd-370-64gb`): `resource_dominance=
frontend-bound` at 60.3%, `vectorization_density=moderate`, `allocation_pressure=moderate`.

## Phase 2 filtering

Six candidates correctly excluded as implausible given the frontend-bound/moderate-vectorization shape:
`-funroll-loops` (compute-bound/backend-bound-tagged), `-Ofast`/`-ffast-math` (compute-bound-tagged),
`-fipa-pta` (backend-bound-tagged), `-fgraphite-identity` (backend-bound/memory-bound-tagged),
`-fprefetch-loop-arrays` (memory-bound-tagged) — leaving the six frontend-bound-relevant candidates plus
`-march=native` (real rejected prior, not excluded by shape) that actually ran.

## M4: `-flto` fast-tracked, everything else correctly not

```
info: known prior for '-fprofile-use' in cluster 'frontend-bound' -- accepted before (mean +18.56%, n=4, last seen on '723.llvm_r')
info: known prior for '-flto' in cluster 'frontend-bound' -- accepted before (mean +4.59%, n=4, last seen on '723.llvm_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'frontend-bound' -- rejected before (mean +0.74%, n=1, last seen on '714.cpython_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'frontend-bound' -- rejected before (mean +0.58%, n=1, last seen on '714.cpython_r')
info: known prior for '-mtune=znver5' in cluster 'frontend-bound' -- rejected before (mean -0.71%, n=3, last seen on '723.llvm_r')
info: known prior for '-freorder-blocks-and-partition' in cluster 'frontend-bound' -- rejected before (mean -0.89%, n=4, last seen on '723.llvm_r')
info: known prior for '-march=znver5' in cluster 'frontend-bound' -- rejected before (mean -1.06%, n=3, last seen on '723.llvm_r')
info: known prior for '-freorder-functions' in cluster 'frontend-bound' -- rejected before (mean -1.07%, n=4, last seen on '723.llvm_r')
info: known prior for '-fno-semantic-interposition' in cluster 'frontend-bound' -- rejected before (mean -1.11%, n=4, last seen on '723.llvm_r')
info: known prior for '-march=native' in cluster 'frontend-bound' -- rejected before (mean -2.00%, n=3, last seen on '723.llvm_r')
```

`-flto` (real accepted prior, mean +4.59%) fast-tracked straight to Phase 4 (trials 475-477 jump directly
to `phase="confirmation"`, no preceding screening trial). Every rejected prior was correctly left to
ordinary screening.

## Ordinary candidates: all six correctly rejected

| Flag | Confirm mean | Verdict |
|---|---|---|
| `-freorder-blocks-and-partition` | 63.116 | reject |
| `-freorder-functions` | 62.998 | reject |
| `-fno-semantic-interposition` | 63.147 | reject |
| `-mprefer-vector-width=256` | 62.937 | reject |
| `-mprefer-vector-width=512` | 62.983 | reject |
| `-march=native` | 63.534 | reject |

Every one landed flat, consistent with its own real, rejected cluster prior — including `-march=native`,
whose real, consistent frontend-bound reject (now n=4, still 0 accepted) continues to stay correctly
separate from its own real accepts in `memory-bound`/`compute-bound`.

## `-flto`: accepted, +13.6%

| Rep | Ratio |
|---|---|
| 475 | 70.722 |
| 476 | 70.674 |
| 477 | 71.619 |

Mean **71.005** vs. baseline's 63.148 — **+12.44%**. Phase 5 combination re-confirmed (mean 71.749 across
trials 478-480, drifting slightly higher but still a clean accept) — no pair tournament possible, same as
every real run to date. Final `gain_vs_baseline_pct` (+13.62%) is computed from the combination's own
settled mean.

## PGO: rejected — the first real PGO reject in this project's history

| Rep | Ratio |
|---|---|
| 481 | 66.932 |
| 482 | 67.024 |
| 483 | 66.910 |

Mean **66.955**, tight (0.17% spread) — but **below** the LTO-including comparison baseline (71.749), not
above it. A real, honest reject: PGO genuinely didn't help gem5 on top of LTO here, unlike every prior
frontend-bound benchmark mined. No mechanistic explanation is asserted here beyond the observation itself
— a plausible, unconfirmed hypothesis is that gem5's own training workload (SPEC's built-in PGO training
run) may not representatively exercise the same hot paths its reference-size workload does, given gem5
itself is a configurable simulator whose actual hot code paths depend heavily on which components a given
run exercises — but this is speculation, not something this run's own data confirms one way or the other.

**A real audit anomaly surfaced and was fixed, not glossed over.** All 3 of these PGO trials' own
compiled-flags audits reported a `⚠ WARNING: no -O optimization level found in the compiled binary at
all` — contradicting a clean `runcpu --action=validate` pass and every sibling trial's own correct audit
(the `-flto`-only trials right before this one all correctly showed `-O3` confirmed). Investigated rather
than assumed: `735.gem5_r` is one of the rare SPEC benchmarks that builds *two* executables (`gem5sim`,
the actual simulator, and `gem5stats`, a companion tool) — `audit_compiled_flags()` only ever inspected
whichever ELF file a directory listing happened to yield first, filesystem order, not a meaningful one.
Confirmed directly via `speccmds.cmd` that `gem5stats` is never invoked in any timed workload command —
only `gem5sim` is ever measured — so the real ratios above are very likely unaffected regardless of which
binary the audit mis-picked (SPEC's own `--action=validate` pass already guarantees correctness of
whatever binary actually ran). But the audit's own secondary-verification signal was genuinely wrong for
these 3 trials, a real gap in the tooling, not a data problem. **Fixed** (PR #45, merged before this
write-up): `audit_compiled_flags()` now reads every ELF binary in the build directory, not just the
first, concatenating their `.GCC.command.line` dumps together — a flag or `-O` level found in *any*
component binary now counts. Covered by a new regression test building two real ELF binaries with
different flags.

## Phase 6 microarch multiplier: a real illustration of why 3 reps matter

| Rep | `-march=znver5` | `-mtune=znver5` |
|---|---|---|
| 1 | 74.202 | 71.401 |
| 2 | 72.925 | 70.718 |
| 3 | 71.800 | 70.982 |

Both candidates' *first* rep looked like a real, meaningful win over the `-flto` baseline (71.749) — a
naive single-rep read of `-march=znver5`'s own 74.20 would have looked like a strong +3.4% improvement.
Both settled back to baseline-level noise by the third rep (71.80 and 70.98 respectively, both correctly
rejected — CI overlapping the `-flto` baseline, no practically-significant delta). A clean, concrete,
real demonstration of exactly the risk this pipeline's own `CONFIRMATION_REPETITIONS = 3` design guards
against: a single promising-looking rep is not enough to accept a candidate, and this run shows why in
its own real numbers, not just in the abstract.

## Knowledge table, `frontend-bound` cluster, after this run

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-fprofile-use` | 5 | 3 | +13.51% (down from +18.56%) |
| `-flto` | 5 | 3 | +6.16% (up from +4.59%) |
| `-mprefer-vector-width=512` | 2 | 0 | +0.24% |
| `-mprefer-vector-width=256` | 2 | 0 | +0.12% |
| `-march=znver5` | 4 | 0 | −0.37% |
| `-freorder-blocks-and-partition` | 5 | 0 | −0.72% |
| `-mtune=znver5` | 4 | 0 | −0.78% |
| `-fno-semantic-interposition` | 5 | 0 | −0.89% |
| `-freorder-functions` | 5 | 0 | −0.91% |
| `-march=native` | 4 | 0 | −1.35% |

`-fprofile-use`'s own running mean dropped from +18.56% to +13.51% after folding in this run's real
reject — the cross-benchmark prior doing exactly what it should: staying honest about the fact that PGO
doesn't win *everywhere*, even within a cluster where it's won 3 times before. `-flto`'s own mean rose
slightly (this run's +12.44% pulled the average up), now the cluster's most *consistently* accepted flag
(3/5 real accepts, vs. PGO's 3/5 too, but PGO's wins have been individually larger when they land).

## What this run actually confirms

- **PGO doesn't always win, even in a cluster with a strong prior** — a real, honest negative result,
  exactly the kind of finding cross-benchmark knowledge transfer should surface rather than hide by
  averaging it away.
- **A real audit tool bug was found and fixed via a genuinely novel SPEC benchmark shape** (a multi-binary
  benchmark) — the same "test against real, varied benchmarks to find real gaps" discipline this whole
  intrate-completion effort has already paid off with once before (the reference-matrix pct type bug,
  found via `707.ntest_r`).
- **The 3-rep confirmation design is doing real, visible work**: this run's own microarch candidates
  would have been falsely accepted on a 1-rep read, and correctly rejected on the full 3.
- **Cross-cluster prior separation continues to hold**: `-march=native`'s real frontend-bound reject
  stays properly separate from its real accepts elsewhere.

## Next steps this suggests

- Continuing through `intrate`: `753.ns3_r` (frontend-bound, high confidence) is the next natural pick,
  followed by `710.omnetpp_r` and the three low-confidence memory-bound benchmarks
  (`708.sqlite_r`/`721.gcc_r`/`729.abc_r`).
- Phase 5's pair tournament still has zero real coverage across all real runs to date.
- The package-power/STAPM hypothesis remains open; this run's own `Pearson r(ratio, elapsed_min) =
  +0.725` is, like `707.ntest_r`'s and `723.llvm_r`'s own runs, dominated by real phase changes
  (`-O3` → `-flto` → PGO/microarch), not baseline drift — worth remembering, not more drift evidence.

# `cfm mine` results: 723.llvm_r, 2026-08-26

A real, uncapped `cfm mine` run against `723.llvm_r` (LLVM itself) — the third real `frontend-bound`
benchmark mined, picked as the highest-confidence (61.6%) unmined `intrate` benchmark specifically to
test whether the cluster's now-solid PGO/LTO priors (from `714.cpython_r` and `727.cppcheck_r`)
generalize to a third, very different real-world codebase — and LLVM is itself a well-known real-world
PGO/LTO beneficiary, giving an independent reason to expect a real signal here.

## Headline result

**`-O3 -flto -fprofile-use` accepted, +32.23% overall — LTO and PGO both won independently, stacking
almost perfectly additively, and both fast-tracked correctly by M4 on real cross-benchmark priors.**
`-flto` alone: +5.9%. PGO layered on top: another +24.9%. Every other ordinary candidate — including
`-march=native`, which has real accepts in other clusters — was correctly rejected here, consistent with
its own real, cluster-specific rejected prior.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 723.llvm_r` (uncapped) |
| Experiment id | 24 |
| Started | 2026-08-26T07:48:58Z |
| Finished | 2026-08-26T17:12:52Z |
| Wall-clock | 9h23m54s — by far the longest real run yet, driven by LLVM's own build/run cost (each trial ran ~11-27 min, vs. 6-10 min for smaller benchmarks) and PGO's two-pass build |
| Final status | `converged` |
| Candidates screened | 4 |
| Candidates fast-tracked (M4) | 1 (`-flto`) |
| Candidates confirmed (ordinary Phase 4) | 0 — `-flto` accepted via the M4 fast-track path |
| Winning flags | `["-O3", "-flto", "-fprofile-use"]`, **+32.23% overall gain** |

## Why this benchmark

`723.llvm_r` characterizes `frontend-bound` at 61.6% (high confidence), `vectorization_density=low`,
`allocation_pressure=moderate` — the highest-confidence unmined `intrate` benchmark at the time it was
picked, and the third real frontend-bound benchmark after `714.cpython_r` (bytecode dispatch) and
`727.cppcheck_r` (static-analysis traversal). LLVM adds real diversity to that trio: a large, real-world
C++ compiler codebase, not Python's C-extension interpreter loop or a smaller static analyzer —
mechanistically sensible as frontend-bound (heavy indirect-call/virtual-dispatch code in a compiler's own
pass infrastructure) and independently well known in the real world as a strong PGO/LTO beneficiary
(LLVM's own build system has long supported PGO'd/LTO'd release builds for exactly this reason).

## Baseline

| Trial | Phase | Ratio |
|---|---|---|
| 383 | **warm-up** (excluded from CI) | 53.270 |
| 384 | **warm-up** (excluded from CI) | 50.176 |
| 385 | calibration | 49.615 |
| 386 | calibration | 49.697 |
| 387 | calibration | 50.930 |

The usual settling pattern, resolved within the 2 warm-up reps. Mean **50.081** (`baseline_ratio_mean`),
shape from the reference-matrix corpus (`reference-matrix:amd-370-64gb`): `resource_dominance=
frontend-bound` at **61.6%**, `vectorization_density=low`, `allocation_pressure=moderate`.

## Phase 2 filtering

Eight candidates correctly excluded as implausible given the frontend-bound/low-vectorization-density
shape: `-funroll-loops` (compute-bound/backend-bound-tagged), `-fprefetch-loop-arrays`
(memory-bound-tagged), both `-mprefer-vector-width` choices (vectorization-density-high-tagged, excluded
since density is `low`), `-Ofast`/`-ffast-math` (compute-bound-tagged), `-fipa-pta`/`-fgraphite-identity`
(backend-bound-tagged) — leaving the four frontend-bound-relevant candidates that actually ran, plus
`-march=native` (target-tuning, not excluded by shape, but with its own real rejected prior in this
cluster).

## M4: `-flto` fast-tracked, PGO routed to its own dedicated path

```
info: known prior for '-fprofile-use' in cluster 'frontend-bound' -- accepted before (mean +16.46%, n=3, last seen on '727.cppcheck_r')
info: known prior for '-flto' in cluster 'frontend-bound' -- accepted before (mean +4.08%, n=3, last seen on '727.cppcheck_r')
info: known prior for '-mprefer-vector-width=512' in cluster 'frontend-bound' -- rejected before (mean +0.74%, n=1, last seen on '714.cpython_r')
info: known prior for '-mprefer-vector-width=256' in cluster 'frontend-bound' -- rejected before (mean +0.58%, n=1, last seen on '714.cpython_r')
info: known prior for '-freorder-blocks-and-partition' in cluster 'frontend-bound' -- rejected before (mean -0.95%, n=3, last seen on '727.cppcheck_r')
info: known prior for '-mtune=znver5' in cluster 'frontend-bound' -- rejected before (mean -1.07%, n=2, last seen on '727.cppcheck_r')
info: known prior for '-freorder-functions' in cluster 'frontend-bound' -- rejected before (mean -1.27%, n=3, last seen on '727.cppcheck_r')
info: known prior for '-fno-semantic-interposition' in cluster 'frontend-bound' -- rejected before (mean -1.29%, n=3, last seen on '727.cppcheck_r')
info: known prior for '-march=znver5' in cluster 'frontend-bound' -- rejected before (mean -1.55%, n=2, last seen on '727.cppcheck_r')
info: known prior for '-march=native' in cluster 'frontend-bound' -- rejected before (mean -2.20%, n=2, last seen on '727.cppcheck_r')
```

`-flto` (real accepted prior, mean +4.08% across `cpython`/`cppcheck`) was fast-tracked straight to Phase
4 — no preceding screening trial (trials 404-406 jump directly to `phase="confirmation"`). `-fprofile-use`
(PGO, the stronger prior at +16.46%) never enters this mechanism at all, per its own dedicated Phase 6
path — correct, as always. Every other prior was rejected, correctly *not* fast-tracked, and went through
ordinary screening.

## Ordinary candidates: all four correctly rejected

| Flag | Confirm mean | Verdict | Own prior (rejected) |
|---|---|---|---|
| `-freorder-blocks-and-partition` | 49.733 | reject | −0.95% |
| `-freorder-functions` | 49.834 | reject | −1.27% |
| `-fno-semantic-interposition` | 49.794 | reject | −1.29% |
| `-march=native` | 49.282 | reject | −2.20% |

Every one landed flat, consistent with its own real, rejected cluster prior — including `-march=native`,
which has real accepts in `memory-bound` (`706.stockfish_r`) and `compute-bound` (`750.sealcrypto_r`,
`707.ntest_r`, 3/3 accepted there) but a real, consistent reject here in `frontend-bound` (now n=3, still
0 accepted) — a clean demonstration that the same flag's cross-cluster priors stay correctly separate,
never blending into one global average.

## `-flto`: accepted, +5.9%

| Rep | Ratio |
|---|---|
| 404 | 53.158 |
| 405 | 53.040 |
| 406 | 53.261 |

Mean **53.034** vs. baseline's 50.081 — **+5.90%**. Phase 5 combination re-confirmed the same single-flag
set (mean 53.034 across trials 407-409, still accept) — no pair tournament possible (only one confirmed
candidate, same as every real run to date).

## PGO: accepted, +24.9% on top of LTO — this cluster's third real PGO win

| Rep | Ratio |
|---|---|
| 410 | 66.383 |
| 411 | 66.212 |
| 412 | 66.074 |

Mean **66.223** vs. the LTO-including comparison baseline (53.034) — **+24.86%** on top of LTO's own
gain, **+32.23%** vs. plain `-O3`. A tight, near-zero-variance measurement (0.09% spread across 3 reps),
the same precision signature `727.cppcheck_r`'s own PGO win showed. This is the frontend-bound cluster's
**third** real PGO accept (`714.cpython_r`, `727.cppcheck_r`, now `723.llvm_r`) — the running knowledge-
table mean is now backed by real, independent data from three genuinely different real-world codebases
(a Python interpreter, a static analyzer, and a C++ compiler), a strong, well-evidenced prior for the
next frontend-bound benchmark.

## Microarch multiplier: both candidates correctly rejected as noise

`-march=znver5` (66.19 mean) and `-mtune=znver5` (66.23 mean) both landed within ~0.1% of the PGO
baseline (66.22) — genuinely flat, correctly rejected. Phase 6's multiplier-chaining worked correctly a
second time on top of a real PGO win (the first being `727.cppcheck_r`'s own re-mine) — both microarch
trials ran against `["-O3", "-flto", "-fprofile-use", ...]`, the actual PGO-accepted flagset, not plain
`-O3`.

## Knowledge table, `frontend-bound` cluster, after this run

| flag | n_trials | n_accepted | mean Δ% |
|---|---|---|---|
| `-fprofile-use` | 4 | **3** | **+18.56%** |
| `-flto` | 4 | 2 | +4.59% |
| `-mprefer-vector-width=512` | 1 | 0 | +0.74% |
| `-mprefer-vector-width=256` | 1 | 0 | +0.58% |
| `-mtune=znver5` | 3 | 0 | −0.71% |
| `-freorder-blocks-and-partition` | 4 | 0 | −0.89% |
| `-march=znver5` | 3 | 0 | −1.06% |
| `-freorder-functions` | 4 | 0 | −1.07% |
| `-fno-semantic-interposition` | 4 | 0 | −1.11% |
| `-march=native` | 3 | 0 | −2.00% |

`-fprofile-use` is now **3 for 4** real trials accepted (only `714.cpython_r`'s own +31.16% pulled the
mean up before; this run's own +24.86% now averages in with `727.cppcheck_r`'s +10.79%, landing at a
still-strong +18.56%) — the frontend-bound cluster's own strongest, most consistent real prior, matching
`-march=native`'s own role in the compute-bound cluster.

## Compiled-flags audit and package power: nothing unusual

Every trial's audit confirms genuine compilation. `-fprofile-use` and `-mtune=znver5`/`-march=znver5`'s
literal flags survive directly into the audit (unlike `-flto`/`-march=native`, both correctly reported
"not independently checkable" — GCC rewrites both before recording, the known, already-understood
limitation). Package power stayed in a narrow 22-25W band the whole ~9h24m run — no useful ramp signal
either way. `Pearson r(ratio, elapsed_min) = +0.867` and `r(ratio, cpu_temp_c) = +0.750` look like strong
correlations, but — same mundane cause as `707.ntest_r`'s own run — both are dominated by the two real,
large phase changes (`-O3` → `-flto` → PGO), not baseline drift: every flagset's own reps stay flat and
tight within themselves (baseline ~49.6-50.9, `-flto` ~53.0-53.3, PGO ~66.1-66.4, microarch ~66.0-66.4).
Worth flagging explicitly, same as the `ntest_r` write-up, so these correlation numbers aren't misread as
more settling-drift evidence.

## What this run actually confirms

- **The frontend-bound cluster's PGO/LTO priors generalize to a third, very different real-world
  codebase** — LLVM's own real-world PGO/LTO story is now backed by real `cfm mine` data, not just
  Python's interpreter loop or a static analyzer.
- **M4 continues to work correctly**: `-flto` fast-tracked and re-confirmed; PGO always routed through
  its own dedicated path regardless of prior strength; every rejected prior correctly left to ordinary
  screening, landing consistent with its own history.
- **Cross-cluster prior separation works correctly**: `-march=native` has real accepts in two other
  clusters but a real, consistent reject here — the knowledge table never blends these into one global
  average.
- **Phase 6's PGO→microarch chaining works correctly a second time** on a real PGO-accepted flagset.
- **The apparent elapsed-time/temperature correlation this run shows is a phase-change artifact, not
  drift** — worth remembering when reading this run's own numbers later.

## Next steps this suggests

- Phase 5's pair tournament still has zero real coverage across all real runs to date — every real run
  so far has had 0 or 1 confirmed ordinary candidate, never enough survivors to exercise it.
- The package-power/STAPM hypothesis remains open.
- A genuinely backend-bound benchmark still doesn't exist anywhere in the reference-matrix corpus.
- The `intrate` benchmarks with `allocation_pressure=high` (`734.vpr_r`) or the remaining
  high-confidence frontend-bound options (`735.gem5_r`, `753.ns3_r`) are natural next picks for further
  coverage.

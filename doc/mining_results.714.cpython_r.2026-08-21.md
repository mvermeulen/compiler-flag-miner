# `cfm mine` results: 714.cpython_r, 2026-08-21

The fourth real `cfm mine` run (experiment 8 in `cfm.db`), and the first against a genuinely
different characterized shape — `frontend-bound` rather than the `memory-bound` stockfish and lbm
both were. First real test of the previously-always-excluded flag categories (`-flto`,
`-fprofile-generate`/`-fprofile-use`, `-freorder-*`, `-fno-semantic-interposition`). Same headline
conclusion as the first three runs (`-O3` remains peak), but with an important caveat on the PGO
result specifically, and a different flavor of the same baseline-timing sensitivity
`doc/mining_results.782.lbm_r.2026-08-21.md` already flagged.

## Headline result

**`-O3` alone remains the peak config, fourth benchmark in a row.** All 7 screened candidates were
rejected. Unlike the first three runs, this time the rejected set finally includes the flags this
project's own catalog calls "historically one of the highest-value single flags for frontend/
speculation-bound workloads" (`-fprofile-use`'s own note) — but **the PGO result here should not be
read as "PGO doesn't help cpython_r"**, for a real, already-documented reason below.

## Why `cpython_r`: an externally-motivated hypothesis, and why it didn't get a fair test

CPython's own real-world build system (`--enable-optimizations`) is well known for using PGO+LTO —
the specific reason this benchmark was picked over another frontend-bound option. But **M1's
candidate model doesn't implement PGO's real two-step workflow at all** — this is an already-documented
scope boundary, not a bug discovered here: `cfm/orchestrator.py`'s own module docstring lists
"LTO/PGO/microarch multipliers" under "Phase 6... not this module's concern yet," and
`cfm/compilers/gcc.py`'s `validate_flagset()` explicitly declines to auto-require `-fprofile-generate`
before `-fprofile-use`, with a comment noting the real flow is "a two-step build/run/rebuild sub-flow
... never simultaneous."

Phase 3/4 instead tried each as an independent, standalone single-flag addition to `-O3`:
- **`-fprofile-generate` alone** just builds an instrumented binary and measures *its* runtime — which
  carries real instrumentation overhead and produces no usable optimization on its own. Its `-4.26%`
  confirmed delta reflects that overhead, not a verdict on PGO.
- **`-fprofile-use` alone**, with no preceding `-fprofile-generate` run against this exact flagset,
  has no `.gcda` profile data to read — GCC most likely silently fell back to unguided compilation
  (equivalent to plain `-O3`). Its `-3.42%` delta doesn't reflect trained-profile behavior at all.

Confirmed `714.cpython_r` does ship a distinct SPEC `train` input (separate from `refrate`) — so
representativeness (`doc/DESIGN.md` §15's PGO caveat, about training on an unrepresentative workload)
was never actually the blocker here; the blocker is purely that the real generate→train→use workflow
is Phase 6 work, not implemented yet. A real PGO evaluation for this benchmark is still an open
question this run cannot answer.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 714.cpython_r` (uncapped) |
| Started | 2026-08-21T10:50:15Z |
| Finished | 2026-08-21T13:16:20Z |
| Wall-clock | **2h26m5s** |
| Final status | `converged` |
| Candidates screened | 7 (of 7 plausible) |
| Candidates accepted | 0 |
| Winning flags | `["-O3"]`, 0.0% gain |
| Baseline shape | `resource_dominance=frontend-bound`, `vectorization_density=low`, `allocation_pressure=moderate` |
| Characterization source | `reference-matrix:amd-370-64gb` |

## Candidate generation: the first real test of the frontend-bound category

Of 18 applicable catalog flags: 3 skipped (unresolved placeholders, as always), **8 excluded** as
implausible against this frontend-bound/low-vectorization shape — `-funroll-loops`,
`-fprefetch-loop-arrays` (now excluded via the `memory-bound-corroborated` signal, since this shape
contradicts it), `-mprefer-vector-width=256`/`512` (`vectorization-density-high` signal, contradicted
by `vectorization_density=low`), `-Ofast`, `-ffast-math`, `-fipa-pta`, `-fgraphite-identity` — leaving
**7 survivors**: `-flto`, `-fprofile-generate`, `-fprofile-use`, `-freorder-blocks-and-partition`,
`-freorder-functions`, `-fno-semantic-interposition`, `-march=native`. This is the first run where the
frontend/speculation-bound-targeted categories actually got a real trial rather than being filtered
out before ever costing a measurement.

## Screening → confirmation, flag by flag

| Flag | Screening ratio | Confirm mean | Delta vs. baseline | CI overlaps baseline? |
|---|---|---|---|---|
| `-flto` | 61.807 | 60.565 | **-4.46%** | yes |
| `-fprofile-generate` | 61.368 | 60.691 | **-4.26%** (instrumentation overhead — see caveat above) | yes |
| `-fprofile-use` | 61.725 | 61.222 | **-3.42%** (no profile data available — see caveat above) | yes |
| `-freorder-blocks-and-partition` | 61.656 | 60.482 | **-4.59%** | yes |
| `-freorder-functions` | 61.818 | 60.900 | **-3.93%** | yes |
| `-fno-semantic-interposition` | 61.174 | 60.582 | **-4.43%** | yes |
| `-march=native` | 60.906 | 60.680 | **-4.28%** | yes |

Baseline: 3 reps `[64.499, 63.632, 62.046]`, mean **63.392**, CI `[60.301, 66.483]`.

## A second flavor of baseline-timing sensitivity

Every single confirmed delta is negative and tightly clustered (-3.4% to -4.6%) — not scattered the
way genuine independent per-flag noise would be. That consistency, across flags with no obvious
mechanical reason to behave identically, points to a **systematic difference between baseline's
measurement window and everything after it**, not seven unrelated small regressions. Concretely:
baseline's 3 reps (mean 63.39) were measured first, in the run's opening ~14 minutes; every screening
and confirmation trial afterward — regardless of which flag — settled into a stable, lower ~60-62
band for the remaining ~2h12m of the run.

This is a different shape than `782.lbm_r`'s finding (a continuous ramp across ~7.8 hours) — here it
looks like a **step**, not a ramp: one anomalously-fast baseline window, then a stable steady state for
the rest of the run. Same underlying lesson as lbm's write-up, via a different mechanism: a baseline
measured once, early, in a short run can still end up unrepresentative of the run's own steady state.
Unlike lbm's case, this doesn't look like it masked a real *win* — every candidate's post-baseline
level is consistent with every other candidate's, suggesting the flags themselves are genuinely
similar to `-O3` here (or all mildly negative by a similar small amount) rather than one being secretly
better. But it reinforces the same open question lbm's write-up raised: is baseline's own
3-repetitions-all-at-once-at-the-start design the right one for a run of any real length.

## Phase 5 (greedy combine)

Not exercised again — zero Phase 4 acceptances, fourth run in a row. Still the most significant
remaining test-coverage gap: the greedy walk and pair-tournament logic have never run against a real
acceptance.

## Timing

Baseline/screening/confirmation trials landed at a brisk **~4:32-4:40 apart** — close to stockfish's
own cadence, confirming lbm's ~21-minute trials were a property of that specific workload, not a new
normal.

## Next steps this suggests

- **A real PGO evaluation needs Phase 6's two-step generate→train→use workflow implemented** before
  any catalog PGO entry gets a fair trial — this run is a live illustration of why single-flag-at-a-time
  screening structurally cannot evaluate it, not new information (already scoped as Phase 6 in
  `doc/DESIGN.md` and `cfm/orchestrator.py`'s own docstring), but a good concrete motivating example if
  Phase 6 needs a demonstration case when it's picked up.
- **The baseline-timing question from `782.lbm_r`'s write-up gets a second, independent data point
  here** — worth treating as a real design item (baseline re-measurement/refresh strategy for
  longer-than-trivial runs) rather than a one-off.
- Three memory-bound + one frontend-bound benchmark mined so far, all four converging on "`-O3` is
  already peak, nothing in the catalog helps on this host" — worth remaining open to the possibility
  that this host/GCC-version/catalog combination is just not finding real wins yet, rather than
  assuming the next differently-shaped benchmark will necessarily break the streak.

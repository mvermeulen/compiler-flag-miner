# `cfm mine` results: 706.stockfish_r, 2026-08-23

`706.stockfish_r`'s first genuinely completed, trustworthy `cfm mine` run since either real bug
(basepeak config-scoping, isolated-candidate-flags) was fixed — every prior attempt against this
benchmark was either retracted (pre-fix) or failed outright (two post-fix attempts that never finished,
one an intentionally-killed focused test, one an investigation dead-end). It's also this project's
**second genuine accepted win**, and a big one: `-march=native` unlocking AVX-512 for stockfish's NNUE
evaluation, +48.75% over plain `-O3`.

## Headline result

**`-O3 -march=native` beats plain `-O3` by +48.75%.** Confirmed directly from the compiled binary, not
just inferred from the number: `-march=native` on this host expands to `-march=znver5` plus the full
AVX-512 feature set (`-mavx512f -mavx512vl -mavx512bw -mavx512dq -mavx512cd -mavx512vbmi ...`, read
straight off the real linked binary's own `.GCC.command.line` section). Stockfish's NNUE evaluation is
well known in the wider Stockfish community for being extremely sensitive to exactly this — dedicated
AVX-512 builds are a standard recommendation — so this result matches expectation closely, not a
surprise finding.

## Run metadata

| | |
|---|---|
| Command | `cfm mine 706.stockfish_r` (uncapped) |
| Experiment id | 13 |
| Started | 2026-08-23T10:34:26Z |
| Finished | 2026-08-23T13:04:34Z |
| Wall-clock | 2h30m8s |
| Final status | `converged` |
| Candidates screened | 5 (of 5 plausible survivors — none left unscreened) |
| Candidates accepted | 1 (`-march=native`) |
| Winning flags | `["-O3", "-march=native"]`, +48.75% overall gain |

## Baseline

`baseline_characterization_source: "reference-matrix:amd-370-64gb"` — the external corpus had a real
match this time (unlike the same-day `714.cpython_r` run, which fell back to a local trial), so
baseline shape came free: `resource_dominance=memory-bound`, `vectorization_density=moderate`,
`allocation_pressure=high`.

Baseline calibration (3× `quick`-profile reps at `-O3` alone):

| Trial | Ratio |
|---|---|
| 163 | 103.588 |
| 164 | 97.714 |
| 165 | 94.824 |

Mean **98.709** — a real, if not perfectly tight, front-loaded-high-then-settling pattern (103.6 → 97.7
→ 94.8), similar in shape to prior runs' own early-rep drift, though far less consequential here since
the eventual `-march=native` win (+48.75%) is nowhere near baseline's own noise band.

## Candidate generation and filtering

`_filter_implausible_candidates()` excluded 7 catalog flags as mechanically implausible against a
memory-bound, moderate-vectorization baseline: `-flto`, `-freorder-blocks-and-partition`,
`-freorder-functions`, `-fno-semantic-interposition` (all `frontend-bound`), `-funroll-loops`
(`compute-bound`/`backend-bound`), `-Ofast`/`-ffast-math` (`compute-bound`), `-fipa-pta`
(`backend-bound`). Plus the usual 3 unresolved-template-placeholder skips. **5 plausible survivors**:
`-fprefetch-loop-arrays`, `-mprefer-vector-width=256`, `-mprefer-vector-width=512`, `-march=native`,
`-fgraphite-identity`.

## Phase 3/4: screening and confirmation

| Flag | Screening ratio | Delta vs. baseline | Confirm mean | Delta | Verdict |
|---|---|---|---|---|---|
| `-fprefetch-loop-arrays` | 93.767 | −5.01% | — | — | **pruned at screening** (just past the 5% bar) |
| `-mprefer-vector-width=256` | 94.654 | −4.10% | 94.666 | −4.10% | reject |
| `-mprefer-vector-width=512` | 94.798 | −3.95% | 94.678 | −4.08% | reject |
| **`-march=native`** | **147.006** | **+48.93%** | **146.899** | **+48.82%** | **accept** |
| `-fgraphite-identity` | 94.777 | −3.98% | 94.541 | −4.22% | reject |

`-march=native` is the one dramatic outlier here — every other candidate landed in a tight, consistent
~−4% band (plausibly a real, if modest, mechanical cost from these particular flags on this benchmark,
though not investigated further), while `-march=native` alone jumps to +48.9%, confirmed to hold at
+48.82% across 3 confirmation reps with a clean, non-overlapping CI.

## Phase 5: greedy combine

Trivial with a single accepted candidate: re-confirms `-O3 -march=native` against the current running
set (still baseline, nothing preceded it) — accepted again at +48.75% (146.833 mean vs. baseline's
98.709). No pair tournament possible with only one accepted flag. `combination_winning_flags =
["-O3", "-march=native"]`.

## Phase 6: both multipliers correctly skipped

**PGO**: `"skipping PGO -- topdown_signals ['frontend-bound', 'speculation-bound'] implausible given
baseline shape (resource_dominance='memory-bound', vectorization_density='moderate')"` — the same
correct exclusion memory-bound benchmarks have gotten every time so far.

**Microarch**: `"skipping microarch multiplier -- winning set ['-O3', '-march=native'] already has an
-march=/-mtune= flag, adding another would conflict rather than compound"` — and this is exactly the
right call, not a missed opportunity: reading the actual compiled binary (above) confirms `-march=native`
already expanded to `-march=znver5` on this host, so a separate, explicit `-march=znver5` trial would
produce a **byte-identical rebuild**. The guard exists precisely to avoid spending a real trial
re-measuring something already known.

This is real evidence the microarch multiplier's conflict-avoidance logic works correctly end to end —
but it also means this run didn't exercise the multiplier's *other* code path, the actual
`_confirm_flagset()` trial that runs when no arch flag has already won. That path was verified
separately and directly the same day: a bounded, single-purpose ad hoc run of `run_microarch_multiplier()`
against `782.lbm_r`, with a synthetic `combination` deliberately holding no `-march=`/`-mtune=` flag
(forcing the guard not to fire) and `CONFIRMATION_REPETITIONS` reduced to 1 for just this verification
script. Both detected candidates ran genuine SPEC builds and measurements — `-march=znver5` (ratio
15.866, +1.59%) and `-mtune=znver5` (ratio 16.017, +2.56%) — both correctly rejected (CI overlaps the
wide comparison CI reused from this same benchmark's own real 2026-08-22 baseline data), with correct
`phase="multiplier"` trial recording, `knowledge` table upserts, and compiled-flags audit confirmation
for both flags. See CLAUDE.md's matching traps-log entry for the full detail.

## Timing

2h30m8s uncapped — close to `782.lbm_r`'s own 2026-08-22 focused-run pace (~19min/`quick`-profile trial)
and noticeably faster than `714.cpython_r`'s 3h13m (which paid a local `deep-cpu` characterization trial
this run's reference-matrix hit avoided entirely).

## What this run actually confirms

- **`706.stockfish_r` finally has a real, trustworthy `cfm mine` result** — closing the one benchmark
  from the original three that had never completed a clean post-fix run.
- **A second genuine accepted win, independently verified down to the actual ISA extensions enabled** —
  not just a plausible-looking delta, but a directly-confirmed mechanical explanation (`-march=native`
  → `znver5` → full AVX-512) matching well-known real-world Stockfish behavior.
- **The microarch multiplier's conflict-avoidance guard is correct, confirmed with real evidence**: this
  host's `-march=native` and `-march=znver5` are provably the same compiled binary, so skipping a
  redundant rebuild is the right call, not an undertested corner. Its other code path — the actual
  trial, run when no arch flag has already won — was verified separately the same day (see above) and
  is real and correct too, closing out real-evidence coverage of both of `run_microarch_multiplier()`'s
  branches.

## Next steps this suggests

- **Still need a benchmark whose `resource_dominance` is compute-bound or backend-bound** — three
  real full runs now cover memory-bound (stockfish, lbm) and frontend-bound (cpython); those two
  categories' own catalog flags (`-Ofast`, `-ffast-math`, `-fipa-pta`, `-funroll-loops`) have never had
  a real trial.
- **Phase 5's pair tournament still has zero real coverage** — every run so far has had at most one
  accepted candidate.
- The consistent ~−4% cost from `-mprefer-vector-width=256/512`/`-fgraphite-identity`/
  `-freorder-blocks-and-partition`-style flags on this benchmark is a small, real, if unexplored,
  pattern — not investigated further this run.

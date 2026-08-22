# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

**Status: M0/M1's pipeline mechanics are real and working, but every prior "verified"/"real run"
result before 2026-08-21 measured the wrong binary — retracted pending a fresh corrected run.** See
`CLAUDE.md`'s Non-obvious traps log ("Resolved 2026-08-21: `generate_config()`'s per-trial `basepeak
= no` override was silently ignored by SPEC since this project's very first commit") for the full
story: every real trial ever run — M0's own original verification, and all four `doc/mining_results.
*.md` write-ups (two `706.stockfish_r` runs, `782.lbm_r`, `714.cpython_r`) — silently built and
measured the fixed *base*-tuning binary (`gcc_O3.cfg`'s own `-g -O3 -march=native`) regardless of
which candidate flags `cfm` intended to test. The bug is now fixed and re-verified live through `cfm`'s
own real `generate_config()`/`build()` code path (a genuinely different binary now gets built for a
genuinely different flag set) — but no `cfm measure`/`cfm mine` run has been *re-run* end-to-end since
the fix, so nothing should be treated as "shipped and verified" again until one has.
What *is* still true and unaffected by this bug: the mechanical pipeline's plumbing itself (build →
`wspy-run` → `wspy-validate`/`wspy-store`/`wspy-archetype` → `.rsf` ratio parsing → `cfm.db`
recording) all genuinely works, since none of that cares which flags went into a binary, only that one
got built and measured correctly; M1's phase state machine, statistics, and CLI wiring are real code
that ran for real, just against non-signal; Phase 2's `_filter_implausible_candidates()` and the
reference-matrix characterization work (`cfm/reference_matrix.py`) are both untouched by this bug
(neither depends on `generate_config()`'s peak-override rendering). The `knowledge` table's 13 rows
from the four affected runs have been cleared (all contaminated). Compiler-knowledge catalog wiring
beyond M1/M2.5's scope (a full signature-aware *ranking* pass, not just include/exclude — M2's "left to
M2's ranking pass" note, §14), cross-benchmark knowledge transfer, and the LLM driver are still ahead —
M2/M3/M4 (doc/DESIGN.md §13's layout table marks exactly what exists vs. what's still pending, module
by module) — none of which are blocked by this bug either, but none of which have been validated
against real signal yet.

## Documentation map

- `doc/prompt.txt` — the original design brief.
- `doc/DESIGN.md` — the architecture: agents, control flow, data model, cross-benchmark knowledge
  transfer, LLM integration, modularity seams, decisions (§15), and the phased build plan (§14,
  M0-M6). Read this before making any structural change — this file covers *practices*, DESIGN.md
  covers *design*.
- `config/gcc_flag_catalog.seed.json` — seed GCC/GFortran flag knowledge base.
- `schema/cfm_schema.sql` — `cfm.db` schema, kept separate from wspy's own `store.db`.
- `vendor/wspy` — the pinned wspy submodule (see "wspy dependency" below).
- `git log`/`git blame` for history — same convention wspy's `CLAUDE.md` uses; this file covers
  current practice only, not why a decision was made (that's `doc/DESIGN.md` §15, or git history for
  anything DESIGN.md itself doesn't capture).

## wspy dependency

`vendor/wspy` is a **git submodule** pinned to a specific, tested wspy commit — not a live checkout
this project tracks automatically. This exists because cfm's `instrumentation/wspy.py` depends on
wspy's exact CLI output *shape* (manifest field names, the run-index record schema, `wspy-archetype`'s
key=value output), and wspy is under active, independent development; pinning means a wspy change
never silently changes cfm's behavior mid-session, and an update is a deliberate, reviewable step.

- **Bootstrapping a fresh clone**: `./scripts/bootstrap_wspy.sh` — runs `git submodule update --init
  --recursive` then `make -C vendor/wspy` (checks for `gcc` and `sqlite3.h`/`libsqlite3-dev` first,
  with an actionable error if either's missing, rather than a raw compiler failure). Idempotent, safe
  to re-run after a submodule bump.
- **`cfm/config.py`'s default `wspy_dir`** resolves to `vendor/wspy` relative to the package's own
  location (matching `db.py`'s existing trick for finding `schema/cfm_schema.sql`), not the caller's
  cwd. `CFM_WSPY_DIR` still overrides this — point it at a live `~/source/wspy` working tree when
  actively co-developing a wspy change against cfm, before that change is ready to pin.
- **Bumping the pin** (an "orderly update," not an automatic one): on its own `feature/<slug>` branch —
  `cd vendor/wspy && git fetch && git checkout <new-ref> && cd ../.. && git add vendor/wspy` — then
  `make -C vendor/wspy` (rebuilding is not automatic) and `.venv/bin/pytest -q`, confirming
  `tests/test_wspy_interface.py` still passes before opening the PR. Those contract tests exist
  specifically to catch a wspy update silently changing an output shape cfm's parsers depend on — a
  bump that changes their result is real signal, not a flaky test to retry past.
- **`tests/test_wspy_interface.py`** is the interface-test suite the submodule pin exists to be checked
  against: real `wspy`/`wspy-run`/`wspy-store`/`wspy-archetype` invocations against a tiny toy C
  workload (compiled on the fly), asserting the exact manifest/run-index/archetype-output shapes
  `cfm/instrumentation/wspy.py` depends on. Skips cleanly (not a failure) when `vendor/wspy` hasn't
  been built yet, so `pytest -q` still passes on a fresh clone before `bootstrap_wspy.sh` has run.

## Development workflow

Full branch/PR discipline, same shape as wspy's:

- **Branch naming**: `feature/<slug>`, one branch per `doc/DESIGN.md` §14 milestone item (or a
  natural sub-piece of one), not a grab-bag spanning several. Doc-only tweaks (typo fixes, wording,
  a DESIGN.md clarification) can still go straight to `main`, same carve-out wspy uses — this applies
  to anything that changes actual behavior once `cfm/` exists: code, `schema/cfm_schema.sql`,
  `config/gcc_flag_catalog.seed.json` entries.
- **Starting a feature**: `git checkout main && git pull && git checkout -b feature/<slug>`.
- **While working**: commit normally; rebase/merge `main` in as needed, don't rewrite already-pushed
  history.
- **Finishing**: push the branch and open a PR with `gh pr create`. Merge through GitHub — don't
  merge feature branches into `main` locally and push `main` directly.
- **Scope**: keep a branch to one milestone item where practical; a phase-sized effort (e.g. all of
  M1) lands as a series of small merged PRs, not one long-lived branch — mirrors wspy's own
  "one branch per inventory row" rule.

## Schema and prompt-template versioning

- **`cfm.db`**: `schema_meta.schema_version` (already seeded at `1` in `schema/cfm_schema.sql`) bumps
  MINOR for an additive change (new column, new table), MAJOR for anything removed/renamed —
  identical semantics to wspy's `MANIFEST_SCHEMA_VERSION`/`STORE_SCHEMA_VERSION`/
  `RUN_INDEX_SCHEMA_VERSION` constants (see wspy's `CLAUDE.md` "Common edits" section for the exact
  model). A schema change lands with its version bump in the same commit, never separately.
- **LLM prompt templates** (`cfm/llm/prompts/`, once they exist): each template file carries its own
  version constant, bumped whenever a wording change could plausibly change model output — mirrors
  `prompts/perf_analysis.tmpl`'s `PERF_ANALYSIS_TEMPLATE_VERSION` line-comment convention exactly.
- **Automated drift check**: build a `tests/doc_version_check.sh`-equivalent alongside M0/M1 (not
  deferred indefinitely) that greps for `schema/cfm_schema.sql`'s `schema_meta` seed value and every
  prompt template's version constant, and fails if a doc (`doc/DESIGN.md` §7's embedded schema
  excerpt, or a future `doc/PROMPT_INDEX.md`) disagrees with the real file. `doc/DESIGN.md`'s §7 SQL
  excerpt has already drifted out of sync with `schema/cfm_schema.sql` once by hand during design —
  exactly the class of bug this check exists to catch once there's code to run it from.

## Enforced rules (non-negotiable)

- **Never commit SPEC-licensed content to this repo.** No SPEC CPU2026 source, benchmark
  inputs/workloads, or proprietary result files ever land in git history here — only generated
  artifacts we own outright (rendered configs, flag lists, reports, catalog/schema files).
- **No trial's performance number counts without a clean `runcpu --action=validate` pass on that
  exact trial.** No exceptions for flags that "should obviously be safe" — this is `doc/DESIGN.md`
  §11's correctness gate, promoted here so it survives even if DESIGN.md's rationale section is
  trimmed later.
- **Mining jobs assume exclusive machine access.** Perf counters and SPEC's own run discipline both
  want the box to itself (`doc/DESIGN.md` §11, §5) — never launch a mining run on a shared/multi-user
  host without explicit confirmation first, and never launch a second `cfm measure`/`cfm mine`
  invocation while one is already running on this host (`cfm/lock.py` now enforces this mechanically
  and will refuse the second one — see Non-obvious traps below for why it was added).
- **Maintain the "Non-obvious traps" log below.** Same discipline as wspy's
  `doc/INVESTIGATION_ARCHIVE.md` "Non-obvious implementation traps" section — a real gotcha found
  during implementation gets written down here, flagged as required reading before touching related
  code again, not left to be rediscovered.

## Non-obvious traps

- **Resolved 2026-08-09: SPEC's `.rsf` ratio field, confirmed against a real run — field name was right,
  two structural assumptions weren't.** (See the 2026-08-21 `basepeak` entry below for a critical
  caveat on this same verification run: the *parsing* findings here remain correct, but the specific
  numbers quoted may have come from a base-tuning build, not the peak+LTO one this run intended.) A
  real `--action=validate --iterations 3` run of
  `706.stockfish_r` (`gcc_O3` peak, `-O3 -march=native -flto`, 14m25s wall-clock) confirmed `ratio` is
  the correct field name (formula checks out exactly: `ratio == copies * reference / reported_time`,
  `32 * 1260 / 315.907284 == 127.632384`) — but two things the original guess got wrong meant `ratio`
  came back `None` anyway until both were fixed:
  1. **No non-iteration-indexed rollup field exists.** Every field lives under
     `spec.cpu2026.results.<bench>.<tune>.<NNN>.<field>` (`NNN` = zero-padded iteration index, one
     block per `--iterations` run) — never a bare `spec.cpu2026.results.<bench>.<tune>.ratio`. Original
     code stripped the `<bench>.<tune>.` prefix and looked for an exact `"ratio"` key, which could never
     match a scoped key like `"000.ratio"`. Fixed by collecting every `NNN.ratio` value across
     iterations and reporting the **median** (`cfm/workloads/spec_cpu2026.py`'s `_iteration_values()`)
     — deliberately not SPEC's own "reportable run" selection rule, which this project doesn't need to
     replicate; just an outlier-robust aggregate for a mining trial's number.
  2. **`.rsf` uses `"key: value"` (colon-space), not `"key=value"`.** `util.parse_kv_lines()`'s default
     separator is `"="` (correct for `wspy-archetype`'s own trace-output format, which really is
     `=`-separated — confirmed the same session) but wrong for `.rsf`. The hand-written unit-test
     fixtures used `"="` too, so they passed against the *same wrong assumption* this bug depended on —
     they were only caught by testing against `tests/fixtures/706.stockfish_r.peak.sample.rsf`, a real
     captured excerpt, not another hand-written guess. **Lesson for next time this class of bug shows
     up**: a hand-rolled fixture that encodes the same assumption as the code it's testing proves
     nothing; prefer a fixture copied from real captured output whenever one is available cheaply.
- **A bare `subprocess.run()` does not get SPEC's `shrc`-exported environment.** `runcpu` needs
  `PATH`/`PERL5LIB`/etc. that `$SPEC/shrc` exports; wspy's own `workload/cpu2017/run_test.sh` gets
  this for free by sourcing `shrc` once into its own long-lived shell before calling anything else.
  `cfm/workloads/spec_cpu2026.py` doesn't have that luxury (Python subprocess calls don't inherit a
  sourced-but-not-exported shell function's environment), so every `runcpu` invocation is individually
  wrapped as `bash -c 'cd $SPECDIR && source shrc && ulimit -s unlimited && exec runcpu ...'` — don't
  "simplify" this back to a bare `subprocess.run(["runcpu", ...])`, it will fail to find `runcpu` (and
  worse, may silently find a *different* stale `runcpu` on `PATH`) without the sourced environment.
- **`wspy-run`'s run-directory `manifest.json` and a per-pass `run.manifest.json` are two different,
  incompatible schemas.** The former (`layout_version`) is `wspy-run`'s own directory index, listing
  each pass and *its* manifest filename via `passes[].manifest`; the latter is the real wspy manifest
  `wspy-validate` understands. An earlier version of `_validate()` globbed `*manifest*.json` and fed
  both to `wspy-validate`, which always reported `FAIL` on the run-level one (`no schema_version field
  -- doesn't look like a wspy manifest`) and made every run look unvalidated regardless of the actual
  counter collection's health. Fixed by reading `manifest.json`'s own `passes[].manifest` list instead
  of globbing — caught by `tests/test_wspy_interface.py`, a real contract test against the built
  submodule, not by inspection. See `doc/ARTIFACT_CONTRACT.md`'s "Unified output layout" in `vendor/wspy`.
- **`wspy` doesn't create `--run-index`'s (or `--manifest`'s) parent directory.** It just prints
  `warning: unable to open run index file: <path>` to stderr and silently drops the record — no
  nonzero exit, no obvious failure at the call site. The actual symptom shows up two steps downstream:
  `wspy-store` reports `0 record(s)` ingested, and `wspy-archetype --run <host:id>` reports "no run
  found," neither of which mentions the real cause. `characterize()` now `mkdir -p`s both
  `run_index_path.parent` and `store_db.parent` (sqlite3 has the identical behavior) before invoking
  `wspy-run`.
- **`wspy-run --run-id` names the output *directory*, not the run identity `wspy-store`/`wspy-archetype`
  key on.** Each underlying `wspy` process (one per profile "pass") generates its own, unrelated
  `run_id` (`<start-time-to-millisecond>-<pid>`, `doc/ARTIFACT_CONTRACT.md`) and writes *that* to
  `--run-index` — not the `--run-id` string `wspy-run` was called with. `characterize()` originally
  built `wspy_run_ref` from the caller-supplied `run_id` directly, which meant `wspy-archetype --run
  <hostname>:<run_id>` could never find anything (`wspy-archetype: no run found for ...`) even on a
  perfectly healthy run. Fixed via `_resolve_run_identity()`, which diffs the run-index file's line
  count before/after the `wspy-run` call and reads the real `(hostname, run_id)` back off the
  newly-appended record — falling through to `_resolve_multi_pass_identity()` (M1, see the next entry)
  if a multi-pass profile appended more than one new line, rather than guessing.
- **Resolved (M1): a multi-pass profile's "obviously right" pass for archetype data was wrong —
  confirmed live, not by inspection.** `deep-cpu` launches 3 separate `wspy` processes per invocation
  (`systemtime`, `counters`, `amdtopdown` — one `wspy-run --list` entry, three real processes). The
  natural first guess for "which one feeds `wspy-archetype`'s `resource_dominance` scoring" is
  `counters` — `wspy-run --help` literally describes it as "used for topdown characterization," and
  it's the pass covering `topdown2`/`cache2`/`cache3`/`memory`/`float`/`topdown-frontend`/
  `topdown-optlb`. **That guess is wrong**: `counters` runs via wspy's native `--passes=` multipass
  execution with no `--csv` (human-readable output only, matching the `wspy-store`-only-parses-CSV
  trap two entries below), so its own `wspy-archetype --run` scorecard comes back
  `resource_dominance=unknown, confidence=insufficient-data` even though real topdown data was
  measured. It's the plain, non-multiplexed `amdtopdown` pass (`--csv --counters=topdown`) whose
  scorecard is actually populated (`resource_dominance=memory-bound`, `resource_dominance_pct=89.80`
  in a live confirming run against a toy workload). Correlating "pass name" (only in the run-level
  `manifest.json`'s `passes[]` list) to "run_id" (only in the run-index) isn't direct — neither file
  carries the other's identifier — but both independently record the same millisecond-precision
  ISO-8601 `start_time`/`timing.start_time`, confirmed byte-for-byte as an exact join key. Implemented
  in `cfm/instrumentation/wspy.py`'s `_ARCHETYPE_PASS_NAME` map (`{"deep-cpu": "amdtopdown"}`, only
  the one profile M1 actually uses) plus `_resolve_multi_pass_identity()`; any other multi-pass
  profile (`deep-cpu-intel`, `deep-gpu`, `zen4plus-deep`, a comma-composed profile list) still raises
  rather than guessing. **Lesson for next time**: a tool's own docs describing what a pass is "used
  for" describe its human-readable narrative role, not necessarily which pass a *different* downstream
  tool's machine-readable classification actually reads from — check the real scorecard per pass, not
  the profile description, before wiring a new multi-pass profile in here.
- **`wspy-store` only parses metric *values* out of CSV output — human-readable text enriches the
  manifest fields but carries zero `run_features`.** Passing `--counters=topdown` without `--csv`
  still measures and reports the data (visible in the human-readable printout), but
  `wspy-store`'s own summary line says `0 metric-set(s) ingested, 1 skipped`, and every
  `run_features` row lands `coverage=unavailable` — so `wspy-archetype` correctly, silently reports
  `resource_dominance=unknown` even though the counters were genuinely measured. Not a cfm bug once
  understood (`quick`, cfm's own screening-tier profile, is deliberately non-CSV and IPC/system-only —
  see `doc/DESIGN.md` §6 Phase 3, it isn't meant to characterize anything), but a real trap for hand-
  rolled `wspy` invocations (as in `tests/test_wspy_interface.py`'s direct-CLI contract test) or any
  future profile addition that wants `resource_dominance` populated: it must include `--csv`.
- **A toy C workload with no observable result gets its entire loop dead-code-eliminated at `-O2`.**
  `tests/test_wspy_interface.py`'s first toy binary (`return (int)(a & 0)`, discarding the loop's only
  effect) ran in `elapsed 0.002` — gcc had removed the loop entirely, so every topdown-dependent
  assertion downstream was silently measuring process-startup noise, not real counter data. Fixed by
  `printf`-ing the accumulated value, same as wspy's own toy suite in `doc/NEW_WORKLOAD_COOKBOOK.md`
  already does for exactly this reason. Worth remembering for any future hand-written toy/benchmark
  workload, not just this one.
- **SQLite's (standard SQL's) `UNIQUE` constraint never treats two `NULL`s as conflicting --
  `INSERT ... ON CONFLICT(...)` silently stops upserting once a scoping column can be `NULL`.**
  `cfm.db`'s `knowledge` table (§7/§8) is scoped `UNIQUE(cluster_key, compiler, compiler_version,
  target_arch, flag)`, and both `compiler_version`/`target_arch` are nullable columns (a host/GCC
  detection that hasn't run yet, or a caller that hasn't wired it through). `db.py`'s first
  `upsert_knowledge()` used `INSERT ... ON CONFLICT(...) DO UPDATE` — works fine once every scoping
  column is non-`NULL`, but with `compiler_version`/`target_arch` both `NULL` (a real M1 call shape:
  no host/GCC detection wired in yet), SQLite's own unique index never considers two `NULL`-valued
  rows a conflict, so `ON CONFLICT` never fires and every call silently `INSERT`s a fresh row instead
  of accumulating into the existing one — no error, just quietly wrong `n_trials`/`mean_delta_pct`
  from the second call onward. Fixed by looking the existing row up first with SQL `IS` (which *is*
  `NULL`-safe, unlike `=`) and updating it **by id** instead of relying on `ON CONFLICT` at all. Caught
  by `test_upsert_knowledge_null_compiler_version_and_target_arch_still_upserts`, not by inspection --
  worth remembering for any future `UNIQUE`-scoped upsert where one of the scoping columns can be
  `NULL`, not just this table.
- **Resolved 2026-08-18: wspy#270's watch item — `wspy-testpoint`'s "wrong pass" bug is fixed
  upstream, confirmed by the pin bump.** The watch item below (originally filed against PR #194) asked
  to confirm live, before wiring in `wspy-testpoint aggregate --csv` for M2.5, whether
  `collect_archetype_scorecards()`'s `"counters"`-name preference would hit the same empty-CSV trap as
  the `deep-cpu`/`amdtopdown` entry above. It would have — but wspy's own PR #271 (`joblib.py:
  pick_counters_pass_id() prefers a pass with real run_features data`, closing wspy#270) fixed exactly
  this, citing the identical number this project's own trap entry does (`resource_dominance=
  memory-bound` at 89.80% on the real `amdtopdown` pass vs. `unknown`/`insufficient-data` on the
  empty-CSV `counters` pass for the same collection), and PR #273 refined the tie-break to the
  *richest* pass by measured-row count rather than just "first with any data." Both fixes reach
  `wspy-testpoint`'s `collect_archetype_scorecards()`, not just the web UI's own archetype badge.
  `vendor/wspy` was bumped past both (`1c192a7` → `3839815`, `feature/bump-wspy-pin-archetype-axes`);
  `tests/test_wspy_interface.py`'s live `deep-cpu` contract test
  (`test_characterize_succeeds_on_deep_cpu_with_a_populated_scorecard`) still passes against the new
  build, confirming cfm's own direct `wspy-archetype --run` path (`_resolve_multi_pass_identity()`
  above) is unaffected — cfm doesn't call `wspy-testpoint` yet, so the `collect_archetype_scorecards()`
  half of this is confirmed by upstream's own commit evidence and test suite (`testpoint_smoke.sh`),
  not yet independently exercised by a cfm-side test; that's real verification for M2.5 item 2 to pick
  up once `wspy-testpoint aggregate --csv` actually gets wired in here, not before.
- **Superseded by the same bump: several M2.5-item-1 signature axes now ship natively in
  `wspy-archetype` instead of needing cfm-side computation.** The same 113-commit range (past
  `1c192a7`) that closed wspy#270 also closed [wspy#227](https://github.com/mvermeulen/wspy/issues/227)
  — `vectorization_density` (from `float_pct`, PR #269) with low/moderate/high thresholds fit against
  the CPU2026 reference-matrix corpus (147 runs, 3 machines), not a cfm-side single-host guess — plus
  `allocation_pressure` (from `fault_rate`, PR #268) and `frontend_latency_pct`/`frontend_bandwidth_pct`/
  `on_cpu`/`core_utilization` (PRs #266/#267/#272) as further native `run_features`/scorecard axes.
  `doc/DESIGN.md` §14's M2.5 item 1 and §15's wspy#227 entry described cfm computing these itself
  (a `wspy-summary --metric float` shell-out, explicitly labeled uncalibrated) — that plan predates
  this bump and needs updating to read the axes directly off `wspy-archetype`'s scorecard instead.
- **Resolved 2026-08-19: `vectorization_density`/`allocation_pressure`/`core_utilization` read
  `"unknown"` under cfm's own `deep-cpu` profile through a three-issue upstream chain
  (wspy#274 → #275 → #276) — now fixed, confirmed live, pin bumped past all three
  (`3839815` → `bc65f57`).** Timeline, in case this class of "pass fixed upstream, pin bump still
  blocked" recurs:
  1. **wspy#274** (root cause, filed 2026-08-18): `profiles/deep-cpu.conf`'s `counters` pass *does*
     include `float`/`fault_rate`'s source counter groups in its `--passes=...` sweep, but ran with no
     `--csv`, so `wspy-store` never ingested it into `run_features` regardless of which pass
     `wspy-archetype` read from — neither of `deep-cpu`'s other two passes (`systemtime`, `amdtopdown`)
     collects `float`/`fault_rate` either, so there was no `deep-cpu` pass with real data for these axes
     at all.
  2. **wspy#275** closed #274 (adds `--csv` to the `counters` pass), confirmed live to do exactly that —
     but turning `--csv` on for that pass also made `wspy-validate` run its per-column sanity check
     against it for the first time, surfacing a new, previously-latent bug:
  3. **wspy#276** (filed 2026-08-19): `topdown.c`'s `print_l3cache()` divides `l3_miss / l3_access *
     100.0` with no zero-guard; on this host `l3_lookup_state.*` counters are unavailable
     (`/sys/devices/amd_l3/type not found`), so both are `0` and the CSV `l3miss` column came out
     `-nan%`, failing the whole `counters` manifest (`wspy-validate` correctly rejecting a non-finite
     CSV value) even though the other 57/57 counters in the same pass measured fine. Caught by
     `tests/test_wspy_interface.py::test_characterize_succeeds_on_deep_cpu_with_a_populated_scorecard`
     going from pass to fail (`signature.validated` False where it was True) on a trial pin bump to
     `aaf4392` (past #275) — real bump-time signal per the "Bumping the pin" discipline above, not a
     flaky retry. `feature/bump-wspy-pin-text-out-csv-fix` (PR #14) was left open, unmerged, blocked on
     this.
  4. wspy#276 closed same-day (PR #277: a shared `safe_div()` helper applied to every `topdown.c`
     miss/access-style division with the same unguarded shape, not just `print_l3cache()`, plus a
     regression test). Bumped the pin past it (`bc65f57`); `test_characterize_succeeds_...` passes
     again, and — the actual payoff — **`_ARCHETYPE_PASS_NAME["deep-cpu"]` now points at `"counters"`
     instead of `"amdtopdown"`** (`cfm/instrumentation/wspy.py`; the earlier `"amdtopdown"` choice was
     only ever a workaround for `"counters"` having no usable CSV — see the wspy#270-superseded entry
     below). Confirmed live: querying `wspy-archetype` on `"counters"`'s own run_id yields
     `vectorization_density=low, allocation_pressure=low, core_utilization=low, confidence=high` on a
     toy scalar workload (vs. `unknown`/`unknown`/`unknown`/`low` from `"amdtopdown"`), with
     `resource_dominance` itself agreeing between the two passes (`memory-bound`, ~86.6%) — `"counters"`
     is strictly the richer pass now that it validates. `config/gcc_flag_catalog.seed.json`'s
     `vectorization-density-high`-gated entries (`-mprefer-vector-width=256/512`) are now actually
     *reachable* from a real `deep-cpu` trial, not just correctly keyed. **PR #14 merged (`72065b6`,
     2026-08-19)** with this fix and the resulting doc updates.
- **2026-08-20: two concurrent `cfm mine` invocations crashed the host — SPEC's `lock.CPU2026` is not a
  mutex, and nothing in `cfm` itself stopped a second invocation from starting.** Two `cfm mine
  706.stockfish_r` runs were launched ~13 seconds apart (`cfm.db` experiments 3 and 4, `started_at`
  `06:57:45Z`/`06:57:58Z`). Both reached SPECrate's build+run fan-out around the same time — SPECrate
  methodology runs many parallel copies of the benchmark binary (one per core-ish; `stockfish_base.`
  measured 1.5-1.7GB RSS each here) — and the two runs' copies together exceeded the host's 91GB RAM.
  `journalctl -b -1 -k` showed the OOM-killer invoked repeatedly for about 90 seconds, eventually
  killing `systemd-journald` itself, consistent with the box becoming unresponsive enough to need a
  hard reboot. `/home/mev/cpu2026/result/lock.CPU2026` looked like it might be a run mutex but is just
  a run-ID counter (`cat` returns a bare integer, e.g. `092`) — it never blocked the second `runcpu`
  invocation from starting. After reboot, `cfm.db`'s experiments 3/4 (and two older orphans from
  2026-08-09) were left permanently `status='running'` with no `finished_at` — `cli.py`'s `mine`
  handler only calls `db.finish_experiment()` *after* the whole try block succeeds, so any hard failure
  (crash, or even a plain `RuntimeError` from inside the phases) leaves the row stuck; had to fix up by
  hand with `db.finish_experiment(conn, experiment_id, status="failed")` after the fact. **Fixed via
  `cfm/lock.py`**:
  a host-wide `fcntl.flock()`-based lock, held for the duration of any `cfm measure`/`cfm mine`
  invocation, refusing (never queueing) a second concurrent one — deliberately not a hand-rolled PID
  file with a staleness check, because the kernel releases an `flock` automatically when the holding
  process's fd closes for *any* reason (normal exit, exception, or being OOM-killed), so a crashed job's
  lock needs no manual cleanup — the exact failure mode this incident hit. Default lock path is
  `<spec_dir>/.cfm-mining.lock` (host-wide, alongside the SPEC install, not repo-relative — see
  `cfm/config.py`'s `lock_file` field), overridable via `--lock-file`/`CFM_LOCK_FILE` same as every
  other `CfmConfig` path. doc/DESIGN.md §11 previously stated "this project adds no new
  concurrency-control code" for exactly this class of thing — that line is now corrected there.
  **Resolved 2026-08-20 (same day, follow-up fix): the stuck-at-`running` bookkeeping gap itself.**
  `cfm/agents/spec_agent.py`'s `run_one_trial()` now wraps its body (after `experiment_id` is known) in
  a `try/except Exception` that calls `db.finish_experiment(conn, experiment_id, status="failed")`
  before re-raising — every orchestrator phase (screen/confirm/combine) funnels through this one
  function with no per-candidate catch of its own, so an unhandled exception from *any* of them was
  always going to abort the whole `cfm mine` run regardless; this just makes sure `cfm.db` records that
  instead of leaving the row stuck. One case doesn't route through `run_one_trial`'s own try/except,
  though: `orchestrator.run_baseline()`'s "every calibration repetition returned no usable ratio" check
  runs *after* those calls all returned normally (no exception, just no ratio), so it has its own
  matching `finish_experiment(..., status="failed")` immediately before its `raise RuntimeError(...)`.
  Covered by `tests/test_agents_spec_agent.py::test_run_one_trial_marks_experiment_failed_on_unexpected_exception`
  and an assertion added to `tests/test_orchestrator.py::test_run_baseline_raises_when_every_repetition_fails_to_build`.
- **2026-08-20: `mvermeulen.org/workload`'s WordPress REST API serves published pages fully
  anonymously — confirmed live, not assumed — which is what made `cfm/reference_matrix.py` (M2.5 item
  2's deferred half) possible without any credentials on the mining host at all.** `vendor/wspy`'s own
  `web/wp_client.py` always sends a Basic-Auth header (from `~/.config/wspy/publish.json`'s
  `wp_cfg`), so it was easy to assume reading needs the same credentials writing does. Tested directly
  against the real site instead: a plain unauthenticated `GET
  /wp-json/wp/v2/pages?slug=cpu2026` returns real published-page data (`200`, real `id`/`slug`/
  `parent`/`link` fields), and even a deliberately garbage `Authorization: Basic Og==` header (empty
  `:`-only credentials) still returns `200` with real data — WordPress just serves published content
  to anonymous GETs regardless, standard REST API behavior most hosts don't turn off. Two follow-on
  findings from the same investigation:
  1. **`content.raw` needs `context=edit` (auth); `content.rendered` doesn't, and carries the exact
     same `<pre class="wp-block-preformatted">` block text.** `wp_client.fetch_page_raw_content()`
     always requests `context=edit` (needed for its own drift-detection use case, comparing against
     exactly what's stored) — `cfm/reference_matrix.py`'s own `_fetch_rendered_content()` deliberately
     doesn't reuse that function, requesting plain `.rendered` instead, confirmed live to contain the
     identical counters.txt text (it's literally what's shown on the public page).
  2. **The reference-matrix corpus is `mvermeulen.org/**workload**`, a separate WordPress instance
     from `mvermeulen.org` itself** (a subdirectory multisite install, its own `wp-json` root at
     `mvermeulen.org/workload/wp-json/`) — querying the bare `mvermeulen.org/wp-json/...` returns 200
     with real but *unrelated* data (a personal blog/bike-trips site), which looks like a working
     integration until the returned pages never match anything cpu2026-shaped. Caught by checking a
     plain page-listing response's own `link` header, which named the correct subdirectory root
     directly.
  Also confirmed live: `cfm/orchestrator.py`'s `_characterize_baseline()` recovers a real
  `resource_dominance` (`memory-bound`) for `706.stockfish_r` from a completely different real machine
  (`amd-370-64gb`) with zero local setup on this mining host — agreeing with this host's own earlier
  local characterization of the same benchmark. `vectorization_density`/`allocation_pressure` came
  back `unknown` from this path at first (not a cfm bug — `vendor/wspy`'s `web/counter_text.py` wasn't
  yet name-aligned for `float_pct`/`fault_rate` the way it was for the topdown axes; filed upstream as
  [wspy#278](https://github.com/mvermeulen/wspy/issues/278)) — degraded safely regardless, since
  `_filter_implausible_candidates()` never excludes a candidate on unknown/absent signal data.
  **Resolved same day**: wspy#278 closed via #279 (`float_pct`)/#280 (`fault_rate`), pin bumped past it
  (`bc65f57`→`247a6dd`, no C rebuild needed — both fixes are pure-Python). Live-verified the actual
  payoff, not just that the issue closed: `fetch_shape()` now recovers real
  `vectorization_density="moderate"`/`allocation_pressure="high"` from `amd-370-64gb` — and those
  values **exactly match** this host's own local `deep-cpu` characterization of the same benchmark from
  the same day's real mining run (experiment 6), independent confirmation the whole recovery chain
  (HTML fetch → `counters.txt` parsing → `wspy-archetype --run-guest` scoring) is actually correct, not
  merely internally consistent with itself.
- **Resolved 2026-08-21: `generate_config()`'s per-trial `basepeak = no` override was silently ignored
  by SPEC since this project's very first commit — every real trial ever run, M0 through four full
  `cfm mine` runs, actually built and measured the fixed *base*-tuning binary (`-g -O3 -march=native`,
  `gcc_O3.cfg`'s own suite-wide default), never whichever candidate flags `cfm` thought it was testing.**
  Surfaced while scoping real PGO/FDO support (the user's own instinct — "want to work this through
  before we try cpython again... otherwise we aren't really looking at the other benchmarks" — turned
  out to be far more literal than either of us expected). `generate_config()` rendered:
  ```
  {bench}: basepeak = no
  {bench}=peak:
     OPTIMIZE = <candidate flags>
  ```
  — `basepeak = no` as a separate, *unscoped* line before the `{bench}=peak:` block. This looks
  correct (search "706.stockfish_r=peak:" in `Docs/config.html`, the exact example this was modeled
  on) but `Docs/config.txt`'s own `basepeak` entry has a warning easy to read past: *"this works only
  if the basepeak option is placed in the header section [or, per its own worked example, scoped
  per-benchmark-and-tune as `997.noisy=peak: basepeak=yes`]. Put it anywhere else, spend more time
  indoors."* An unscoped `{bench}: basepeak = no` is exactly "anywhere else" — SPEC silently keeps the
  suite-wide `default: basepeak = yes` (`gcc_O3.cfg`'s own shipped default) in effect regardless, so
  peak tuning transparently reuses/rebuilds the *base* binary every time.
  **Confirmed live, reproduced twice, root-caused, and fixed** — not by inspection: a real
  `runcpu --action=build` with `cfm`'s exact unscoped shape built `782.lbm_r` and logged `"Building
  782.lbm_r peak gcc_O3: (build_base_gcc_O3.0000)"` / `"Build successes for fprate: 782.lbm_r(base)"`
  (note "peak" only in the human-readable label — the actual directory name and success line both say
  `base`) with `OPTIMIZE="-g -O3 -march=native"` in the real compile/link command lines, completely
  ignoring the candidate flags requested. The identical config with `basepeak = no` moved *inside* the
  `{bench}=peak:` block built `build_peak_gcc_O3.0000` for real, with the requested flags genuinely
  reaching the compile/link lines. Fix: move `basepeak = no` inside the section. Verified again through
  `cfm`'s own real (now-fixed) `generate_config()`/`build()` code path, not just the hand-written
  diagnostic config, before considering this closed.
  **Blast radius**: every trial recorded before this fix — M0's original "shipped and verified" run,
  and all four `doc/mining_results.*.md` write-ups (two `706.stockfish_r` runs, `782.lbm_r`,
  `714.cpython_r`) — measured the *same binary* regardless of which candidate flag was nominally under
  test. Every "screening ratio"/"confirmation delta"/"accept-reject verdict" in those docs reflects
  pure run-to-run noise between repeated builds of an *identical* program, not any real flag effect;
  every `knowledge` table row those runs produced was upserted from the same non-signal and has been
  cleared (`DELETE FROM knowledge;`, 13 contaminated rows). Silver lining, not spin: since every trial
  in an affected run measured the identical binary, the *timing/environmental* findings in
  `doc/mining_results.782.lbm_r.2026-08-21.md` (the ~7.8-hour monotonic drift) and
  `doc/mining_results.714.cpython_r.2026-08-21.md` (the step-shaped noise) are now known for certain to
  be pure host/environmental noise, unconfounded by any real flag difference — if anything a *cleaner*
  characterization of this host's run-to-run variance than originally realized, even though every
  per-flag conclusion drawn from the same data is void. `_filter_implausible_candidates()` (Phase 2)
  and the reference-matrix characterization work (`cfm/reference_matrix.py`) are both unaffected —
  neither touches `generate_config()`'s peak-override rendering at all.
  **Lesson for next time**: a unit test asserting the exact *unscoped* line as the "correct" rendered
  shape (`tests/test_workloads_spec_cpu2026.py`'s original assertion) passed throughout, because it only
  checked substring presence, never SPEC's own interpretation of the config — exactly the "a hand-rolled
  fixture encodes the same assumption as the code it's testing proves nothing" lesson from the `.rsf`
  entry above, recurring in a new shape: this time the fixture wasn't hand-written data but a
  hand-written *assertion* about correct-looking-but-untested config syntax. Fixed test now asserts
  `basepeak`'s *position* relative to the section header, not just its presence, and a real re-run
  through `runcpu --action=build` is what actually caught this, not any unit test.
- **2026-08-21: ad hoc real-SPEC verification via a direct `run_one_trial()` call bypasses
  `cfm/lock.py` entirely — nearly caused a repeat of the 2026-08-20 OOM incident, self-inflicted this
  time.** While independently re-verifying the basepeak fix (previous entry) against the real pipeline,
  a `python3 -c "run_one_trial(...)"` one-liner was used instead of `cfm measure`/`cfm mine` — the host
  lock is acquired inside `cli.py`'s command handlers, not inside `run_one_trial()`/the orchestrator
  functions themselves, so calling them directly, as any ad hoc script or future debugging session
  might, holds no lock at all. A first such call was killed by a `timeout 300` wrapper that expired
  before a slow (~21 min) `782.lbm_r` trial finished — `timeout` signals only its immediate child
  (`python3`), not the grandchild `runcpu`/`specinvoke`/benchmark-copy process tree underneath it
  (`bash -c '... exec runcpu ...'`'s own `exec` replaces bash with runcpu in place, but the *further*
  children `runcpu` itself forks are unaffected by a signal sent to a process two generations up), so
  the real SPECrate copies kept running, orphaned, after the wrapper exited. A second, immediately-
  following verification call then launched a *second* full set of copies on top of the still-running
  first set — real memory: 91Gi/91Gi used, 7.7Gi/8Gi swap, load average 59, and the kernel OOM-killer
  did fire (confirmed via `dmesg`, four `lbm_r_peak.gcc_` processes killed) before both process trees
  were found and killed by hand (`pkill -9 -f lbm_r_peak` and matching `runcpu`/`specinvoke`/config-name
  patterns). Unlike the 2026-08-20 incident this time the kill list stayed contained to the benchmark
  processes themselves (nothing suite-critical like `systemd-journald` was hit) and the host didn't
  need a hard reboot to recover — confirmed live via `free`/`ps` immediately after — but a reboot was
  still done anyway before the next real run, for certainty rather than because anything specific was
  still known-broken. **Lesson**: `cfm/lock.py`'s protection is real but scoped to the CLI entry
  points (`cli.py`'s `measure`/`mine` handlers) — any direct call into `run_one_trial()`,
  `orchestrator.run_baseline()`, or similar for ad hoc verification/debugging against the real SPEC
  install needs its own manual exclusivity discipline (confirm nothing else is running first, same as
  the rule for `cfm measure`/`cfm mine` themselves) since the lock provides none of its own. Also
  motivated two small, low-risk additions to `run_one_trial()` itself, done the same day: an
  independent post-build compiled-flags audit (`-frecord-gcc-switches` + reading the binary's own
  `.GCC.command.line` section back, since trusting `runcpu`'s own "Build successes" report alone is
  exactly what let the basepeak bug hide undetected for so long) and a per-trial `cpu_temp` record
  (parsed from data `wspy`'s `--system` flag — on by default for every `quick`-profile trial cfm
  already runs — was already collecting and printing, just never read by anything before now) to make
  a future "why did this run's later trials look different" question answerable from `cfm.db` alone,
  without needing to actively gate or wait on thermal state mid-run (a real idea, floated the same
  session, but deliberately not implemented yet — no calibrated threshold/timeout exists to tune an
  active gate against, and adding new blocking logic to an unattended overnight run before one does is
  a real risk, not a free improvement).
- **Resolved 2026-08-22: the "18x slowdown" mystery — screening/confirmation candidates were tested in
  total isolation from the baseline's own `-O3`, not layered on top of it. A genuine `-O0`-vs-`-O3`
  comparison, not a hardware problem.** Surfaced the morning after the basepeak fix (previous entry),
  during the first real, focused post-fix mining run: a screening trial's ratio crashed from
  baseline's ~95-102 to ~7, and its wall-clock exploded from ~7 minutes to ~90+ minutes. Several real
  hypotheses were chased and each was genuinely ruled out with live evidence before finding the actual
  cause — worth recording the sequence, since each dead end was a reasonable thing to check, not a
  wasted detour:
  1. **Power profile** (`powerprofilesctl` showed `"balanced"`, not `"performance"`) — plausible at
     first (a power-constrained mobile/APU chip), but the user's own prior experience running fine on
     `"balanced"` was the right pushback, and a fresh isolated trial afterward under `"performance"`
     mode didn't cleanly separate the two anyway.
  2. **Simple clock-frequency throttling** — directly falsified by the numbers: this chip's sustained
     frequency range under full load tops out around 3-8x slower at the extreme low end, nowhere near
     the observed ~13-18x. Real thermal throttling *cannot* be the sole mechanism for a gap this large.
  3. **Swap thrashing / memory pressure** — ruled out via real historical `sar` data (`sysstat`'s
     10-minute samples): 0% swap used and a flat ~58% memory utilization for the entire window,
     including the slow trials.
  4. **A cold/slow build** — ruled out by reading the actual SPEC log: `"Up to date 706.stockfish_r
     peak gcc_O3"` — the binary was cached, not recompiled; 100% of the ~90-minute anomaly was in the
     *run* phase alone.
  **Actual root cause**, found by directly inspecting the compiled binary's own audit trail (the
  previous entry's `-frecord-gcc-switches` addition) rather than the environment: `cfm/orchestrator.py`
  passed `flags=[candidate.flag]` to `run_one_trial()`/`_confirm_flagset()` in `screen_candidates()`,
  `confirm_candidates()`, and the pair-tournament half of `greedy_combine()` — the candidate flag
  *alone*, never combined with `baseline.flags`. A live audit hypothesis for the slow trial read
  `"compiled-flags audit -- confirmed compiled in: ['-fprefetch-loop-arrays']"` — no `-O3` anywhere.
  Stockfish's NNUE evaluation is extremely sensitive to both optimization level and vector instruction
  availability, so testing it at an effective `-O0` (no `-O` flag at all implies GCC's own default)
  produced exactly the ~13-18x regression observed — no hardware explanation needed. **This bug was
  completely masked by the basepeak bug until the moment that one was fixed**: before the fix, every
  trial silently rebuilt/reused the identical base-tuning binary regardless of what `flags` list was
  passed in, so a wrong `flags` list had zero observable effect. It only became visible the instant
  candidate flags started actually reaching the compiler for the first time in this project's history.
  **Could this have been caught sooner?** Yes — the compiled-flags audit already had the answer
  (baseline's own trial showed `confirmed compiled in: ['-O3']`; the broken trial's own row, sitting in
  the same `cfm.db`, never mentioned `-O3` at all) well before any of the thermal/power/swap
  investigation above started. The gap wasn't the audit's existence, it was that (a) nothing
  cross-referenced a trial's audit against baseline's own, and (b) the orchestrator's own unit tests
  encoded the identical wrong assumption the code had (`ScriptedBackends`' `ratio_sequences` fixtures
  were keyed by the bare candidate flag, e.g. `("-good",)`, matching the bug) — the third recurrence of
  the "a hand-rolled fixture encodes the same assumption as the code it's testing proves nothing" class
  of bug in this project's own history (the `.rsf` entry, the `basepeak` entry, now this).
  **Fix**: `screen_candidates()`/`confirm_candidates()`/`greedy_combine()`'s pair tournament now render
  `baseline.flags + [candidate.flag]` (or `+ sorted({a, b})` for a pair) -- matching the greedy walk's
  own cumulative step, which was already correct. `_confirm_flagset()`'s knowledge-table upsert
  (previously gated on `len(flags) == 1`, now never true for Phase 4 since `flags` always includes
  baseline's own) switched to gating on `phase == "confirmation"` instead, reading the actual candidate
  off `flags[-1]` rather than `flags[0]`. Every affected test's fixture updated to the corrected shape
  — including tests that were passing *for the wrong reason* (an exhausted/never-matched mock queue
  silently producing "no usable ratio," which happened to satisfy the same assertion a real accept/
  reject would have) — not just the ones that outright failed. Verified for real: the identical
  candidate that produced the broken audit now compiles with `-O3` genuinely present, confirmed via
  `audit_compiled_flags()` against a real build.
  **New generic safety net, motivated directly by "could this have been caught sooner"**: the audit
  (`_summarize_compiled_flags_audit()`) now unconditionally checks the compiled dump for *any* `-O`
  optimization level at all and emits a loud `⚠ WARNING` if none is found — regardless of what `flags`
  itself claimed to want, so a *future* caller making this same class of mistake surfaces it
  automatically in `cfm.db`, without requiring a human to notice by manually diffing two trials' audit
  rows against each other (which is what actually happened this time).

## Build & test

```
git submodule update --init --recursive  # or ./scripts/bootstrap_wspy.sh (also builds it, see below)
./scripts/bootstrap_wspy.sh               # builds vendor/wspy -- checks for gcc/libsqlite3-dev first
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q                      # unit tests + wspy contract tests (skip cleanly if
                                          # vendor/wspy isn't built yet) -- no real runcpu/SPEC calls
.venv/bin/cfm init-db --db /tmp/x.db     # sanity-checks schema application, no SPEC/wspy needed
.venv/bin/cfm measure 706.stockfish_r --flags "-O3 -march=native -flto"
                                          # the real thing -- needs vendor/wspy built (preflight() says
                                          # so explicitly if it isn't) and a working SPEC CPU2026
                                          # install; a real invocation launches an actual SPEC build+run
                                          # (minutes, real CPU/disk use) -- confirm with the user before
                                          # running this one, per the exclusive-machine-access rule.
.venv/bin/cfm mine 706.stockfish_r --max-trials 20
                                          # M1's full search loop -- same real-SPEC/wspy prerequisites as
                                          # `measure` above, but many more trials (baseline alone is 3
                                          # confirmation-grade deep-cpu builds+runs) -- same "confirm with
                                          # the user first" rule applies, doubly so here; hasn't been run
                                          # for real against this host's SPEC install yet (see Status
                                          # above), only against mocked backends in tests/test_orchestrator.py.
```

`tests/` has two tiers: pure-logic unit tests (config resolution, `.rsf`/trace-output parsing, `cfm.db`
schema and accessors, SPEC config rendering, preflight's binary-existence check, and the orchestrator's
phase logic against mocked `WorkloadBackend`/`InstrumentationBackend` fakes — no SPEC license or wspy
checkout needed at all) and `tests/test_wspy_interface.py`'s contract tests (real
`wspy`/`wspy-run`/`wspy-store`/`wspy-archetype`/`wspy-summary` invocations against a toy C workload,
skipped cleanly rather than failed when `vendor/wspy` isn't built). Neither tier touches a real
`runcpu`/SPEC install — `cfm measure`/`cfm mine` above are the only things that do, and both are
manual/opt-in, never part of the automated suite.

## Architecture

**Data flow (M0):** `cfm measure` (`cli.py`) → `agents/spec_agent.run_one_trial()` → SPEC Runner
(`workloads/spec_cpu2026.py`: render a trial config, build, hand a `runcpu --action=validate` argv to
—) → Instrumentation (`instrumentation/wspy.py`: `wspy-run` executes that argv, then `wspy-validate`/
`wspy-store`/`wspy-archetype` sequence over the result) → back to the SPEC Runner to parse the `.rsf`
ratio → one row each in `cfm.db`'s `experiments`/`trials` tables (`db.py`), regardless of outcome.

**Data flow (M1):** `cfm mine` (`cli.py`) → `orchestrator.run_baseline()` (Phase 1, 3×
`run_one_trial()` at the `deep-cpu` profile) → `orchestrator.generate_candidates()` (Phase 2,
`compilers/gcc.py` filtered by `benchmark_languages()`) → `orchestrator.screen_candidates()` (Phase 3,
1× `run_one_trial()` per candidate at the `quick` profile, prunes clearly-worse) →
`orchestrator.confirm_candidates()` (Phase 4, 3× `run_one_trial()` per survivor, `cfm/stats.py`'s CI
accept/reject vs. baseline, `knowledge` table upsert) → `orchestrator.greedy_combine()` (Phase 5,
cumulative re-confirmation plus a bounded random-pair tournament) → a plain JSON summary on stdout,
every trial along the way still landing in `cfm.db` regardless of phase or outcome, same as M0.

| File | Responsibility |
|---|---|
| `cfm/util.py` | `parse_kv_lines()` — shared `key=value`-per-line parser for both wspy's trace-style CLI output and SPEC's `.rsf` format; `normalize_flag_base()`/`catalog_flag_base()` — shared flag-name normalization between `scripts/audit_flags_from_spec_results.py` and `compilers/gcc.py`. |
| `cfm/config.py` | `CfmConfig.from_env()` — env-var-driven paths/hostname (`CFM_SPEC_DIR`, `CFM_WSPY_DIR`, ... — see the file for the full list and defaults), explicit kwargs > environment > built-in default, resolved at call time. |
| `cfm/lock.py` | `host_lock()` — the host-wide `flock`-based mutex `cfm measure`/`cfm mine` hold for their entire invocation (doc/DESIGN.md §11's "cross-invocation exclusivity" bullet); raises `MiningLockHeld` immediately (never queues/waits) if another invocation already holds it. See Non-obvious traps below for why it's `flock`-based, not a PID file. |
| `cfm/db.py` | Applies `schema/cfm_schema.sql` (idempotent) and provides typed `create_experiment`/`record_trial`/`update_trial_verdict`/`get_experiment`/`list_trials`/`list_trials_by_phase`/`finish_experiment`/`set_baseline_run_ref`/`record_hypothesis`/`upsert_knowledge` accessors. No ORM. |
| `cfm/stats.py` | Confidence-interval statistics for Phase 4's confirmation stage — `confidence_interval()`/`non_overlapping()`, replicating `wspy-summary`'s own documented CI formula (mean, sample stddev, Student's t 95%) applied to `cfm.db`'s own `trials.ratio` values, since `wspy-summary` itself has no way to see SPEC's `ratio` field (doc/DESIGN.md §6 Phase 4). |
| `cfm/compilers/base.py` | `CompilerBackend` interface + `FlagCandidate`/`ValidationResult` dataclasses (doc/DESIGN.md §4.3/§12). |
| `cfm/compilers/gcc.py` | The only implementation: `candidate_flags_for_signature()` (M1: ignores its own `signature` arg, returns the whole applicable-language catalog uniformly), `validate_flagset()` (unknown-flag/conflict checks against `config/gcc_flag_catalog.seed.json`), `render_optimize_string()`, plus `benchmark_languages()` (reads a benchmark's language from SPEC's own `Spec/object.pm`). |
| `cfm/workloads/base.py` | `WorkloadBackend` interface + `BuildResult`/`RunResult` dataclasses (doc/DESIGN.md §4.1/§12). |
| `cfm/workloads/spec_cpu2026.py` | The only implementation: renders a per-trial SPEC config via `include:` + a `<bench>=peak:` override section (`basepeak = no` scoped *inside* it — see Non-obvious traps above for why that scoping is load-bearing), always appends `-frecord-gcc-switches` to the rendered `OPTIMIZE` line, drives `runcpu --action=build`/`--action=validate` through a `shrc`-sourcing `bash -c` wrapper, parses the resulting `.rsf` file. `audit_compiled_flags()` independently reads a just-built binary's own `.GCC.command.line` section back via `readelf`, for `run_one_trial()`'s own compiled-flags audit (below). |
| `cfm/instrumentation/base.py` | `InstrumentationBackend` interface + `RunSignature` dataclass (doc/DESIGN.md §4.2/§12). |
| `cfm/instrumentation/wspy.py` | The only implementation: `preflight()` checks all six wspy binaries exist; `characterize()` runs `wspy-run <profile> -- <command>`, then resolves the *real* run identity from the run-index file (see Non-obvious traps — single-pass and the `deep-cpu` multi-pass profile both work), then `wspy-validate`/`wspy-store`/`wspy-archetype`. `check_regression()` wraps `wspy-summary --check-regression` as a secondary environment/counter-sanity guardrail (never the accept/reject decision — that's `cfm/stats.py`, over `cfm.db`'s own data). |
| `cfm/agents/spec_agent.py` | `run_one_trial()` — the M0 pipeline glue described above. `workload`/`instrumentation` backends and `profile` are injectable/overridable per call (`orchestrator.py` needs a different wspy profile per phase, and its own tests inject fakes — no real SPEC/wspy calls); all default to the real M0 behavior when omitted. Also records two best-effort, degrade-gracefully hypothesis notes per trial once a build succeeds: `_summarize_compiled_flags_audit()` (cross-checks the requested flags against `workload.audit_compiled_flags()`'s real compiled-binary readback) and `_extract_cpu_temp_c()` (parses `wspy`'s own already-collected `cpu temp` reading out of `RunSignature.raw_output` — see Non-obvious traps below for why both were added the same day). The only agent module that exists; `knowledge_agent`/`hypothesis_agent`/`report_agent` are M2-M3. |
| `cfm/orchestrator.py` | Phase state machine (doc/DESIGN.md §5-6). `run_baseline()` (Phase 1, sec. 14 M2.5 item 2: shape — resource_dominance/vectorization_density/allocation_pressure — via `_characterize_baseline()`, which now tries `cfm/reference_matrix.py`'s external corpus lookup first and falls back to one local `deep-cpu --iterations 1` characterization trial only when no matching published entry exists, plus `CONFIRMATION_REPETITIONS` cheap `quick`-profile calibration trials feeding `cfm/stats.py`'s CI either way; `_characterize_baseline()` stays the one isolated seam either shape source flows through), `generate_candidates()` (Phase 2, M1's whole-catalog read from `compilers/gcc.py` still ignores `resource_dominance` per that module's own M1-vs-M2 boundary, but sec. 14 M2.5 item 3 layers `_filter_implausible_candidates()` on top — drops a candidate only when *every* `topdown_signals` entry is confidently contradicted by the baseline's characterized shape, never on unknown/absent data), `screen_candidates()` (Phase 3, one cheap `quick`-profile trial per candidate, prunes only a clearly-worse point estimate), `confirm_candidates()` (Phase 4, re-confirms each survivor against the baseline's CI via `_confirm_flagset()`'s calibration-profile reps — accept requires both non-overlapping CI *and* a delta clearing `MIN_PRACTICAL_SIGNIFICANCE_PCT`, M2.5 item 3's asymmetric bar — `check_regression()` as a sanity-only guardrail on accept, `knowledge` table upsert per single flag), `greedy_combine()` (Phase 5, cumulative greedy walk re-confirmed against the *current* running set each step via the same `_confirm_flagset()`, plus a bounded random-pair tournament evaluated against baseline that can still replace the greedy winner). |
| `cfm/reference_matrix.py` | `fetch_shape()` — read-only, fully anonymous (no WordPress login/credentials needed at all, confirmed live) external reference-matrix corpus lookup, doc/DESIGN.md §14 M2.5 item 2's deferred half. Walks `mvermeulen.org/workload`'s published page hierarchy directly (own minimal anonymous HTTP client), reuses `vendor/wspy`'s `web/counter_text.py` (direct pinned-submodule import, a deliberate narrow exception to "stable CLI only") to parse recovered `counters.txt` blocks, then scores the result via the real `wspy-archetype --run-guest` CLI. Degrades to `None` on any failure — no network, no matching page, nothing recoverable — never raises; `_characterize_baseline()`'s local `deep-cpu` trial is still the fallback. See CLAUDE.md's Non-obvious traps below for the anonymous-access/`.rendered`-vs-`.raw` finding and the (now-resolved) [wspy#278](https://github.com/mvermeulen/wspy/issues/278) `vectorization_density`/`allocation_pressure` gap. |
| `cfm/cli.py` | `cfm measure`/`cfm init-db`/`cfm mine`. `mine` wires all five orchestrator phases in sequence, `--max-trials` best-effort-caps Phase 2's candidate list (the widest fan-out point — Phase 4/5's own trial count isn't separately capped yet), prints a plain JSON summary (winning flags, ratio, %gain) — no curated report yet, that's M3. |
| `scripts/bootstrap_wspy.sh` | Initializes + builds the `vendor/wspy` submodule ("wspy dependency" above). |
| `vendor/wspy` | Pinned wspy submodule — not part of this project's own code, never edited here. |

## Common edits

- **New workload/suite backend** (e.g. `workloads/spec_cpu2017.py`): implement `WorkloadBackend`'s
  four methods (`workloads/base.py`). `run_command()` must return an argv, not execute anything —
  see that file's docstring for why. Fork wspy's own `workload/cpu2017/run_test.sh` for the real
  `runcpu`/`shrc` mechanics rather than re-deriving them (doc/DESIGN.md §4.1's "existing groundwork"
  note).
- **New instrumentation backend** (e.g. a `perf stat`-only fallback): implement
  `InstrumentationBackend.characterize()` (`instrumentation/base.py`), returning the same
  `RunSignature` shape so nothing downstream needs to know which backend produced it.
- **New `cfm.db` field**: add the column to `schema/cfm_schema.sql` (it's applied via
  `executescript()`, so a fresh db always gets the latest DDL — there is no migration-step dispatch
  yet, unlike wspy's `store.c`; add one when this project has existing-database rows worth preserving
  across a schema change), bump `schema_meta.schema_version` in the same commit (MINOR/MAJOR per the
  "Schema and prompt-template versioning" section above), and update `doc/DESIGN.md` §7's SQL excerpt
  to match — the two have drifted out of sync once already by hand; don't let it happen again in code.
- **New `cfm db.py` accessor**: keep it a direct, obvious SQL statement (no ORM) — matches every
  existing accessor in that file.

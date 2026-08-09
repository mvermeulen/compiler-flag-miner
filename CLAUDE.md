# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

**Status: M0 shipped, M1 in progress** (doc/DESIGN.md §14) — the mechanical pipeline (`cfm measure`)
is unit-tested and has been verified end to end against this host's real SPEC CPU2026/wspy install
(a real `--action=validate` run, single-pass `quick` profile). M1's rule-based screening/confirmation
loop (§6 Phases 1-5) is under active development, landing as a series of small merged PRs (git log has
current progress). Compiler-knowledge catalog wiring, cross-benchmark knowledge transfer, and the LLM
driver are still ahead — M2-M3 (doc/DESIGN.md §13's layout table marks exactly what exists vs. what's
still pending, module by module).

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
  host without explicit confirmation first.
- **Maintain the "Non-obvious traps" log below.** Same discipline as wspy's
  `doc/INVESTIGATION_ARCHIVE.md` "Non-obvious implementation traps" section — a real gotcha found
  during implementation gets written down here, flagged as required reading before touching related
  code again, not left to be rediscovered.

## Non-obvious traps

- **Resolved 2026-08-09: SPEC's `.rsf` ratio field, confirmed against a real run — field name was right,
  two structural assumptions weren't.** A real `--action=validate --iterations 3` run of
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
```

`tests/` has two tiers: pure-logic unit tests (config resolution, `.rsf`/trace-output parsing, `cfm.db`
schema and accessors, SPEC config rendering, preflight's binary-existence check — no SPEC license or
wspy checkout needed at all) and `tests/test_wspy_interface.py`'s contract tests (real
`wspy`/`wspy-run`/`wspy-store`/`wspy-archetype` invocations against a toy C workload, ~25s total,
skipped cleanly rather than failed when `vendor/wspy` isn't built). Neither tier touches a real
`runcpu`/SPEC install — `cfm measure` above is the only thing that does, and it's manual/opt-in, never
part of the automated suite.

## Architecture

**Data flow (M0):** `cfm measure` (`cli.py`) → `agents/spec_agent.run_one_trial()` → SPEC Runner
(`workloads/spec_cpu2026.py`: render a trial config, build, hand a `runcpu --action=validate` argv to
—) → Instrumentation (`instrumentation/wspy.py`: `wspy-run` executes that argv, then `wspy-validate`/
`wspy-store`/`wspy-archetype` sequence over the result) → back to the SPEC Runner to parse the `.rsf`
ratio → one row each in `cfm.db`'s `experiments`/`trials` tables (`db.py`), regardless of outcome.

| File | Responsibility |
|---|---|
| `cfm/util.py` | `parse_kv_lines()` — shared `key=value`-per-line parser for both wspy's trace-style CLI output and SPEC's `.rsf` format. |
| `cfm/config.py` | `CfmConfig.from_env()` — env-var-driven paths/hostname (`CFM_SPEC_DIR`, `CFM_WSPY_DIR`, ... — see the file for the full list and defaults), explicit kwargs > environment > built-in default, resolved at call time. |
| `cfm/db.py` | Applies `schema/cfm_schema.sql` (idempotent) and provides typed `create_experiment`/`record_trial`/`get_experiment`/`list_trials`/`finish_experiment` accessors. No ORM. |
| `cfm/workloads/base.py` | `WorkloadBackend` interface + `BuildResult`/`RunResult` dataclasses (doc/DESIGN.md §4.1/§12). |
| `cfm/workloads/spec_cpu2026.py` | The only implementation: renders a per-trial SPEC config via `include:` + a `<bench>=peak:` override section, drives `runcpu --action=build`/`--action=validate` through a `shrc`-sourcing `bash -c` wrapper (see Non-obvious traps above), parses the resulting `.rsf` file. |
| `cfm/instrumentation/base.py` | `InstrumentationBackend` interface + `RunSignature` dataclass (doc/DESIGN.md §4.2/§12). |
| `cfm/instrumentation/wspy.py` | The only implementation: `preflight()` checks all five wspy binaries exist; `characterize()` runs `wspy-run <profile> -- <command>`, then resolves the *real* run identity from the run-index file (see Non-obvious traps), then `wspy-validate`/`wspy-store`/`wspy-archetype`. Raises `RuntimeError` on a multi-pass profile (e.g. `deep-cpu`) — not supported yet, see the same section. |
| `cfm/agents/spec_agent.py` | `run_one_trial()` — the M0 pipeline glue described above. The only agent module that exists; `knowledge_agent`/`hypothesis_agent`/`report_agent` are M2-M3. |
| `cfm/cli.py` | `cfm measure`/`cfm init-db`. Not `cfm mine` — that's the orchestrator's entry point, M1. |
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

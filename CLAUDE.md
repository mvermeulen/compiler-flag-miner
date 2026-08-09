# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

**Status: M0 shipped** (doc/DESIGN.md §14) — the mechanical pipeline (`cfm measure`) exists and is
unit-tested, but hasn't yet been exercised against this host's real SPEC CPU2026/wspy install (wspy
isn't built here yet — `preflight()` catches that and fails cleanly rather than mid-pipeline). No
search loop, compiler-knowledge catalog wiring, cross-benchmark knowledge transfer, or LLM driver yet
— those are M1-M3 (doc/DESIGN.md §13's layout table marks exactly what exists vs. what's still
pending, module by module).

## Documentation map

- `doc/prompt.txt` — the original design brief.
- `doc/DESIGN.md` — the architecture: agents, control flow, data model, cross-benchmark knowledge
  transfer, LLM integration, modularity seams, decisions (§15), and the phased build plan (§14,
  M0-M6). Read this before making any structural change — this file covers *practices*, DESIGN.md
  covers *design*.
- `config/gcc_flag_catalog.seed.json` — seed GCC/GFortran flag knowledge base.
- `schema/cfm_schema.sql` — `cfm.db` schema, kept separate from wspy's own `store.db`.
- `git log`/`git blame` for history — same convention wspy's `CLAUDE.md` uses; this file covers
  current practice only, not why a decision was made (that's `doc/DESIGN.md` §15, or git history for
  anything DESIGN.md itself doesn't capture).

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

- **SPEC's `.rsf` ratio field name is an educated guess, not a confirmed fact.**
  `cfm/workloads/spec_cpu2026.py`'s `CANDIDATE_RATIO_FIELDS` assumes the per-benchmark/tune ratio
  lives under a `...ratio` key in the `.rsf` file, based on SPEC's docs and CPU2017-generation
  naming conventions — but no `--action=run`/`validate` has ever completed on this host (only
  `--action=build`), so there is no real `.rsf` file to check it against yet. The first real trial run
  must confirm or correct this list; update this entry (don't just delete it) once it has, so the next
  session knows the guess was actually verified rather than just no-longer-flagged.
- **A bare `subprocess.run()` does not get SPEC's `shrc`-exported environment.** `runcpu` needs
  `PATH`/`PERL5LIB`/etc. that `$SPEC/shrc` exports; wspy's own `workload/cpu2017/run_test.sh` gets
  this for free by sourcing `shrc` once into its own long-lived shell before calling anything else.
  `cfm/workloads/spec_cpu2026.py` doesn't have that luxury (Python subprocess calls don't inherit a
  sourced-but-not-exported shell function's environment), so every `runcpu` invocation is individually
  wrapped as `bash -c 'cd $SPECDIR && source shrc && ulimit -s unlimited && exec runcpu ...'` — don't
  "simplify" this back to a bare `subprocess.run(["runcpu", ...])`, it will fail to find `runcpu` (and
  worse, may silently find a *different* stale `runcpu` on `PATH`) without the sourced environment.

## Build & test

```
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q                      # unit tests only -- no real SPEC/wspy calls, see below
.venv/bin/cfm init-db --db /tmp/x.db     # sanity-checks schema application, no SPEC/wspy needed
.venv/bin/cfm measure 706.stockfish_r --flags "-O3 -march=native -flto"
                                          # the real thing -- needs `make` run in the wspy checkout
                                          # first (`preflight()` says so explicitly if it isn't) and a
                                          # working SPEC CPU2026 install; a real invocation launches an
                                          # actual SPEC build+run (minutes, real CPU/disk use) --
                                          # confirm with the user before running this one, per the
                                          # exclusive-machine-access rule above.
```

`tests/` covers pure logic only (config resolution, `.rsf`/trace-output parsing, `cfm.db` schema and
accessors, SPEC config rendering, preflight's binary-existence check) — nothing that shells out to a
real `runcpu` or `wspy` binary, so the suite runs identically on a host with no SPEC license or wspy
checkout at all. A real end-to-end run is the manual, opt-in `cfm measure` invocation above, not part
of the automated test suite.

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
| `cfm/instrumentation/wspy.py` | The only implementation: `preflight()` checks all five wspy binaries exist; `characterize()` runs `wspy-run <profile> -- <command>`, then `wspy-validate`/`wspy-store`/`wspy-archetype`. |
| `cfm/agents/spec_agent.py` | `run_one_trial()` — the M0 pipeline glue described above. The only agent module that exists; `knowledge_agent`/`hypothesis_agent`/`report_agent` are M2-M3. |
| `cfm/cli.py` | `cfm measure`/`cfm init-db`. Not `cfm mine` — that's the orchestrator's entry point, M1. |

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

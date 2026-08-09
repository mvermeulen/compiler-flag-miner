# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

**Status: planning stage, no `cfm/` code yet.** This file is deliberately a minimal placeholder —
practices and conventions only. It does not describe an "Architecture" or "Common edits" section
(wspy's `CLAUDE.md` has both) because there is no mechanism yet to describe accurately; a section
that claims to cover mechanism before mechanism exists goes stale on day one. Expand this file with
those sections once `cfm/` (doc/DESIGN.md §13) actually lands — wspy's own `CLAUDE.md` is the
template to imitate for shape/tone at that point, not to copy before there's something real to say.

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

None yet — this project has no code. Entries go here as they're found, each with enough context
(what broke, why it wasn't obvious, what to check before repeating the mistake) that a future session
doesn't have to rediscover it the hard way.

## Build & test

No code yet. See `doc/DESIGN.md` §14 for the M0-M6 phased build plan; M0 ("mechanical pipeline, no
search, no LLM") is the first milestone that will give this section something real to say. Until
then, there is nothing to build or test here beyond the docs/schema/catalog files themselves.

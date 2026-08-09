# compiler-flag-miner

An agentic system for intelligently mining compiler flags for peak performance. First target: SPEC
CPU2026 gcc/gfortran, instrumented via [wspy](https://github.com/mvermeulen/wspy), orchestrated by a
deterministic Python state machine with a local LLM (llama.cpp or Ollama) doing narrowly-scoped,
structured-output reasoning at specific decision points -- never freely driving the tool loop.

Status: **M0 shipped** -- the mechanical pipeline (`cfm measure`: generate a SPEC config for one
hand-chosen flag set, build, run under wspy instrumentation, record the result) exists and is
unit-tested, not yet exercised against a live SPEC/wspy install. No search loop, LLM, or
cross-benchmark knowledge transfer yet -- see `doc/DESIGN.md` §14 for the M0-M6 plan and §13 for
exactly what's implemented vs. pending.

- `doc/prompt.txt` -- the original design brief.
- `doc/DESIGN.md` -- the architecture: agents, control flow, data model, cross-benchmark knowledge
  transfer, LLM integration, modularity seams, decisions (§15), and the phased build plan (§14, M0-M6).
- `config/gcc_flag_catalog.seed.json` -- seed GCC/GFortran optimization-flag knowledge base, not yet
  wired into any code (M2) but referenced by `doc/DESIGN.md` section 4.3.
- `schema/cfm_schema.sql` -- SQLite schema for experiment/trial/knowledge-base state
  (`doc/DESIGN.md` section 7), kept separate from wspy's own `store.db`.
- `cfm/` -- the Python package. `pip install -e '.[dev]'` then `cfm --help`; see `CLAUDE.md`'s
  "Build & test" section for the full command set including the unit test suite.
- `CLAUDE.md` -- development practices/conventions (git workflow, schema versioning discipline,
  enforced safety rules, architecture/common-edits reference) for anyone (human or Claude Code)
  working in this repo.

Read `doc/DESIGN.md` first.

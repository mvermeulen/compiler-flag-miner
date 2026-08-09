# compiler-flag-miner

An agentic system for intelligently mining compiler flags for peak performance. First target: SPEC
CPU2026 gcc/gfortran, instrumented via [wspy](https://github.com/mvermeulen/wspy), orchestrated by a
deterministic Python state machine with a local LLM (llama.cpp or Ollama) doing narrowly-scoped,
structured-output reasoning at specific decision points -- never freely driving the tool loop.

Status: **design only, no code yet.**

- `doc/prompt.txt` -- the original design brief.
- `doc/DESIGN.md` -- the architecture: agents, control flow, data model, cross-benchmark knowledge
  transfer, LLM integration, modularity seams, and a phased build plan (M0-M5).
- `config/gcc_flag_catalog.seed.json` -- seed GCC/GFortran optimization-flag knowledge base referenced
  by `doc/DESIGN.md` section 4.3.
- `schema/cfm_schema.sql` -- SQLite schema for experiment/trial/knowledge-base state
  (`doc/DESIGN.md` section 7), kept separate from wspy's own `store.db`.
- `CLAUDE.md` -- development practices/conventions (git workflow, schema versioning discipline,
  enforced safety rules) for anyone (human or Claude Code) working in this repo.

Read `doc/DESIGN.md` first.

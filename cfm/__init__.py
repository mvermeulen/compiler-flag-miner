"""compiler-flag-miner (cfm): agentic system for mining compiler flags for peak
performance. See doc/DESIGN.md for the full architecture.

M0 scope only right now (doc/DESIGN.md sec. 14) -- the mechanical pipeline for one
fixed, hand-chosen flag set: generate a SPEC CPU2026 peak config, build it, run it
under wspy instrumentation, and persist one validated, wspy-measured trial to cfm.db.
No orchestrator phase machine, screening/confirmation search, compiler-knowledge
catalog wiring, cross-benchmark knowledge transfer, or LLM driver yet -- those are
M1-M3. `cfm measure` (cfm/cli.py) is today's entry point; `cfm mine` (the
search-driving command doc/DESIGN.md sec. 6 describes) doesn't exist until M1.
"""

__version__ = "0.1.0"

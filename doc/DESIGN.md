# compiler-flag-miner: architecture design

Status: design, no code yet. This document is the answer to `doc/prompt.txt`'s brief. It describes
an agentic system ("cfm") that mines compiler flags for peak performance, built to be modular across
compilers/workloads/instrumentation/LLM backends, with SPEC CPU2026 gcc/gfortran as the first
concrete target.

## 1. Goals and non-goals

**Goal (v1)**: given a SPEC CPU2026 benchmark name (e.g. `706.stockfish_r`), autonomously produce a
`runcpu` peak-tuning configuration that beats the `-O3` base build, with evidence (performance
counters, statistical confidence) for *why* each flag helped, and durable cross-benchmark learnings.

**Non-goals (v1)**: SPEC "reportable run" compliance (fair-use rules, `basepeak`, disclosure
requirements) — this is a performance-mining tool, not a submission-generation tool, though nothing
here precludes later feeding a mined peak config into a compliant run. Also not in scope: multi-node
distributed search, GPU-offload flag mining, or non-GCC compilers — those are explicitly the
modularity seams this design leaves open, not v1 work.

**Reuse, don't rebuild**: wspy already solves instrumentation, storage, statistics, and workload
classification. This design adds a thin new layer on top — SPEC config generation, a GCC flag
knowledge base, an experiment-design loop, and an LLM-assisted hypothesis/report layer — rather than
re-implementing anything wspy already does well. Every "agent" below is mostly a orchestration
wrapper around existing wspy CLIs (`wspy-run`, `wspy-store`, `wspy-summary`, `wspy-archetype`,
`wspy-validate`, `wspy-analyze`) plus SPEC's `runcpu`.

## 2. Design principles

1. **Deterministic core, LLM at the edges.** wspy's own `wspy-analyze` design note is the model to
   follow: "narration over classification — every bottleneck category/verdict fed into the prompt was
   computed by deterministic code before this tool ever runs, never re-derived by the model." This
   system inherits that split hard. The reason it matters *more* here than for wspy-analyze: this
   system's LLM is local (llama.cpp/Ollama, likely an 8B-70B class model), not a frontier model with
   strong long-horizon tool-use. A local model driving a multi-hour build/run/measure loop via free-form
   tool calling is a reliability risk (dropped steps, hallucinated flag names, runaway loops). So the
   **orchestrator is a deterministic Python state machine**; the LLM is called for narrowly-scoped,
   structured-output tasks embedded *inside* that state machine (see §9), never given the wheel.
2. **Every trial is falsifiable.** A candidate flag set's "win" is only real if (a) the SPEC build
   succeeds, (b) `runcpu --action=validate` accepts the output against the reference, and (c) the
   performance delta clears wspy-summary's own statistical bar (non-overlapping 95% CI vs. the current
   baseline, not just a higher point estimate from a single run). No step here invents new statistics —
   `wspy-summary`'s verdict/CI logic is reused directly.
3. **Learnings generalize by *workload shape*, not by name.** Requirement 4 asks for retained learnings
   "so they might also be tried with future benchmarks." The generalization key is `wspy-archetype`'s
   `resource_dominance`/cluster classification, not the SPEC benchmark string — a brand-new benchmark
   that clusters near `706.stockfish_r` (frontend/speculation-bound) inherits stockfish's flag history
   as a prior, whether or not anyone hand-labeled the similarity. This reuses `wspy-archetype
   --kmeans`/`--nearest` rather than inventing a second similarity metric.
4. **Modularity via three small interfaces**, so "expand to other compilers/workloads" (the explicit
   ask) is an implementation of an interface, not a rewrite: a **compiler backend** (flag catalog +
   validation + config rendering), a **workload backend** (build/run/parse for one benchmark suite), and
   an **instrumentation backend** (raw counters → a workload "signature"). wspy is the only
   instrumentation backend today but isn't hard-baked into the orchestrator's control flow.
5. **Everything is data.** Every trial, hypothesis, and cross-benchmark learning is a row in SQLite, not
   a log line — the same posture wspy takes with `wspy-store`. This is what makes the knowledge base
   (§8) and the final report (§10) regenerable rather than hand-maintained.
6. **Safety over cleverness.** Aggressive flags (`-Ofast`, unsafe-math, PGO with a mismatched training
   run) can silently produce a *faster but wrong* binary. Correctness validation gates every performance
   number; nothing downstream ever sees an unvalidated trial's numbers. See §11.

## 3. System overview

```
                         ┌─────────────────────────────────────────────┐
                         │              Orchestrator (cfm)              │
                         │   deterministic phase state-machine (§6)     │
                         └───────────────┬───────────────────────────────┘
                                          │ calls, in narrow/typed ways
        ┌───────────────┬────────────────┼────────────────┬──────────────────┐
        ▼                ▼                ▼                ▼                  ▼
 ┌─────────────┐  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  ┌───────────────┐
 │ SPEC Runner  │  │ Instrument.  │ │  Compiler    │ │  Hypothesis  │  │  Local LLM     │
 │ agent        │  │ agent (wspy) │ │  Knowledge   │ │  / Experiment│  │  driver        │
 │              │  │              │ │  agent (gcc) │ │  Designer    │  │  (llama.cpp /  │
 │ runcpu:      │  │ wspy-run,    │ │              │ │              │  │   Ollama, one  │
 │ generate cfg,│  │ wspy-store,  │ │ flag catalog,│ │ ranks/prunes │  │  OpenAI-chat-  │
 │ build, run,  │  │ wspy-summary,│ │ candidate    │ │ candidates,  │  │  compatible    │
 │ validate,    │  │ wspy-archetype│ │ flags per   │ │ decides next │  │  interface)    │
 │ parse ratio  │  │ wspy-validate│ │ topdown      │ │ trial, judges│  │                │
 │              │  │              │ │ signature    │ │ convergence  │  │                │
 └──────┬───────┘  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘  └───────┬────────┘
        │                 │                │                │                   │
        └─────────────────┴────────────────┴────────────────┴───────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────────────────┐
                         │   cfm.db (SQLite): experiments, trials,      │
                         │   hypotheses, knowledge (§7) — plus wspy's   │
                         │   own store.db (runs/run_features), joined   │
                         │   by run_id                                  │
                         └─────────────────┬─────────────────────────────┘
                                          ▼
                         ┌─────────────────────────────────────────────┐
                         │   Report agent — curated Markdown report,    │
                         │   reusing wspy-testpoint's block/curation    │
                         │   idiom + wspy-analyze's prompt-template     │
                         │   idiom for the narrative section            │
                         └─────────────────────────────────────────────┘
```

Two SQLite databases, not one: wspy's `store.db` (schema owned by wspy, ingested via `wspy-store
--run-index`) holds raw counters/features; `cfm.db` (schema owned by this project, §7) holds
experiment/trial/knowledge-base state and references wspy runs by `(hostname, run_id)` — the same
foreign-key idiom `wspy-testpoint` already uses to link its own `runs.json` back into `wspy-store`.
Not merging them keeps wspy's schema versioning independent of this project's, exactly the boundary
wspy already draws between itself and `wspy-testpoint`/`wspy-publish`.

## 4. Agents and their responsibilities

Mapped directly to `doc/prompt.txt`'s five items, plus the orchestrator and knowledge base that tie
them together.

### 4.1 SPEC Runner agent

Owns everything `runcpu`-shaped: generating a new config file (or `--define`/OPTIMIZE-string variant
of an existing one — see below) for a candidate flag set, running `--action=build`, `--action=run` or
`--action=validate`, and parsing the result. Concretely:

- **Config generation**: SPEC CPU config files (`gcc_O3.cfg` in the existing scaffolding, see
  `workload/cpu2026/*/gcc_O3/{base,peak}/`) set `OPTIMIZE`/`COPTIMIZE`/`FOPTIMIZE`/`CXXOPTIMIZE` per
  tuning level. This agent renders a new config from a small Jinja-style template plus a flag-set
  object, rather than hand-editing SPEC's own `.cfg` syntax per trial — one template, one flags list in,
  one `.cfg` out. Base and peak configs get separate OPTIMIZE lines (SPEC's own base/peak distinction —
  base requires one flag set for the *whole suite*, peak allows per-benchmark tuning; v1 mines *peak*
  config, since per-benchmark tuning is exactly what "find peak compiler options" means).
- **Build/run/validate**: shells out to `runcpu`, capturing stdout/stderr the same way
  `workload/cpu2017/run_test.sh` already does (`| tee <log>`), parses exit status and the generated
  result files for pass/fail and estimated ratio/score. A failed build or a failed `--action=validate`
  (output doesn't match SPEC's reference) marks the trial `invalid` — never reaches the performance
  comparison stage. This is the correctness gate from principle 2/6.
- **Existing groundwork**: `workload/cpu2026/{706.stockfish_r,707.ntest_r,708.sqlite_r,709.cactus_r}`
  already have working `gcc_O3` base+peak build scaffolding on this host (`source.json`,
  `build.gcc_O3.log`) spanning intrate and fprate — real, already-proven `runcpu` mechanics to build
  the SPEC Runner agent against immediately, no new SPEC-side plumbing required to start.
- **Interface** (`workloads/base.py`, §12, implemented): `generate_config(bench, tune, flags) ->
  Path`, `build(bench, tune, config_path) -> BuildResult`, `run_command(bench, tune, config_path,
  iterations) -> argv`, `parse_result(bench, tune, raw_output) -> RunResult`. Note the one refinement
  from earlier drafts: `run_command` returns the argv for the measured run rather than executing it
  (originally sketched as `run(...) -> RunResult` directly) — this class never launches the measured
  run itself, since wrapping it in `wspy-run` is the whole reason it happens under the Instrumentation
  agent's control (§4.2) instead. This is the seam a future `workloads/spec_cpu2017.py` or
  `workloads/phoronix.py` implements identically.

### 4.2 Instrumentation agent (wspy)

A thin Python wrapper over the existing wspy CLI surface — no new instrumentation code, this agent's
whole job is sequencing wspy's own tools correctly and turning their output into typed Python values
the rest of the system consumes:

- Wraps each trial's SPEC run in `wspy-run --suite cpu2026 --benchmark <bench> --run-id <id> <profile>
  -- runcpu ...` (the exact pattern `workload/cpu2017/run_test.sh` already establishes for CPU2017 —
  this agent is that script's logic, parameterized and called from Python instead of hand-invoked per
  benchmark). Profile choice is tiered (§6.3): `quick` for screening trials, `deep-cpu` for confirmation.
- After each run: `wspy-store --db store.db --run-index <index>` (ingest),
  `wspy-validate <manifest>` (sanity, distinct from SPEC's own correctness validate above — this one
  catches counter-collection problems: permission-denied counters, truncated CSV),
  `wspy-archetype --run <host:run_id>` (get `resource_dominance`/`memory_attribution` — the "signature"
  the Compiler Knowledge and Hypothesis agents key off), `wspy-summary --run-id ... --check-regression`
  style comparison against the running baseline for the statistical accept/reject call.
- **Interface** (`instrumentation/base.py`, implemented): `characterize(command, suite, benchmark,
  run_id, profile, output_root) -> RunSignature` — this is the method that actually shells out to
  `wspy-run <profile> -- <command>` (the `command` argv comes from the SPEC Runner agent's
  `run_command()`, §4.1) — where `RunSignature` bundles the wspy run id, the archetype scorecard, and
  the metric table wspy-summary would report — the one object every other agent reasons about, so a
  future non-wspy instrumentation backend (e.g. raw `perf stat` on a host without wspy) only needs to
  produce the same `RunSignature` shape. `preflight()` checks all five wspy binaries exist before any
  subprocess call, failing fast and specifically (mirroring `wspy --preflight`'s own posture) rather
  than surfacing a missing binary as an opaque subprocess error mid-pipeline.
- **`deep-cpu` (multi-pass) confirmation-stage support is built (M1).** `characterize()` resolves
  which of `deep-cpu`'s 3 underlying `wspy` processes (`systemtime`/`counters`/`amdtopdown`, each with
  its own independently-generated `run_id`) actually carries the CSV topdown data
  `wspy-archetype`'s `resource_dominance` scoring reads — confirmed live to be `counters` (updated post
  wspy#274/#275/#276, pin `bc65f57`; it was `amdtopdown` through the earlier `1c192a7`/`3839815` pins,
  before `counters` had `--csv` output at all — CLAUDE.md's "wspy dependency" traps log has the full
  story, including the wrong initial guess). Single-pass profiles (`quick`) and the `deep-cpu`
  multi-pass profile both work end to end; any other multi-pass profile
  (`deep-cpu-intel`/`deep-gpu`/`zen4plus-deep`/a comma-composed list) still raises rather than
  guessing, since none of those are exercised by this project yet.
- **wspy dependency**: `vendor/wspy` is a git submodule pinned to a specific, tested commit (not a live
  checkout this project tracks automatically), with `tests/test_wspy_interface.py` as a contract-test
  suite run against it — real `wspy`/`wspy-run`/`wspy-store`/`wspy-archetype` invocations against a toy
  workload, asserting the exact output shapes this section's code depends on. See CLAUDE.md's "wspy
  dependency" section for the bootstrap/update workflow; this is the concrete implementation of
  principle 2's "every trial is falsifiable" applied one level down, to the instrumentation layer
  itself rather than just to a flag trial's result.

### 4.3 Compiler Knowledge agent (GCC/GFortran)

Owns a **flag catalog**: name, GCC version introduced, applicable languages (C/C++/Fortran), category,
conflicts/requires (e.g. `-fprofile-use` requires a prior `-fprofile-generate` training run), a risk tag
(`safe` / `changes-fp-semantics` / `needs-validation`), and — the part that makes this useful for
hypothesis generation — a table of **topdown-signature → candidate flags**, seeded from
`gcc-16.2.0`'s Optimize-Options docs and well-established autotuning literature. A starting seed
(committed as `config/gcc_flag_catalog.seed.json`, see §13) rather than something the LLM invents at
runtime, because a hallucinated flag name fails loudly at build time and wastes a whole build+run
cycle — validated ahead of time, not discovered by trial-and-error:

| `resource_dominance` signature (from `wspy-archetype`)              | Candidate flags to try first |
|---|---|
| `frontend-bound`, elevated `icache_miss_pct`                        | `-freorder-blocks-and-partition`, `-freorder-functions`, PGO (`-fprofile-use`), `-flto`, reduced `--param max-inline-insns-auto` (code-size pressure may be self-inflicted) |
| `speculation-bound`, elevated `branch_mispredict_pct`                | PGO (branch probabilities beat static heuristics), `-mbranch-cost=N` tuning, *reverse* hypothesis: back off `-funroll-loops` if it's currently on (unrolling can hurt predictability on data-dependent branches) |
| `memory-bound`, `memory_attribution=corroborated`, cache/TLB signal | `-fprefetch-loop-arrays` + `--param prefetch-latency=N`, huge pages as a *system-level* companion action (flagged, not a compiler flag, but recorded alongside since it interacts with the same signal) |
| `vectorization_density=high` (native `wspy-archetype` axis, wspy PR #269/wspy#227) | `-mprefer-vector-width=256/512` — re-keyed off this axis directly rather than `resource_dominance` (a memory-bound *integer* workload doesn't benefit from a wider vector width just because it's memory-bound; §4.3's "Generalizing the signature vocabulary" note and §14 M2.5 item 1) |
| `memory-bound`, `uncorroborated` or `blocked`/`oversubscribed`       | **Do not chase compiler flags** — `wspy-archetype`'s own read says the CPU wasn't stalled by hardware; a real finding, but for the SPEC Runner/environment, not the flag search |
| `compute-bound`/`retiring` high, narrow margin, few misses anywhere  | Diminishing-returns signal — low priority for aggressive flags; `-march=<detected-uarch>` (from wspy's own `cpu_info.c` vendor/model detection) for the last few percent, then stop |
| Any signature, once base flags plateau                              | `-flto` (whole-program IPA) and PGO as compounding multipliers, tried *after* single-flag search converges (§6.3) — both are bigger, slower trials (LTO changes build time materially; PGO needs a training run) so they're deliberately late-stage, not part of the cheap screening pass |

- **Validation**: before any flag reaches the SPEC Runner agent, this agent checks it against the
  catalog (spelling, GCC-version applicability, conflicts) and against the *detected* GCC version/target
  (`gcc -v`, `wspy`'s own `cpu_info` vendor/model detection for `-march=`/`-mtune=` choices) — this is
  what keeps an LLM-proposed flag (§4.4) from silently wasting a build cycle on a typo or a flag that
  doesn't exist in the installed GCC.
- **Interface** (`compilers/base.py`): `candidate_flags_for_signature(signature) -> [FlagCandidate]`,
  `validate_flagset(flags, gcc_version, target) -> ValidationResult`, `render_optimize_string(flags) ->
  str`. `compilers/gcc.py` is the concrete implementation; `compilers/llvm.py`/`compilers/aocc.py` are
  the future modularity seam.

**Generalizing the signature vocabulary beyond topdown L1 (M2.5, §14).** The table above is keyed
purely on `resource_dominance`/`memory_attribution` — both derived only from topdown L1 percentages
(retire/frontend/backend/speculate). That's real signal, but too coarse for some catalog entries: e.g.
`-mprefer-vector-width=256/512` is currently gated on `memory-bound-corroborated`/`compute-bound` alone
(confirmed against the seed catalog live, 2026-08-09), meaning a memory-bound *integer* workload
(hash tables, graph traversal, chess move generation) gets vector-width flags proposed just as readily
as a genuinely FP-heavy one — those flags are near-irrelevant without floating-point/vector work to
widen. Confirmed live the same session that wspy already *measures* several relevant additional
counters that just aren't wired into this table yet:
  - **Floating-point/vector-op density** — wspy's `float` metric (AMD-only, `topdown.c:print_float()`,
    `(fp_ret_fops_AVX512+...+fp_ret_fops_scalar)/instructions*100`) is real and already reaches
    `store.db` as a generic metric (confirmed live via a direct `wspy --counters=float --csv` probe),
    but isn't yet promoted into `run_features` — `wspy-archetype`'s own maintainers already flagged
    this exact gap in `archetype.c`'s own header comment ("a new axis, e.g. floating-point density once
    `--float` has real cross-workload validation") as a deliberately deferred extension, not an
    oversight. **Update 2026-08-18: no longer a gap** — wspy's PR #269 promoted this to a real
    `vectorization_density` axis once the reference-matrix corpus supplied the cross-workload
    validation the maintainers were waiting for (§14 M2.5 item 1, §15).
  - **Page-fault rate** — unlike `float`, wspy's `fault_rate` ((minflt+majflt)/elapsed) is *already* a
    promoted `[feature]` reaching `run_features` today (confirmed against `doc/METRICS.md`) — purely a
    cfm-side gap (never added to this catalog's signal vocabulary), no wspy-side work needed to use it.
    **Update 2026-08-18:** wspy's PR #268 went further and added an `allocation_pressure`
    `wspy-archetype` axis derived from this same `fault_rate` field — the remaining cfm-side gap is
    now just referencing the axis in this catalog, not deriving anything from the raw feature.
  - Other PDF-suggested axes (`backend_memory` vs. `backend_cpu` split, `icache`/`opcache`/`dTLB` miss
    rates, IBS DRAM-bound rate) are a mix of already-`[feature]` and `[raw]`-only — each needs the same
    live check before assuming either way, not a blanket assumption. (PRs #266/#267/#272 added
    `frontend_latency_pct`/`frontend_bandwidth_pct` and `on_cpu`/`core_utilization` natively in the same
    upstream range, 2026-08-18 — not on this bulleted list originally, but the same kind of gap closing.)

See §14's M2.5 for the concrete plan (new `RunSignature` fields, expanded catalog `topdown_signals`
vocabulary, and how this relates to the external reference-matrix corpus) and §15 for the resolved
design questions (where a new axis is computed, and how document-style guidance like a generated
GCC-optimization guide should — and shouldn't — reach the LLM).

### 4.4 Hypothesis / Experiment Designer agent

The bridge between "counters say X" and "here's the next trial to run" — deterministic ranking logic,
with one bounded LLM call for creative augmentation (§9). Per iteration:

1. Pull candidate flags from the Compiler Knowledge agent (rule-based, keyed on the current baseline's
   `resource_dominance` signature).
2. Pull **prior track record** for those same flags from `cfm.db`'s `knowledge` table, keyed by the
   nearest archetype cluster (§8) — a flag that already has a strong positive track record on
   similar-shaped benchmarks is promoted to the front of the queue.
3. One structured LLM call: given the ranked candidate list + signature + prior knowledge summary, the
   LLM may (a) re-rank within the given list with a one-line rationale each, and (b) propose up to N
   *additional* flag names not already in the list — those additions are **always** re-validated by the
   Compiler Knowledge agent before being queued, same as rule-based candidates; a hallucinated flag
   here is filtered out silently, at worst wasting an LLM call, never a build cycle.
3. Emit the next trial (or batch of trials) to run, and — after results return — the accept/reject
   verdict (statistical, from wspy-summary's CI logic, not the LLM) that both updates the running
   baseline and writes a `knowledge` row.

### 4.5 Local LLM driver

One driver, two backends, because both expose (or can expose) an OpenAI-chat-compatible endpoint:
Ollama natively serves `/v1/chat/completions` alongside its own API, and `llama.cpp`'s `llama-server`
serves the same OpenAI-compatible surface. So `llm/driver.py` is a single client against that shape
(`base_url` + `model` config only), not two separate integrations — `--llm ollama:qwen2.5-coder:32b`
vs. `--llm llamacpp:http://localhost:8080` just changes the base URL/model string. This also means
adding vLLM or LM Studio later needs zero new code, matching the "modular ... expand to other
compilers, other workloads" spirit applied to the LLM axis too. **Default target: Ollama** (§15) —
`wspy-analyze` already runs against a local Ollama daemon on this host, so M3 has zero new local-LLM
setup to stand up; `llama-server` is supported identically from day one, just not the default.

Every call the rest of the system makes to this driver is **structured-output** (JSON-schema- or
grammar-constrained where the backend supports it — llama.cpp's GBNF grammars and Ollama's `format:
json` both work for this) — free-form prose is only ever requested for the final report narrative
(§9, job 4), never for anything the orchestrator branches on.

### 4.6 Knowledge base

Not really a separate "agent" so much as the persistence layer both the Hypothesis Designer and the
Compiler Knowledge agent read/write — but called out as its own component because it's the direct
implementation of prompt requirement 4's "retain learnings... so they might also be tried with future
benchmarks." Detailed schema in §7-8.

## 5. What the Orchestrator actually is

A deterministic Python state machine (`cfm/orchestrator.py`) implementing the phase sequence in §6,
calling the five agents above as plain function calls (not LLM tool-calls). Its job:

- Enforce budget guardrails (max trials, max wall-clock) regardless of what any agent "wants."
- Sequence phases and hold the "current best" flag set + its baseline statistics.
- Decide phase transitions from deterministic rules (budget exhausted, N consecutive non-improving
  trials, statistical convergence) — the LLM's "should we stop?" opinion (§9, job 3) is logged as an
  advisory annotation on the decision, never the sole trigger.
- Own the one `wspy-queue`-style constraint that matters here: **one trial runs at a time** on a given
  host (perf counters and SPEC's own run discipline both assume exclusive machine use) — trials are
  literally submitted through `wspy-queue` (already built, already handles this) rather than
  reimplementing serialization.

## 6. Control flow for the v1 use case

`cfm mine 706.stockfish_r --compiler-config gcc_O3.cfg --budget 25-trials --llm ollama:qwen2.5-coder:32b`

### Phase 0 — Preflight
Confirm: SPEC CPU2026 install reachable (`runcpu --action=build` on a null change, or reuse the
existing `source.json`/build log if still fresh), wspy built (`wspy --capabilities`), LLM endpoint
reachable (one cheap completion), `cfm.db` schema up to date. Fail fast and specifically — same
posture as `wspy --preflight`.

### Phase 1 — Baseline
Build+run the benchmark at the **starting** configuration (typically the existing `gcc_O3` base/peak —
already built on this host for the 4 scaffolded benchmarks) via the SPEC Runner agent; characterize via
the Instrumentation agent with the `deep-cpu` profile, 3 repetitions minimum (wspy-summary's own
`thin` threshold). This becomes the running baseline every subsequent trial is compared against, and
its `resource_dominance` signature drives Phase 2.

### Phase 2 — Hypothesis generation
Compiler Knowledge agent produces rule-based candidates from the baseline's signature; Hypothesis
Designer merges in cross-benchmark knowledge-base priors (§8) and the one bounded LLM re-rank/augment
call (§4.4); output is a prioritized trial queue, deduplicated and pre-validated.

### Phase 3 — Screening (cheap, one-factor-at-a-time)
Each candidate flag tried **individually** against the baseline, one build+run each, `quick` wspy
profile (fast, noisier — this stage exists to prune, not to conclude). A flag whose single-run result
is *clearly* worse than baseline (large negative delta, not just noise) is dropped; everything else
proceeds to confirmation. This bounds the expensive stage's input size — with, say, 30-60 flags in the
catalog, screening at one run each is far cheaper than confirming all of them at 3+ reps.

**Compared against baseline's most recent calibration rep, not its full-run mean** (`BaselineResult.
most_recent_ratio`, changed 2026-08-24 — real finding, not a hypothetical: see CLAUDE.md's Non-obvious
traps log's `750.sealcrypto_r` entry). Baseline's own 3 calibration reps can still be visibly settling
by the time Phase 3 starts immediately afterward; comparing every screening trial against the mean of
all 3 (pulled up by the earlier, higher reps) systematically biases every delta negative regardless of
the candidate's own real effect, not just adding noise. The most-recent rep is free — it's already
collected — and directly reflects wherever the benchmark had actually settled to by the time screening
begins. Confirmed for real the same day: a fresh re-mine of `750.sealcrypto_r` itself reproduced the
same real baseline-settling pattern, and this time all 5 previously-pruned flags correctly survived
screening and reached real Phase 4 confirmation, resolving the original run's own open question for
real (a genuine, clean reject, not a screening artifact) — see
`doc/mining_results.750.sealcrypto_r.2026-08-24b.md`.

### Phase 4 — Confirmation (statistical)
Surviving flags re-run individually with the `deep-cpu` profile, 3+ repetitions, and compared to the
baseline via wspy-summary's CI logic: accept only if the improvement's 95% CI doesn't overlap the
baseline's. Each accept/reject is written to `cfm.db`'s `trials` and `knowledge` tables (a *reject* is
retained too — a documented negative result is exactly the kind of learning that should transfer to the
next benchmark, so a future run doesn't re-spend a trial re-discovering it).

### Phase 5 — Greedy combination
Confirmed-positive flags are combined **greedily**: sort by observed lift, add one at a time to a
running "candidate peak" set, re-confirm the cumulative set at each step (interaction effects are not
assumed additive — a combination can underperform the sum of its parts, or occasionally outperform it).
Stop adding when the next flag's addition doesn't clear the statistical bar over the current cumulative
set. A small tournament of random *pairs* from the surviving set (not just the greedy path) catches
synergy the greedy order might miss, bounded to a fixed small trial count so it doesn't blow the budget.

### Phase 6 — Compounding multipliers (LTO / PGO / microarch)
Tried once the flag-level search plateaus, each as its own bigger trial layered on top of the winning
set from Phase 5: `-flto` (materially changes build time — a separate trial, not folded into screening),
PGO (needs a training run first — `-fprofile-generate` build, then a run using the benchmark's own
SPEC-provided train workload as the training input when one exists, per §15's decision, then
`-fprofile-use` rebuild — its own two-step sub-flow; a benchmark with no distinct train input gets its
PGO trial marked with an explicit representativeness caveat, §15), and a small fixed set of
`-march=`/`-mtune=` choices relevant to the *detected* host microarchitecture (reusing wspy's own
`cpu_info.c` vendor/model detection rather than an open-ended search over every `-march` value GCC
knows).

**PGO's real two-step build/train/rebuild sub-flow: rendering implemented and live-verified, orchestrator
wiring implemented (both 2026-08-22).** `cfm/workloads/spec_cpu2026.py`'s `generate_config()`
now recognizes `-fprofile-use`'s presence in the requested `flags` (the same "flags is the trial's full
logical identity" convention every other candidate already uses — no separate parameter) and renders
SPEC's own native `PASS1_OPTIMIZE`/`PASS2_OPTIMIZE` config mechanism (Docs/config.txt sec. VI) instead
of the flat single-`OPTIMIZE`-line shape every other candidate uses — `runcpu` itself then drives the
whole build-instrumented → train (using the benchmark's own SPEC-provided train workload, automatically
— no cfm-side orchestration of the training run needed at all) → rebuild-optimized sequence internally,
inside one `--action=build` invocation. Confirmed live end to end against `782.lbm_r` on this host: the
real SPEC log shows pass 1 compiling with `-fprofile-generate -fprofile-update=atomic`, `"Copy 0 of
782.lbm_r (peak train) run 1 finished"` (a single serial training copy, never fanned out across
SPECrate's own `copies` parameter — see §15's decision on why `-fprofile-update=atomic` is applied
anyway despite this), pass 2 recompiling with `-fprofile-use -fprofile-correction`, and the final
linked binary's own `.GCC.command.line` audit section showing `-fprofile-use -fprofile-correction`
compiled in (never `-fprofile-generate`, confirming the PASS2 rebuild is what actually got linked, not a
silently-reused PASS1 binary — exactly the class of failure the basepeak trap (CLAUDE.md) taught this
project to check for directly rather than trust `runcpu`'s own success report alone). `-fprofile-generate`/
`-fprofile-use` are also now excluded from `cfm/compilers/gcc.py`'s ordinary per-flag candidate list
entirely (`category == "pgo"`) — neither is meaningful tested alone against a single OPTIMIZE line (see
the now-retracted `doc/mining_results.714.cpython_r.2026-08-21.md`'s live illustration of exactly why).
`cfm/orchestrator.py`'s `run_pgo_multiplier()` now calls this rendering path with the Phase 5 winning
set (`combination.winning_flags + [PGO_FLAG]`), compared against Phase 5's own winning CI via the same
`_confirm_flagset()` machinery Phase 4/5 already use (`phase="multiplier"`, the schema's own
`trials.phase` CHECK constraint already anticipated this value). Two things keep an implausible or
already-decided-against PGO trial from spending its real ~2x build-time cost for nothing: a cheap
plausibility check mirroring `_filter_implausible_candidates()` (`compiler.pgo_topdown_signals()`, skip
outright — no trial spent — only when *every* signal is confidently contradicted by baseline's
characterized shape, same "absence of information is never implausible" rule as Phase 2's own check),
and `cli.py`'s `--skip-pgo` escape hatch for a cheaper/faster focused run. Accepted, it becomes the
final winning flagset (`cli.py`'s `mine` summary JSON's `winning_flags`/`winning_ratio_mean`, distinct
from `combination_winning_flags`/`combination_winning_ratio_mean` which always show Phase 5's own,
unmodified, result); rejected or skipped, Phase 5's own winning set is reported unchanged. Knowledge-
table upsert now fires for `phase in ("confirmation", "multiplier")` (was `"confirmation"`-only),
keyed on `PGO_FLAG` for the multiplier case. Verified against `tests/test_orchestrator.py`'s mocked-
backend tier (accept/reject/skip-as-implausible/unknown-shape-not-excluded/knowledge-upsert cases) and
`tests/test_cli.py`'s wiring tests, then confirmed for real end to end (2026-08-23): a full, uncapped
`cfm mine 714.cpython_r` run landed the project's first genuine accepted candidate of any kind through
this exact code path — `-flto` (+8.00%) then real two-pass PGO (+31.16% more) for +41.65% overall vs.
plain `-O3`, `714.cpython_r` picked deliberately as the one previously-mined benchmark whose
`frontend-bound` baseline actually clears `pgo_topdown_signals()`'s plausibility check. See
`doc/mining_results.714.cpython_r.2026-08-23.md` for the full write-up, and CLAUDE.md's matching
traps-log entry for a real audit false-negative (`-flto` on an LTO build) found and fixed along the way.

**Microarch multiplier: implemented and live-verified (2026-08-23).** `cfm/hostinfo.py`'s
`detect_microarch_flags()` shells out to `vendor/wspy`'s own `cpu_info` binary (a real, always-built
Makefile target) and parses its plain-text core listing — deliberately narrow, mapping only the AMD
`Zen5`/`Zen5c` core labels wspy can confidently distinguish to a concrete `-march=`/`-mtune=` value
(`znver5`); the ambiguous bare `Zen` bucket (wspy's own enum has no per-generation Zen1-4 distinction at
all, confirmed by reading `cpu_info.h` directly), Intel's generation-less buckets, and every ARM
Cortex/Neoverse label are all left unmapped rather than guessed at, degrading to "nothing detected" — a
clean skip, never a trial, matching this project's "never guess, verify or skip" discipline.
`cfm/orchestrator.py`'s `run_microarch_multiplier()` mirrors `run_pgo_multiplier()`'s own shape: tries
each detected flag independently (never combined with each other — `-march=X` already implies `-mtune=X`
as GCC's own default), layered on top of whatever the *prior* Phase 6 stage left behind via a duck-typed
`combination` argument (accepts either Phase 5's own `CombinationResult` or `run_pgo_multiplier()`'s own
`MultiplierResult`, both exposing `.winning_flags`/`.winning_ci` under the same names — lets `cli.py`
chain PGO → microarch without either function needing to know the other's return type). Skips entirely
when nothing was detected, or when the incoming winning set already carries an `-march=`/`-mtune=` flag
(most likely `-march=native`, already tried via the ordinary Phase 2-5 per-flag path — a second, different
microarch flag on top would conflict, not compound). Verified live against a real `782.lbm_r` build with
`-O3 -march=znver5`: compiled successfully, and — unlike `-march=native`, which GCC expands away before
recording — the literal `-march=znver5` text survives straight into the compiled binary's own
`.GCC.command.line` audit section, confirming both that the flag reached the compiler and that the audit
can verify it directly for this one. Exercised end to end the same day (2026-08-23): a real, uncapped
`cfm mine 706.stockfish_r` run correctly fired the conflict-avoidance guard (`-march=native` won via the
ordinary per-flag path first, confirmed byte-identical to `-march=znver5` on this host), and a separate,
bounded ad hoc verification against `782.lbm_r` (a synthetic `combination` deliberately holding no arch
flag, forcing the guard not to fire) exercised the actual trial path for real: both `-march=znver5`/
`-mtune=znver5` ran genuine SPEC builds and were correctly rejected. See CLAUDE.md's matching traps-log
entry and `doc/mining_results.706.stockfish_r.2026-08-23.md` for the full detail.

### Phase 7 — Finalize and report
Winning flag set assembled into a real `runcpu` peak config; one final confirmation run at higher
repetition count (locks in the number being reported); Report agent renders a curated Markdown report
(§10); `cfm.db`'s `knowledge` table is updated with every trial's outcome tagged by this benchmark's
archetype cluster, ready for the next benchmark to draw on.

## 7. `cfm.db` schema (new tables, alongside wspy's own `store.db`)

```sql
-- One mining run against one benchmark.
CREATE TABLE experiments (
  id INTEGER PRIMARY KEY,
  benchmark TEXT NOT NULL,          -- e.g. '706.stockfish_r'
  hostname TEXT NOT NULL,
  compiler TEXT NOT NULL,           -- 'gcc'
  compiler_version TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  budget_trials INTEGER,
  budget_wallclock_s INTEGER,
  status TEXT NOT NULL,             -- running|converged|budget-exhausted|failed
  baseline_run_ref TEXT             -- 'hostname:run_id' into wspy's store.db
);

-- One SPEC build+run attempt for one candidate flag set.
CREATE TABLE trials (
  id INTEGER PRIMARY KEY,
  experiment_id INTEGER NOT NULL REFERENCES experiments(id),
  phase TEXT NOT NULL,              -- screening|confirmation|combination|multiplier
  parent_trial_id INTEGER REFERENCES trials(id),   -- for greedy-combination lineage
  flags_json TEXT NOT NULL,         -- the exact flag list tried
  optimize_string TEXT NOT NULL,    -- rendered OPTIMIZE line, for reproducibility
  build_status TEXT NOT NULL,       -- ok|build-failed|validate-failed
  wspy_run_ref TEXT,                -- 'hostname:run_id' into wspy's store.db, null if build failed
  ratio REAL,                       -- SPEC estimated ratio/score, null if invalid
  delta_vs_baseline_pct REAL,
  verdict TEXT,                     -- accept|reject|inconclusive
  ci_overlap INTEGER,               -- 0/1, from wspy-summary's CI comparison
  created_at TEXT NOT NULL
);

-- Rationale trail: why a trial was proposed (rule-based, analogical, or LLM).
CREATE TABLE hypotheses (
  id INTEGER PRIMARY KEY,
  trial_id INTEGER NOT NULL REFERENCES trials(id),
  proposed_by TEXT NOT NULL,        -- rule|analogical|llm
  rationale TEXT NOT NULL,
  evidence_json TEXT,               -- counter signature snapshot that motivated it
  confidence REAL
);

-- Cross-benchmark generalization table -- the actual "retained learning."
-- Keyed by archetype cluster, not benchmark name, so it transfers. Scoped strictly by
-- compiler_version/target_arch (§15 decision) -- a GCC bump or a different microarch
-- starts confidence accumulation fresh for that combination rather than reusing old rows.
CREATE TABLE knowledge (
  id INTEGER PRIMARY KEY,
  cluster_key TEXT NOT NULL,        -- wspy-archetype resource_dominance label, or a
                                     -- --kmeans centroid id once enough history exists
  compiler TEXT NOT NULL,
  compiler_version TEXT,
  target_arch TEXT,                 -- detected microarch, e.g. 'znver4'
  flag TEXT NOT NULL,
  n_trials INTEGER NOT NULL DEFAULT 0,
  n_accepted INTEGER NOT NULL DEFAULT 0,
  mean_delta_pct REAL,
  stddev_delta_pct REAL,
  last_benchmark TEXT,
  last_updated TEXT NOT NULL,
  UNIQUE(cluster_key, compiler, compiler_version, target_arch, flag)
);
```

`trials.wspy_run_ref`/`experiments.baseline_run_ref` are the join keys back into wspy's `store.db` —
this table never duplicates counter data, only references it, the same "don't own what wspy already
owns" boundary `wspy-testpoint`'s `runs.json` draws.

## 8. Cross-benchmark knowledge transfer, concretely

1. After Phase 1 (baseline characterization) for a *new* benchmark, run `wspy-archetype --nearest
   <this-run>` (or `--kmeans` once there's enough history to re-cluster) against the accumulated store
   to find which existing, already-mined benchmarks this one most resembles.
2. Query `knowledge` for `cluster_key` matching those nearest benchmarks' own archetype label —
   `SELECT flag, mean_delta_pct, n_accepted, n_trials FROM knowledge WHERE cluster_key = ? ORDER BY
   mean_delta_pct DESC`.
3. Seed Phase 2's candidate queue with those flags **first**, ahead of the generic rule-based catalog —
   a flag with a strong track record on similar-shaped benchmarks skips straight to Phase 4
   (confirmation) rather than Phase 3 (screening), since it's already been screened once, elsewhere.
4. This is why `resource_dominance` (not the raw benchmark name) is the knowledge key: `707.ntest_r` and
   `706.stockfish_r` are unrelated SPEC benchmarks (Othello vs. chess engines) but if both land in the
   same frontend/speculation-bound archetype cluster, stockfish's mined flags become ntest's starting
   prior for free — exactly the transfer the prompt asked for, implemented by piggybacking on
   `wspy-archetype`'s existing similarity metric instead of inventing a new one.

## 9. What the LLM is actually asked to do (four bounded jobs, all structured output)

1. **Hypothesis re-rank/augment** (§4.4): given a JSON candidate list + signature + knowledge-base
   summary, return a re-ordered list with one-line rationales, plus up to N new flag proposals (always
   re-validated deterministically before use).
2. **Trial-outcome narration**: given a before/after counter snapshot and the deterministic
   accept/reject verdict, explain *why* in prose (for the report and for `hypotheses.rationale`) — same
   "explain, don't reclassify" contract as `wspy-analyze`'s existing prompt template (§10 reuses that
   template's own instructional preamble nearly verbatim).
3. **Convergence opinion**: given the trial history, an advisory "worth continuing?" judgment, logged
   alongside — never overriding — the deterministic budget/diminishing-returns stop rule.
4. **Report narrative**: the free-form job — executive summary and discussion prose for the final
   report, given every deterministic number already computed (matches the existing published report's
   own "AI Narrative Analysis" section, generated by `wspy-analyze` against the *same* Ollama-backed
   workflow this project's driver reuses).

Every prompt template is a versioned file under `cfm/llm/prompts/` (mirroring
`prompts/perf_analysis.tmpl`'s own `PERF_ANALYSIS_TEMPLATE_VERSION` convention) — a version number
bumped whenever wording could change model output, so a rendered `aiprompt.txt`-equivalent artifact
can always be traced to the exact template that produced it.

## 10. Report agent

Reuses, rather than reinvents, the report shape already live at the linked example URL and the
block/curation model `wspy-testpoint render` already implements: command-line/config section, counters
table (before/after, baseline vs. mined peak), an archetype/signature section, an AI narrative section
(LLM job 4 above), and plots (`wspy-plot` against the confirmation-stage `--interval` CSVs). Concretely
this agent assembles a `curation.json` + generated section files the same way `wspy-testpoint render`
already does, so the *existing* web launcher/report browser and `wspy-publish` pipeline can serve a
mining report with zero new rendering code — new content, existing renderer.

Report highlights section (deterministic, not LLM-authored): baseline ratio vs. peak ratio and % gain,
the winning flag list with each flag's individual measured contribution, the rejected-flag list (a
genuine finding — "these didn't help *this* benchmark," worth recording even negatively), and which
prior knowledge-base entries were reused vs. newly discovered here.

## 11. Safety and guardrails

- **Correctness gates everything**: SPEC's own `--action=validate` must pass before a trial's ratio is
  usable at all; flag sets carrying the Compiler Knowledge agent's `changes-fp-semantics` risk tag
  (`-Ofast`, `-ffast-math` and sub-flags) are still eligible to try (they're real, common wins) but are
  never accepted without a clean validate pass on that specific trial — no exceptions, no "probably
  fine."
- **Hard budget ceilings** (trial count, wall-clock) enforced by the orchestrator, independent of LLM
  opinion (§9 job 3 is advisory only, per principle 1).
- **Serial execution within a run**: one trial's build+run+measure at a time, via `wspy-queue`, since
  perf counters and SPEC's own run assumptions both want exclusive machine use.
- **Cross-invocation exclusivity: `cfm/lock.py`'s host-wide `flock` lock**, held for the duration of
  any `cfm measure`/`cfm mine` invocation, refusing (not queueing) a second concurrent one on the same
  host. This reverses this section's earlier stance ("this project adds no new concurrency-control
  code") after a real incident (CLAUDE.md's "Non-obvious traps" log, 2026-08-20): two `cfm mine`
  invocations launched ~13s apart both reached SPECrate's per-copy fan-out around the same time,
  saturating the host's RAM and forcing a hard reboot — `wspy-queue`'s serialization (above) only
  covers trials *within* one orchestrator process, never stopped a second process from starting in the
  first place, and SPEC's own `lock.CPU2026` file is just a run-ID counter, not a mutex.
- **Everything reproducible**: every trial's rendered SPEC config, wspy manifest, and run-index entry
  persists (same artifact-contract posture wspy already guarantees) — any trial's exact result can be
  re-run or bundled (`wspy-bundle`) independent of `cfm.db` staying intact.
- **No silent flag reuse across incompatible targets**: a flag's `knowledge` row is scoped by
  `(cluster_key, compiler, compiler_version, target_arch)` (§15's strict-scoping decision) — moving to a
  different GCC major version or a different target microarchitecture starts a fresh confidence
  accumulation for that combination, never blindly trusting old rows.

## 12. Modularity / extension points

| Axis | Interface | v1 implementation | Future implementations |
|---|---|---|---|
| Compiler | `compilers/base.py` | `compilers/gcc.py` (GCC + GFortran, shared flag catalog with a per-language applicability tag) | `compilers/llvm.py`, `compilers/aocc.py` |
| Workload/suite | `workloads/base.py` | `workloads/spec_cpu2026.py` | `workloads/spec_cpu2017.py` (fork of the already-working `workload/cpu2017/run_test.sh` pattern), `workloads/phoronix.py` (wspy already materializes Phoronix test points — see `wspy-phoronix-import`) |
| Instrumentation | `instrumentation/base.py` | `instrumentation/wspy.py` | a `perf stat`-only fallback for hosts without a wspy build, same `RunSignature` output shape |
| LLM | `llm/driver.py` | one OpenAI-chat-compatible client, pointed at Ollama or `llama-server` | vLLM, LM Studio, or a hosted API — `base_url`/`model` change only |

## 13. Repository layout

Marked per-item with what's actually implemented (M0) vs. still pending (a later milestone, §14):

```
compiler-flag-miner/
  doc/
    prompt.txt                    (existing)
    DESIGN.md                     (this document)
  config/
    gcc_flag_catalog.seed.json    (seed knowledge base; not yet read by any code -- M2)
  schema/
    cfm_schema.sql                (DDL from §7)
  vendor/
    wspy                          [M0] git submodule, pinned commit -- see CLAUDE.md's
                                   "wspy dependency" section for the bootstrap/update workflow
  scripts/
    bootstrap_wspy.sh             [M0] git submodule update --init + make -C vendor/wspy
  cfm/                            (python package)
    util.py                       [M0] shared helpers (parse_kv_lines, ...)
    config.py                     [M0] CfmConfig, env-var-driven
    db.py                         [M0] cfm.db schema application + typed accessors
    workloads/{base,spec_cpu2026}.py     [M0] SPEC Runner agent (§4.1)
    instrumentation/{base,wspy}.py       [M0] Instrumentation agent (§4.2)
    agents/spec_agent.py          [M0] run_one_trial(): the M0 pipeline glue --
                                   workload/instrumentation backends and the wspy
                                   profile are now injectable/overridable per call
                                   (M1: orchestrator.py needs a different profile
                                   per phase, and its own tests need fakes with no
                                   real SPEC/wspy calls)
    cli.py                        [M0+M1] `cfm measure <benchmark> --flags "..."`
                                   (M0) and `cfm mine <benchmark> [--max-trials N]`
                                   (M1) -- `mine` wires all five orchestrator
                                   phases into one command, unit-tested against
                                   mocked orchestrator calls, but not yet run for
                                   real against this host's SPEC/wspy install
                                   (that's a manual, opt-in confirmation step,
                                   same posture `cfm measure` had before M0's own
                                   real-run milestone)
    orchestrator.py                [M1] phase state machine (§5-6) -- Phases 1-5
                                   (baseline/candidate generation/screening/
                                   confirmation/greedy combination) all built and
                                   wired into `cfm mine` (cli.py); see that row
                                   for what's still outstanding before this is a
                                   "shipped and verified" milestone the way M0 is
    compilers/{base,gcc}.py        [M1] Compiler Knowledge agent (§4.3) -- built ahead of M2
                                   on purpose: candidate_flags_for_signature() ignores its
                                   own signature argument in M1 ("static catalog priors
                                   only"), returning the whole applicable-language catalog
                                   uniformly; M2 wires real resource_dominance-based
                                   filtering into this same file rather than creating it
                                   fresh
    agents/{knowledge_agent,hypothesis_agent}.py   [M2/M4]
    llm/driver.py, llm/prompts/    [M3] local LLM driver (§4.5, §9)
    agents/report_agent.py         [M3] Report agent (§10)
  tests/                           [M0] pure-logic unit tests, plus
                                   test_wspy_interface.py's contract tests (real
                                   wspy/wspy-run/wspy-store/wspy-archetype calls
                                   against a toy workload, skip cleanly if
                                   vendor/wspy isn't built) -- neither tier shells
                                   out to a real runcpu/SPEC install; a real
                                   end-to-end smoke run against this host's SPEC
                                   install is a separate, manual, opt-in step
  pyproject.toml                   [M0] stdlib-only, `pip install -e .` gives `cfm`
```

## 14. Phased build plan

- **M0 — mechanical pipeline, no search, no LLM. Shipped and verified end to end against a real SPEC
  run** (`cfm measure <benchmark> --flags "..."`, not the eventual `cfm mine` search command — that's
  M1). Given one fixed, hand-chosen flag set, generate a real peak config, build, run under `wspy-run`,
  and get one validated, wspy-measured ratio for `706.stockfish_r`. Proves the SPEC Runner +
  Instrumentation agents' plumbing end to end — literally: a real `--action=validate --iterations 3`
  run (`-O3 -march=native -flto`, 14m25s wall-clock) completed with `spec_validated: true`,
  `wspy_validated: true`, and a real extracted ratio (`151.206688`, median across 3 iterations). Getting
  there caught and fixed real bugs on both sides of the pipeline rather than leaving them for a future
  session to hit blind — full detail in CLAUDE.md's Non-obvious traps log:
  - **Instrumentation side**, caught by `tests/test_wspy_interface.py` (real `vendor/wspy` submodule +
    a toy workload, not just unit tests): a manifest-schema mismatch in `_validate()`, `wspy`'s silent
    no-op on a missing `--run-index` parent directory, and a `wspy-run --run-id`-vs-wspy's-own-
    generated-`run_id` identity mismatch.
  - **SPEC Runner side**, only caught by the real run itself: `.rsf` has no non-iteration-indexed
    rollup field (every value lives under a per-`NNN`-iteration block — fixed by reporting the median
    across iterations) and uses `"key: value"`, not `"key=value"` (the hand-written unit-test fixtures
    used `=` too, so they'd passed against the same wrong assumption — only a fixture copied from a real
    captured `.rsf` excerpt caught it, now `tests/fixtures/706.stockfish_r.peak.sample.rsf`). The
    `ratio` field name itself was right the whole time; both bugs were structural, not a wrong guess.
  Single-pass profiles (`quick`) only; `deep-cpu`/multi-pass support is explicitly deferred, see §4.2.
- **M1 — rule-based screening/confirmation loop (§6 Phases 1-5), no LLM. Shipped and verified end to
  end against a real SPEC run, 2026-08-20.** Static catalog priors only; `cfm mine <benchmark>` wires
  all five phases together (`orchestrator.py`), backed by `cfm/stats.py`'s CI logic for the
  accept/reject bar. Every phase function and the CLI's own argument/summary-building logic is
  unit-tested against mocked `WorkloadBackend`/`InstrumentationBackend` backends, plus the real,
  live-confirmed `deep-cpu` multi-pass fix from M1's first PR (§4.2) -- and, matching the bar M0 set
  ("shipped and verified" only after a real run, never on unit tests alone), a real
  `cfm mine 706.stockfish_r --max-trials 8` run: 2h18m wall-clock, all five phases completed cleanly,
  correctly rejected all 4 screened candidates (each looked marginally better under cheap
  single-iteration screening but measurably worse under 3-rep confirmation -- exactly the false-accept
  case §15's asymmetric-bar decision is designed to catch), and live-confirmed
  `_filter_implausible_candidates()` (M2.5 item 3) excluding 10 of 18 catalog flags against the
  baseline's real characterized shape, not just mocks. Two real gaps surfaced and fixed along the way,
  detailed in CLAUDE.md's Non-obvious traps log: a host-exclusivity lock (`cfm/lock.py`, after two
  concurrent `cfm mine` invocations crashed the host once) and a fix so a crashed/failed run's
  experiment row no longer gets stuck at `status='running'` forever.
- **M2 — signature-aware candidate filtering.** Wire in `wspy-archetype`'s `resource_dominance`/
  `memory_attribution` to drive Compiler Knowledge agent candidate selection (the table in §4.3),
  instead of trying the whole catalog uniformly.
- **M2.5 — generalized signature axes, external reference-matrix corpus, adaptive trial cost.**
  Motivated directly by two things confirmed live during M1's real end-to-end verification run
  (2026-08-09): the existing signature vocabulary is too coarse for some catalog entries (§4.3's new
  "Generalizing the signature vocabulary" note), and a single confirmation-grade (`deep-cpu`, 3
  repetitions) trial against a real, substantial SPEC benchmark took multiple hours on real hardware
  (PMU multiplexing — this host's 6 general-purpose counter slots can't fit `deep-cpu`'s full counter
  sweep in one pass, so wspy internally re-executes the workload several times per pass; invisible
  against a toy sub-second probe, very real against a multi-minute real benchmark). Three concrete
  pieces of work, sequenced by dependency:
  1. **New `RunSignature` fields — now largely a native `wspy-archetype` read, not a cfm-side
     computation (updated 2026-08-18, post wspy pin bump `1c192a7`→`3839815`).** The original plan here
     was to reach `fp_op_density_pct` via a `wspy-summary --metric float` shell-out and hand-roll an
     explicitly-uncalibrated threshold, since `float_pct` wasn't a promoted `wspy-archetype` axis yet
     (see the wspy#227 entry in §15). That's superseded: wspy's own PR #269 added a `vectorization_density`
     axis (low/moderate/high) from `float_pct` directly to `wspy-archetype`'s scorecard, with thresholds
     fit against the CPU2026 reference-matrix corpus (147 runs, 3 machines) — closing wspy#227 upstream
     instead of cfm needing to contribute it later. PR #268 likewise adds `allocation_pressure` from
     `fault_rate` natively. So this item is now: read `vectorization_density`/`allocation_pressure`
     (plus PRs #266/#267/#272's `frontend_latency_pct`/`frontend_bandwidth_pct`/`on_cpu`/
     `core_utilization`) straight off the scorecard `RunSignature` already parses, no new shell-out or
     threshold logic needed. Expand `config/gcc_flag_catalog.seed.json`'s `topdown_signals` vocabulary
     and §4.3's table to reference these — e.g. re-key `-mprefer-vector-width=256/512` off
     `vectorization_density` instead of the current too-coarse `memory-bound-corroborated`/
     `compute-bound` pair. See CLAUDE.md's "Non-obvious traps" (the wspy#270-superseded entries) for the
     confirming pin-bump detail. **Done** (`feature/vectorization-density-signal`): `RunSignature` now
     carries dedicated `vectorization_density`/`allocation_pressure` fields, and
     `-mprefer-vector-width=256/512` are re-keyed onto a new `vectorization-density-high`
     `topdown_signals` entry. Live-confirmed the same session, though: neither field actually resolved
     to a real value from cfm's own `deep-cpu` profile at the time — a separate, real `deep-cpu.conf`
     gap (its `counters` pass carried `float`/`fault_rate` but with no `--csv`, so `wspy-store` never
     ingested them), not fixed by that pin bump and not this item's own scope. Filed upstream as
     [wspy#274](https://github.com/mvermeulen/wspy/issues/274).
     **Resolved (pin bump past wspy#274/#275/#276, `bc65f57`, 2026-08-19):** wspy#275 gave the
     `counters` pass real `--csv` output, and wspy#276 (a zero-guard fix for a `-nan%` CSV column that
     #275 exposed) let it actually pass `wspy-validate`. `_ARCHETYPE_PASS_NAME["deep-cpu"]` now points
     at `"counters"` instead of `"amdtopdown"` (confirmed live to be the objectively richer pass —
     `confidence=high` vs. `low`, same `resource_dominance` conclusion either way), and
     `vectorization_density`/`allocation_pressure` resolve to real values (`low`/`moderate`/`high`) from
     a real `deep-cpu` trial. See CLAUDE.md's matching trap entry.
  2. **Split "characterization" (shape) from "calibration" (the actual number) — leverage the external
     reference-matrix corpus (`mvermeulen.org/workload`) for the former, always measure the latter
     locally.** Confirmed live (2026-08-09) exactly where deep-cpu's cost actually goes, from a real
     706.stockfish_r trial's own manifest timestamps: of ~2.6 hours total, the `counters` pass alone
     (deep-cpu's `--passes=...` sweep, multiplexed into 8 separate sub-executions to fit 10 requested
     counter groups into 6 hardware PMU slots, each sub-execution its own full `--iterations 3` SPEC
     run) is ~121 of those ~155 minutes — **~78% of the cost, for exactly the topdown/cache/float data
     that makes up "shape."** That's precisely what `706.stockfish_r`'s own reference-matrix page
     already publishes (backend-bound 41%, frontend 29.7%, AVX-128-dominant/negligible-AVX-512 vector
     density) — reusing it instead of re-deriving it locally removes the dominant cost, provided shape
     is stable enough across similar machines to trust (this project's own working assumption, not
     proven universally).
     - **Characterization** (topdown shape, FP/vector density, ...): sourced from
       `wspy-testpoint aggregate --suite --benchmark --machine --db <db> [--report-root <path>] --csv`
       — an **already-existing, already-working stable CLI** in the currently-pinned wspy build
       (confirmed live), so this is a `WspyInstrumentation`-style shell-out addition, not new wspy
       feature work or a departure from cfm's "only integrate via stable wspy CLIs, never import wspy's
       internal Python" posture. When no reference-matrix entry exists yet for a (benchmark, base-
       config) combination, fall back to *one* local `deep-cpu` run (shape needs one measurement, not a
       3-rep CI) at **`--iterations 1`, not 3** — the user's own `wspy-publish` contribution runs
       already use `--iterations 1` throughout, since the real repetition/robustness for
       *characterization* purposes comes from `deep-cpu`'s own ~8-way pass-level multiplexing, not from
       stacking SPEC's own iteration count on top of it (confirmed with the user 2026-08-10; M1's
       current `run_baseline()`/confirmation code defaults to `iterations=3` even under `deep-cpu`,
       which this corrects for the characterization path specifically — a further ~3x reduction on top
       of item 2's own headline saving, e.g. the `counters` pass alone drops from ~121 min to ~40 min).
       **Contribute the result back** via `wspy-publish`, following the corpus's own existing
       contribution conventions exactly (a real machine slug per `doc/REPORT_HIERARCHY.md`, the
       architecture-appropriate standard profile — e.g. `zen4plus-deep` for a Zen4/5 AMD host, not a
       blind `deep-cpu` — and now `--iterations 1` too, matching how every other real contribution to
       this corpus is collected, not a one-off oddball). This is a rare, one-time-per-(benchmark,
       config) cost, not a per-trial one.
     - **Calibration** (the actual ratio, on *this* host, under *this* flag set): always measured
       locally — cross-machine numbers are never substituted for it (SOC/frequency/config differences
       mean they're not assumed comparable) — but using the `quick` profile (already Phase 3
       screening's own profile: ipc + system metrics, cheap, and specifically well-suited to a single
       run — confirmed with the user) instead of `deep-cpu`, since shape no longer needs to come from
       this measurement at all. Every *routine* calibration run (baseline reps, confirmation/combination
       checks) stays local-only, never published — only the rare characterization fallback above is a
       publishing event.
     Net effect: baseline (3 reps) drops from ~7.8 hours to roughly 3× `quick`'s own cost (tens of
     minutes, not hours); a Phase 4/5 candidate's confirmation drops the same way. §15 records the
     non-comparability decision explicitly.
     **Done, minimal scope** (`feature/characterization-calibration-split`, 2026-08-19):
     `orchestrator.py`'s `run_baseline()` now spends exactly one `deep-cpu --iterations 1`
     characterization trial (`_characterize_baseline()`) plus `CONFIRMATION_REPETITIONS` `quick`-profile
     calibration trials (`CALIBRATION_PROFILE`/`CALIBRATION_ITERATIONS`, also `--iterations 1` — the
     user confirmed extending the fallback's own `--iterations 1` reasoning to *routine* calibration
     reps too, not just the rare fallback case, since `CONFIRMATION_REPETITIONS`'s own cross-trial CI is
     what supplies the robustness now); `_confirm_flagset()` (shared by Phase 4/5) does the same. The
     characterization trial's ratio is recorded as a real trial row but excluded from the CI sample, so
     a deep-cpu-profile measurement never mixes with quick-profile ones in one statistic.
     **Was deliberately not implemented at first** (2026-08-19): `wspy-testpoint`'s own CLI subcommands
     (`characterize`/`aggregate`/`render`) all turned out to require *this* host's own `--machine`
     slug/local `runs.json`/store presence to exist before they'd even attempt the WordPress-recovery
     half — a real structural gate, not a config gap, so "already-existing, already-working stable CLI"
     had undersold the real integration cost.
     **Done** (`feature/reference-matrix-characterization`, 2026-08-20), a different shape than
     originally planned: `cfm/reference_matrix.py` talks to `mvermeulen.org/workload` directly rather
     than through `wspy-testpoint`, sidestepping that gate entirely — confirmed live that the site's
     WordPress REST API serves published-page content (including full-depth `counters.txt` `<pre>`
     blocks) to fully anonymous, unauthenticated GET requests, so **no `wp_cfg`/Application Password is
     needed on the mining host at all** (a hard requirement from the user going in: a mining host must
     never need to be able to log in anywhere). `_characterize_baseline()` tries
     `reference_matrix.fetch_shape()` first, falling back to the local `deep-cpu` trial only when no
     matching published entry exists — exactly the drop-in-replacement seam that function was always
     kept isolated for. Deliberately reuses `vendor/wspy`'s own `web/counter_text.py` directly (a
     pinned-submodule Python import, not a CLI shell-out) for the actual `counters.txt`-block parsing —
     a narrow, confirmed-with-the-user exception to cfm's usual "stable CLI only" posture, since
     reimplementing ~370 lines of already-debugged parsing logic was judged the worse trade; the only
     wspy CLI actually shelled out to is `wspy-archetype --run-guest` (real, stable, pre-existing).
     Verified end to end against real data, same day: `resource_dominance` recovers correctly
     (`memory-bound`, agreeing with this host's own earlier local characterization of
     `706.stockfish_r`) from a completely different real machine (`amd-370-64gb`) with zero local setup
     on this host at all. `vectorization_density`/`allocation_pressure` initially came back `unknown`
     from this path — `counter_text.py`'s WordPress-recovery parsing wasn't yet name-aligned for
     `float_pct`/`fault_rate` the way it was for the topdown axes; filed upstream as
     [wspy#278](https://github.com/mvermeulen/wspy/issues/278), not a cfm-side bug, and degraded safely
     regardless (`_filter_implausible_candidates()` never excludes on unknown data). **Resolved same
     day**: wspy#278 closed (#279/#280), pin bumped past it — live-verified `fetch_shape()` now recovers
     real `vectorization_density="moderate"`/`allocation_pressure="high"`, exactly matching this host's
     own local `deep-cpu` characterization of the same benchmark (independent confirmation the whole
     recovery chain is correct, not just internally consistent).
  3. **Adaptive trial-count strategy, biased toward cheap rejection over expensive precision.**
     (Two baseline repetitions from this same live run measured 105.03 and 127.65 — a ~21% spread —
     but this machine was *not* under exclusive use for that window per CLAUDE.md's own rule, so it's
     confounded, not a clean measurement of intrinsic run-to-run noise; noted for completeness, not
     cited as evidence below.) Per the user's own framing (2026-08-10): the first cut is about
     *direction* ("will this flag significantly improve peak performance or not?"), and the
     risk of a false accept (noise misread as a real win, permanently polluting the peak config and the
     cross-benchmark `knowledge` table for a flag whose category isn't even mechanically relevant to
     this workload — e.g. an FP/vector-tuning flag being "confirmed" as helpful on a workload with
     near-zero measured FP density) is worse than a false reject (missing a small real win). Concretely:
     - Phase 3 screening (unchanged, already 1 `quick`-profile run) plus Phase 2 candidate generation
       itself de-prioritizing/excluding a flag category whose relevant signal is essentially absent in
       the workload's own characterized shape (item 1's new signature fields) is the *first*, cheapest
       line of defense — better to never spend a trial on a mechanically-implausible flag than to
       correctly reject it later at real cost.
     - Phase 4/5 confirmation uses a small, fixed number of `quick`-profile reps (not `deep-cpu`'s 3)
       and an **asymmetric accept bar**: require a clearly large, unambiguous improvement to accept
       (statistical *and* practical significance — non-overlapping CI is necessary but not sufficient;
       a technically-non-overlapping but small delta, the "is this 0.8% up or 0.8% down" case, defaults
       to **reject**, not to spending more reps trying to resolve it). No further escalation attempted
       for an individual flag that misses this bar — deliberately not symmetric with the accept path.
     - Combining several individually-modest flags is already Phase 5's job (greedy combination already
       re-measures the *cumulative* set's own effect, judged against the same bar, rather than needing
       each increment individually resolved to high precision) — this is the answer to "what if several
       ~0.5% effects together are real," not a separate mechanism.
     - A flag-category-vs-shape mismatch tightening the accept bar further (not just Phase 2 filtering)
       is a real, sound refinement (bigger prior against an implausible category needs more evidence to
       overcome) but explicitly deferred past this first cut, per the user's own stated preference for
       starting simple.
     The reference matrix's own historical spread (`stddev`/`cv_percent` across its many prior
     repetitions) is a real, data-backed noise-floor estimate for calibrating "clearly large" above, once
     available for a given benchmark — a fixed conservative fallback threshold otherwise. Phase 1
     (baseline) still gets 3 reps regardless (it's the yardstick everything else compares against, not a
     flag being screened) — now at `quick`'s cost, not `deep-cpu`'s.
     **Done** (`feature/adaptive-accept-bar`, 2026-08-19): `orchestrator.py`'s `generate_candidates()`
     now runs `_filter_implausible_candidates()` (new) over item 2's baseline shape fields
     (`resource_dominance`/`vectorization_density`) — a candidate is excluded only when *every one* of
     its `topdown_signals` is confidently contradicted (never on `None`/`"unknown"` — absence of
     information never excludes), keyed off the seed catalog's real vocabulary
     (`frontend-bound`/`speculation-bound`/`compute-bound`/`backend-bound` against `resource_dominance`
     directly, `memory-bound-corroborated` against `resource_dominance == "memory-bound"`,
     `vectorization-density-high` against `vectorization_density == "low"`;
     `retiring-high-narrow-margin` is never excluded on this signal, per this table's own "low priority,
     not exclude" framing — a real verdict on it needs a "margin" field this doesn't have, left to M2's
     ranking pass). `_confirm_flagset()`'s accept condition (shared Phase 4/5) is now `non_overlapping(...)
     and delta_pct >= MIN_PRACTICAL_SIGNIFICANCE_PCT` (a new constant, `1.0` — the documented fixed
     fallback, since the reference-matrix stddev/cv% source isn't wired in under item 2's shipped scope),
     subsuming the old `ci.mean > compare_ci.mean` check. No escalation path added for a rejected
     candidate, matching this item's deliberately asymmetric design.
- **M3 — local LLM integration**, default Ollama (§9 all four jobs, §15) plus the Report agent's
  narrative section. The LLM's structured context for jobs 1/2 (§9) includes whatever deterministic
  signature fields M2.5 adds (FP density, page-fault rate, ...) as pre-classified labels, not raw
  counters for the model to threshold itself — the same "generated GCC-optimization guide" content a
  document like a hand-written counter-to-flag mapping PDF provides belongs *upstream*, mined into
  M2.5's deterministic rule table, not handed to the LLM as free-form context to reason over raw
  numbers with (principle 1's whole reason for existing: a small local model doing open-ended
  quantitative reasoning reliably is the risk that principle guards against). The LLM's own narrative
  job can still *reference* a pre-classified signal ("this workload showed elevated FP density") as
  color once it's a real, computed field — it just never does the thresholding itself.
- **M4 — cross-benchmark knowledge transfer** (§8): implemented 2026-08-23. The write side
  (`orchestrator._confirm_flagset()`'s own `upsert_knowledge()` calls) has existed since M1; this
  milestone builds the read side. `cfm/agents/knowledge_agent.py`'s `known_flags_for_cluster()` queries
  `cfm.db`'s own `knowledge` table by `cluster_key` (`BaselineResult.resource_dominance` itself, already
  a consistent string vocabulary shared across every benchmark's own characterization since M1/M2.5 --
  no separate `wspy-archetype --nearest`/`--kmeans` discovery step needed, since the "which benchmarks
  does this one resemble" question §8 point 1 originally posed is already answered for free by the
  cluster key every benchmark already computes). `cfm/orchestrator.py`'s
  `split_candidates_by_known_prior()` partitions Phase 2's candidate list into flags with a real
  *accepted* prior in this cluster (fast-tracked straight to Phase 4 via `confirm_known_candidates()`,
  skipping Phase 3's screening trial entirely -- "already been screened once, elsewhere," §8 point 3) and
  everything else (a rejected prior, or no prior at all -- unchanged, still goes through the normal
  screen-then-confirm flow). `cli.py`'s `mine` command prints an `"info: known prior for ..."` line per
  known flag either way, and the summary JSON's own `candidates_fast_tracked_from_prior_knowledge` field
  makes the transfer directly visible in a run's own output -- satisfying this milestone's own stated
  bar ("confirm its starting hypothesis queue is visibly informed by the first benchmark's results")
  concretely rather than just in principle. A fast-tracked flag still gets a full, real confirmation-
  grade trial against *this* benchmark's own baseline before anything is accepted -- a cross-benchmark
  prior changes which candidates get tried and in what order, never the correctness bar itself (§15's
  "external data is a hypothesis aid, never a substitute measurement," the same posture already applied
  to the reference-matrix corpus). Verified against the mocked-backend tier
  (`tests/test_agents_knowledge_agent.py`, `tests/test_orchestrator.py`'s split/confirm-known cases,
  `tests/test_cli.py`'s wiring cases), then confirmed for real end to end (2026-08-24): a re-mined
  `782.lbm_r` run fast-tracked `-march=native` straight to Phase 4 on `706.stockfish_r`'s real +48.75%
  prior (mechanically proven, not just logged -- its trials have no preceding screening trial, unlike
  every normally-screened candidate), then correctly *rejected* it (+1.79%, inside this benchmark's own
  CI) -- a real, honest result showing the mechanism promotes what's worth trying first without assuming
  a prior's own magnitude transfers unchanged. The `knowledge` table's own running mean for
  `-march=native` updated from `+48.82%` to `+25.31%` accordingly. See
  `doc/mining_results.782.lbm_r.2026-08-24.md` for the full write-up.
- **M5 — expand the modularity seams** (§12): a second compiler or workload backend, proving the
  interfaces actually held.
- **M6 — uniform base-tuning search** (deferred per §15's peak-only decision): once enough peak-mining
  history exists across a benchmark cluster, search for one flag set that stays a net win *uniformly*
  across the whole cluster, using `knowledge` grouped by `cluster_key` instead of by single benchmark.

## 15. Decisions

The four decisions below were open questions in earlier drafts of this document; resolved before any
code was written so M0-M4 have no ambiguity to stall on.

- **Peak-only for v1** (base-config uniform tuning deferred). v1 mines peak (per-benchmark) flags only —
  the more tractable target, and the direct match for the prompt's "find peak compiler options." A
  uniform-across-a-cluster base-tuning search is real future work (**M6**, added to §14), reusing the
  same `knowledge` table grouped by cluster instead of by single benchmark, once enough peak-mining
  history exists to make that search worthwhile.
- **PGO training input: SPEC's own reference/train input, when the benchmark ships one.** Phase 6's
  `-fprofile-generate` → `-fprofile-use` sub-flow uses the benchmark's own SPEC-provided train workload
  as the training run by default (`config/gcc_flag_catalog.seed.json`'s `-fprofile-generate`/
  `-fprofile-use` entries already carry this note). For a benchmark with no distinct train input, the
  Compiler Knowledge agent marks that PGO trial `needs_validation` with an explicit
  representativeness caveat in `hypotheses.rationale`, rather than silently substituting a held-out
  slice of the reference workload — a PGO win recorded without that caveat should be trusted; one
  recorded with it should get a second look before being folded into a peak config.
- **Knowledge staleness: strict scoping.** `knowledge` rows are scoped by `(cluster_key, compiler,
  compiler_version, target_arch, flag)` (already reflected in `schema/cfm_schema.sql`'s `UNIQUE`
  constraint) — a GCC version bump or a move to a different target microarchitecture starts confidence
  accumulation fresh for that combination rather than silently trusting old rows. This is the safer
  default given how flag effects can shift across compiler releases; a loosened, discount-weighted
  cross-version reuse policy is explicitly *not* v1 scope, revisit only if strict scoping turns out to
  make the knowledge base too slow to warm up on a new host/toolchain in practice.
- **Default local LLM backend: Ollama.** `wspy-analyze` already runs against a local Ollama daemon on
  this host (it's what produced the existing published reports' "AI Narrative Analysis" section), so M3
  targets Ollama first — zero new local-LLM setup, and the narrative-quality bar (§9 job 4) has a
  real, already-published example to match. The `llm/driver.py` interface (§4.5) supports `llama-server`
  identically via the same OpenAI-chat-compatible client; adding it as a second `--llm` target later is
  a config change, not new code, so it's not blocked on this decision — just not the M3 default.
- **Resolved 2026-08-18, superseding the original "computed cfm-side first" decision below: wspy
  promoted `float_pct`/vectorization-density into `wspy-archetype` itself, closing wspy#227
  upstream — no cfm-side threshold work needed.** The decision as originally written (kept for
  history): `float` (FP-op density) wasn't promoted into wspy's own `run_features`/`wspy-archetype`
  axis set at the time, its maintainers deliberately waiting for "real cross-workload validation"
  before picking thresholds, so cfm planned to read the underlying `[raw]` metric directly (a
  `wspy-summary`-style shell-out) and do its own explicitly-uncalibrated threshold classification,
  contributing a real axis upstream later once cfm's own mining produced enough data to ground one —
  tracked as [wspy#227](https://github.com/mvermeulen/wspy/issues/227), filed 2026-08-09. That
  cross-workload validation arrived from the external reference-matrix corpus instead (147 SPEC
  CPU2026 runs, 3 machines), and wspy's own PR #269 added a `vectorization_density` axis
  (low/moderate/high, thresholds fit against that corpus) directly to `wspy-archetype`'s scorecard,
  closing wspy#227 upstream — bumped into cfm via the `1c192a7`→`3839815` pin update. §14's M2.5
  item 1 now reads this axis directly rather than computing it; the same bump's PR #268 similarly
  natively adds `allocation_pressure` (from `fault_rate`).
- **External reference-matrix data is a hypothesis aid, never a substitute measurement.** SOC/frequency/
  configuration differences across the machines `mvermeulen.org/workload`'s corpus spans mean a cross-
  machine number is *not* assumed comparable to a trial on the actual host being optimized — it
  informs "does this look directionally promising" (candidate ranking) and "how much noise should we
  expect" (adaptive trial-count's stop/escalate decision, M2.5 item 3), never an accept/reject verdict
  by itself. Every accepted result still has to independently clear cfm's own `--action=validate` +
  non-overlapping-CI bar on the host it's actually being mined for, no exceptions — the same posture §11
  already takes toward every other trial, just reaffirmed here since a new external data source is
  exactly the kind of thing that invites a shortcut around it.
- **Reference-matrix access: shell out to `wspy-testpoint aggregate`, not wspy's internal Python.**
  Confirmed live (2026-08-09) that this CLI already exists and works in the currently-pinned wspy build
  — `scripts/publish_reference_matrix.py` (wspy's own repo) already builds the published site from
  exactly this tool's output, so cfm reusing it is asking wspy for data through the same door its own
  publishing pipeline uses, not a new integration surface. `--db <path>` against cfm's own accumulating
  `results/store.db` (zero new dependencies, grows organically as cfm mines more benchmarks) is the
  near-term path; a `vendor/workload`-style pinned clone of the real report-root repository (richer,
  genuine cross-machine data via `--report-root`) is real future work, not needed to start M2.5.
- **A false accept is worse than a false reject (2026-08-10, user decision).** M2.5's adaptive
  trial-count design (§14) is deliberately asymmetric, not a textbook symmetric hypothesis test: a
  flag needs a clearly large, unambiguous improvement to be *accepted* (statistical *and* practical
  significance, not just a non-overlapping CI on a small delta), but any candidate that misses that bar
  is rejected outright, with no extra reps spent trying to rescue an ambiguous result. Rationale: an
  incorrectly-accepted flag doesn't just cost this benchmark's peak config — it pollutes the
  cross-benchmark `knowledge` table (§8) other benchmarks inherit from, and the failure mode is sharpest
  exactly where a flag's catalog category has little mechanical relevance to the workload's own
  characterized shape (an FP/vector-tuning flag "confirmed" on a near-zero-FP-density benchmark, on
  noise alone). A missed small-but-real win is comparatively cheap — recoverable later (a future M2.5
  refinement, or Phase 5's own combination search catching it alongside other flags), an incorrectly
  accepted one is not.
- **PGO mechanism: SPEC's own native `PASS1_OPTIMIZE`/`PASS2_OPTIMIZE`, not a hand-rolled
  generate/run/use flow (2026-08-22).** Confirmed live that `runcpu` already drives the whole
  build-instrumented → train → rebuild-optimized sequence internally, using the benchmark's own
  SPEC-provided train workload automatically, given just these two config lines (Docs/config.txt sec.
  VI) — asking cfm to re-implement that sequencing itself (a separate instrumented build, its own
  `wspy-run` invocation against the train input, manual profile-directory bookkeeping between the two
  compiles) would be real, unnecessary work duplicating something SPEC's own tooling already does
  correctly. §6 Phase 6 and `cfm/workloads/spec_cpu2026.py` implement this.
  - **Concurrency (`-fprofile-update`): confirmed live, not assumed, that SPEC's own FDO training step
    is not a concurrency hazard as currently used here.** The natural worry — SPECrate's own methodology
    runs many parallel copies of the benchmark binary for the real timed measurement, and GCC's default
    `-fprofile-update=single` corrupts profile counters under concurrent writers to the same `.gcda`
    file — turned out not to apply to the *training* step specifically: a real build against
    `782.lbm_r` on this host logged `"Copy 0 of 782.lbm_r (peak train) run 1 finished"` — a single
    serial training copy, never fanned out across `copies` regardless of how many copies the real
    reference-size run uses (Docs/config.txt sec. VIII.C's own worked FDO example shows the identical
    `"Copy 0"` shape). `-fprofile-update=atomic` is applied to the pass-1 (instrumented) build anyway,
    as cheap, correctness-preserving insurance rather than a fix for an observed corruption — this
    project has already been burned once by trusting an assumption about SPEC's own mechanics without
    directly verifying it (CLAUDE.md's basepeak trap), and the insurance costs nothing measurable here
    while covering a real future risk this hasn't been checked against: `parallel_test` being turned on
    (SPEC's own switch for running multiple simultaneous test/train verification copies, off by default
    for cfm's `--noreportable` invocations but a real config knob nonetheless), or a benchmark spawning
    worker threads during training independently of the `OMP_NUM_THREADS=1` SPEC forces automatically
    for a SPECrate run's OpenMP parallelism specifically (not necessarily every thread a benchmark might
    spawn on its own).
  - **`-fprofile-correction` is applied to the pass-2 (optimized) build unconditionally too** — GCC's
    own documentation describes profile-count inconsistencies (whenever the profiled run's control flow
    can differ even slightly from what pass 1 recorded) as a real, common cause of a hard pass-2 build
    failure, not a hypothetical edge case worth skipping.
  - **Catalog wiring**: `-fprofile-generate`/`-fprofile-use` are excluded from
    `compilers/gcc.py`'s ordinary per-flag candidate list (`category == "pgo"`) — Phase 6's PGO trial is
    its own dedicated two-pass flow, never sourced from the same per-flag loop Phase 2/3 use for every
    other candidate, since testing either flag alone against a single OPTIMIZE line is meaningless (the
    now-retracted `doc/mining_results.714.cpython_r.2026-08-21.md` is a live illustration of exactly
    this mistake, made before this decision existed).
- **Microarch multiplier: only map what wspy's own detection can distinguish *and* what this project can
  verify — never guess (2026-08-23).** §6 Phase 6 calls for reusing wspy's own `cpu_info.c` vendor/model
  detection rather than an open-ended `-march` search; reading `vendor/wspy/cpu_info.h`'s own core-vendor
  enum directly (before writing any mapping code, not after) showed it only distinguishes AMD Zen cores
  by generation for `CORE_AMD_ZEN5`/`CORE_AMD_ZEN5C` specifically — the bare `CORE_AMD_ZEN` bucket
  (printed as plain `"Zen"`) covers Zen1 through Zen4 with no finer distinction at all, and Intel's own
  buckets (`CORE_INTEL_ATOM`/`CORE_INTEL_CORE`) carry no generation information either. Mapping the
  ambiguous `"Zen"` label to any specific `-march=znverN` would be a real, unverified guess — exactly the
  class of mistake this project's own history (the basepeak trap, the isolated-candidate-flags bug) has
  already been burned by more than once. `cfm/hostinfo.py`'s `_LABEL_TO_MARCH` therefore only maps
  `Zen5`/`Zen5c` → `znver5` — the one case both confidently detectable by wspy *and* verifiable on this
  project's own real AMD Zen5 mining host — and degrades to "nothing detected" (a clean skip, never a
  trial) for every other label, including the ambiguous bare `Zen` bucket, an unbuilt/missing `cpu_info`,
  a non-zero exit, or a genuinely mixed/hybrid host where the available cores disagree with each other.
  A narrower real feature now than a broader guessed one — extending the mapping to more vendors/
  generations is real future work, gated on having an actual host to verify each new entry against, not
  on writing more mapping-table rows blind.

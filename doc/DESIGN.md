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
  `wspy-archetype`'s `resource_dominance` scoring reads — confirmed live to be `amdtopdown`, not the
  `counters` pass wspy's own docs might suggest at first read (CLAUDE.md's "wspy dependency" traps log
  has the full story, including the wrong initial guess). Single-pass profiles (`quick`) and the
  `deep-cpu` multi-pass profile both work end to end; any other multi-pass profile
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
| `memory-bound`, `memory_attribution=corroborated`, cache/TLB signal | `-fprefetch-loop-arrays` + `--param prefetch-latency=N`, vector-width tuning (`-mprefer-vector-width=256/512`), huge pages as a *system-level* companion action (flagged, not a compiler flag, but recorded alongside since it interacts with the same signal) |
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
- **Serial execution**: one trial's build+run+measure at a time, via `wspy-queue`, since perf counters
  and SPEC's own run assumptions both want exclusive machine use — this project adds no new
  concurrency-control code.
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
    agents/spec_agent.py          [M0] run_one_trial(): the M0 pipeline glue
    cli.py                        [M0] `cfm measure <benchmark> --flags "..."` --
                                   NOT `cfm mine`; the search-driving orchestrator
                                   command doesn't exist until M1
    orchestrator.py                [M1] phase state machine (§5-6) -- pending, not yet built
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
- **M1 — rule-based screening/confirmation loop (§6 Phases 1-5), no LLM.** Static catalog priors only;
  first fully-automated "peak beats base" result, backed by wspy-summary's own statistical bar.
- **M2 — signature-aware candidate filtering.** Wire in `wspy-archetype`'s `resource_dominance`/
  `memory_attribution` to drive Compiler Knowledge agent candidate selection (the table in §4.3),
  instead of trying the whole catalog uniformly.
- **M3 — local LLM integration**, default Ollama (§9 all four jobs, §15) plus the Report agent's
  narrative section.
- **M4 — cross-benchmark knowledge transfer** (§8): mine a second, differently-shaped benchmark and
  confirm its starting hypothesis queue is visibly informed by the first benchmark's results.
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

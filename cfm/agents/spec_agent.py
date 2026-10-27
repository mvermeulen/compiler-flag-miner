"""SPEC Runner agent, M0 scope -- doc/DESIGN.md sec. 14 M0: "given one fixed,
hand-chosen flag set, generate a real peak config, build, run under wspy-run, and
get one validated, wspy-measured ratio." ``run_one_trial`` is that pipeline end to
end, with every step's outcome persisted to cfm.db regardless of result -- a
build/validate failure is still a real trial record (doc/DESIGN.md sec. 6 Phase 4's
"a documented negative result is exactly the kind of learning that should
transfer"), never silently dropped.

Of the other named agents in doc/DESIGN.md sec. 13's proposed layout,
``knowledge_agent`` now exists (M4, cross-benchmark knowledge transfer --
``agents/knowledge_agent.py``); ``hypothesis_agent``/``report_agent`` don't yet --
they're M3 scope, where there's an actual LLM driver and report renderer for them
to operate against.
"""

from __future__ import annotations

import re
import statistics
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

from .. import db
from ..bandwidth import BandwidthGate
from ..config import CfmConfig
from ..hostinfo import read_package_power_watts
from ..instrumentation.base import InstrumentationBackend
from ..instrumentation.wspy import WspyInstrumentation
from ..workloads.base import WorkloadBackend
from ..workloads import workload_for


# Package power is sampled this often while the timed run is going (2026-10-26).
# The single post-run reading it replaced came after wspy's own post-processing,
# when the load had already ended.
POWER_SAMPLE_INTERVAL_S = 2.0


class _PowerSampler:
    """Reads ``power_reader`` every ``POWER_SAMPLE_INTERVAL_S`` on a background
    thread between ``start()`` and ``stop()``. ``stop()`` returns the median of
    the readings and how many there were. The median, because the window also
    covers wspy's few seconds of post-processing after the benchmark exits."""

    def __init__(self, power_reader: Callable[[], Optional[float]], interval: float = POWER_SAMPLE_INTERVAL_S):
        self.power_reader = power_reader
        self.interval = interval
        self.samples: list[float] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            try:
                value = self.power_reader()
            except Exception:
                value = None
            if value is not None:
                self.samples.append(value)

    def start(self) -> "_PowerSampler":
        self._thread.start()
        return self

    def stop(self) -> tuple[Optional[float], int]:
        self._stop.set()
        self._thread.join()
        return (statistics.median(self.samples) if self.samples else None), len(self.samples)


def new_run_id() -> str:
    # Sortable-by-time like wspy-run's own default run-id shape, without needing to
    # be byte-identical to it -- we always pass --run-id explicitly.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


# GCC rewrites these before recording them into .GCC.command.line (-march=native/
# -mtune=native expand into dozens of concrete -m*/--param= flags, e.g.
# "-march=znver5 -mmmx -mpopcnt ..." -- confirmed live, 2026-08-21, no literal
# "native" survives anywhere in the recording) -- a literal substring check
# against these two specifically would always report "missing" even on a
# perfectly correct build, so audit_compiled_flags()'s check skips them rather
# than raising a false alarm.
#
# -flto joins this set for a different reason, confirmed live 2026-08-22
# against a real accepted 714.cpython_r PGO+LTO trial: on an LTO build,
# -frecord-gcc-switches's own recorded ".GCC.command.line" section reflects
# GCC's *internal LTRANS re-invocation* of itself at final-link time ("GNU
# GIMPLE 15.2.0 ... -fltrans"), not the original per-translation-unit -flto
# flag -- so a literal "-flto" substring check always reports "missing" on an
# LTO build too, even though LTO genuinely ran (independently confirmed via
# the real SPEC log's own "lto-wrapper: ... using serial compilation of 51
# LTRANS jobs" line, and via -flto appearing on every real per-TU compile
# command in that same log -- just not in the final linked binary's own
# recorded-switches section). Caught by this exact audit output on a real,
# otherwise-correct accepted trial -- see CLAUDE.md's Non-obvious traps log.
_AUDIT_UNVERIFIABLE_LITERAL_FLAGS = frozenset({"-march=native", "-mtune=native", "-flto", "-no-pie"})


def _audit_token_recorded(token: str, audit_dump: str) -> bool:
    # GCC records a preprocessor -D/-U with a space ("-U _FORTIFY_SOURCE").
    spaced = re.sub(r"^-([DU])(?=\S)", r"-\1 ", token)
    return token in audit_dump or spaced in audit_dump


# Confirmed live, 2026-08-22 (CLAUDE.md's Non-obvious traps log): a real GCC
# ".GCC.command.line" dump for a genuinely-optimized build always has exactly
# one of these. Its complete absence is a strong, cheap, generic signal that
# something upstream handed this trial a flags list with no -O level at all --
# exactly the shape of the screen_candidates()/confirm_candidates() bug this
# same investigation found (candidate flags tested in total isolation, never
# combined with the baseline's own -O3). This check doesn't know or care
# *why* -O is missing -- it would catch a similar mistake in a future caller
# just as well, not just this one.
_OPTIMIZATION_LEVEL_RE = re.compile(r"-O(?:0|1|2|3|s|g|z|fast)\b")


def _summarize_compiled_flags_audit(flags: list[str], audit_dump: str) -> str:
    """Best-effort literal-substring check of each requested flag against
    audit_compiled_flags()'s raw `.GCC.command.line` dump -- confirms what SPEC
    actually compiled with, independent of runcpu's own "Build successes"
    report (CLAUDE.md's Non-obvious traps log, 2026-08-21 basepeak entry, on
    why that report alone isn't sufficient). Not a hard pass/fail signal: every
    catalog flag *other* than the three in _AUDIT_UNVERIFIABLE_LITERAL_FLAGS
    (-fprofile-use/-generate, -fno-stack-protector, -fcf-protection=none,
    -mprefer-vector-width=N, ...) is recorded by GCC verbatim, so a real
    substring match is meaningful for them.

    Also flags -- loudly, unconditionally -- if no `-O` optimization level
    shows up in the compiled binary at all, regardless of whether one was
    expected in `flags`. This is deliberately *not* gated on `flags` itself
    containing an `-O` entry: the whole point is to catch a case where the
    caller's own `flags` list was already wrong (missing the baseline's own
    `-O3`) before anyone has to notice by manually diffing two trials' audit
    rows against each other, which is what actually happened the first time
    (2026-08-22).
    """
    found, missing, skipped = [], [], []
    for flag in flags:
        # A catalog entry can be several tokens ("-fno-pie -no-pie"); it counts
        # as compiled in when every checkable token is.
        checkable = [t for t in flag.split() if t not in _AUDIT_UNVERIFIABLE_LITERAL_FLAGS]
        if not checkable:
            skipped.append(flag)
        elif all(_audit_token_recorded(t, audit_dump) for t in checkable):
            found.append(flag)
        else:
            missing.append(flag)
    parts = []
    if found:
        parts.append(f"confirmed compiled in: {found}")
    if missing:
        parts.append(f"NOT FOUND in compiled binary (see CLAUDE.md's basepeak trap): {missing}")
    if skipped:
        parts.append(f"not independently checkable (GCC expands these before recording): {skipped}")
    if not _OPTIMIZATION_LEVEL_RE.search(audit_dump):
        parts.append(
            "⚠ WARNING: no -O optimization level found in the compiled binary at all -- "
            "this trial's build very likely got no real optimization (see CLAUDE.md's Non-obvious "
            "traps log, 2026-08-22 entry on screen_candidates()/confirm_candidates() once testing a "
            "candidate flag in total isolation from the baseline's own -O3)"
        )
    return "compiled-flags audit -- " + "; ".join(parts)


def _record_compiled_flags_audit(conn, workload, benchmark: str, tune: str, trial_id: int, flags: list[str]) -> None:
    """Independent audit of what SPEC actually compiled with, not just what
    runcpu's own "Build successes" report claims -- see
    workloads/spec_cpu2026.py's audit_compiled_flags() docstring and CLAUDE.md's
    Non-obvious traps log (2026-08-21 basepeak entry) for why that report alone
    wasn't enough once already. getattr-guarded since fake WorkloadBackends in
    tests don't implement this (optional, degrade-gracefully signal, never
    load-bearing for the trial's own build_status). Also recorded for a trial
    skipped as unchanged: a stale binary that silently ignored the requested
    flags would look exactly like "no code change", and this is what tells the
    two apart.
    """
    audit_fn = getattr(workload, "audit_compiled_flags", None)
    if audit_fn is None:
        return
    audit_dump = audit_fn(benchmark, tune)
    if audit_dump is not None:
        db.record_hypothesis(
            # proposed_by="rule": schema/cfm_schema.sql's hypotheses.proposed_by
            # CHECK constraint only allows ('rule','analogical','llm') -- this is
            # a deterministic, rule-based check like every other hypothesis this
            # module records, not a fundamentally new category; the "compiled-flags
            # audit --" rationale prefix is what distinguishes it at a glance.
            conn, trial_id=trial_id, proposed_by="rule",
            rationale=_summarize_compiled_flags_audit(flags, audit_dump),
        )


# wspy's system.c prints "cpu temp             XX.X C" (SYSTEM_TEMP, on by
# default in system_mask, present whenever a profile passes --system -- every
# "quick"-profile trial already does, cfm/orchestrator.py's CALIBRATION_PROFILE/
# SCREENING_PROFILE both being "quick"). This data has been sitting in every
# trial's own RunSignature.raw_output all along -- not a new collection
# mechanism, just the first time anything parses it out. Motivated by a real
# 2026-08-21 near-incident (CLAUDE.md's Non-obvious traps log): an ad hoc
# verification script that bypassed cfm/lock.py briefly ran two concurrent
# SPECrate builds and got the host to the edge of OOM again -- a per-trial
# thermal record, squirreled away cheaply, is exactly the kind of data that
# would help debug a "why did this run's later trials look different" question
# after the fact, without needing to actively gate/wait on it mid-run (which
# risks adding untested blocking logic to an unattended overnight run before a
# sensible threshold/timeout exists to tune it against).
_CPU_TEMP_RE = re.compile(r"cpu temp\s+([\d.]+)\s*C", re.IGNORECASE)


def _extract_cpu_temp_c(raw_output: str) -> Optional[float]:
    match = _CPU_TEMP_RE.search(raw_output)
    return float(match.group(1)) if match else None


# One gate per output root for the life of the process, so the session's best
# bandwidth reading carries across every trial of a `cfm mine` run.
_SESSION_GATES: dict = {}


def _session_gate(cfg: CfmConfig) -> BandwidthGate:
    key = cfg.output_root.resolve()
    if key not in _SESSION_GATES:
        _SESSION_GATES[key] = BandwidthGate(cfg.output_root / ".cache")
    return _SESSION_GATES[key]


def run_one_trial(
    cfg: CfmConfig,
    *,
    benchmark: str,
    flags: list[str],
    tune: str = "peak",
    iterations: int = 3,
    phase: str = "screening",
    profile: Optional[str] = None,
    experiment_id: Optional[int] = None,
    parent_trial_id: Optional[int] = None,
    workload: Optional[WorkloadBackend] = None,
    instrumentation: Optional[InstrumentationBackend] = None,
    power_reader: Optional[Callable[[], Optional[float]]] = None,
    bandwidth_gate: Optional[BandwidthGate] = None,
    skip_if_same_code_as: Optional[list[str]] = None,
) -> dict:
    """``workload``/``instrumentation`` are injectable (defaulting to the real
    backend ``workload_for()`` picks for ``benchmark`` -- SPEC CPU2026, or Phoronix
    for a ``pts/`` name -- and ``WspyInstrumentation``, both built from ``cfg``) so
    ``cfm/orchestrator.py``'s tests can pass in fakes conforming to
    ``workloads.base.WorkloadBackend``/``instrumentation.base.InstrumentationBackend``
    and exercise the orchestrator's phase logic with no real SPEC/wspy calls --
    ``cfm measure`` (``cli.py``) and every M0 caller keep working unchanged, since
    both default to ``None``. ``profile`` overrides ``cfg.wspy_profile`` for this
    one call -- the orchestrator needs a different wspy profile per phase (``quick``
    for screening and calibration, ``deep-cpu`` for baseline's one-off
    characterization rep, doc/DESIGN.md sec. 6 and sec. 14 M2.5 item 2),
    which a single fixed ``cfg.wspy_profile`` can't express across calls sharing one
    ``CfmConfig``. ``parent_trial_id`` is passed straight through to
    ``db.record_trial()`` -- doc/DESIGN.md sec. 6 Phase 5's greedy-combination
    lineage (``trials.parent_trial_id``), unused before M1's confirmation stage.
    ``power_reader`` is injectable too, same reasoning as ``workload``/
    ``instrumentation`` -- unlike those two, ``read_package_power_watts()``
    reads *this actual host's* live sysfs state directly, regardless of which
    workload/instrumentation backend is in play, so a test running on a real
    machine with a real `amdgpu` hwmon (e.g. this project's own mining host)
    would otherwise get a real, non-deterministic hypothesis row even with
    fully faked workload/instrumentation backends -- confirmed live, 2026-08-24
    (a real test failure caught this the same day the feature was added, not
    inspection). Tests pass ``lambda: None`` to suppress it deterministically.
    ``bandwidth_gate`` (cfm/bandwidth.py) runs between the build and the timed
    run, waiting out a throttled memory-bandwidth state; when omitted, the
    process-wide gate is used if ``cfg.bandwidth_gate`` is set, and none otherwise.
    ``skip_if_same_code_as`` names the flagset this trial builds on (the baseline,
    or the running set it adds to). When the built code's fingerprint equals the
    one already recorded for that flagset in this experiment, the flags under
    test changed nothing, so the trial is recorded with no ratio and the timed
    run is skipped; the result dict carries ``unchanged_from_trial_id``. It never
    skips when either fingerprint is unknown.
    """
    workload = workload or workload_for(cfg, benchmark)
    # Looked up per call (not bound as the default) so tests can monkeypatch it.
    power_reader = power_reader or read_package_power_watts
    run_index_path = cfg.output_root / "cpu2026" / "run-index.jsonl"
    instrumentation = instrumentation or WspyInstrumentation(
        cfg.wspy_dir,
        store_db=cfg.output_root / "store.db",
        run_index_path=run_index_path,
    )
    profile = profile or cfg.wspy_profile

    problems = instrumentation.preflight()
    if problems:
        raise RuntimeError("wspy preflight failed:\n  " + "\n  ".join(problems))

    conn = db.connect(cfg.db_path)
    try:
        if experiment_id is None:
            experiment_id = db.create_experiment(
                conn, benchmark=benchmark, hostname=cfg.hostname, compiler="gcc",
            )

        try:
            config_path = workload.generate_config(benchmark, tune, flags)
            optimize_string = " ".join(flags)

            build_result = workload.build(benchmark, tune, config_path)
            if not build_result.ok:
                trial_id = db.record_trial(
                    conn, experiment_id=experiment_id, phase=phase, flags=flags,
                    optimize_string=optimize_string, build_status="build-failed",
                    parent_trial_id=parent_trial_id,
                )
                return {
                    "experiment_id": experiment_id, "trial_id": trial_id,
                    "build_status": "build-failed", "build_output": build_result.raw_output,
                }

            fingerprint_fn = getattr(workload, "code_fingerprint", None)
            code_fingerprint = fingerprint_fn(benchmark, tune) if fingerprint_fn is not None else None
            reference = (
                db.latest_code_fingerprint(conn, experiment_id, skip_if_same_code_as)
                if skip_if_same_code_as is not None and code_fingerprint is not None else None
            )
            if reference is not None and reference[1] == code_fingerprint:
                reference_trial_id = reference[0]
                trial_id = db.record_trial(
                    conn, experiment_id=experiment_id, phase=phase, flags=flags,
                    optimize_string=optimize_string, build_status="ok",
                    parent_trial_id=parent_trial_id, code_fingerprint=code_fingerprint,
                )
                _record_compiled_flags_audit(conn, workload, benchmark, tune, trial_id, flags)
                rationale = (
                    f"no code change: the built executables are identical to trial "
                    f"{reference_trial_id} ({skip_if_same_code_as}), so the timed run was skipped"
                )
                db.record_hypothesis(conn, trial_id=trial_id, proposed_by="rule", rationale=rationale)
                print(f"info: trial {trial_id} {flags}: {rationale}")
                return {
                    "experiment_id": experiment_id, "trial_id": trial_id, "build_status": "ok",
                    "ratio": None, "unchanged_from_trial_id": reference_trial_id,
                }

            gate = bandwidth_gate or (_session_gate(cfg) if cfg.bandwidth_gate else None)
            gate_result = gate.wait() if gate is not None else None

            run_id = new_run_id()
            command = workload.run_command(benchmark, tune, config_path, iterations=iterations)
            sampler = _PowerSampler(power_reader).start()
            try:
                signature = instrumentation.characterize(
                    # A pts/ name's slash would nest wspy's run directory, so wspy
                    # gets the bare test name under the backend's own suite.
                    command=command, suite=getattr(workload, "suite", "cpu2026"),
                    benchmark=benchmark.rsplit("/", 1)[-1], run_id=run_id,
                    profile=profile, output_root=cfg.output_root,
                )
            finally:
                power_median_w, power_samples = sampler.stop()
            run_result = workload.parse_result(benchmark, tune, signature.raw_output)

            build_status = "ok" if run_result.ok else "validate-failed"
            trial_id = db.record_trial(
                conn, experiment_id=experiment_id, phase=phase, flags=flags,
                optimize_string=optimize_string, build_status=build_status,
                wspy_run_ref=signature.wspy_run_ref, ratio=run_result.ratio,
                parent_trial_id=parent_trial_id, code_fingerprint=code_fingerprint,
            )

            _record_compiled_flags_audit(conn, workload, benchmark, tune, trial_id, flags)

            # Per-trial thermal record -- see _extract_cpu_temp_c()'s own
            # comment for why this is worth squirreling away even though
            # nothing here actively gates or waits on it.
            cpu_temp_c = _extract_cpu_temp_c(signature.raw_output)
            if cpu_temp_c is not None:
                db.record_hypothesis(
                    conn, trial_id=trial_id, proposed_by="rule",
                    rationale=f"host cpu_temp at measurement: {cpu_temp_c:.1f} C",
                )

            # Per-trial package-power record -- added 2026-08-24 to test
            # doc/settling_baseline_drift_investigation.2026-08-24.md's
            # hypothesis 2 directly (a STAPM-style sustained power limit
            # easing upward over a run's own real wall-clock minutes), rather
            # than only inferring it from the elapsed-time-vs-cpu_temp_c
            # correlation gap that hypothesis was first raised from. Same
            # "squirrel it away, don't gate on it" posture as cpu_temp_c above
            # -- see read_package_power_watts()'s own docstring.
            if gate_result is not None:
                db.record_hypothesis(
                    conn, trial_id=trial_id, proposed_by="rule", rationale=gate_result.rationale(),
                )

            # SPECspeed thread placement (2026-10-23), getattr-guarded like the audit above.
            placement_fn = getattr(workload, "thread_placement", None)
            placement_note = placement_fn(benchmark)[1] if placement_fn is not None else ""
            if placement_note:
                db.record_hypothesis(
                    conn, trial_id=trial_id, proposed_by="rule", rationale=placement_note,
                )

            # Median of the readings taken during the run; a run shorter than one
            # sampling interval falls back to a single reading after it.
            package_power_w = power_median_w
            power_note = f" (median of {power_samples} samples during the run)"
            if package_power_w is None:
                package_power_w = power_reader()
                power_note = " (one reading after the run)"
            if package_power_w is not None:
                db.record_hypothesis(
                    conn, trial_id=trial_id, proposed_by="rule",
                    rationale=f"host package_power at measurement: {package_power_w:.2f} W{power_note}",
                )

            return {
                "experiment_id": experiment_id, "trial_id": trial_id,
                "build_status": build_status, "wspy_run_ref": signature.wspy_run_ref,
                "wspy_validated": signature.validated, "spec_validated": run_result.validated,
                "resource_dominance": signature.resource_dominance,
                # resource_dominance_pct: how dominant that shape actually is (0-100) --
                # wspy-archetype already computes this (RunSignature has carried it since
                # M1), it just never reached this dict before. Threaded through so
                # BaselineResult can carry it too -- M2's own signature-aware ranking
                # (cfm/compilers/gcc.py) uses it as the "narrow margin" signal doc/DESIGN.md
                # sec. 4.3's table calls for on the retiring-high-narrow-margin row.
                "resource_dominance_pct": signature.resource_dominance_pct,
                "vectorization_density": signature.vectorization_density,
                "allocation_pressure": signature.allocation_pressure,
                "ratio": run_result.ratio,
                "cpu_temp_c": cpu_temp_c,
                "package_power_w": package_power_w,
                "bandwidth_probe_gbps": gate_result.probe_gbps if gate_result else None,
            }
        except Exception:
            # An unhandled exception here (not a build/validate *failure*, which
            # is itself a normal, recorded trial outcome above) means this trial
            # blew up in a way nothing downstream can recover from -- every
            # orchestrator phase (screen/confirm/combine) lets such an exception
            # propagate straight out to `cfm mine`'s CLI handler with no
            # per-candidate catch, so the whole experiment is aborting regardless
            # of which call raised. Mark it `failed` here, at the one place that
            # always knows the experiment_id, rather than leaving the row stuck
            # at `running` forever (CLAUDE.md's Non-obvious traps log,
            # 2026-08-20 entry -- this is exactly the gap that entry flagged).
            db.finish_experiment(conn, experiment_id, status="failed")
            raise
    finally:
        conn.close()

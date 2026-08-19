"""Instrumentation-backend interface -- doc/DESIGN.md sec. 4.2 / sec. 12.

``wspy.py`` is the only implementation today; a ``perf stat``-only fallback for
hosts without a wspy build is the modularity seam this interface defines, not yet
implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RunSignature:
    """The one object every other agent reasons about (doc/DESIGN.md sec. 4.2):
    bundles the wspy run identity, wspy-archetype's classification, and the metric
    table wspy-summary would report for this run.
    """

    wspy_run_ref: str  # 'hostname:run_id'
    validated: bool  # wspy-validate's counter-collection sanity check -- distinct
    # from SPEC's own --action=validate correctness check, which
    # lives on workloads.base.RunResult instead.
    resource_dominance: Optional[str] = None
    resource_dominance_pct: Optional[float] = None
    memory_attribution: Optional[str] = None
    # vectorization_density/allocation_pressure (doc/DESIGN.md sec. 14 M2.5 item 1): native
    # wspy-archetype scorecard axes (wspy PRs #269/#268, closing wspy#227) -- "low"/"moderate"/"high",
    # or "unknown" when the underlying float_pct/fault_rate data wasn't measured for the pass
    # wspy-archetype scored. As of the wspy pin bump that added these (2026-08-18), a real `deep-cpu`
    # run still reports both as "unknown" -- deep-cpu.conf's `counters` pass carries float/fault_rate
    # in its --passes sweep but without --csv (same non-CSV trap as CLAUDE.md's `deep-cpu`/`amdtopdown`
    # entry), so wspy-store never ingests them into run_features regardless of the pass-selection fix;
    # confirmed live, see CLAUDE.md's "Non-obvious traps" (filed upstream as wspy#274). Populated here
    # anyway (not deferred until that gap closes) since any other characterization path -- a future
    # `wspy-testpoint aggregate`
    # reference-matrix read (M2.5 item 2), or a hand-run `wspy --counters=float --csv` probe -- can
    # already produce a real value for the same field.
    vectorization_density: Optional[str] = None
    allocation_pressure: Optional[str] = None
    metrics: dict = field(default_factory=dict)
    raw_output: str = ""


class InstrumentationBackend:
    def characterize(
        self, command: list[str], suite: str, benchmark: str, run_id: str,
        profile: str, output_root,
    ) -> RunSignature:
        """Executes ``command`` under this backend's instrumentation (e.g.
        ``wspy-run <profile> -- <command>``) and returns its signature. This is the
        method that actually launches the measured run -- see
        ``cfm/workloads/base.py``'s ``WorkloadBackend`` docstring for why that
        responsibility lives here rather than on the workload backend.
        """
        raise NotImplementedError

    def check_regression(self, wspy_run_ref: str) -> list[dict]:
        """Optional secondary environment/counter-sanity guardrail for
        doc/DESIGN.md sec. 6 Phase 4's confirmation stage (``wspy.py``'s
        implementation wraps ``wspy-summary --check-regression``) -- never the
        accept/reject decision itself, which is computed directly over
        ``cfm.db``'s own ``trials.ratio`` (``cfm/stats.py``). Defaults to "nothing
        to report" so a backend with no equivalent tool (e.g. a future bare
        ``perf stat`` fallback, sec. 12) doesn't need to implement this at all.
        """
        return []

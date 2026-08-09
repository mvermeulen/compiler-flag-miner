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

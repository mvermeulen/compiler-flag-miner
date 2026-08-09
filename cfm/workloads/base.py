"""Workload-backend interface -- doc/DESIGN.md sec. 4.1 / sec. 12.

One implementation per benchmark suite. ``spec_cpu2026.py`` is the only one that
exists; ``spec_cpu2017.py`` (forking wspy's own already-working
``workload/cpu2017/run_test.sh`` pattern) and ``phoronix.py`` are the modularity
seam this interface defines, not yet implemented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class BuildResult:
    ok: bool
    log_path: Path
    raw_output: str


@dataclass
class RunResult:
    """Result of parsing one measured run's output. ``ok``/``validated`` both refer
    to SPEC's own ``--action=validate`` correctness check (doc/DESIGN.md sec. 11's
    gate) -- distinct from wspy-validate's counter-collection sanity check, which
    lives on ``RunSignature`` (``cfm/instrumentation/base.py``) instead.
    """

    ok: bool
    validated: bool
    ratio: Optional[float]
    seconds: Optional[float]
    status: str  # 'ok' | 'ok-no-rsf' | 'build-failed' | 'validate-failed'
    raw_output: str
    result_files: list[Path] = field(default_factory=list)


class WorkloadBackend:
    """doc/DESIGN.md sec. 4.1 interface. Note on ``run_command`` vs. the design
    doc's originally-sketched ``run(...)`` name: this class never launches the
    measured run itself -- it only builds the argv, which an
    ``InstrumentationBackend`` (``cfm/instrumentation/base.py``) wraps in
    ``wspy-run <profile> -- <command>`` and actually executes, since wrapping the
    measured run in wspy is the whole reason it happens under the instrumentation
    agent's control rather than this one's.
    """

    def generate_config(self, bench: str, tune: str, flags: list[str]) -> Path:
        raise NotImplementedError

    def build(self, bench: str, tune: str, config_path: Path) -> BuildResult:
        raise NotImplementedError

    def run_command(self, bench: str, tune: str, config_path: Path, iterations: int) -> list[str]:
        raise NotImplementedError

    def parse_result(self, bench: str, tune: str, raw_output: str) -> RunResult:
        raise NotImplementedError

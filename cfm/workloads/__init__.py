"""Workload backends. ``workload_for()`` picks one from the benchmark's name."""

from __future__ import annotations

from .base import WorkloadBackend
from .phoronix import PhoronixWorkload, is_phoronix_benchmark
from .spec_cpu2026 import SpecCpu2026Workload


def workload_for(cfg, benchmark: str) -> WorkloadBackend:
    """``pts/<test>-<version>`` -> Phoronix Test Suite, anything else -> SPEC CPU2026."""
    if is_phoronix_benchmark(benchmark):
        return PhoronixWorkload(cfg.pts_home, cfg.output_root)
    return SpecCpu2026Workload(cfg.spec_dir, cfg.spec_config)

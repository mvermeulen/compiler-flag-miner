"""Workload backends. ``workload_for()`` picks one from the benchmark's name."""

from __future__ import annotations

from pathlib import Path

from .base import WorkloadBackend
from .phoronix import PhoronixWorkload, is_phoronix_benchmark
from .spec_cpu2026 import SpecCpu2026Workload

# One PhoronixWorkload per (pts_home, output_root) per process, i.e. per `cfm
# mine`. run_one_trial() asks for a backend on every trial, and the Phoronix
# backend keeps state across trials: which PGO profiles it has trained. A fresh
# instance per trial retrained every PGO rep (crafty re-mine, 2026-10-27).
_phoronix_backends: dict[tuple[Path, Path], PhoronixWorkload] = {}


def workload_for(cfg, benchmark: str) -> WorkloadBackend:
    """``pts/<test>-<version>`` -> Phoronix Test Suite, anything else -> SPEC CPU2026."""
    if is_phoronix_benchmark(benchmark):
        key = (Path(cfg.pts_home).resolve(), Path(cfg.output_root).resolve())
        if key not in _phoronix_backends:
            _phoronix_backends[key] = PhoronixWorkload(cfg.pts_home, cfg.output_root)
        return _phoronix_backends[key]
    return SpecCpu2026Workload(cfg.spec_dir, cfg.spec_config)

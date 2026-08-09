"""Runtime configuration: paths and hostname, env-var-driven.

Same convention wspy's own ``workload/cpu2017/run_test.sh`` uses (``TESTNAME``,
``SPECDIR``, ``SPECCONFIG``, ``WSPY``, ``OUTROOT`` environment variables read with
built-in defaults), namespaced ``CFM_*`` here to avoid colliding with that script's
own variables when both are sourced in the same shell.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else default


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class CfmConfig:
    spec_dir: Path
    spec_config: str
    wspy_dir: Path
    output_root: Path
    db_path: Path
    wspy_profile: str
    hostname: str

    @classmethod
    def from_env(
        cls,
        *,
        spec_dir: Optional[str] = None,
        spec_config: Optional[str] = None,
        wspy_dir: Optional[str] = None,
        output_root: Optional[str] = None,
        db_path: Optional[str] = None,
        wspy_profile: Optional[str] = None,
        hostname: Optional[str] = None,
    ) -> "CfmConfig":
        """Resolve config: explicit keyword argument (e.g. from argparse) wins over
        the environment; the environment wins over the built-in default. Read
        entirely at call time, not import time, so callers (including tests) can
        set environment variables right before calling this and see them take
        effect -- a module-level ``os.environ.get(...)`` default would freeze at
        import time instead and silently ignore a later ``os.environ`` change.
        """
        return cls(
            spec_dir=Path(spec_dir) if spec_dir else _env_path("CFM_SPEC_DIR", Path.home() / "cpu2026"),
            spec_config=spec_config or _env_str("CFM_SPEC_CONFIG", "gcc_O3.cfg"),
            wspy_dir=Path(wspy_dir) if wspy_dir else _env_path("CFM_WSPY_DIR", Path.home() / "source" / "wspy"),
            output_root=Path(output_root) if output_root else _env_path("CFM_OUTPUT_ROOT", Path("results")),
            db_path=Path(db_path) if db_path else _env_path("CFM_DB", Path("cfm.db")),
            wspy_profile=wspy_profile or _env_str("CFM_WSPY_PROFILE", "quick"),
            hostname=hostname or socket.gethostname(),
        )

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

# vendor/wspy is a git submodule (CLAUDE.md's "wspy dependency" section) pinned to a
# specific, tested wspy commit -- the default `wspy_dir`, resolved relative to this
# package's own location (not the caller's cwd) the same way db.py locates
# schema/cfm_schema.sql. CFM_WSPY_DIR still overrides this, e.g. to point at a live
# ~/source/wspy working tree while co-developing a wspy change against cfm before
# it's pinned -- see CLAUDE.md for when that's appropriate vs. bumping the pin.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_VENDORED_WSPY_DIR = _REPO_ROOT / "vendor" / "wspy"


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
    lock_file: Path

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
        lock_file: Optional[str] = None,
    ) -> "CfmConfig":
        """Resolve config: explicit keyword argument (e.g. from argparse) wins over
        the environment; the environment wins over the built-in default. Read
        entirely at call time, not import time, so callers (including tests) can
        set environment variables right before calling this and see them take
        effect -- a module-level ``os.environ.get(...)`` default would freeze at
        import time instead and silently ignore a later ``os.environ`` change.
        """
        resolved_spec_dir = (
            Path(spec_dir) if spec_dir else _env_path("CFM_SPEC_DIR", Path.home() / "cpu2026")
        )
        return cls(
            spec_dir=resolved_spec_dir,
            spec_config=spec_config or _env_str("CFM_SPEC_CONFIG", "gcc_O3.cfg"),
            wspy_dir=Path(wspy_dir) if wspy_dir else _env_path("CFM_WSPY_DIR", _VENDORED_WSPY_DIR),
            output_root=Path(output_root) if output_root else _env_path("CFM_OUTPUT_ROOT", Path("results")),
            db_path=Path(db_path) if db_path else _env_path("CFM_DB", Path("cfm.db")),
            wspy_profile=wspy_profile or _env_str("CFM_WSPY_PROFILE", "quick"),
            hostname=hostname or socket.gethostname(),
            # Host-wide, not repo-relative: the resource this guards (perf counters,
            # SPEC's own run discipline) is the whole host, not this clone -- lives
            # alongside the SPEC install by default so it's shared across clones/
            # worktrees on the same box. See cfm/lock.py.
            lock_file=(
                Path(lock_file) if lock_file
                else _env_path("CFM_LOCK_FILE", resolved_spec_dir / ".cfm-mining.lock")
            ),
        )

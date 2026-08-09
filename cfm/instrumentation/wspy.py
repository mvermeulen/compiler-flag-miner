"""Wraps the wspy CLI surface -- doc/DESIGN.md sec. 4.2. No new instrumentation
logic lives here, only correct sequencing of wspy's own tools:
``wspy-run`` (execute the measured command under instrumentation), ``wspy-store``
(ingest into the normalized store), ``wspy-validate`` (counter-collection sanity),
``wspy-archetype`` (resource_dominance/memory_attribution classification).
"""

from __future__ import annotations

import socket
import subprocess
from pathlib import Path
from typing import Optional

from ..util import parse_kv_lines
from .base import InstrumentationBackend, RunSignature


class WspyInstrumentation(InstrumentationBackend):
    def __init__(self, wspy_dir, store_db, run_index_path, hostname: Optional[str] = None):
        self.wspy_dir = Path(wspy_dir)
        self.wspy_bin = self.wspy_dir / "wspy"
        self.wspy_run_bin = self.wspy_dir / "wspy-run"
        self.wspy_store_bin = self.wspy_dir / "wspy-store"
        self.wspy_validate_bin = self.wspy_dir / "wspy-validate"
        self.wspy_archetype_bin = self.wspy_dir / "wspy-archetype"
        self.store_db = Path(store_db)
        self.run_index_path = Path(run_index_path)
        self.hostname = hostname or socket.gethostname()

    def preflight(self) -> list[str]:
        """Returns human-readable problems, empty if none -- mirrors wspy's own
        "fail fast and specifically" posture (`wspy --preflight`, doc/DESIGN.md
        Phase 0) rather than letting a missing binary surface as an opaque
        subprocess error three calls deep. ``wspy-run`` is a bash script (always
        present in a checkout); the rest are C binaries that need `make` run in the
        wspy checkout first.
        """
        problems = []
        for label, path in (
            ("wspy", self.wspy_bin),
            ("wspy-run", self.wspy_run_bin),
            ("wspy-store", self.wspy_store_bin),
            ("wspy-validate", self.wspy_validate_bin),
            ("wspy-archetype", self.wspy_archetype_bin),
        ):
            if not path.exists():
                problems.append(f"{label} not found at {path} -- run `make` in {self.wspy_dir}")
        return problems

    def characterize(
        self, command: list[str], suite: str, benchmark: str, run_id: str,
        profile: str, output_root,
    ) -> RunSignature:
        output_root = Path(output_root)
        rundir = output_root / suite / benchmark / run_id
        argv = [
            str(self.wspy_run_bin), "--wspy", str(self.wspy_bin),
            "--suite", suite, "--benchmark", benchmark, "--run-id", run_id,
            "-o", str(output_root), "--run-index", str(self.run_index_path),
            profile, "--",
        ] + command
        proc = subprocess.run(argv, capture_output=True, text=True)
        raw = proc.stdout + proc.stderr

        validated = self._validate(rundir)
        self._ingest()
        scorecard = self._archetype(run_id)

        return RunSignature(
            wspy_run_ref=f"{self.hostname}:{run_id}",
            validated=validated,
            resource_dominance=scorecard.get("resource_dominance"),
            resource_dominance_pct=_to_float(scorecard.get("resource_dominance_pct")),
            memory_attribution=scorecard.get("memory_attribution"),
            metrics=scorecard,
            raw_output=raw,
        )

    def _validate(self, rundir: Path) -> bool:
        manifests = sorted(rundir.glob("*manifest*.json"))
        if not manifests:
            return False
        proc = subprocess.run(
            [str(self.wspy_validate_bin), *[str(m) for m in manifests]],
            capture_output=True, text=True,
        )
        return proc.returncode == 0

    def _ingest(self) -> None:
        subprocess.run(
            [str(self.wspy_store_bin), "--db", str(self.store_db),
             "--run-index", str(self.run_index_path)],
            capture_output=True, text=True, check=False,
        )

    def _archetype(self, run_id: str) -> dict:
        proc = subprocess.run(
            [str(self.wspy_archetype_bin), "--db", str(self.store_db),
             "--run", f"{self.hostname}:{run_id}"],
            capture_output=True, text=True,
        )
        return parse_kv_lines(proc.stdout)


def _to_float(value) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None

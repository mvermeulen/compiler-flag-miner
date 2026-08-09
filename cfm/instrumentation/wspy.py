"""Wraps the wspy CLI surface -- doc/DESIGN.md sec. 4.2. No new instrumentation
logic lives here, only correct sequencing of wspy's own tools:
``wspy-run`` (execute the measured command under instrumentation), ``wspy-store``
(ingest into the normalized store), ``wspy-validate`` (counter-collection sanity),
``wspy-archetype`` (resource_dominance/memory_attribution classification).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from ..util import parse_kv_lines
from .base import InstrumentationBackend, RunSignature


class WspyInstrumentation(InstrumentationBackend):
    def __init__(self, wspy_dir, store_db, run_index_path):
        self.wspy_dir = Path(wspy_dir)
        self.wspy_bin = self.wspy_dir / "wspy"
        self.wspy_run_bin = self.wspy_dir / "wspy-run"
        self.wspy_store_bin = self.wspy_dir / "wspy-store"
        self.wspy_validate_bin = self.wspy_dir / "wspy-validate"
        self.wspy_archetype_bin = self.wspy_dir / "wspy-archetype"
        self.store_db = Path(store_db)
        self.run_index_path = Path(run_index_path)

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
        # wspy itself doesn't create --run-index's parent directory -- it just warns
        # "unable to open run index file" and silently drops the record, which then
        # makes wspy-store ingest nothing and wspy-archetype report no such run,
        # further downstream where it's much less obvious why. Same for store_db's
        # parent (sqlite3 has the identical "won't create missing directories"
        # behavior). Caught by tests/test_wspy_interface.py, not by inspection.
        self.run_index_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_db.parent.mkdir(parents=True, exist_ok=True)
        lines_before = _count_lines(self.run_index_path)

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
        real_hostname, real_run_id = self._resolve_run_identity(lines_before)
        scorecard = self._archetype(real_hostname, real_run_id)

        return RunSignature(
            wspy_run_ref=f"{real_hostname}:{real_run_id}",
            validated=validated,
            resource_dominance=scorecard.get("resource_dominance"),
            resource_dominance_pct=_to_float(scorecard.get("resource_dominance_pct")),
            memory_attribution=scorecard.get("memory_attribution"),
            metrics=scorecard,
            raw_output=raw,
        )

    def _validate(self, rundir: Path) -> bool:
        # rundir/manifest.json is wspy-run's own *run-directory-layout* manifest
        # (doc/ARTIFACT_CONTRACT.md "Unified output layout" -- `layout_version`, a
        # different schema from a wspy manifest and not something wspy-validate
        # understands) -- it enumerates each pass's own manifest file via
        # `passes[].manifest`, and those per-pass files are what actually needs
        # validating. An earlier version of this method globbed `*manifest*.json`
        # and fed the run-level file to wspy-validate too, which always reported
        # FAIL on it and made every run look unvalidated -- caught by
        # tests/test_wspy_interface.py, a real contract test against the built
        # submodule, not by inspection.
        run_manifest_path = rundir / "manifest.json"
        if not run_manifest_path.exists():
            return False
        try:
            run_manifest = json.loads(run_manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            return False
        pass_manifests = [
            rundir / entry["manifest"]
            for entry in run_manifest.get("passes", [])
            if entry.get("manifest")
        ]
        if not pass_manifests:
            return False
        proc = subprocess.run(
            [str(self.wspy_validate_bin), *[str(m) for m in pass_manifests]],
            capture_output=True, text=True,
        )
        return proc.returncode == 0

    def _ingest(self) -> None:
        subprocess.run(
            [str(self.wspy_store_bin), "--db", str(self.store_db),
             "--run-index", str(self.run_index_path)],
            capture_output=True, text=True, check=False,
        )

    def _resolve_run_identity(self, lines_before: int) -> tuple[str, str]:
        """wspy-run's own ``--run-id`` only names the *output directory*
        (doc/ARTIFACT_CONTRACT.md sec. "Unified output layout": "it identifies the
        whole wspy-run invocation, which may launch several wspy processes, not one
        of them"). Each underlying ``wspy`` process invocation (one per profile
        "pass") generates its *own*, unrelated ``run_id``
        (``<start-time-to-millisecond>-<pid>``) -- and that generated id, not the
        caller-supplied ``--run-id``, is what ``wspy-store``/``wspy-archetype``
        actually key on. This reads it back from the run-index file's
        newly-appended line(s) instead of assuming it equals the ``run_id`` this
        class was called with -- a real bug caught by tests/test_wspy_interface.py,
        not by inspection.
        """
        if not self.run_index_path.exists():
            raise RuntimeError(f"wspy-run wrote no run-index record to {self.run_index_path}")
        all_lines = self.run_index_path.read_text().splitlines()
        new_lines = all_lines[lines_before:]
        if not new_lines:
            raise RuntimeError(f"wspy-run wrote no new run-index record to {self.run_index_path}")
        if len(new_lines) > 1:
            # A multi-pass profile (e.g. deep-cpu) launches several wspy processes,
            # each getting its own run_id -- which one carries the
            # topdown/archetype-relevant data isn't resolved yet. M0 only exercises
            # single-pass profiles (the "quick" default) end to end; fail loudly
            # here rather than silently guessing which pass "the" run is.
            raise RuntimeError(
                f"{len(new_lines)} new run-index records from one wspy-run invocation "
                "(a multi-pass profile) -- characterize() doesn't yet know which one "
                "to treat as 'the' run for archetype scoring. Single-pass profiles "
                "like 'quick' are the only ones M0 supports (doc/DESIGN.md sec. 14); "
                "resolving this is part of wiring deep-cpu in for M1's confirmation "
                "stage (doc/DESIGN.md sec. 6 Phase 4)."
            )
        record = json.loads(new_lines[0])
        return record["hostname"], record["run_id"]

    def _archetype(self, hostname: str, run_id: str) -> dict:
        proc = subprocess.run(
            [str(self.wspy_archetype_bin), "--db", str(self.store_db),
             "--run", f"{hostname}:{run_id}"],
            capture_output=True, text=True,
        )
        return parse_kv_lines(proc.stdout)


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as f:
        return sum(1 for _ in f)


def _to_float(value) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None

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

# Which named pass (from the run-level manifest.json's own passes[] list) carries the
# CSV topdown data wspy-archetype's resource_dominance scoring actually reads, for a
# multi-pass profile whose wspy-run invocation launches more than one wspy process. Not
# guessable from the profile's documentation alone -- confirmed live against a real
# `deep-cpu` run (doc/DESIGN.md sec. 4.2, CLAUDE.md's Non-obvious traps log has the full
# story): the natural first guess is deep-cpu's "counters" pass (wspy-run --help
# describes it as "used for topdown characterization"), but that pass has no --csv (it's
# wspy's native --passes= multipass sweep, human-readable output only), so wspy-store
# can't ingest its metric values at all -- its own wspy-archetype scorecard comes back
# resource_dominance=unknown, confidence=insufficient-data. It's deep-cpu's "amdtopdown"
# pass (--csv --counters=topdown, a plain non-multiplexed topdown-percentages pass) whose
# scorecard is actually populated. Only deep-cpu is mapped -- any other multi-pass
# profile (deep-cpu-intel, deep-gpu, zen4plus-deep, a comma-composed profile list) raises
# rather than guessing, same posture as the single-new-line check this replaces.
_ARCHETYPE_PASS_NAME = {
    "deep-cpu": "amdtopdown",
}


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
        real_hostname, real_run_id = self._resolve_run_identity(rundir, profile, lines_before)
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

    def _resolve_run_identity(self, rundir: Path, profile: str, lines_before: int) -> tuple[str, str]:
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
        if len(new_lines) == 1:
            record = json.loads(new_lines[0])
            return record["hostname"], record["run_id"]
        return self._resolve_multi_pass_identity(rundir, profile, new_lines)

    def _resolve_multi_pass_identity(
        self, rundir: Path, profile: str, new_lines: list[str],
    ) -> tuple[str, str]:
        """A multi-pass profile (e.g. ``deep-cpu``) launches several ``wspy``
        processes in one ``wspy-run`` invocation, each appending its own run-index
        record -- see ``_ARCHETYPE_PASS_NAME``'s comment for which *named* pass
        actually carries archetype-relevant data, confirmed live rather than
        guessed. Correlating "pass name" (only recorded in the run-level
        ``manifest.json``'s ``passes[]`` list, doc/ARTIFACT_CONTRACT.md "Unified
        output layout") to "run_id" (only recorded in the run-index) isn't direct --
        neither a per-pass ``--manifest`` file nor a run-index record carries the
        other's identifier -- but both independently record the same
        millisecond-precision ISO-8601 ``start_time``/``timing.start_time``, which
        is an exact, checkable join key (confirmed byte-for-byte against a real run).
        """
        pass_name = _ARCHETYPE_PASS_NAME.get(profile)
        if pass_name is None:
            raise RuntimeError(
                f"{len(new_lines)} new run-index records from one wspy-run invocation "
                f"(profile {profile!r}) -- characterize() only knows which pass carries "
                f"archetype-relevant CSV topdown data for {sorted(_ARCHETYPE_PASS_NAME)}. "
                "Add a mapping entry to _ARCHETYPE_PASS_NAME (confirmed against a real "
                "run, see its comment) before using this profile here."
            )
        run_manifest_path = rundir / "manifest.json"
        run_manifest = json.loads(run_manifest_path.read_text())
        pass_entries = {p["name"]: p for p in run_manifest.get("passes", [])}
        entry = pass_entries.get(pass_name)
        if entry is None or not entry.get("manifest"):
            raise RuntimeError(
                f"profile {profile!r}'s designated pass {pass_name!r} has no manifest "
                f"entry in {run_manifest_path}"
            )
        pass_manifest = json.loads((rundir / entry["manifest"]).read_text())
        start_time = pass_manifest["timing"]["start_time"]

        records = [json.loads(line) for line in new_lines]
        matches = [r for r in records if r.get("start_time") == start_time]
        if len(matches) != 1:
            raise RuntimeError(
                f"expected exactly one new run-index record with start_time "
                f"{start_time!r} (profile {profile!r}, pass {pass_name!r}), found "
                f"{len(matches)}"
            )
        return matches[0]["hostname"], matches[0]["run_id"]

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

"""SPEC CPU2026 ``runcpu`` wrapper -- doc/DESIGN.md sec. 4.1.

v1 mines *peak* tuning only (sec. 15's decision); a benchmark's base-config OPTIMIZE
line is never touched here. Uniform base-tuning is M6, deferred, not yet built.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Optional

from ..util import parse_kv_lines
from .base import BuildResult, RunResult, WorkloadBackend

# Candidate .rsf field-name suffixes for "the" per-benchmark/tune ratio, most-likely
# first. SPEC has kept the .rsf raw-result format's dotted-key naming stable across
# generations (runcpu.html: "will always include .rsf, for raw (unformatted) run
# data"; "spec.cpu2026.results.<bench>.<tune>.<field>" per its own "Rolling
# round-robin rate results" section, e.g. spec.cpu2026.results.714_cpython_r.base.
# time_avg), and "ratio" is the term SPEC has used for this field since CPU2017 --
# but this hasn't been confirmed against a real .rsf file on THIS host yet: no
# --action=run/validate has ever completed here, only --action=build (see
# workload/cpu2026/*/gcc_O3/*/build.gcc_O3.log in the wspy checkout). The first real
# M0 run must confirm or correct this list; record the outcome as a CLAUDE.md
# "Non-obvious traps" entry either way.
CANDIDATE_RATIO_FIELDS = ("ratio", "selected_ratio", "reported_ratio")

_EXIT_RE = re.compile(r"\[runcpu (\w+) exited (\d+)\]")
_LOG_PATH_RE = re.compile(r"The log for this run is in (\S+)")


class SpecCpu2026Workload(WorkloadBackend):
    def __init__(self, spec_dir, base_config: str = "gcc_O3.cfg"):
        self.spec_dir = Path(spec_dir)
        self.base_config = base_config
        self.config_dir = self.spec_dir / "config"
        self.result_dir = self.spec_dir / "result"

    def _shrc_command(self, inner: str) -> list[str]:
        # Mirrors wspy's own workload/cpu2017/run_test.sh shrc-sourcing convention:
        # runcpu needs SPEC's shrc-exported environment (PATH, PERL5LIB, ...), which
        # a bare subprocess.run() doesn't inherit on its own. `exec` hands off to
        # runcpu directly instead of leaving bash sitting in the process tree above
        # it -- matters once a trial's confirmation pass (doc/DESIGN.md sec. 6 Phase
        # 4) adds a wspy --tree pass, where an extra shell layer would otherwise show
        # up as a spurious wrapper node.
        return [
            "bash", "-c",
            f"cd {self.spec_dir} && source shrc && ulimit -s unlimited && exec {inner}",
        ]

    def generate_config(self, bench: str, tune: str, flags: list[str]) -> Path:
        if tune != "peak":
            raise ValueError(
                f"tune={tune!r} not supported -- v1 mines peak-only "
                "(doc/DESIGN.md sec. 15; uniform base-tuning is M6, not yet built)"
            )
        optimize_string = " ".join(flags)
        digest = hashlib.sha1(optimize_string.encode()).hexdigest()[:10]
        config_path = self.config_dir / f"cfm-{bench}-{digest}.cfg"
        # `include:` pulls in the real base config unmodified (SPEC's own
        # config.html "Included files" section) -- this trial's override only
        # touches the one benchmark's peak section, via the exact `<bench>=peak:`
        # section syntax SPEC's own docs demonstrate (search "706.stockfish_r=peak:"
        # in Docs/config.html for the source example this mirrors). `basepeak = no`
        # is required alongside it: the shipped gcc_O3.cfg sets `basepeak = yes`
        # suite-wide, which makes peak silently reuse the base binary/measurement
        # unless overridden per-benchmark here.
        config_path.write_text(
            f"include: {self.base_config}\n\n"
            f"{bench}: basepeak = no\n"
            f"{bench}=peak:\n"
            f"   OPTIMIZE = {optimize_string}\n"
        )
        return config_path

    def build(self, bench: str, tune: str, config_path: Path) -> BuildResult:
        cmd = self._shrc_command(
            f"runcpu --config {config_path.stem} --action=build --tune {tune} {bench}"
        )
        proc = subprocess.run(cmd, capture_output=True, text=True)
        raw = proc.stdout + proc.stderr
        exit_code = _last_runcpu_exit(raw, action="build")
        ok = proc.returncode == 0 and exit_code in (0, None)
        log_match = _LOG_PATH_RE.search(raw)
        log_path = Path(log_match.group(1)) if log_match else self.result_dir
        return BuildResult(ok=ok, log_path=log_path, raw_output=raw)

    def run_command(self, bench: str, tune: str, config_path: Path, iterations: int = 3) -> list[str]:
        # --action=validate builds (if needed), runs, and checks output against
        # SPEC's own reference -- doc/DESIGN.md sec. 11's correctness gate, and the
        # same single-action pattern workload/cpu2017/run_test.sh already uses. This
        # is the command an InstrumentationBackend wraps in
        # `wspy-run ... -- <this>`; see cfm/workloads/base.py's WorkloadBackend
        # docstring for why this class never launches it directly.
        return self._shrc_command(
            f"runcpu --config {config_path.stem} --action=validate --tune {tune} "
            f"--iterations {iterations} {bench}"
        )

    def parse_result(self, bench: str, tune: str, raw_output: str) -> RunResult:
        exit_code = _last_runcpu_exit(raw_output, action="validate")
        success_line = _find_success_line(raw_output)
        bench_succeeded = success_line is not None and bench in success_line
        if exit_code not in (0, None) or not bench_succeeded:
            return RunResult(
                ok=False, validated=False, ratio=None, seconds=None,
                status="validate-failed", raw_output=raw_output,
            )

        rsf_path = _latest_rsf(self.result_dir)
        if rsf_path is None:
            return RunResult(
                ok=True, validated=True, ratio=None, seconds=None,
                status="ok-no-rsf", raw_output=raw_output,
            )

        fields = parse_kv_lines(rsf_path.read_text(errors="replace"))
        prefix = f"spec.cpu2026.results.{bench.replace('.', '_')}.{tune}."
        scoped = {key[len(prefix):]: value for key, value in fields.items() if key.startswith(prefix)}
        return RunResult(
            ok=True, validated=True,
            ratio=_first_float(scoped, CANDIDATE_RATIO_FIELDS),
            seconds=_first_float(scoped, ("time_avg",)),
            status="ok", raw_output=raw_output, result_files=[rsf_path],
        )


def _last_runcpu_exit(raw_output: str, action: str) -> Optional[int]:
    matches = [m for m in _EXIT_RE.finditer(raw_output) if m.group(1) == action]
    return int(matches[-1].group(2)) if matches else None


def _find_success_line(raw_output: str) -> Optional[str]:
    for line in raw_output.splitlines():
        if line.startswith("Success:"):
            return line
    return None


def _latest_rsf(result_dir: Path) -> Optional[Path]:
    if not result_dir.exists():
        return None
    candidates = sorted(result_dir.glob("CPU2026.*.rsf"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def _first_float(fields: dict, keys: tuple) -> Optional[float]:
    for key in keys:
        if key in fields:
            try:
                return float(fields[key])
            except ValueError:
                continue
    return None

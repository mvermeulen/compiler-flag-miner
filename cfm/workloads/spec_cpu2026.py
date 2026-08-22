"""SPEC CPU2026 ``runcpu`` wrapper -- doc/DESIGN.md sec. 4.1.

v1 mines *peak* tuning only (sec. 15's decision); a benchmark's base-config OPTIMIZE
line is never touched here. Uniform base-tuning is M6, deferred, not yet built.
"""

from __future__ import annotations

import hashlib
import re
import statistics
import subprocess
from pathlib import Path
from typing import Optional

from ..util import parse_kv_lines
from .base import BuildResult, RunResult, WorkloadBackend

# .rsf field name for the per-*iteration* SPECrate score, confirmed against a real
# --action=validate --iterations 3 run of 706.stockfish_r on this host (CLAUDE.md's
# Non-obvious traps log has the full story -- an earlier version of this constant
# was an unconfirmed guess that turned out to be missing a whole path segment, not a
# wrong field name): keys look like
# spec.cpu2026.results.706_stockfish_r.peak.000.ratio, one such block per iteration
# (000, 001, 002, ...), never a single non-iteration-indexed rollup field. The
# formula checks out exactly against the sibling fields in the same block:
# ratio == copies * reference / reported_time (32 * 1260 / 315.907284 == 127.632384
# for iteration 000 of the confirming run). "ratio_avg" also exists per iteration
# (the mean of per-copy ratios rather than the reference/reported_time formula
# above) -- deliberately not used here, since it's a different, looser statistic.
_RATIO_FIELD = "ratio"
_SECONDS_FIELD = "reported_time"
_ITERATION_FIELD_RE = re.compile(r"^\d{3}\.(\w+)$")

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
        # -frecord-gcc-switches, always appended (doc/DESIGN.md's non-
        # comparability decision doesn't apply -- this only adds a small ELF
        # metadata section, never touches codegen, so it can't affect the
        # measured ratio): embeds the actual expanded compiler invocation into
        # a .GCC.command.line section of the compiled binary, letting
        # audit_compiled_flags() below independently confirm what SPEC actually
        # built with, rather than trusting `runcpu`'s own "Build successes"
        # report alone -- exactly the gap the basepeak trap above exploited
        # undetected for this project's entire history (CLAUDE.md's Non-obvious
        # traps log, 2026-08-21). Not folded into `digest` above -- it's a fixed
        # constant on every trial, not part of what makes one trial's flagset
        # distinct from another's.
        render_string = f"{optimize_string} -frecord-gcc-switches"
        config_path = self.config_dir / f"cfm-{bench}-{digest}.cfg"
        # `include:` pulls in the real base config unmodified (SPEC's own
        # config.html "Included files" section) -- this trial's override only
        # touches the one benchmark's peak section, via the exact `<bench>=peak:`
        # section syntax SPEC's own docs demonstrate (search "997.noisy=peak:" in
        # Docs/config.txt's basepeak entry for the source example this mirrors).
        # `basepeak = no` is required alongside it: the shipped gcc_O3.cfg sets
        # `basepeak = yes` suite-wide, which makes peak silently reuse the base
        # binary/measurement unless overridden per-benchmark here.
        #
        # CRITICAL: `basepeak = no` MUST live *inside* the `{bench}=peak:` block,
        # not as a separate unscoped `{bench}: basepeak = no` line before it --
        # Docs/config.txt's own basepeak entry warns "this works only if the
        # basepeak option is placed in the header section [or, per its own
        # worked example, scoped per-benchmark-and-tune as `997.noisy=peak:
        # basepeak=yes`]. Put it anywhere else, spend more time indoors." An
        # earlier version of this method used the unscoped form and it was
        # silently ignored -- confirmed live, 2026-08-21 (CLAUDE.md's Non-obvious
        # traps log): every real mining trial from M0 through four full `cfm
        # mine` runs actually built and measured the *base*-tuning binary
        # (`-g -O3 -march=native`, gcc_O3.cfg's own fixed default) regardless of
        # which candidate flags this method thought it was rendering. The build
        # log's own label even said "peak" while silently using
        # `build_base_gcc_O3.NNNN` and reporting "Build successes for ...:
        # <bench>(base)" -- the *only* externally-visible sign anything was
        # wrong, easy to miss without specifically checking for it.
        config_path.write_text(
            f"include: {self.base_config}\n\n"
            f"{bench}=peak:\n"
            f"   basepeak = no\n"
            f"   OPTIMIZE = {render_string}\n"
        )
        return config_path

    def audit_compiled_flags(self, bench: str, tune: str) -> Optional[str]:
        """Independent, best-effort audit of what SPEC *actually* compiled --
        reads the just-built binary's own `.GCC.command.line` section
        (`-frecord-gcc-switches`, always appended in `generate_config()` above)
        via `readelf`, rather than trusting `runcpu`'s own "Build successes"
        report. Exists specifically because that report alone was not enough
        to catch the basepeak trap (CLAUDE.md's Non-obvious traps log,
        2026-08-21) -- the build log said "peak" while silently building
        `base`, and nothing before this method would have noticed.

        Finds the most-recently-modified `build_<tune>_*` directory for this
        benchmark (SPEC's own build-dir naming; the tag component, e.g.
        `gcc_O3`, comes from the base config's own compiler identification, not
        this trial's own config filename, so it can't be predicted from
        `config_path` alone) and the one ELF file inside it (as opposed to the
        accompanying `simple-build-*.sh` build script, identified by the ELF
        magic number rather than a benchmark-specific name convention, which
        differs per benchmark). Returns the raw `readelf -p .GCC.command.line`
        output, or `None` if the build directory, binary, or `readelf` itself
        can't be found/read -- degrades gracefully, same posture as
        `instrumentation/wspy.py`'s `check_regression()` (a sanity signal,
        never a build/trial correctness verdict itself).
        """
        build_root = self.spec_dir / "benchspec" / "CPU" / bench / "build"
        candidates = sorted(
            build_root.glob(f"build_{tune}_*"),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        if not candidates:
            return None
        exe_path = None
        for entry in candidates[0].iterdir():
            if not entry.is_file():
                continue
            try:
                if entry.read_bytes()[:4] == b"\x7fELF":
                    exe_path = entry
                    break
            except OSError:
                continue
        if exe_path is None:
            return None
        try:
            proc = subprocess.run(
                ["readelf", "-p", ".GCC.command.line", str(exe_path)],
                capture_output=True, text=True,
            )
        except OSError:
            return None
        return proc.stdout if proc.returncode == 0 else None

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
        #
        # --noreportable is required, not optional: this shipped SPEC install's
        # gcc_O3.cfg sets `reportable = 1` (its own default per config.html), and
        # --action=validate/report/makebundle with reportable on requires every
        # benchmark in the full SPECrate2026_int benchset to be present
        # (parse.pl's FULL_BSET_CHECK) -- a single-benchmark mining trial never
        # satisfies that, regardless of --iterations. Confirmed live: without this
        # flag, runcpu fails immediately (0s elapsed) with "ERROR: A reportable
        # run was requested; individual benchmark selection is not allowed,"
        # before ever building/running anything -- a real bug caught by the first
        # actual `cfm mine` run against this host's SPEC install (doc/DESIGN.md
        # sec. 14's M1 status), not by inspection or the earlier M0 manual
        # verification (which evidently didn't go through this exact code path).
        return self._shrc_command(
            f"runcpu --config {config_path.stem} --action=validate --tune {tune} "
            f"--iterations {iterations} --noreportable {bench}"
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

        # .rsf uses "key: value" (colon-space), not "key=value" -- a different
        # convention from wspy-archetype's own trace output (parse_kv_lines'
        # default), confirmed by reading the real file: the default "=" separator
        # matched zero lines here (none of these keys contain "="), so every ratio
        # silently came back None even once the iteration-index fix above landed.
        fields = parse_kv_lines(rsf_path.read_text(errors="replace"), sep=": ")
        prefix = f"spec.cpu2026.results.{bench.replace('.', '_')}.{tune}."
        # Stripping the prefix leaves keys like "000.ratio"/"001.ratio" (one block
        # per --iterations run, see _RATIO_FIELD's comment above) -- never a bare
        # "ratio". Reporting the median across iterations rather than picking one is
        # deliberate: SPEC's own rate-mode methodology already medians per-copy
        # times within an iteration (runcpu.html's "Rolling round-robin rate
        # results"), and doing the same one level up, across iterations, is the
        # same outlier-robust idea applied consistently for a *mining* trial's
        # number (not a "reportable run" -- SPEC's own official selection rule
        # for that is a separate, stricter thing this project doesn't need to
        # replicate).
        scoped = {key[len(prefix):]: value for key, value in fields.items() if key.startswith(prefix)}
        ratios = _iteration_values(scoped, _RATIO_FIELD)
        seconds_values = _iteration_values(scoped, _SECONDS_FIELD)
        return RunResult(
            ok=True, validated=True,
            ratio=statistics.median(ratios) if ratios else None,
            seconds=statistics.median(seconds_values) if seconds_values else None,
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


def _iteration_values(scoped: dict, field: str) -> list[float]:
    """Collects one value per iteration block (scoped keys shaped "NNN.<field>")
    for the given field name, skipping any that don't parse as a float rather than
    raising -- a malformed/partial .rsf record shouldn't crash the whole trial.
    """
    values = []
    for key, value in scoped.items():
        match = _ITERATION_FIELD_RE.match(key)
        if match and match.group(1) == field:
            try:
                values.append(float(value))
            except ValueError:
                continue
    return values

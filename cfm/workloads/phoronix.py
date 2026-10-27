"""Phoronix Test Suite backend -- doc/DESIGN.md sec. 4.1.

A benchmark is named by its PTS identifier, ``pts/<test>-<version>`` (e.g.
``pts/coremark-1.0.1``). The test must already be installed by PTS itself
(``phoronix-test-suite install pts/coremark``): that's what downloads its source
archives and pulls in its system dependencies, and this backend reuses both.

PTS's own runner is never invoked. ``build()`` replays the test profile's
``install.sh`` in a private build directory under ``<output_root>/phoronix/``,
with the trial's flags as ``CFLAGS``/``CXXFLAGS`` and the environment variables
PTS itself would set (``HOME`` is the install directory, so ``cd ~`` and
``~/install-exit-status`` land there). ``run_command()`` runs the test script
``install.sh`` generated, directly, so wspy measures the benchmark rather than
PTS's PHP harness and its own repetition logic. ``parse_result()`` reads the
score out of each run's ``$LOG_FILE`` with the profile's ``OutputTemplate``.

Two things PTS doesn't provide that this project needs are handled here:

- **Correctness gate.** CLAUDE.md's enforced rule (no number counts without a
  validation pass) needs a per-test output check, and PTS has no generic
  reference-output comparison. ``_VALIDATORS`` holds one per supported test; a
  test without one is refused up front rather than measured unchecked.
- **PGO.** With ``-fprofile-use`` in the flags, ``build()`` does an instrumented
  build, one training run of the test itself, then the optimized rebuild. PTS
  tests have no separate training input, so unlike SPEC's train workload, the
  profile comes from the same workload that's then measured.

Only the simplest profile shape is supported: one ``OutputTemplate``, no test
options menu, no ``pre.sh``/``post.sh``/``interim.sh``, higher-is-better scores
(the trial ratio is the score itself). Anything else is refused with a reason.

The trial's flags also go in as ``CFLAGS_OVERRIDE``. About a dozen profiles
(tscp, crafty, n-queens, ...) build with ``CFLAGS="$CFLAGS -O3 -march=native"``
unless that variable is set, which would put their flags after ours and win
(doc/phoronix_cflags_survey.md). Profiles that don't read it ignore it.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import statistics
import subprocess
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ..hostinfo import fastest_cpus
from .base import BuildResult, RunResult, WorkloadBackend
from .elf import code_digest, command_line_dump, is_linked_elf

PTS_PREFIX = "pts/"

_PGO_TRAIN_FLAG = "-fprofile-generate"
_PGO_USE_FLAG = "-fprofile-use"
# Same defensive extras as the SPEC backend's PASS1/PASS2 lines (see
# cfm/workloads/spec_cpu2026.py). -fprofile-update=atomic matters more here:
# coremark's training run forks one process per core.
_PGO_PASS1_EXTRA = "-fprofile-update=atomic"
_PGO_PASS2_EXTRA = "-fprofile-correction"

_RESULT_PLACEHOLDER = "#_RESULT_#"
_PLACEHOLDER_RE = re.compile(r"#_[A-Z0-9_]+_#")
_NUMBER_RE = r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"

_SOURCE_LANGUAGES = {
    ".c": "c",
    ".cc": "cxx", ".cpp": "cxx", ".cxx": "cxx", ".C": "cxx",
    ".f": "fortran", ".F": "fortran", ".f90": "fortran", ".F90": "fortran", ".f95": "fortran",
}


def is_phoronix_benchmark(bench: str) -> bool:
    return bench.startswith(PTS_PREFIX)


def _coremark_valid(log: str) -> bool:
    # CoreMark checks its own list/matrix/state CRCs against known values and
    # prints this line only when every one matched; a mismatch prints "ERROR!"
    # lines and "Errors detected" instead.
    return "Correct operation validated" in log and "ERROR" not in log and "Errors detected" not in log


# TSCP's built-in benchmark searches one fixed position to depth 5, three times,
# with no time limit, so a correct build always visits exactly this many nodes
# and finds this principal variation (confirmed on erie, 2026-10-27, with PTS's
# own -O3 -march=native build).
TSCP_NODES = 550778
TSCP_PV = "c2a4 d6c7 g2d5 e6d5 c1e3"


def _tscp_valid(log: str) -> bool:
    nodes = re.findall(r"^Nodes: (\d+)$", log, re.M)
    scores = re.findall(r"^Nodes per second: ", log, re.M)
    return (
        bool(nodes)
        and all(int(n) == TSCP_NODES for n in nodes)
        and len(scores) == len(nodes)
        and log.count(TSCP_PV) == 3 * len(nodes)
    )


# Test name (identifier without "pts/" and version) -> output check.
_VALIDATORS: dict[str, Callable[[str], bool]] = {
    "coremark": _coremark_valid,
    "tscp": _tscp_valid,
}

# Coremark's per-process iteration count. With no arguments (how PTS's wrapper
# runs it) coremark sizes its own run: it times 10x more iterations until a run
# takes 1 s, then scales by 1 + 10/int(seconds). On erie that timing run sits
# near 2 s, so builds landed on either 9.6M or 17.6M total iterations (27 s or
# 47 s), faster code tending to the longer one -- a confound under a power
# limit (doc/mining_results.pts_coremark-1.0.1.2026-10-26.md). 600,000 per
# process is the 9.6M case, the one most of that mine's baseline used.
COREMARK_ITERATIONS = 600_000

# TSCP runs for 0.66 s and reports the best of three ~220 ms searches, timed to
# the millisecond, so one run's score moves in 0.45% steps and varies by about
# 3%. The override runs it this many times (~26 s) and parse_result() averages
# the scores in the log.
TSCP_RUNS = 40

# Test name -> shell command run from the build directory in place of the
# profile's wrapper script, writing to $LOG_FILE. Used when the wrapper can't
# express a setting the mine needs. ``{cpu}`` becomes one of the host's fastest
# CPUs, for pinning a single-threaded test (on erie, a Zen5 core rather than a
# 3.5 GHz Zen5c one, which the scheduler would otherwise pick at random).
# Coremark's linux64 port reads seeds and iterations from argv; 0x0 0x0 0x66 are
# the seeds it defaults to (its "performance run"), so its CRC validation still
# applies.
_RUN_OVERRIDES: dict[str, str] = {
    "coremark": f'cd coremark-master && ./coremark.exe 0x0 0x0 0x66 {COREMARK_ITERATIONS} > "$LOG_FILE" 2>&1',
    "tscp": (
        f'cd tscp181 && for i in $(seq {TSCP_RUNS}); do taskset -c {{cpu}} ./tscp || exit $?; done '
        '> "$LOG_FILE" 2>&1'
    ),
}


@dataclass(frozen=True)
class _Profile:
    identifier: str      # "pts/coremark-1.0.1"
    name: str            # "coremark"
    profile_dir: Path    # test-profiles/pts/coremark-1.0.1
    install_dir: Path    # installed-tests/pts/coremark-1.0.1 (PTS's own install)
    downloads: tuple[str, ...]
    executable: str
    arguments: str
    output_template: str


def _text(root: ET.Element, path: str) -> str:
    node = root.find(path)
    return (node.text or "").strip() if node is not None else ""


def _for_linux(platform_specific: str) -> bool:
    platforms = [p.strip().lower() for p in platform_specific.split(",") if p.strip()]
    return not platforms or "linux" in platforms


def _template_regex(template: str) -> re.Pattern:
    """PTS ``OutputTemplate`` line -> regex. ``#_RESULT_#`` captures a number,
    any other ``#_..._#`` placeholder matches one non-space token, and runs of
    whitespace match any whitespace. Tokens after the result's are dropped: PTS
    picks the result by its position on the line, and templates often carry a
    sample of the rest (TSCP's ends in "(Score: 1.034)", which varies per run)."""
    lines = [line for line in template.splitlines() if _RESULT_PLACEHOLDER in line]
    if len(lines) != 1:
        raise ValueError(f"OutputTemplate must have exactly one {_RESULT_PLACEHOLDER} line: {template!r}")
    tokens = lines[0].split()
    last = next(i for i, token in enumerate(tokens) if _RESULT_PLACEHOLDER in token)
    parts = []
    for token in tokens[:last + 1]:
        pieces = re.split(r"(#_[A-Z0-9_]+_#)", token)
        parts.append("".join(
            _NUMBER_RE if piece == _RESULT_PLACEHOLDER
            else r"\S+" if _PLACEHOLDER_RE.fullmatch(piece)
            else re.escape(piece)
            for piece in pieces
        ))
    return re.compile(r"\s+".join(parts))


class PhoronixWorkload(WorkloadBackend):
    suite = "phoronix"

    def __init__(
        self, pts_home, output_root, cpu_count: Callable[[], Optional[int]] = os.cpu_count,
        cpu_lister: Callable[[], list[int]] = fastest_cpus,
    ):
        self.pts_home = Path(pts_home)
        # Absolute, because HOME and LOG_FILE point into it and install.sh/the test
        # script cd around (cfg.output_root defaults to a relative "results").
        self.output_root = Path(output_root).resolve()
        self.cpu_count = cpu_count
        # Injectable so unit tests don't read this host's sysfs, as in the SPEC backend.
        self.cpu_lister = cpu_lister
        self._profiles: dict[str, _Profile] = {}
        # run_command() picks a fresh log directory per measured run; parse_result()
        # reads it back. wspy-run never echoes the benchmark's own output, so the
        # logs on disk are the only place the score exists.
        self._last_run_dir: dict[str, Path] = {}

    # -- profile ------------------------------------------------------------

    def profile(self, bench: str) -> _Profile:
        if bench not in self._profiles:
            self._profiles[bench] = self._load_profile(bench)
        return self._profiles[bench]

    def _load_profile(self, bench: str) -> _Profile:
        if not is_phoronix_benchmark(bench):
            raise RuntimeError(f"{bench!r} isn't a PTS identifier (expected pts/<test>-<version>)")
        profile_dir = self.pts_home / "test-profiles" / bench
        install_dir = self.pts_home / "installed-tests" / bench
        if not (profile_dir / "test-definition.xml").exists():
            raise RuntimeError(f"no PTS test profile at {profile_dir}")
        if not install_dir.is_dir():
            raise RuntimeError(
                f"{bench} isn't installed by PTS ({install_dir} missing) -- run "
                f"`phoronix-test-suite install {bench}` first; it downloads the sources this build uses"
            )
        slug = bench[len(PTS_PREFIX):]
        name = slug.rsplit("-", 1)[0] if re.search(r"-\d[\w.]*$", slug) else slug

        problems = []
        if name not in _VALIDATORS:
            problems.append(
                f"no output validator for {name!r} (cfm/workloads/phoronix.py's _VALIDATORS) -- "
                "every measured number needs a correctness check"
            )
        for script in ("pre.sh", "post.sh", "interim.sh"):
            if (profile_dir / script).exists():
                problems.append(f"{script} isn't supported")
        if not (profile_dir / "install.sh").exists():
            problems.append("no install.sh")

        definition = ET.parse(profile_dir / "test-definition.xml").getroot()
        if definition.find("TestSettings/Option") is not None:
            problems.append("test options menus aren't supported")
        proportion = _text(definition, "TestInformation/Proportion") or "HIB"
        if proportion != "HIB":
            problems.append(f"Proportion {proportion} isn't supported (only higher-is-better)")

        template = ""
        results_path = profile_dir / "results-definition.xml"
        parsers = ET.parse(results_path).getroot().findall("ResultsParser") if results_path.exists() else []
        if len(parsers) != 1:
            problems.append(f"expected exactly one ResultsParser, found {len(parsers)}")
        else:
            extra = sorted({child.tag for child in parsers[0]} - {"OutputTemplate"})
            if extra:
                problems.append(f"ResultsParser settings {extra} aren't supported")
            template = _text(parsers[0], "OutputTemplate")
            try:
                _template_regex(template)
            except ValueError as exc:
                problems.append(str(exc))

        downloads = ()
        downloads_path = profile_dir / "downloads.xml"
        if downloads_path.exists():
            # A package marked PlatformSpecific for other platforms only (TSCP's
            # Windows .exe.zip) is one PTS never downloads on Linux.
            downloads = tuple(
                (pkg.findtext("FileName") or "").strip()
                for pkg in ET.parse(downloads_path).getroot().iter("Package")
                if _for_linux(pkg.findtext("PlatformSpecific") or "")
            )
        missing = [f for f in downloads if not (install_dir / f).exists()]
        if missing:
            problems.append(f"downloaded files missing from {install_dir}: {missing}")

        if problems:
            raise RuntimeError(f"{bench} can't be mined: " + "; ".join(problems))
        return _Profile(
            identifier=bench, name=name, profile_dir=profile_dir, install_dir=install_dir,
            downloads=downloads,
            executable=_text(definition, "TestInformation/Executable") or name,
            arguments=_text(definition, "TestSettings/Default/Arguments"),
            output_template=template,
        )

    # -- paths and environment ----------------------------------------------

    def _work_dir(self, bench: str) -> Path:
        return self.output_root / "phoronix" / bench[len(PTS_PREFIX):]

    def build_dir(self, bench: str) -> Path:
        # One fixed directory per benchmark, wiped before every build, like SPEC's
        # own build directories. A fixed path also keeps PGO's mangled .gcda
        # names identical between the instrumented and optimized builds.
        return self._work_dir(bench) / "build"

    def _env(self, bench: str, **extra: str) -> dict[str, str]:
        cores = self.cpu_count() or 1
        env = dict(os.environ)
        env.update({
            "HOME": str(self.build_dir(bench)),
            "NUM_CPU_CORES": str(cores),
            "NUM_CPU_JOBS": str(cores * 2),
            "OS_TYPE": "Linux",
            "OS_ARCH": platform.machine(),
        })
        env.update(extra)
        return env

    # -- WorkloadBackend --------------------------------------------------------

    def generate_config(self, bench: str, tune: str, flags: list[str]) -> Path:
        """No rendered config file exists for PTS; this just records the trial's
        flags for ``build()``. ``tune`` is ignored (PTS has no base/peak split)."""
        self.profile(bench)  # refuse an unsupported test before anything is built
        digest = hashlib.sha1(" ".join(flags).encode()).hexdigest()[:10]
        config_path = self._work_dir(bench) / "configs" / f"cfm-{digest}.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({"benchmark": bench, "flags": flags}, indent=2) + "\n")
        return config_path

    def build(self, bench: str, tune: str, config_path: Path) -> BuildResult:
        prof = self.profile(bench)
        flags = json.loads(Path(config_path).read_text())["flags"]
        log_path = self._work_dir(bench) / "build.log"
        # -frecord-gcc-switches always appended, as in the SPEC backend: it lets
        # audit_compiled_flags() read back what was actually compiled.
        plain = [f for f in flags if f not in (_PGO_TRAIN_FLAG, _PGO_USE_FLAG)] + ["-frecord-gcc-switches"]

        if _PGO_USE_FLAG not in flags:
            ok, raw = self._install(prof, plain)
        else:
            profile_data = self._work_dir(bench) / "pgo-profile"
            shutil.rmtree(profile_data, ignore_errors=True)
            ok, raw = self._install(prof, plain + [f"{_PGO_TRAIN_FLAG}={profile_data}", _PGO_PASS1_EXTRA])
            if ok:
                ok, train_raw = self._train(prof)
                raw += train_raw
            if ok:
                ok, use_raw = self._install(
                    prof, plain + [f"{_PGO_USE_FLAG}={profile_data}", _PGO_PASS2_EXTRA],
                )
                raw += use_raw

        log_path.write_text(raw)
        return BuildResult(ok=ok, log_path=log_path, raw_output=raw)

    def _install(self, prof: _Profile, cflags: list[str]) -> tuple[bool, str]:
        build_dir = self.build_dir(prof.identifier)
        shutil.rmtree(build_dir, ignore_errors=True)
        build_dir.mkdir(parents=True)
        for filename in prof.downloads:
            shutil.copy2(prof.install_dir / filename, build_dir / filename)
        flag_string = " ".join(cflags)
        env = self._env(
            prof.identifier, CFLAGS=flag_string, CXXFLAGS=flag_string, FFLAGS=flag_string,
            CFLAGS_OVERRIDE=flag_string,
        )
        proc = subprocess.run(
            ["sh", str(prof.profile_dir / "install.sh")],
            cwd=build_dir, env=env, capture_output=True, text=True,
        )
        raw = f"## install.sh with CFLAGS={flag_string}\n{proc.stdout}{proc.stderr}"
        status_file = build_dir / "install-exit-status"
        status = status_file.read_text().strip() if status_file.exists() else "0"
        ok = proc.returncode == 0 and status == "0" and (build_dir / prof.executable).exists()
        return ok, raw

    def _train(self, prof: _Profile) -> tuple[bool, str]:
        """One unmeasured run of the instrumented build, writing the PGO profile."""
        log = self._work_dir(prof.identifier) / "pgo-train.log"
        proc = subprocess.run(
            ["sh", "-c", self._run_script(prof, log)],
            cwd=self.build_dir(prof.identifier), env=self._env(prof.identifier),
            capture_output=True, text=True,
        )
        text = log.read_text(errors="replace") if log.exists() else ""
        ok = proc.returncode == 0 and _VALIDATORS[prof.name](text)
        return ok, f"## PGO training run ({'ok' if ok else 'FAILED'})\n{proc.stdout}{proc.stderr}{text}"

    def _run_script(self, prof: _Profile, log: Path) -> str:
        # PTS runs the test script with cwd and HOME both the install directory;
        # the script writes its output to $LOG_FILE and its exit status to
        # ~/test-exit-status. Fail on either.
        build_dir = shlex.quote(str(self.build_dir(prof.identifier)))
        command = _RUN_OVERRIDES.get(prof.name)
        if command is None:
            command = f"./{shlex.quote(prof.executable)} {prof.arguments}"
        elif "{cpu}" in command:
            command = command.replace("{cpu}", str(self._pinned_cpu()))
        return (
            f"cd {build_dir} && rm -f test-exit-status && "
            f"export LOG_FILE={shlex.quote(str(log))} && ( {command} ); "
            f"rc=$?; [ $rc -eq 0 ] || exit $rc; "
            f"[ ! -f test-exit-status ] || [ \"$(cat test-exit-status)\" = 0 ]"
        )

    def _pinned_cpu(self) -> int:
        # Same choice as the SPEC backend's thread_placement(): a fastest CPU, not
        # CPU 0 (which takes most interrupts) when there's a choice.
        fast = self.cpu_lister() or [0]
        return next((c for c in fast if c != 0), fast[0])

    def run_command(self, bench: str, tune: str, config_path: Path, iterations: int = 3) -> list[str]:
        prof = self.profile(bench)
        stamp = f"{time.strftime('%Y%m%dT%H%M%S')}-{time.time_ns() % 1_000_000_000:09d}"
        run_dir = self._work_dir(bench) / "runs" / stamp
        run_dir.mkdir(parents=True)
        self._last_run_dir[bench] = run_dir
        # Each iteration's status goes to its own file rather than the shell's
        # exit code, which wspy-run doesn't pass back.
        steps = [
            f"( {self._run_script(prof, run_dir / f'run-{i}.log')} ); "
            f"echo $? > {shlex.quote(str(run_dir / f'run-{i}.status'))}"
            for i in range(1, iterations + 1)
        ]
        env = self._env(bench)
        assignments = [f"{k}={env[k]}" for k in ("HOME", "NUM_CPU_CORES", "NUM_CPU_JOBS", "OS_TYPE", "OS_ARCH")]
        return ["env", *assignments, "sh", "-c", "; ".join(steps)]

    def parse_result(self, bench: str, tune: str, raw_output: str) -> RunResult:
        prof = self.profile(bench)
        run_dir = self._last_run_dir.get(bench)
        logs = sorted(run_dir.glob("run-*.log")) if run_dir is not None else []
        failed = RunResult(
            ok=False, validated=False, ratio=None, seconds=None,
            status="validate-failed", raw_output=raw_output, result_files=logs,
        )
        if not logs:
            return failed
        pattern = _template_regex(prof.output_template)
        scores = []
        for log in logs:
            status_file = log.with_suffix(".status")
            if not status_file.exists() or status_file.read_text().strip() != "0":
                return failed
            text = log.read_text(errors="replace")
            if not _VALIDATORS[prof.name](text):
                return failed
            matches = pattern.findall(text)
            if not matches:
                return failed
            # A log with several scores (TSCP's repeated runs) contributes their
            # mean: the scores are quantized, and a median would stay on a step.
            scores.append(statistics.fmean(float(m) for m in matches))
        # Median across iterations, the same outlier-robust aggregate the SPEC
        # backend uses for its per-iteration ratios.
        return RunResult(
            ok=True, validated=True, ratio=statistics.median(scores), seconds=None,
            status="ok", raw_output=raw_output, result_files=logs,
        )

    # -- audits used by cfm/agents/spec_agent.py --------------------------------

    def _linked_binaries(self, bench: str) -> list[Path]:
        build_dir = self.build_dir(bench)
        if not build_dir.is_dir():
            return []
        return [p for p in sorted(build_dir.rglob("*")) if is_linked_elf(p)]

    def audit_compiled_flags(self, bench: str, tune: str) -> Optional[str]:
        return command_line_dump(self._linked_binaries(bench))

    def code_fingerprint(self, bench: str, tune: str) -> Optional[str]:
        return code_digest(self._linked_binaries(bench))

    def benchmark_languages(self, bench: str) -> list[str]:
        """Languages of the source files in the last build's directory. PTS
        profiles don't declare a language, and ``cfm mine`` only asks after the
        baseline trials have built the test at least once."""
        build_dir = self.build_dir(bench)
        found = {
            _SOURCE_LANGUAGES[p.suffix]
            for p in build_dir.rglob("*") if p.suffix in _SOURCE_LANGUAGES and p.is_file()
        } if build_dir.is_dir() else set()
        if not found:
            raise RuntimeError(f"no C/C++/Fortran sources under {build_dir} -- has {bench} been built yet?")
        return [lang for lang in ("c", "cxx", "fortran") if lang in found]

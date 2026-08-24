"""Host microarchitecture detection -- doc/DESIGN.md sec. 6 Phase 6's microarch
multiplier: "a small fixed set of -march=/-mtune= choices relevant to the
*detected* host microarchitecture (reusing wspy's own cpu_info.c vendor/model
detection rather than an open-ended search over every -march value GCC
knows)." This module is that reuse -- it shells out to the pinned wspy
submodule's own `cpu_info` binary (built by `make` alongside `wspy` itself,
part of the Makefile's default `all:` target, not a throwaway debug tool)
rather than re-deriving CPUID/vendor detection here.

Deliberately narrow: wspy's own `cpu_info.c` only confidently distinguishes a
handful of AMD core labels (`CORE_AMD_UNKNOWN`, `CORE_AMD_ZEN`, `CORE_AMD_ZEN5`,
`CORE_AMD_ZEN5C` -- confirmed by reading the enum directly, no per-generation
Zen1/2/3/4 label exists at all) and two generic Intel buckets
(`CORE_INTEL_ATOM`/`CORE_INTEL_CORE`, no generation info either). Only the
labels precise enough to map to one specific, correct GCC `-march=` value
without guessing are mapped here (`Zen5`/`Zen5c` -> `znver5`, confirmed live
against this project's own AMD Zen5 mining host); everything else --
including the ambiguous bare `Zen` bucket, which could mean anything from
Zen1 through Zen4 -- degrades to "nothing detected," never a guess. Matches
this project's established "never guess, verify or skip" discipline
(CLAUDE.md's Non-obvious traps log has several entries about exactly this
class of mistake elsewhere in the pipeline).

Also houses `read_package_power_watts()` (added 2026-08-24) -- an unrelated second piece of live host
diagnostics: a best-effort per-trial package-power sample, added specifically to test
`doc/settling_baseline_drift_investigation.2026-08-24.md`'s hypothesis 2 (a STAPM-style sustained power
limit easing upward over a run's own real wall-clock minutes) directly, rather than only inferring it
from the elapsed-time-vs-`cpu_temp_c` correlation gap that hypothesis was first raised from.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

# Only core labels wspy's own cpu_info.c can report with enough precision to
# name one correct GCC -march= value -- see this module's own docstring for
# why every other label (bare "Zen", *_UNKNOWN, Intel's generation-less
# buckets, every ARM Cortex/Neoverse label -- real GCC -mcpu= targets exist
# for those too, but this project has no ARM mining host to verify against)
# is deliberately left unmapped rather than guessed.
_LABEL_TO_MARCH = {
    "Zen5": "znver5",
    "Zen5c": "znver5",  # physically compact cores, same ISA generation
}

# Matches one core line from cpu_info's real stdout, e.g. "\t   * 0 Zen5" --
# confirmed against this host's own real cpu_info output. The '*'/' ' marker
# is cpu_info.c's own is_available flag; only available cores count towards
# detection. A hybrid/ARM core's own extra " (pmu_type=N,cluster=M)" suffix
# deliberately doesn't match \s*$ here, so such lines are silently excluded
# from the label set rather than mis-parsed -- on a genuinely hybrid or ARM
# host this collapses to "no single label agreed on," which is exactly the
# "don't guess" outcome this module wants for a case it can't verify anyway.
_CORE_LINE_RE = re.compile(r"^\s*([* ])\s+(\d+)\s+(\S+)\s*$")


def detect_microarch_flags(wspy_dir) -> list[str]:
    """Returns a small, fixed candidate list (`["-march=<uarch>", "-mtune=<uarch>"]`)
    for the host's confidently-detected microarchitecture, or `[]` if nothing
    could be determined without guessing: `cpu_info` missing/unbuilt (this
    project's own posture on an optional wspy binary -- degrade gracefully,
    same as `check_regression()`/`audit_compiled_flags()` elsewhere, never a
    hard failure for what's genuinely a bonus multiplier), a non-zero exit, no
    available cores parsed, the available cores disagreeing with each other
    (a genuinely mixed/hybrid host -- picking either label over the other
    would be a guess), or an available-core label with no entry in
    `_LABEL_TO_MARCH`.
    """
    cpu_info_bin = Path(wspy_dir) / "cpu_info"
    if not cpu_info_bin.exists():
        return []
    try:
        proc = subprocess.run(
            [str(cpu_info_bin)], capture_output=True, text=True, timeout=10,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []

    labels = set()
    for line in proc.stdout.splitlines():
        match = _CORE_LINE_RE.match(line)
        if match and match.group(1) == "*":
            labels.add(match.group(3))

    if len(labels) != 1:
        return []  # no cores parsed, or a genuinely mixed/ambiguous host

    uarch = _LABEL_TO_MARCH.get(next(iter(labels)))
    if uarch is None:
        return []
    return [f"-march={uarch}", f"-mtune={uarch}"]


# The hwmon driver name for this host's own package-power sensor -- confirmed
# live, 2026-08-24, by enumerating /sys/class/hwmon/hwmon*/name directly on
# the real mining host: "amdgpu" is present alongside "k10temp" (the source
# _extract_cpu_temp_c() already reads) and exposes a real power1_average
# reading (~9W at idle, confirmed by hand). On this integrated APU (CPU+GPU
# sharing one power budget, not a discrete GPU) that sensor reports combined
# package power, not GPU-only draw -- exactly what a package-level power-limit
# hypothesis needs. Discovered by driver *name* here too, not a hardcoded
# "hwmonN" path: hwmon device numbering is assigned by kernel enumeration
# order at boot, not stable across reboots or hosts (same reasoning as
# detect_microarch_flags() never hardcoding a cpu_info path shape).
_POWER_HWMON_DRIVER_NAME = "amdgpu"

_DEFAULT_HWMON_ROOT = Path("/sys/class/hwmon")


def read_package_power_watts(hwmon_root: Path = _DEFAULT_HWMON_ROOT) -> Optional[float]:
    """Best-effort, single-point-in-time read of this host's own package power
    draw, in watts, via the `amdgpu` hwmon driver's `power1_average` sensor
    (microwatts, per the standard Linux hwmon ABI -- converted here). A single
    snapshot taken once per trial, same precision level as
    `_extract_cpu_temp_c()`'s own single reading -- not integrated over the
    trial's own duration, just whatever the driver's own internal rolling
    average happens to read at the moment this is called (typically shortly
    after the trial's real measurement finishes, from `run_one_trial()`'s own
    call site).

    If this climbs across a sequence of same-flag trials the way `ratio`
    already does, that's direct evidence for
    `doc/settling_baseline_drift_investigation.2026-08-24.md`'s hypothesis 2;
    if it doesn't, that hypothesis is weakened in favor of one of the others
    still on the table there.

    Returns `None` -- degrade, never raise -- if no `amdgpu` hwmon is found,
    or its `power1_average` file can't be read (a non-AMD host, a driver
    naming difference, permissions, a transient sysfs read failure): a
    best-effort diagnostic sample, never load-bearing for the trial's own
    correctness.
    """
    if not hwmon_root.is_dir():
        return None
    for entry in sorted(hwmon_root.iterdir()):
        try:
            if entry.joinpath("name").read_text().strip() != _POWER_HWMON_DRIVER_NAME:
                continue
            microwatts = int(entry.joinpath("power1_average").read_text().strip())
        except (OSError, ValueError):
            continue
        return microwatts / 1_000_000.0
    return None

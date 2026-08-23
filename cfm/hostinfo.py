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
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

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

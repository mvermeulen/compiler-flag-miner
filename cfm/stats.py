"""Confidence-interval statistics for M1's Phase 4 confirmation stage
(doc/DESIGN.md sec. 6 Phase 4: "accept only if the improvement's 95% CI doesn't
overlap the baseline's"). Replicates wspy-summary's own documented formula
(doc/ARTIFACT_CONTRACT.md's "Summary tables" section, confirmed live this session
against real ``wspy-summary`` output) -- mean, sample stddev (``n-1`` denominator,
0 for ``n<2``), Student's t 95% CI, "PASS"/"WARN:thin" for ``n<3`` -- rather than
inventing a different one (doc/DESIGN.md principle 2: "No step here invents new
statistics").

``wspy-summary`` itself can't be shelled out to for *this* comparison, though:
it computes its CI over wspy's own tracked counters (ipc, elapsed, ...) and has no
way to see SPEC's ``ratio`` field, which ``cfm/workloads/spec_cpu2026.py`` parses
independently and stores only in ``cfm.db``'s ``trials.ratio``. So this module
applies wspy-summary's own formula directly to a list of ``ratio`` values instead
-- see ``cfm/instrumentation/wspy.py``'s ``check_regression()`` for where
``wspy-summary --check-regression`` *is* still used, as a secondary environment/
counter-sanity guardrail, never the accept/reject decision itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Two-tailed 95% (alpha=0.05) Student's t critical values, indexed by degrees of
# freedom -- a standard statistics reference table, not derived here. Beyond the
# table's range this falls back to the normal approximation (z=1.96), same as most
# textbook t-tables do; M1's confirmation stage realistically never sees more than
# a handful of repetitions per flagset, but the fallback keeps this correct anyway.
_T_TABLE_95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
    26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
}
_Z_95 = 1.960


def _t_critical(df: int) -> float:
    if df < 1:
        raise ValueError(f"degrees of freedom must be >= 1, got {df}")
    return _T_TABLE_95.get(df, _Z_95)


@dataclass
class ConfidenceInterval:
    n: int
    mean: float
    stddev: float
    low: float
    high: float
    verdict: str  # 'PASS' | 'WARN:thin' -- wspy-summary's own n<3 thin threshold


def confidence_interval(values: list[float]) -> ConfidenceInterval:
    """95% CI of the mean, wspy-summary's own formula (see module docstring).
    Raises on an empty list -- there's no meaningful "confidence interval of
    nothing," and every caller here always has at least one measured trial by the
    time it calls this.
    """
    n = len(values)
    if n == 0:
        raise ValueError("confidence_interval() needs at least one value")
    mean = sum(values) / n
    if n < 2:
        stddev = 0.0
        margin = 0.0
    else:
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        stddev = math.sqrt(variance)
        margin = _t_critical(n - 1) * stddev / math.sqrt(n)
    verdict = "PASS" if n >= 3 else "WARN:thin"
    return ConfidenceInterval(n=n, mean=mean, stddev=stddev, low=mean - margin, high=mean + margin, verdict=verdict)


def non_overlapping(a: ConfidenceInterval, b: ConfidenceInterval) -> bool:
    """True iff a's and b's 95% CIs don't overlap at all -- doc/DESIGN.md sec. 6
    Phase 4's accept bar ("the improvement's 95% CI doesn't overlap the
    baseline's"), not just a higher point estimate from a single run.
    """
    return a.high < b.low or b.high < a.low

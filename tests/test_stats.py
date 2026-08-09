import math

import pytest

from cfm.stats import _t_critical, confidence_interval, non_overlapping


def test_t_critical_matches_known_reference_values():
    # Standard two-tailed 95% Student's t table values, independently checkable
    # against any statistics reference -- not derived from this module.
    assert _t_critical(1) == 12.706
    assert _t_critical(2) == 4.303
    assert _t_critical(9) == 2.262
    assert _t_critical(30) == 2.042
    assert _t_critical(31) == 1.960  # beyond the table -> normal approximation
    assert _t_critical(1000) == 1.960


def test_t_critical_rejects_non_positive_df():
    with pytest.raises(ValueError):
        _t_critical(0)


def test_confidence_interval_raises_on_empty_list():
    with pytest.raises(ValueError):
        confidence_interval([])


def test_confidence_interval_n1_is_degenerate_at_the_mean():
    ci = confidence_interval([5.0])
    assert ci.n == 1
    assert ci.mean == 5.0
    assert ci.stddev == 0.0
    assert ci.low == ci.high == 5.0
    assert ci.verdict == "WARN:thin"


def test_confidence_interval_n2_matches_hand_computed_value():
    # mean=11, sample stddev (n-1 denominator) = sqrt(((10-11)^2+(12-11)^2)/1) = sqrt(2).
    # margin = t(df=1) * stddev/sqrt(n) = 12.706 * sqrt(2)/sqrt(2) = 12.706 exactly.
    ci = confidence_interval([10.0, 12.0])
    assert ci.n == 2
    assert ci.mean == pytest.approx(11.0)
    assert ci.stddev == pytest.approx(math.sqrt(2))
    assert ci.low == pytest.approx(11.0 - 12.706)
    assert ci.high == pytest.approx(11.0 + 12.706)
    assert ci.verdict == "WARN:thin"  # n<3, wspy-summary's own thin threshold


def test_confidence_interval_n3_matches_hand_computed_value():
    # mean=10, sample stddev = sqrt(((9-10)^2+0+(11-10)^2)/2) = 1.
    # margin = t(df=2) * 1/sqrt(3) = 4.303/sqrt(3).
    ci = confidence_interval([9.0, 10.0, 11.0])
    assert ci.n == 3
    assert ci.mean == pytest.approx(10.0)
    assert ci.stddev == pytest.approx(1.0)
    expected_margin = 4.303 / math.sqrt(3)
    assert ci.low == pytest.approx(10.0 - expected_margin)
    assert ci.high == pytest.approx(10.0 + expected_margin)
    assert ci.verdict == "PASS"


def test_confidence_interval_zero_variance_is_a_zero_width_ci_not_thin():
    ci = confidence_interval([5.0, 5.0, 5.0])
    assert ci.stddev == 0.0
    assert ci.low == ci.high == 5.0
    assert ci.verdict == "PASS"  # n>=3 -- legitimately zero variance, not "thin"


def test_non_overlapping_true_when_clearly_separated():
    baseline = confidence_interval([10.0, 10.0, 10.0])
    candidate = confidence_interval([20.0, 20.0, 20.0])
    assert non_overlapping(baseline, candidate) is True
    assert non_overlapping(candidate, baseline) is True  # symmetric


def test_non_overlapping_false_when_ranges_overlap():
    baseline = confidence_interval([10.0, 10.0, 10.0])
    candidate = confidence_interval([5.0, 10.0, 15.0])  # wide CI spanning baseline's mean
    assert non_overlapping(baseline, candidate) is False
    assert non_overlapping(candidate, baseline) is False

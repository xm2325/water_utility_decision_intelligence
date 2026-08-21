import pandas as pd
import pytest

from yw_decisioning.temporal_robustness import quarterly_policy_robustness, temporal_robustness_summary


def _daily():
    rows=[]
    for date in pd.date_range("2025-01-01", periods=180, freq="D"):
        total = 10.0
        for p, c in [("capacity_constrained", 8.0), ("highest_flow", 4.0), ("random", 1.0)]:
            rows.append({
                "DATE": date, "policy": p, "capacity": 20,
                "total_signal": total, "captured_signal": c,
                "candidate_count": 30, "selected_count": 20,
            })
    return pd.DataFrame(rows)


def test_quarterly_summary_preserves_frozen_policy_gaps():
    s, c = quarterly_policy_robustness(_daily())
    assert s["quarter"].nunique() == 2
    assert (c[c["comparison_policy"] == "highest_flow"]["capture_difference_pp"] == 40.0).all()


def test_temporal_summary_reports_all_quarters_reference_better():
    s, c = quarterly_policy_robustness(_daily())
    out = temporal_robustness_summary(s, c)
    assert out["comparisons"]["highest_flow"]["quarters_reference_better"] == 2
    assert out["comparisons"]["random"]["quarters_reference_better"] == 2


def test_partial_quarter_is_retained_with_observed_day_count():
    d = _daily()[lambda x: x["DATE"] <= pd.Timestamp("2025-01-15")]
    s, _ = quarterly_policy_robustness(d)
    ref = s[s["policy"] == "capacity_constrained"].iloc[0]
    assert ref["observed_days"] == 15


def test_missing_comparator_fails_explicitly():
    d = _daily()[lambda x: x["policy"] != "random"]
    with pytest.raises(ValueError, match="missing policies"):
        quarterly_policy_robustness(d)

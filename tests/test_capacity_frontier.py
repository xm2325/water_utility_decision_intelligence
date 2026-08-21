import pandas as pd
import pytest

from yw_decisioning.capacity_frontier import build_capacity_frontier


def _summary():
    return pd.DataFrame({
        "policy": ["capacity_constrained"] * 3,
        "capacity": [5, 10, 20],
        "mean_selected_per_day": [5.0, 10.0, 18.0],
        "signal_capture": [0.50, 0.70, 0.86],
        "candidate_recall": [0.10, 0.20, 0.36],
        "mean_backlog_candidates": [30.0, 25.0, 17.0],
        "capacity_utilisation": [1.0, 1.0, 0.9],
        "analyst_hours_per_day": [5/3, 10/3, 6.0],
    })


def test_capacity_frontier_uses_actual_reviews_for_marginal_gain():
    f = build_capacity_frontier(_summary())
    row = f[f["capacity"] == 20].iloc[0]
    assert row["delta_selected_per_day"] == 8.0
    assert row["delta_signal_capture_pp"] == pytest.approx(16.0)
    assert row["marginal_capture_pp_per_extra_review"] == pytest.approx(2.0)
    assert row["backlog_reduction_per_extra_review"] == pytest.approx(1.0)


def test_capacity_frontier_reports_unused_capacity():
    f = build_capacity_frontier(_summary())
    assert f.loc[f["capacity"] == 20, "unused_capacity_per_day"].iloc[0] == 2.0


def test_capacity_frontier_rejects_nonmonotonic_signal_capture():
    d = _summary()
    d.loc[d["capacity"] == 20, "signal_capture"] = 0.60
    with pytest.raises(ValueError, match="signal capture"):
        build_capacity_frontier(d)

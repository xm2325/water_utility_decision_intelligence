import pandas as pd

from yw_decisioning.decision_value import attach_champion_signal, add_policy_ranks, evaluate_policy_grid, selected_mask
from yw_decisioning.decision_diagnostics import queue_stability


def _predictions():
    rows = []
    for day in pd.date_range("2026-01-01", periods=3, freq="D"):
        for i, dma in enumerate(["A", "B", "C", "D"]):
            excess = [4.0, 2.0, 0.0, 0.0][i]
            rows.append({
                "DATE": day,
                "DMA_ID": dma,
                "target": [9.0, 7.0, 12.0, 3.0][i],
                "simple_baseline_name": "persistence",
                "simple_baseline_upper_exceedance": excess > 0,
                "simple_baseline_anomaly_excess": excess,
                "simple_baseline_investigation_score": excess,
                "ml_upper_exceedance": False,
                "ml_anomaly_excess": 0.0,
                "ml_investigation_score": 0.0,
                "persistence_upper_exceedance": excess > 0,
                "persistence_anomaly_excess": excess,
                "persistence_investigation_score": excess,
            })
    return pd.DataFrame(rows)


def _ranked():
    d = attach_champion_signal(_predictions(), {"champion": "simple_baseline", "baseline_name": "persistence"})
    return add_policy_ranks(d)


def test_champion_signal_uses_frozen_simple_baseline():
    d = attach_champion_signal(_predictions(), {"champion": "simple_baseline"})
    assert d["candidate"].sum() == 6
    assert d["champion_anomaly_excess"].sum() == 18.0


def test_capacity_constrained_never_fills_with_non_candidates():
    d = _ranked()
    selected = d[selected_mask(d, "capacity_constrained", 3)]
    assert len(selected) == 6
    assert selected["candidate"].all()


def test_anomaly_score_fills_capacity_when_rows_exist():
    d = _ranked()
    selected = d[selected_mask(d, "anomaly_score", 3)]
    assert len(selected) == 9
    assert selected.groupby("DATE").size().eq(3).all()


def test_deterministic_random_ranking_is_repeatable():
    a = add_policy_ranks(attach_champion_signal(_predictions(), {"champion": "simple_baseline"}))
    b = add_policy_ranks(attach_champion_signal(_predictions().sample(frac=1, random_state=3), {"champion": "simple_baseline"}))
    ra = a.set_index(["DATE", "DMA_ID"])["rank_random"].sort_index()
    rb = b.set_index(["DATE", "DMA_ID"])["rank_random"].sort_index()
    pd.testing.assert_series_equal(ra, rb)


def test_constrained_signal_capture_is_monotone_with_capacity():
    d = _ranked()
    summary, _ = evaluate_policy_grid(d, capacities=(1, 2, 3))
    vals = summary[summary["policy"] == "capacity_constrained"].sort_values("capacity")["signal_capture"].tolist()
    assert vals == sorted(vals)
    assert vals[-1] == 1.0


def test_queue_stability_reports_identical_daily_queue_as_one():
    d = _ranked()
    stable = queue_stability(d, capacities=(1,))
    row = stable[stable["policy"] == "capacity_constrained"].iloc[0]
    assert row["mean_consecutive_day_jaccard"] == 1.0
    assert row["mean_previous_queue_retention"] == 1.0

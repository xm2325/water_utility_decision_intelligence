import pandas as pd

from yw_decisioning.continuity import continuity_queue, continuity_sensitivity


def _frame():
    rows = []
    values = {
        "2026-01-01": [("A", 5), ("B", 4), ("C", 3), ("D", 0)],
        "2026-01-02": [("A", 1), ("B", 5), ("C", 0), ("D", 4)],
        "2026-01-03": [("A", 0), ("B", 3), ("C", 5), ("D", 4)],
    }
    for day, vals in values.items():
        for dma, excess in vals:
            rows.append({
                "DATE": pd.Timestamp(day),
                "DMA_ID": dma,
                "candidate": excess > 0,
                "champion_anomaly_excess": float(excess),
                "champion_investigation_score": float(excess),
            })
    return pd.DataFrame(rows)


def test_zero_continuity_matches_current_score_top_k():
    q = continuity_queue(_frame(), capacity=2, carryover_fraction=0)
    first = q[q["queue_date"] == pd.Timestamp("2026-01-01")]["DMA_ID"].tolist()
    second = q[q["queue_date"] == pd.Timestamp("2026-01-02")]["DMA_ID"].tolist()
    assert first == ["A", "B"]
    assert second == ["B", "D"]


def test_continuity_never_retains_non_candidate():
    q = continuity_queue(_frame(), capacity=2, carryover_fraction=0.5)
    day3 = q[q["queue_date"] == pd.Timestamp("2026-01-03")]
    assert "A" not in set(day3["DMA_ID"])
    assert day3["candidate"].all()


def test_continuity_reserve_is_maximum_not_quota():
    q = continuity_queue(_frame(), capacity=3, carryover_fraction=1.0)
    day2 = q[q["queue_date"] == pd.Timestamp("2026-01-02")]
    assert len(day2) == 3
    assert set(day2["DMA_ID"]) == {"A", "B", "D"}


def test_sensitivity_zero_has_no_signal_cost():
    summary, _ = continuity_sensitivity(_frame(), capacity=2, carryover_fractions=(0, 0.5))
    zero = summary[summary["carryover_fraction"] == 0].iloc[0]
    assert zero["signal_capture_cost_pp_vs_zero"] == 0
    assert summary["candidate_precision"].eq(1).all()

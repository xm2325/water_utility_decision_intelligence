import pandas as pd

from yw_decisioning.resource_watch import build_resource_watch


def test_resource_watch_uses_same_month_history_and_transparent_flags():
    df = pd.DataFrame(
        [
            {"year": 2023, "month": "July", "month_num": 7, "reservoir_pct": 78, "demand_ml_day": 1285.5, "rainfall_provisional_pct_lta": None},
            {"year": 2024, "month": "July", "month_num": 7, "reservoir_pct": 68, "demand_ml_day": 1338.8, "rainfall_provisional_pct_lta": None},
            {"year": 2025, "month": "July", "month_num": 7, "reservoir_pct": 47, "demand_ml_day": 1290.1, "rainfall_provisional_pct_lta": 102},
            {"year": 2026, "month": "July", "month_num": 7, "reservoir_pct": 65, "demand_ml_day": 1382, "rainfall_provisional_pct_lta": 19.4},
        ]
    )
    out = build_resource_watch(df)
    row = out.iloc[0]
    assert row["reservoir_hist_median_pct"] == 68
    assert row["reservoir_vs_hist_median_pp"] == -3
    assert bool(row["demand_above_hist_max"])
    assert bool(row["rainfall_pressure"])
    assert int(row["active_watch_signals"]) == 3

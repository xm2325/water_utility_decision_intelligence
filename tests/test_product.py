import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.product import build_operational_store  # noqa: E402


def test_build_operational_store_creates_apr_view(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    pd.DataFrame(
        {
            "rag_reference": ["3A.1", "3A.2"],
            "line_description": ["A", "B"],
            "pcl_met": ["No", "Yes"],
            "payment_m": [-3.0, 1.0],
            "underperformance_exposure_m": [3.0, 0.0],
            "exposure_share": [1.0, 0.0],
        }
    ).to_csv(results / "common_pc_portfolio_2025_26.csv", index=False)
    db = tmp_path / "product.sqlite"
    info = build_operational_store(results, db)
    assert info["tables"]["apr_common_pc_portfolio"] == 2
    with sqlite3.connect(db) as con:
        rows = con.execute("SELECT line_description FROM v_apr_negative_payment_priority").fetchall()
    assert rows == [("A",)]


def test_build_operational_store_creates_continuity_frontier(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    pd.DataFrame(
        {
            "carryover_fraction": [0.0, 0.25],
            "signal_capture": [0.85, 0.84],
            "signal_capture_cost_pp_vs_zero": [0.0, 1.0],
            "mean_consecutive_day_jaccard": [0.03, 0.05],
            "mean_previous_queue_retention": [0.05, 0.09],
            "mean_continuity_selected_per_day": [0.0, 1.8],
            "selection_hhi": [0.004, 0.0041],
        }
    ).to_csv(results / "nightflow_continuity_sensitivity.csv", index=False)
    db = tmp_path / "product.sqlite"
    build_operational_store(results, db)
    with sqlite3.connect(db) as con:
        rows = con.execute(
            "SELECT carryover_fraction, signal_capture FROM v_nightflow_continuity_frontier ORDER BY carryover_fraction"
        ).fetchall()
    assert rows == [(0.0, 0.85), (0.25, 0.84)]


def test_build_operational_store_creates_capacity_marginal_view(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    pd.DataFrame({
        "policy": ["capacity_constrained", "capacity_constrained"],
        "capacity": [5, 10], "previous_capacity": [None, 5],
        "mean_selected_per_day": [5.0, 10.0], "signal_capture": [0.5, 0.7],
        "candidate_recall": [0.1, 0.2], "mean_backlog_candidates": [30.0, 25.0],
        "capacity_utilisation": [1.0, 1.0], "analyst_hours_per_day": [1.67, 3.33],
        "unused_capacity_per_day": [0.0, 0.0], "delta_nominal_capacity": [None, 5],
        "delta_selected_per_day": [None, 5.0], "delta_signal_capture_pp": [None, 20.0],
        "marginal_capture_pp_per_extra_review": [None, 4.0],
        "backlog_reduction_per_day": [None, 5.0],
        "backlog_reduction_per_extra_review": [None, 1.0],
        "incremental_analyst_hours_per_day": [None, 1.66], "unretained_signal_pct": [50.0, 30.0],
    }).to_csv(results / "nightflow_capacity_frontier.csv", index=False)
    db = tmp_path / "product.sqlite"
    build_operational_store(results, db)
    with sqlite3.connect(db) as con:
        rows = con.execute("SELECT capacity, marginal_capture_pp_per_extra_review FROM v_nightflow_capacity_marginal_value ORDER BY capacity").fetchall()
    assert rows[1] == (10, 4.0)


def test_product_publishes_temporal_robustness_view(tmp_path):
    import sqlite3
    import pandas as pd
    from yw_decisioning.product import build_operational_store

    results = tmp_path / "results"
    results.mkdir()
    pd.DataFrame([
        {"quarter": "2025Q1", "policy": "capacity_constrained", "observed_days": 90,
         "total_signal": 10.0, "captured_signal": 8.0, "selected_reviews": 100,
         "candidate_alerts": 200, "signal_capture": 0.8, "mean_selected_per_day": 1.1,
         "mean_candidates_per_day": 2.2, "candidate_recall": 0.5}
    ]).to_csv(results / "nightflow_policy_quarterly_summary.csv", index=False)
    db = tmp_path / "product.sqlite"
    build_operational_store(results, db)
    with sqlite3.connect(db) as con:
        row = con.execute("SELECT quarter, signal_capture FROM v_nightflow_temporal_robustness").fetchone()
    assert row == ("2025Q1", 0.8)

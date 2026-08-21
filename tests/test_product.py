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

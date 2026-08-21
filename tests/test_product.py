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

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.edm import reconcile_apr_spills  # noqa: E402


def test_reconciliation_surfaces_mismatch_without_overwrite():
    apr = pd.DataFrame({"year": ["2023-24", "2024-25", "2025-26"], "spills": [77761, 68164, 51560]})
    edm = pd.DataFrame(
        {
            "year": [2023, 2024, 2025],
            "total_discharges": [77761, 68164, 51404],
            "storm_overflows_with_data": [2167, 2171, 2176],
            "total_duration_hours": [516386, 430263, 285230],
            "source_url": ["official"] * 3,
            "retrieved_date": ["2026-08-21"] * 3,
        }
    )
    table, metrics = reconcile_apr_spills(apr, edm)
    assert metrics["matched_years"] == 2
    assert metrics["years_requiring_review"] == [2025]
    row = table[table["calendar_year"] == 2025].iloc[0]
    assert row["apr_total_discharges"] == 51560
    assert row["edm_total_discharges"] == 51404
    assert row["absolute_difference"] == -156
    assert row["review_status"] == "review"

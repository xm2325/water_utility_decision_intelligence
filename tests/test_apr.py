import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.apr import extract_common_pc_portfolio, capacity_curve


def test_portfolio_exposure_and_sorting():
    df = pd.DataFrame({
        "rag_reference": ["3A.1", "3A.1", "3A.2", "3A.2"],
        "line_description": ["A", "A", "B", "B"],
        "units": ["x", "x", "x", "x"],
        "attribute": ["Outperformance or underperformance payment", "PCL met? (Yes/No)", "Outperformance or underperformance payment", "PCL met? (Yes/No)"],
        "value": ["-4", "No", "2", "Yes"],
    })
    p = extract_common_pc_portfolio(df)
    assert p.iloc[0]["line_description"] == "A"
    assert p.iloc[0]["underperformance_exposure_m"] == 4
    assert p.iloc[1]["underperformance_exposure_m"] == 0


def test_capacity_curve_is_monotone():
    p = pd.DataFrame({
        "underperformance_exposure_m": [4.0, 3.0, 1.0],
        "line_description": ["A", "B", "C"],
        "rag_reference": ["3A.1", "3A.2", "3A.3"],
    })
    c = capacity_curve(p)
    assert list(c["observed_exposure_share"]) == [0.5, 0.875, 1.0]

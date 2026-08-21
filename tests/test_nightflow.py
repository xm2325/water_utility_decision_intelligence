import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.nightflow import (  # noqa: E402
    PromotionPolicy,
    collapse_duplicate_dma_dates,
    data_quality_report,
    latest_investigation_priorities,
    make_features,
    promotion_decision,
    rolling_origin_backtest,
)


def synthetic_nightflow(days: int = 220, dmas: int = 4):
    rng = np.random.default_rng(7)
    rows = []
    dates = pd.date_range("2025-01-01", periods=days, freq="D")
    for dma_i in range(dmas):
        dma = f"A{dma_i+1:03d}"
        level = 20 + 4 * dma_i
        previous = level
        for t, date in enumerate(dates):
            seasonal = 1.5 * np.sin(2 * np.pi * t / 30)
            # AR-like signal makes lagged history informative.
            actual = 0.72 * previous + 0.28 * (level + seasonal) + rng.normal(0, 0.35)
            if t in {170, 205} and dma_i == 0:
                actual += 5.0
            rows.append(
                {
                    "DATE": date,
                    "DMA_ID": dma,
                    "ACTUAL_MIN_NIGHT_FLOW": actual,
                    "MIN_NIGHT_FLOW": level - 1,
                    "CENTROID_X": 430000 + 1000 * dma_i,
                    "CENTROID_Y": 430000 + 500 * dma_i,
                    "UNITS": "l/s",
                }
            )
            previous = actual
    return pd.DataFrame(rows)


def test_target_and_persistence_alignment_is_one_step_ahead():
    raw = synthetic_nightflow(days=50, dmas=1)
    d = make_features(raw)
    row = d.iloc[0]
    original = raw.sort_values("DATE").reset_index(drop=True)
    target_date = row["DATE"]
    idx = int(original.index[original["DATE"] == target_date][0])
    assert np.isclose(row["target"], original.loc[idx, "ACTUAL_MIN_NIGHT_FLOW"])
    assert np.isclose(row["lag1"], original.loc[idx - 1, "ACTUAL_MIN_NIGHT_FLOW"])


def test_duplicate_dma_dates_are_consolidated():
    raw = synthetic_nightflow(days=40, dmas=1)
    dup = pd.concat([raw, raw.iloc[[10]]], ignore_index=True)
    out = collapse_duplicate_dma_dates(dup)
    assert len(out) == len(raw)
    r = out[out["DATE"] == raw.iloc[10]["DATE"]].iloc[0]
    assert r["duplicate_rows_same_dma_date"] == 2


def test_quality_report_records_duplicates_and_dma_coverage():
    raw = synthetic_nightflow(days=40, dmas=2)
    raw = pd.concat([raw, raw.iloc[[10]]], ignore_index=True)
    summary, per_dma = data_quality_report(raw)
    assert summary["unique_dmas"] == 2
    assert summary["duplicate_key_excess_rows"] == 1
    assert len(per_dma) == 2


def test_rolling_backtest_has_strict_time_order_and_outputs_uncertainty():
    pred, folds, drift, summary = rolling_origin_backtest(
        synthetic_nightflow(), n_splits=3, min_train_fraction=0.55
    )
    assert len(folds) == 3
    assert summary["test_rows_total"] == len(pred)
    assert {"prediction", "persistence", "simple_baseline", "simple_baseline_name", "upper_band", "upper_exceedance"}.issubset(pred.columns)
    assert set(folds["selected_baseline"]).issubset({"persistence", "seasonal_7d", "rolling_28d_median"})
    for _, r in folds.iterrows():
        assert pd.Timestamp(r["train_end"]) < pd.Timestamp(r["test_start"])
    assert {"feature", "standardised_mean_difference", "drift_flag"}.issubset(drift.columns)


def test_latest_priorities_respect_capacity():
    pred, _, _, _ = rolling_origin_backtest(synthetic_nightflow(), n_splits=2)
    p = latest_investigation_priorities(pred, capacity=2)
    assert p["within_capacity"].sum() <= 2
    assert not ((p["within_capacity"]) & (~p["upper_exceedance"])).any()
    assert p["priority_rank"].is_monotonic_increasing


def test_promotion_gate_can_retain_baseline():
    folds = pd.DataFrame({"relative_mae_improvement": [0.01, -0.10]})
    summary = {"relative_mae_improvement": 0.01, "upper_band_coverage": 0.90}
    decision = promotion_decision(folds, summary, PromotionPolicy())
    assert decision["status"] == "retain_simple_baseline"


def test_calendar_windows_do_not_treat_irregular_rows_as_days():
    raw = synthetic_nightflow(days=20, dmas=1).copy()
    # Remove several dates so seven observations no longer means seven calendar days.
    raw = raw[~raw["DATE"].isin(pd.to_datetime(["2025-01-04", "2025-01-05", "2025-01-08"]))].copy()
    d = make_features(raw)
    row = d[d["DATE"] == pd.Timestamp("2025-01-15")].iloc[0]
    hist = raw[raw["DATE"] <= pd.Timestamp("2025-01-08")].sort_values("DATE")
    expected = hist.iloc[-1]["ACTUAL_MIN_NIGHT_FLOW"]
    assert np.isclose(row["lag7d"], expected)
    # Jan 8 is absent, so the source must be older than the nominal t-7 date.
    assert row["lag7d_staleness_days"] > 0


def test_baseline_champion_controls_operational_queue():
    pred, folds, _, summary = rolling_origin_backtest(synthetic_nightflow(), n_splits=2)
    # Force a baseline decision while leaving the prediction table untouched.
    forced = dict(summary)
    forced["relative_mae_improvement"] = -0.01
    decision = promotion_decision(folds, forced, PromotionPolicy())
    assert decision["champion"] == "simple_baseline"
    p = latest_investigation_priorities(pred, capacity=2, champion=decision["champion"])
    latest = pred[pred["DATE"] == pred["DATE"].max()].set_index("DMA_ID")
    assert p["champion_model"].str.startswith("simple_baseline:").all()
    assert np.allclose(p["expected_flow"], latest.loc[p["DMA_ID"], "simple_baseline"].to_numpy())
    assert (p["upper_exceedance"] == p["champion_upper_exceedance"]).all()



def test_simple_baseline_is_selected_before_test_block():
    pred, folds, _, summary = rolling_origin_backtest(synthetic_nightflow(), n_splits=3)
    assert "selected_baseline" in folds.columns
    assert "mae_selected_baseline" in folds.columns
    assert "relative_mae_improvement_vs_persistence" in folds.columns
    assert summary["latest_selected_baseline"] in {"persistence", "seasonal_7d", "rolling_28d_median"}
    # The selected baseline name is fixed within each held-out fold.
    for fold, g in pred.groupby("fold"):
        expected = folds.loc[folds["fold"] == fold, "selected_baseline"].iloc[0]
        assert g["simple_baseline_name"].nunique() == 1
        assert g["simple_baseline_name"].iloc[0] == expected

def test_data_contract_fails_on_material_missingness():
    from yw_decisioning.nightflow import assess_data_contract

    raw = synthetic_nightflow(days=120, dmas=4)
    raw.loc[raw.index[:100], "MIN_NIGHT_FLOW"] = np.nan
    summary, _ = data_quality_report(raw)
    contract = assess_data_contract(summary)
    assert contract["passed"] is True  # 100 / 480 = 20.8%, below the 50% limit
    raw.loc[raw.index[:300], "MIN_NIGHT_FLOW"] = np.nan
    summary2, _ = data_quality_report(raw)
    contract2 = assess_data_contract(summary2)
    assert contract2["passed"] is False
    assert contract2["checks"]["reference_missingness"] is False

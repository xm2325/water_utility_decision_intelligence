from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd

from .nightflow_data import DataContractPolicy, PromotionPolicy, STATIC_COLUMNS, assess_data_contract
from .nightflow_model import per_dma_performance, promotion_decision, rolling_origin_backtest


def latest_investigation_priorities(
    predictions: pd.DataFrame,
    capacity: int = 20,
    champion: str = "hist_gradient_boosting",
) -> pd.DataFrame:
    """Rank latest observed DMA anomalies using the deployed champion."""

    if capacity < 1:
        raise ValueError("capacity must be positive")
    if champion not in {"hist_gradient_boosting", "persistence_baseline"}:
        raise ValueError(f"Unsupported champion: {champion}")

    d = predictions.copy()
    latest = d["DATE"].max()
    s = d[d["DATE"] == latest].copy()

    if champion == "hist_gradient_boosting":
        s["expected_flow"] = s["prediction"]
        s["champion_upper_band"] = s["ml_upper_band"]
        s["champion_upper_exceedance"] = s["ml_upper_exceedance"]
        s["champion_anomaly_excess"] = s["ml_anomaly_excess"]
        s["champion_investigation_score"] = s["ml_investigation_score"]
        s["champion_residual_z"] = s["residual_z"]
    else:
        s["expected_flow"] = s["persistence"]
        s["champion_upper_band"] = s["persistence_upper_band"]
        s["champion_upper_exceedance"] = s["persistence_upper_exceedance"]
        s["champion_anomaly_excess"] = s["persistence_anomaly_excess"]
        s["champion_investigation_score"] = s["persistence_investigation_score"]
        s["champion_residual_z"] = s["persistence_residual_z"]

    s["champion_model"] = champion
    # Compatibility aliases now refer to the deployed champion rather than always to ML.
    s["upper_band"] = s["champion_upper_band"]
    s["upper_exceedance"] = s["champion_upper_exceedance"]
    s["anomaly_excess"] = s["champion_anomaly_excess"]
    s["investigation_score"] = s["champion_investigation_score"]
    s = s.sort_values(
        ["champion_upper_exceedance", "champion_investigation_score", "champion_anomaly_excess", "champion_residual_z"],
        ascending=[False, False, False, False],
    )
    s["priority_rank"] = np.arange(1, len(s) + 1)
    s["within_capacity"] = s["champion_upper_exceedance"] & (s["priority_rank"] <= capacity)

    cols = [
        "DATE",
        "DMA_ID",
        "champion_model",
        "priority_rank",
        "within_capacity",
        "target",
        "expected_flow",
        "champion_upper_band",
        "champion_upper_exceedance",
        "champion_anomaly_excess",
        "champion_investigation_score",
        "champion_residual_z",
        "upper_band",
        "upper_exceedance",
        "anomaly_excess",
        "investigation_score",
        "rolling28d_std",
        "history_count",
    ]
    for c in STATIC_COLUMNS:
        if c in s.columns:
            cols.append(c)
    return s[cols].reset_index(drop=True)


def save_backtest(
    predictions: pd.DataFrame,
    folds: pd.DataFrame,
    drift: pd.DataFrame,
    summary: dict,
    output_dir: str | Path,
    *,
    quality_summary: dict | None = None,
    quality_by_dma: pd.DataFrame | None = None,
    policy: PromotionPolicy | None = None,
    data_contract_policy: DataContractPolicy | None = None,
    capacity: int = 20,
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    predictions.to_csv(out / "nightflow_backtest_predictions.csv", index=False)
    folds.to_csv(out / "nightflow_fold_metrics.csv", index=False)
    drift.to_csv(out / "nightflow_drift_report.csv", index=False)

    dma_perf = per_dma_performance(predictions)
    dma_perf.to_csv(out / "nightflow_dma_performance.csv", index=False)

    contract = assess_data_contract(quality_summary, data_contract_policy) if quality_summary is not None else None
    decision = promotion_decision(folds, summary, policy, data_contract=contract)
    priorities = latest_investigation_priorities(
        predictions,
        capacity=capacity,
        champion=decision["champion"],
    )
    priorities.to_csv(out / "nightflow_latest_priorities.csv", index=False)

    payload = dict(summary)
    payload["promotion_decision"] = decision
    if quality_summary is not None:
        payload["data_quality"] = quality_summary
    if contract is not None:
        payload["data_contract"] = contract
    with open(out / "nightflow_backtest_metrics.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    with open(out / "nightflow_promotion_decision.json", "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    if contract is not None:
        with open(out / "nightflow_data_contract.json", "w", encoding="utf-8") as f:
            json.dump(contract, f, indent=2)

    if quality_by_dma is not None:
        quality_by_dma.to_csv(out / "nightflow_data_quality_by_dma.csv", index=False)
    if quality_summary is not None:
        with open(out / "nightflow_data_quality_summary.json", "w", encoding="utf-8") as f:
            json.dump(quality_summary, f, indent=2)

    return decision


# Backward-compatible wrapper used by older callers/tests.
def temporal_backtest(df: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, dict]:
    pred, _folds, _drift, summary = rolling_origin_backtest(
        df,
        n_splits=1,
        min_train_fraction=max(0.5, 1 - test_fraction),
    )
    return pred, summary

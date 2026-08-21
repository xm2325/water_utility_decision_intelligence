from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, median_absolute_error
from sklearn.pipeline import Pipeline

from .nightflow_data import PromotionPolicy, feature_columns, make_features


def build_model() -> Pipeline:
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            (
                "model",
                HistGradientBoostingRegressor(
                    loss="absolute_error",
                    learning_rate=0.05,
                    max_iter=300,
                    max_leaf_nodes=31,
                    min_samples_leaf=20,
                    l2_regularization=0.2,
                    random_state=42,
                ),
            ),
        ]
    )


def _split_train_calibration(train: pd.DataFrame, fraction: float = 0.15) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = np.array(sorted(pd.to_datetime(train["DATE"]).unique()))
    if len(dates) < 20:
        return train.iloc[0:0].copy(), train.copy()
    cut = max(1, int(len(dates) * (1 - fraction)))
    cut = min(cut, len(dates) - 1)
    cal_start = pd.Timestamp(dates[cut])
    return train[train["DATE"] < cal_start].copy(), train[train["DATE"] >= cal_start].copy()


def _drift_table(train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows = []
    for c in features:
        a = pd.to_numeric(train[c], errors="coerce")
        b = pd.to_numeric(test[c], errors="coerce")
        pooled = np.sqrt((a.var(ddof=0) + b.var(ddof=0)) / 2)
        smd = (b.mean() - a.mean()) / pooled if pooled and np.isfinite(pooled) else np.nan
        rows.append(
            {
                "feature": c,
                "train_mean": float(a.mean()) if a.notna().any() else np.nan,
                "test_mean": float(b.mean()) if b.notna().any() else np.nan,
                "standardised_mean_difference": float(smd) if np.isfinite(smd) else np.nan,
                "train_missing_rate": float(a.isna().mean()),
                "test_missing_rate": float(b.isna().mean()),
                "missing_rate_delta": float(b.isna().mean() - a.isna().mean()),
            }
        )
    out = pd.DataFrame(rows)
    out["drift_flag"] = (
        out["standardised_mean_difference"].abs().fillna(0) >= 0.25
    ) | (out["missing_rate_delta"].abs() >= 0.10)
    return out


def per_dma_performance(predictions: pd.DataFrame, min_rows: int = 10) -> pd.DataFrame:
    """Measure whether aggregate improvement is shared across DMAs."""

    rows: list[dict] = []
    for dma, g in predictions.groupby("DMA_ID", sort=False):
        if len(g) < min_rows:
            continue
        mae_model = mean_absolute_error(g["target"], g["prediction"])
        mae_base = mean_absolute_error(g["target"], g["persistence"])
        rel = (mae_base - mae_model) / mae_base if mae_base else np.nan
        rows.append(
            {
                "DMA_ID": dma,
                "test_rows": int(len(g)),
                "mae_model": float(mae_model),
                "mae_persistence": float(mae_base),
                "relative_mae_improvement": float(rel) if np.isfinite(rel) else np.nan,
                "model_better": bool(np.isfinite(rel) and rel > 0),
                "mean_model_error": float((g["target"] - g["prediction"]).mean()),
                "mean_persistence_error": float((g["target"] - g["persistence"]).mean()),
            }
        )
    if not rows:
        return pd.DataFrame(
            columns=[
                "DMA_ID",
                "test_rows",
                "mae_model",
                "mae_persistence",
                "relative_mae_improvement",
                "model_better",
                "mean_model_error",
                "mean_persistence_error",
            ]
        )
    return pd.DataFrame(rows).sort_values(["relative_mae_improvement", "DMA_ID"], ascending=[True, True])


def rolling_origin_backtest(
    df: pd.DataFrame,
    n_splits: int = 4,
    min_train_fraction: float = 0.50,
    calibration_fraction: float = 0.15,
    upper_quantile: float = 0.90,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Expanding-window backtest with fair persistence and model bands."""

    d = make_features(df)
    dates = np.array(sorted(pd.to_datetime(d["DATE"]).unique()))
    if len(dates) < 30:
        raise ValueError("Not enough unique dates for rolling-origin backtest")
    if not (1 <= n_splits <= 10):
        raise ValueError("n_splits must be between 1 and 10")

    first_test = max(10, int(len(dates) * min_train_fraction))
    remaining = len(dates) - first_test
    if remaining < n_splits:
        raise ValueError("Not enough dates after initial training window")
    block = max(1, remaining // n_splits)

    features = feature_columns(d)
    predictions: list[pd.DataFrame] = []
    fold_rows: list[dict] = []
    drift_rows: list[pd.DataFrame] = []

    for fold in range(n_splits):
        test_start_idx = first_test + fold * block
        test_end_idx = len(dates) if fold == n_splits - 1 else min(len(dates), test_start_idx + block)
        test_dates = dates[test_start_idx:test_end_idx]
        if len(test_dates) == 0:
            continue

        test_start = pd.Timestamp(test_dates[0])
        test_end = pd.Timestamp(test_dates[-1])
        train_all = d[d["DATE"] < test_start].copy()
        test = d[(d["DATE"] >= test_start) & (d["DATE"] <= test_end)].copy()

        if len(train_all) < 100 or len(test) < 20:
            continue

        train_model, calibration = _split_train_calibration(train_all, calibration_fraction)
        if len(train_model) < 80 or len(calibration) < 20:
            train_model = train_all.copy()
            calibration = train_all.iloc[0:0].copy()

        model = build_model()
        model.fit(train_model[features], train_model["target"])

        if len(calibration):
            cal_model_pred = model.predict(calibration[features])
            cal_model_resid = calibration["target"].to_numpy() - cal_model_pred
            cal_base_resid = calibration["target"].to_numpy() - calibration["lag1"].to_numpy()
            ml_upper_residual_q = float(np.quantile(cal_model_resid, upper_quantile, method="higher"))
            persistence_upper_residual_q = float(np.quantile(cal_base_resid, upper_quantile, method="higher"))
        else:
            ml_upper_residual_q = 0.0
            persistence_upper_residual_q = 0.0

        test["prediction"] = model.predict(test[features])
        test["persistence"] = test["lag1"]
        test["residual"] = test["target"] - test["prediction"]
        test["persistence_residual"] = test["target"] - test["persistence"]

        scale = test["rolling28d_std"].replace(0, np.nan)
        fallback_scale = float(np.nanmedian(scale)) if scale.notna().any() else 1.0
        scale = scale.fillna(fallback_scale if fallback_scale > 0 else 1.0)
        test["residual_z"] = test["residual"] / scale
        test["persistence_residual_z"] = test["persistence_residual"] / scale

        test["ml_upper_band"] = test["prediction"] + ml_upper_residual_q
        test["persistence_upper_band"] = test["persistence"] + persistence_upper_residual_q
        test["ml_upper_exceedance"] = test["target"] > test["ml_upper_band"]
        test["persistence_upper_exceedance"] = test["target"] > test["persistence_upper_band"]
        test["ml_anomaly_excess"] = (test["target"] - test["ml_upper_band"]).clip(lower=0)
        test["persistence_anomaly_excess"] = (test["target"] - test["persistence_upper_band"]).clip(lower=0)
        test["ml_investigation_score"] = test["ml_anomaly_excess"] / scale
        test["persistence_investigation_score"] = test["persistence_anomaly_excess"] / scale

        # Backward-compatible aliases refer to the challenger ML model only.
        test["upper_band"] = test["ml_upper_band"]
        test["upper_exceedance"] = test["ml_upper_exceedance"]
        test["anomaly_excess"] = test["ml_anomaly_excess"]
        test["investigation_score"] = test["ml_investigation_score"]
        test["fold"] = fold + 1
        test["test_start"] = test_start
        test["test_end"] = test_end

        mae_model = mean_absolute_error(test["target"], test["prediction"])
        mae_base = mean_absolute_error(test["target"], test["persistence"])
        rel = (mae_base - mae_model) / mae_base if mae_base else np.nan
        fold_rows.append(
            {
                "fold": fold + 1,
                "train_rows": int(len(train_model)),
                "calibration_rows": int(len(calibration)),
                "test_rows": int(len(test)),
                "train_end": str(train_model["DATE"].max().date()),
                "test_start": str(test_start.date()),
                "test_end": str(test_end.date()),
                "mae_model": float(mae_model),
                "mae_persistence": float(mae_base),
                "relative_mae_improvement": float(rel),
                "median_ae_model": float(median_absolute_error(test["target"], test["prediction"])),
                "median_ae_persistence": float(median_absolute_error(test["target"], test["persistence"])),
                "upper_band_quantile": upper_quantile,
                "ml_upper_residual_q": ml_upper_residual_q,
                "persistence_upper_residual_q": persistence_upper_residual_q,
                "ml_upper_band_coverage": float((test["target"] <= test["ml_upper_band"]).mean()),
                "persistence_upper_band_coverage": float((test["target"] <= test["persistence_upper_band"]).mean()),
                "ml_upper_exceedance_rate": float(test["ml_upper_exceedance"].mean()),
                "persistence_upper_exceedance_rate": float(test["persistence_upper_exceedance"].mean()),
            }
        )

        drift = _drift_table(train_model, test, features)
        drift["fold"] = fold + 1
        drift_rows.append(drift)
        predictions.append(test)

    if not predictions:
        raise ValueError("No valid rolling-origin folds were produced")

    pred = pd.concat(predictions, ignore_index=True)
    folds = pd.DataFrame(fold_rows)
    drift = pd.concat(drift_rows, ignore_index=True)
    dma = per_dma_performance(pred)

    mae_model = mean_absolute_error(pred["target"], pred["prediction"])
    mae_base = mean_absolute_error(pred["target"], pred["persistence"])
    dma_rel = dma["relative_mae_improvement"].dropna() if len(dma) else pd.Series(dtype=float)
    summary = {
        "rows_featured": int(len(d)),
        "test_rows_total": int(len(pred)),
        "folds": int(len(folds)),
        "date_min": str(d["DATE"].min().date()),
        "date_max": str(d["DATE"].max().date()),
        "mae_model": float(mae_model),
        "mae_persistence": float(mae_base),
        "relative_mae_improvement": float((mae_base - mae_model) / mae_base) if mae_base else None,
        "median_ae_model": float(median_absolute_error(pred["target"], pred["prediction"])),
        "median_ae_persistence": float(median_absolute_error(pred["target"], pred["persistence"])),
        "ml_upper_band_coverage": float((pred["target"] <= pred["ml_upper_band"]).mean()),
        "persistence_upper_band_coverage": float((pred["target"] <= pred["persistence_upper_band"]).mean()),
        "ml_upper_exceedance_rate": float(pred["ml_upper_exceedance"].mean()),
        "persistence_upper_exceedance_rate": float(pred["persistence_upper_exceedance"].mean()),
        "drift_features_flagged": int(drift.groupby("feature")["drift_flag"].max().sum()),
        "dmas_evaluated": int(len(dma)),
        "dma_share_model_better": float(dma["model_better"].mean()) if len(dma) else None,
        "dma_median_relative_mae_improvement": float(dma_rel.median()) if len(dma_rel) else None,
        "dma_p10_relative_mae_improvement": float(dma_rel.quantile(0.10)) if len(dma_rel) else None,
        "interpretation": "Positive band exceedances are investigation signals, not confirmed leak labels.",
    }
    # Backward-compatible summary keys refer to ML challenger band.
    summary["upper_band_coverage"] = summary["ml_upper_band_coverage"]
    summary["upper_exceedance_rate"] = summary["ml_upper_exceedance_rate"]
    return pred, folds, drift, summary


def promotion_decision(
    folds: pd.DataFrame,
    summary: dict,
    policy: PromotionPolicy | None = None,
    *,
    data_contract: dict | None = None,
) -> dict:
    policy = policy or PromotionPolicy()
    worst_rel = float(folds["relative_mae_improvement"].min())
    coverage = float(summary.get("ml_upper_band_coverage", summary.get("upper_band_coverage", np.nan)))
    # Older callers may not have DMA diagnostics; actual v0.4 runs always do.
    dma_share = summary.get("dma_share_model_better", 1.0)
    dma_p10 = summary.get("dma_p10_relative_mae_improvement", 0.0)

    checks = {
        "aggregate_mae_improvement": float(summary["relative_mae_improvement"] or -np.inf)
        >= policy.min_relative_mae_improvement,
        "worst_fold_not_materially_worse": worst_rel >= -policy.max_fold_relative_degradation,
        "ml_upper_band_coverage_in_range": policy.min_ml_upper_band_coverage
        <= coverage
        <= policy.max_ml_upper_band_coverage,
        "dma_majority_not_harmed": dma_share is not None and float(dma_share) >= policy.min_dma_share_improved,
        "dma_tail_not_materially_harmed": dma_p10 is not None and float(dma_p10) >= -policy.max_p10_dma_relative_degradation,
    }
    if data_contract is not None:
        checks["data_contract_passed"] = bool(data_contract.get("passed", False))

    promote = all(checks.values())
    return {
        "champion": "hist_gradient_boosting" if promote else "persistence_baseline",
        "status": "promote_ml" if promote else "retain_baseline",
        "checks": checks,
        "policy": asdict(policy),
        "observed": {
            "relative_mae_improvement": summary["relative_mae_improvement"],
            "worst_fold_relative_mae_improvement": worst_rel,
            "ml_upper_band_coverage": coverage,
            "dma_share_model_better": dma_share,
            "dma_p10_relative_mae_improvement": dma_p10,
        },
        "data_contract": data_contract,
        "reason": (
            "ML is selected only when it beats persistence by the configured margin, "
            "is stable across time and DMAs, has plausible uncertainty-band coverage, "
            "and the input data contract passes."
        ),
    }

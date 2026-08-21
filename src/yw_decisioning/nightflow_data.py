from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REQUIRED = {"DATE", "DMA_ID", "ACTUAL_MIN_NIGHT_FLOW", "MIN_NIGHT_FLOW"}
FLOW_COLUMNS = ["ACTUAL_MIN_NIGHT_FLOW", "MIN_NIGHT_FLOW"]
STATIC_COLUMNS = ["CENTROID_X", "CENTROID_Y"]


@dataclass(frozen=True)
class PromotionPolicy:
    """Conservative champion/challenger gate for operational use."""

    min_relative_mae_improvement: float = 0.02
    max_fold_relative_degradation: float = 0.05
    min_ml_upper_band_coverage: float = 0.85
    max_ml_upper_band_coverage: float = 0.97
    min_dma_share_improved: float = 0.50
    max_p10_dma_relative_degradation: float = 0.25


@dataclass(frozen=True)
class DataContractPolicy:
    """Minimum input quality checks before a model can be promoted."""

    min_unique_dmas: int = 3
    min_span_days: int = 90
    max_actual_flow_missing_rate: float = 0.10
    max_reference_flow_missing_rate: float = 0.50
    max_duplicate_key_rate: float = 0.02
    max_negative_actual_flow_rate: float = 0.01
    max_distinct_units: int = 1


def _parse_date(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, errors="coerce", unit="ms")
    return pd.to_datetime(series, errors="coerce")


def load_nightflow(paths: Iterable[str | Path]) -> pd.DataFrame:
    """Load Yorkshire Water night-flow exports and standardise core columns.

    Missing target values are retained at this stage so the data-quality report
    can measure them. Modelling rows are filtered later in ``make_features``.
    """

    frames: list[pd.DataFrame] = []
    for path in paths:
        path = Path(path)
        d = pd.read_csv(path, low_memory=False)
        missing = REQUIRED - set(d.columns)
        if missing:
            raise ValueError(f"{path} missing columns {sorted(missing)}")
        d = d.copy()
        d["source_file"] = path.name
        frames.append(d)

    if not frames:
        raise ValueError("No night-flow files supplied")

    df = pd.concat(frames, ignore_index=True)
    df["DATE"] = _parse_date(df["DATE"])
    df["DMA_ID"] = df["DMA_ID"].astype("string").str.strip()

    for c in FLOW_COLUMNS + STATIC_COLUMNS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "UNITS" in df.columns:
        df["UNITS"] = df["UNITS"].astype("string").str.strip()

    df = df.dropna(subset=["DATE", "DMA_ID"]).copy()
    return df.sort_values(["DMA_ID", "DATE", "source_file"]).reset_index(drop=True)


def collapse_duplicate_dma_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Consolidate duplicate DMA/date records with an explicit aggregation rule."""

    d = df.copy()
    aggregations: dict[str, str] = {
        "ACTUAL_MIN_NIGHT_FLOW": "median",
        "MIN_NIGHT_FLOW": "median",
    }
    for c in STATIC_COLUMNS:
        if c in d.columns:
            aggregations[c] = "median"
    for c in ["UNITS", "DATA_SOURCE", "source_file"]:
        if c in d.columns:
            aggregations[c] = "first"

    d["duplicate_rows_same_dma_date"] = d.groupby(["DMA_ID", "DATE"])["DMA_ID"].transform("size")
    aggregations["duplicate_rows_same_dma_date"] = "max"

    out = d.groupby(["DMA_ID", "DATE"], as_index=False).agg(aggregations)
    return out.sort_values(["DMA_ID", "DATE"]).reset_index(drop=True)


def data_quality_report(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Return portfolio-level and DMA-level data-quality diagnostics."""

    d = df.copy()
    raw_rows = len(d)
    valid_dates = int(d["DATE"].notna().sum())
    duplicate_rows = int(d.duplicated(["DMA_ID", "DATE"], keep=False).sum())
    duplicate_excess = int(d.duplicated(["DMA_ID", "DATE"]).sum())
    units = sorted(x for x in d.get("UNITS", pd.Series(dtype="string")).dropna().astype(str).unique())
    date_min = d["DATE"].min() if valid_dates else pd.NaT
    date_max = d["DATE"].max() if valid_dates else pd.NaT
    span_days = int((date_max - date_min).days) if pd.notna(date_min) and pd.notna(date_max) else 0

    summary = {
        "rows": int(raw_rows),
        "unique_dmas": int(d["DMA_ID"].nunique(dropna=True)),
        "date_min": str(date_min.date()) if pd.notna(date_min) else None,
        "date_max": str(date_max.date()) if pd.notna(date_max) else None,
        "span_days": span_days,
        "duplicate_rows_same_dma_date": duplicate_rows,
        "duplicate_key_excess_rows": duplicate_excess,
        "duplicate_key_rate": float(duplicate_excess / raw_rows) if raw_rows else 0.0,
        "actual_flow_missing_rate": float(d["ACTUAL_MIN_NIGHT_FLOW"].isna().mean()) if raw_rows else 0.0,
        "reference_flow_missing_rate": float(d["MIN_NIGHT_FLOW"].isna().mean()) if raw_rows else 0.0,
        "negative_actual_flow_rate": float((d["ACTUAL_MIN_NIGHT_FLOW"] < 0).fillna(False).mean()) if raw_rows else 0.0,
        "units": units,
        "distinct_units": int(len(units)),
    }

    c = collapse_duplicate_dma_dates(d)
    rows = []
    for dma, g in c.groupby("DMA_ID", sort=False):
        g = g.sort_values("DATE")
        gaps = g["DATE"].diff().dt.total_seconds().div(86400)
        actual = g["ACTUAL_MIN_NIGHT_FLOW"]
        rows.append(
            {
                "DMA_ID": dma,
                "observations": int(len(g)),
                "usable_actual_observations": int(actual.notna().sum()),
                "date_min": g["DATE"].min(),
                "date_max": g["DATE"].max(),
                "median_gap_days": float(gaps.median()) if gaps.notna().any() else np.nan,
                "p95_gap_days": float(gaps.quantile(0.95)) if gaps.notna().any() else np.nan,
                "actual_flow_median": float(actual.median()) if actual.notna().any() else np.nan,
                "actual_flow_iqr": float(actual.quantile(0.75) - actual.quantile(0.25)) if actual.notna().any() else np.nan,
                "actual_flow_missing_rate": float(actual.isna().mean()),
                "reference_flow_missing_rate": float(g["MIN_NIGHT_FLOW"].isna().mean()),
                "duplicate_dates_consolidated": int((g["duplicate_rows_same_dma_date"] > 1).sum()),
            }
        )
    per_dma = pd.DataFrame(rows).sort_values(["observations", "DMA_ID"], ascending=[False, True])
    if len(per_dma):
        summary["median_observations_per_dma"] = float(per_dma["observations"].median())
        summary["p10_observations_per_dma"] = float(per_dma["observations"].quantile(0.10))
    else:
        summary["median_observations_per_dma"] = 0.0
        summary["p10_observations_per_dma"] = 0.0
    return summary, per_dma


def assess_data_contract(summary: dict, policy: DataContractPolicy | None = None) -> dict:
    """Evaluate whether raw inputs meet minimum quality requirements."""

    policy = policy or DataContractPolicy()
    checks = {
        "enough_dmas": int(summary.get("unique_dmas", 0)) >= policy.min_unique_dmas,
        "enough_time_span": int(summary.get("span_days", 0)) >= policy.min_span_days,
        "actual_missingness": float(summary.get("actual_flow_missing_rate", 1.0)) <= policy.max_actual_flow_missing_rate,
        "reference_missingness": float(summary.get("reference_flow_missing_rate", 1.0)) <= policy.max_reference_flow_missing_rate,
        "duplicate_key_rate": float(summary.get("duplicate_key_rate", 1.0)) <= policy.max_duplicate_key_rate,
        "negative_actual_flow_rate": float(summary.get("negative_actual_flow_rate", 1.0)) <= policy.max_negative_actual_flow_rate,
        "unit_consistency": int(summary.get("distinct_units", 999)) <= policy.max_distinct_units,
    }
    passed = all(checks.values())
    return {
        "status": "pass" if passed else "fail",
        "passed": passed,
        "checks": checks,
        "policy": asdict(policy),
        "observed": {
            k: summary.get(k)
            for k in [
                "unique_dmas",
                "span_days",
                "actual_flow_missing_rate",
                "reference_flow_missing_rate",
                "duplicate_key_rate",
                "negative_actual_flow_rate",
                "distinct_units",
                "units",
            ]
        },
    }


def _calendar_features_for_dma(g: pd.DataFrame) -> pd.DataFrame:
    """Create history features using calendar windows, not observation counts."""

    g = g.sort_values("DATE").copy()
    actual = pd.Series(g["ACTUAL_MIN_NIGHT_FLOW"].to_numpy(), index=pd.DatetimeIndex(g["DATE"]), dtype="float64")

    # Previous available observation remains the persistence baseline.
    g["lag1"] = g["ACTUAL_MIN_NIGHT_FLOW"].shift(1)
    g["reference_lag1"] = g["MIN_NIGHT_FLOW"].shift(1)

    # Calendar-aware seven-day lag: most recent observation available at or
    # before t-7 days. This avoids treating seven irregular observations as seven days.
    lookup = pd.DatetimeIndex(g["DATE"] - pd.Timedelta(days=7))
    source_idx = actual.index.get_indexer(lookup, method="ffill")
    lag7d = np.full(len(g), np.nan, dtype=float)
    lag7_source_date = np.full(len(g), np.datetime64("NaT"), dtype="datetime64[ns]")
    valid = source_idx >= 0
    if valid.any():
        lag7d[valid] = actual.to_numpy()[source_idx[valid]]
        lag7_source_date[valid] = actual.index.to_numpy()[source_idx[valid]]
    g["lag7d"] = lag7d
    g["lag7d_source_date"] = pd.to_datetime(lag7_source_date)
    g["lag7d_staleness_days"] = (
        (g["DATE"] - pd.Timedelta(days=7)) - g["lag7d_source_date"]
    ).dt.total_seconds().div(86400)

    # Time-based rolling windows explicitly exclude the current row.
    g["rolling7d"] = actual.rolling("7D", closed="left", min_periods=3).median().to_numpy()
    g["rolling28d"] = actual.rolling("28D", closed="left", min_periods=7).median().to_numpy()
    g["rolling28d_std"] = actual.rolling("28D", closed="left", min_periods=7).std().to_numpy()
    g["rolling28d_count"] = actual.rolling("28D", closed="left").count().to_numpy()

    g["reference_gap"] = g["lag1"] - g["reference_lag1"]
    g["days_since_previous"] = g["DATE"].diff().dt.total_seconds().div(86400)
    g["history_count"] = np.arange(len(g))
    g["short_long_gap"] = g["rolling7d"] - g["rolling28d"]
    g["last_vs_long_gap"] = g["lag1"] - g["rolling28d"]
    g["change_per_day"] = (g["lag1"] - g["rolling7d"]) / g["days_since_previous"].replace(0, np.nan)
    return g


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create one-step-ahead features with a strict point-in-time cutoff.

    For a row dated ``t``, the target is the observed flow at ``t``. Every
    flow-derived predictor uses information strictly before ``t``. Seven- and
    28-day windows use calendar time rather than row counts.
    """

    d = collapse_duplicate_dma_dates(df)
    parts = [_calendar_features_for_dma(g) for _, g in d.groupby("DMA_ID", sort=False)]
    d = pd.concat(parts, ignore_index=True) if parts else d.iloc[0:0].copy()
    d["target"] = d["ACTUAL_MIN_NIGHT_FLOW"]

    d["month_sin"] = np.sin(2 * np.pi * d["DATE"].dt.month / 12.0)
    d["month_cos"] = np.cos(2 * np.pi * d["DATE"].dt.month / 12.0)
    d["dow_sin"] = np.sin(2 * np.pi * d["DATE"].dt.dayofweek / 7.0)
    d["dow_cos"] = np.cos(2 * np.pi * d["DATE"].dt.dayofweek / 7.0)

    return d.dropna(subset=["target", "lag1"]).sort_values(["DATE", "DMA_ID"]).reset_index(drop=True)


def feature_columns(df: pd.DataFrame) -> list[str]:
    features = [
        "lag1",
        "lag7d",
        "lag7d_staleness_days",
        "rolling7d",
        "rolling28d",
        "rolling28d_std",
        "rolling28d_count",
        "reference_lag1",
        "reference_gap",
        "days_since_previous",
        "history_count",
        "short_long_gap",
        "last_vs_long_gap",
        "change_per_day",
        "month_sin",
        "month_cos",
        "dow_sin",
        "dow_cos",
    ]
    for c in STATIC_COLUMNS:
        if c in df.columns and df[c].notna().any():
            features.append(c)
    return features

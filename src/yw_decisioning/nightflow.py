from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, median_absolute_error
from sklearn.pipeline import Pipeline


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
        "units_consistent": int(summary.get("distinct_units", 999)) <= policy.max_distinct_units,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "policy": asdict(policy),
        "observed": {
            "unique_dmas": summary.get("unique_dmas"),
            "span_days": summary.get("span_days"),
            "actual_flow_missing_rate": summary.get("actual_flow_missing_rate"),
            "reference_flow_missing_rate": summary.get("reference_flow_missing_rate"),
            "duplicate_key_rate": summary.get("duplicate_key_rate"),
            "negative_actual_flow_rate": summary.get("negative_actual_flow_rate"),
            "distinct_units": summary.get("distinct_units"),
        },
    }


def _calendar_time_features(g: pd.DataFrame) -> pd.DataFrame:
    # `ACTUAL_MIN_NIGHT_FLOW` for the current target row is never referenced inside this function.
    g = g.sort_values("DATE").copy()
    target_dates = g[["DATE"]].sort_values("DATE")
    hist = g[["DATE", "ACTUAL_MIN_NIGHT_FLOW", "MIN_NIGHT_FLOW"]].sort_values("DATE").copy()

    for c in ["ACTUAL_MIN_NIGHT_FLOW", "MIN_NIGHT_FLOW"]:
        hist[f]
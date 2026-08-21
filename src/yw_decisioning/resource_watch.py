from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

MONTH_ORDER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


def read_watsit_snapshot(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"year", "month", "reservoir_pct", "demand_ml_day"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing Watsit columns: {sorted(missing)}")
    df["month_num"] = df["month"].map(MONTH_ORDER)
    if df["month_num"].isna().any():
        bad = sorted(df.loc[df["month_num"].isna(), "month"].astype(str).unique())
        raise ValueError(f"Unrecognised month names: {bad}")
    return df.sort_values(["year", "month_num"]).reset_index(drop=True)


def build_resource_watch(
    df: pd.DataFrame,
    target_year: int = 2026,
    history_years: tuple[int, ...] = (2023, 2024, 2025),
    rainfall_watch_threshold_pct_lta: float = 75.0,
) -> pd.DataFrame:
    """Build transparent monthly resource-pressure signals.

    These are project watch rules, not Yorkshire Water drought classifications.
    Historical comparisons use only the same calendar month in the supplied
    historical years.
    """
    target = df[df["year"] == target_year].copy()
    hist = df[df["year"].isin(history_years)].copy()
    rows: list[dict] = []
    for _, r in target.iterrows():
        h = hist[hist["month_num"] == r["month_num"]]
        if h.empty:
            continue
        reservoir_hist = h["reservoir_pct"].dropna().astype(float)
        demand_hist = h["demand_ml_day"].dropna().astype(float)
        reservoir = float(r["reservoir_pct"]) if pd.notna(r["reservoir_pct"]) else np.nan
        demand = float(r["demand_ml_day"]) if pd.notna(r["demand_ml_day"]) else np.nan
        rainfall = (
            float(r["rainfall_provisional_pct_lta"])
            if pd.notna(r.get("rainfall_provisional_pct_lta")) else np.nan
        )
        reservoir_median = float(reservoir_hist.median()) if len(reservoir_hist) else np.nan
        demand_median = float(demand_hist.median()) if len(demand_hist) else np.nan
        demand_max = float(demand_hist.max()) if len(demand_hist) else np.nan
        rainfall_pressure = bool(pd.notna(rainfall) and rainfall < rainfall_watch_threshold_pct_lta)
        reservoir_below_median = bool(pd.notna(reservoir) and pd.notna(reservoir_median) and reservoir < reservoir_median)
        demand_above_hist_max = bool(pd.notna(demand) and pd.notna(demand_max) and demand > demand_max)
        rows.append(
            {
                "year": target_year,
                "month": r["month"],
                "month_num": int(r["month_num"]),
                "reservoir_pct": reservoir,
                "reservoir_hist_median_pct": reservoir_median,
                "reservoir_vs_hist_median_pp": reservoir - reservoir_median,
                "demand_ml_day": demand,
                "demand_hist_median_ml_day": demand_median,
                "demand_hist_max_ml_day": demand_max,
                "demand_vs_hist_median_pct": 100.0 * (demand / demand_median - 1.0) if demand_median else np.nan,
                "rainfall_provisional_pct_lta": rainfall,
                "rainfall_watch_threshold_pct_lta": rainfall_watch_threshold_pct_lta,
                "rainfall_pressure": rainfall_pressure,
                "reservoir_below_hist_median": reservoir_below_median,
                "demand_above_hist_max": demand_above_hist_max,
                "active_watch_signals": int(rainfall_pressure) + int(reservoir_below_median) + int(demand_above_hist_max),
                "source_url": r.get("source_url", ""),
                "retrieved_date": r.get("retrieved_date", ""),
            }
        )
    return pd.DataFrame(rows).sort_values("month_num").reset_index(drop=True)


def summarize_resource_watch(watch: pd.DataFrame, current_status_path: str | Path | None = None) -> dict:
    latest = watch.sort_values("month_num").iloc[-1]
    summary = {
        "latest_month": str(latest["month"]),
        "latest_year": int(latest["year"]),
        "active_watch_signals": int(latest["active_watch_signals"]),
        "rainfall_provisional_pct_lta": float(latest["rainfall_provisional_pct_lta"]),
        "reservoir_pct_monthly_table": float(latest["reservoir_pct"]),
        "reservoir_vs_hist_median_pp": float(latest["reservoir_vs_hist_median_pp"]),
        "demand_ml_day": float(latest["demand_ml_day"]),
        "demand_vs_hist_median_pct": float(latest["demand_vs_hist_median_pct"]),
        "demand_above_hist_max": bool(latest["demand_above_hist_max"]),
        "evidence_boundary": (
            "Watch signals are transparent descriptive rules against same-month 2023-2025 values. "
            "They are not Yorkshire Water drought classifications, causal estimates or asset-failure probabilities."
        ),
    }
    if current_status_path is not None and Path(current_status_path).exists():
        status = json.loads(Path(current_status_path).read_text(encoding="utf-8"))
        summary["current_status_reservoir_pct"] = float(status["reservoir_pct"])
        summary["river_status"] = status["river_status"]
        summary["headline_source_month"] = status["month"]
    return summary


def save_resource_watch(snapshot_path: str | Path, results_dir: str | Path, current_status_path: str | Path | None = None) -> dict:
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    df = read_watsit_snapshot(snapshot_path)
    watch = build_resource_watch(df)
    watch.to_csv(results_dir / "watsit_resource_watch_2026.csv", index=False)
    summary = summarize_resource_watch(watch, current_status_path=current_status_path)
    (results_dir / "watsit_resource_watch_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    latest = watch.iloc[-1]
    report = f"""# Watsit multi-signal resource watch — v0.4

The source snapshot reproduces the monthly rainfall, reservoir and demand values published on Yorkshire Water's Watsit page and retrieved on 21 August 2026.

For **{latest['month']} {int(latest['year'])}**:

- provisional rainfall was **{latest['rainfall_provisional_pct_lta']:.1f}% of long-term average**;
- the monthly reservoir table reported **{latest['reservoir_pct']:.0f}%**, **{latest['reservoir_vs_hist_median_pp']:.1f} percentage points** versus the same-month 2023–2025 median;
- demand was **{latest['demand_ml_day']:.0f} Ml/day**, **{latest['demand_vs_hist_median_pct']:.1f}%** above the same-month 2023–2025 median and above the maximum of those three historical July values;
- **{int(latest['active_watch_signals'])}/3** transparent project watch rules were active.

The current-status headline on the source page gives regional reservoir stocks as **{summary.get('current_status_reservoir_pct', float('nan')):.1f}%** and states: **{summary.get('river_status', 'not captured')}**.

## Interpretation boundary

The three rules are deliberately simple: rainfall below 75% of LTA, reservoir below the same-month 2023–2025 median, and demand above the same-month 2023–2025 maximum. The 75% threshold is a **project watch threshold**, not an official drought threshold. The output is a context panel for an operational analyst; it is not a drought classification, causal effect or asset-failure probability.
"""
    (results_dir / "WATSIT_RESOURCE_WATCH.md").write_text(report, encoding="utf-8")
    return summary

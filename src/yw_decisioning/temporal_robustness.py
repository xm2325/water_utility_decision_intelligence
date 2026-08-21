from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED = {"DATE", "policy", "capacity", "total_signal", "captured_signal", "candidate_count", "selected_count"}


def quarterly_policy_robustness(
    daily_metrics: pd.DataFrame,
    capacity: int = 20,
    reference_policy: str = "capacity_constrained",
    comparators: tuple[str, ...] = ("highest_flow", "random"),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarise frozen-policy performance by calendar quarter.

    Calendar quarters are reporting slices, not tuned regimes. Partial quarters
    are kept and labelled with their observed-day count rather than dropped.
    """
    missing = REQUIRED - set(daily_metrics.columns)
    if missing:
        raise ValueError(f"daily metrics missing columns: {sorted(missing)}")

    d = daily_metrics[daily_metrics["capacity"] == capacity].copy()
    if d.empty:
        raise ValueError(f"no rows for capacity={capacity}")
    d["DATE"] = pd.to_datetime(d["DATE"])
    d["quarter"] = d["DATE"].dt.to_period("Q").astype(str)

    policies = (reference_policy, *comparators)
    d = d[d["policy"].isin(policies)].copy()
    present = set(d["policy"].astype(str).unique())
    missing_policies = set(policies) - present
    if missing_policies:
        raise ValueError(f"missing policies: {sorted(missing_policies)}")

    summary = (
        d.groupby(["quarter", "policy"], as_index=False)
        .agg(
            observed_days=("DATE", "nunique"),
            total_signal=("total_signal", "sum"),
            captured_signal=("captured_signal", "sum"),
            selected_reviews=("selected_count", "sum"),
            candidate_alerts=("candidate_count", "sum"),
        )
    )
    summary["signal_capture"] = summary["captured_signal"] / summary["total_signal"].replace(0, np.nan)
    summary["mean_selected_per_day"] = summary["selected_reviews"] / summary["observed_days"]
    summary["mean_candidates_per_day"] = summary["candidate_alerts"] / summary["observed_days"]
    summary["candidate_recall"] = summary["selected_reviews"] / summary["candidate_alerts"].replace(0, np.nan)

    wide = summary.pivot(index="quarter", columns="policy", values="signal_capture")
    date_counts = summary[summary["policy"] == reference_policy].set_index("quarter")["observed_days"]
    comparison_rows: list[dict] = []
    for comparator in comparators:
        for quarter in wide.index:
            ref = float(wide.loc[quarter, reference_policy])
            comp = float(wide.loc[quarter, comparator])
            comparison_rows.append({
                "quarter": quarter,
                "observed_days": int(date_counts.loc[quarter]),
                "reference_policy": reference_policy,
                "comparison_policy": comparator,
                "reference_signal_capture": ref,
                "comparison_signal_capture": comp,
                "capture_difference_pp": 100.0 * (ref - comp),
            })
    comparisons = pd.DataFrame(comparison_rows)
    return summary, comparisons


def temporal_robustness_summary(
    quarterly_summary: pd.DataFrame,
    comparisons: pd.DataFrame,
    reference_policy: str = "capacity_constrained",
) -> dict:
    ref = quarterly_summary[quarterly_summary["policy"] == reference_policy].copy()
    if ref.empty:
        raise ValueError("reference policy missing from quarterly summary")
    gaps = comparisons[comparisons["reference_policy"] == reference_policy]
    out = {
        "quarters": int(ref["quarter"].nunique()),
        "min_observed_days": int(ref["observed_days"].min()),
        "reference_capture_min": float(ref["signal_capture"].min()),
        "reference_capture_max": float(ref["signal_capture"].max()),
        "reference_capture_median": float(ref["signal_capture"].median()),
        "worst_quarter": str(ref.loc[ref["signal_capture"].idxmin(), "quarter"]),
        "best_quarter": str(ref.loc[ref["signal_capture"].idxmax(), "quarter"]),
        "comparisons": {},
    }
    for comparator, g in gaps.groupby("comparison_policy"):
        out["comparisons"][str(comparator)] = {
            "min_capture_difference_pp": float(g["capture_difference_pp"].min()),
            "max_capture_difference_pp": float(g["capture_difference_pp"].max()),
            "quarters_reference_better": int((g["capture_difference_pp"] > 0).sum()),
            "quarters_total": int(len(g)),
        }
    return out

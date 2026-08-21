from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "policy", "capacity", "mean_selected_per_day", "signal_capture",
    "candidate_recall", "mean_backlog_candidates", "capacity_utilisation",
    "analyst_hours_per_day",
}


def build_capacity_frontier(summary: pd.DataFrame, policy: str = "capacity_constrained") -> pd.DataFrame:
    """Convert discrete capacity scenarios into an incremental decision frontier.

    Marginal quantities use *actual mean reviews selected per day* rather than the
    nominal capacity difference, because a candidate-only policy can leave slots
    unused when fewer positive candidates are available.
    """
    missing = REQUIRED_COLUMNS - set(summary.columns)
    if missing:
        raise ValueError(f"capacity summary missing columns: {sorted(missing)}")

    d = summary[summary["policy"] == policy].copy().sort_values("capacity").reset_index(drop=True)
    if len(d) < 2:
        raise ValueError(f"need at least two capacity scenarios for policy {policy!r}")
    if d["capacity"].duplicated().any() or not d["capacity"].is_monotonic_increasing:
        raise ValueError("capacity scenarios must be unique and increasing")

    tol = 1e-12
    if (d["mean_selected_per_day"].diff().dropna() < -tol).any():
        raise ValueError("actual reviews/day must not decrease as capacity rises")
    if (d["signal_capture"].diff().dropna() < -tol).any():
        raise ValueError("signal capture must not decrease as capacity rises")
    if (d["mean_backlog_candidates"].diff().dropna() > tol).any():
        raise ValueError("candidate backlog must not increase as capacity rises")

    d["previous_capacity"] = d["capacity"].shift(1)
    d["delta_nominal_capacity"] = d["capacity"].diff()
    d["delta_selected_per_day"] = d["mean_selected_per_day"].diff()
    d["delta_signal_capture_pp"] = 100.0 * d["signal_capture"].diff()
    d["backlog_reduction_per_day"] = -d["mean_backlog_candidates"].diff()
    d["incremental_analyst_hours_per_day"] = d["analyst_hours_per_day"].diff()
    d["marginal_capture_pp_per_extra_review"] = np.where(
        d["delta_selected_per_day"] > 0,
        d["delta_signal_capture_pp"] / d["delta_selected_per_day"],
        np.nan,
    )
    d["backlog_reduction_per_extra_review"] = np.where(
        d["delta_selected_per_day"] > 0,
        d["backlog_reduction_per_day"] / d["delta_selected_per_day"],
        np.nan,
    )
    d["unused_capacity_per_day"] = d["capacity"] - d["mean_selected_per_day"]
    d["unretained_signal_pct"] = 100.0 * (1.0 - d["signal_capture"])

    return d[[
        "policy", "capacity", "previous_capacity", "mean_selected_per_day",
        "signal_capture", "candidate_recall", "mean_backlog_candidates",
        "capacity_utilisation", "analyst_hours_per_day", "unused_capacity_per_day",
        "delta_nominal_capacity", "delta_selected_per_day", "delta_signal_capture_pp",
        "marginal_capture_pp_per_extra_review", "backlog_reduction_per_day",
        "backlog_reduction_per_extra_review", "incremental_analyst_hours_per_day",
        "unretained_signal_pct",
    ]]

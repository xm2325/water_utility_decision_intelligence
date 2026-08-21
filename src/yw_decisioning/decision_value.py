from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np
import pandas as pd

POLICIES = ("random", "highest_flow", "anomaly_score", "capacity_constrained")


def attach_champion_signal(predictions: pd.DataFrame, decision: dict) -> pd.DataFrame:
    """Attach the frozen champion's operational signal to every held-out row."""
    d = predictions.copy()
    champion = decision.get("champion")
    if champion == "hist_gradient_boosting":
        prefix = "ml"
        d["champion_name"] = "hist_gradient_boosting"
    elif champion == "simple_baseline":
        prefix = "simple_baseline"
        d["champion_name"] = "simple_baseline:" + d["simple_baseline_name"].astype(str)
    elif champion == "persistence_baseline":
        prefix = "persistence"
        d["champion_name"] = "persistence_baseline"
    else:
        raise ValueError(f"Unsupported champion: {champion}")

    d["champion_upper_exceedance"] = d[f"{prefix}_upper_exceedance"].fillna(False).astype(bool)
    d["champion_anomaly_excess"] = pd.to_numeric(d[f"{prefix}_anomaly_excess"], errors="coerce").fillna(0.0).clip(lower=0)
    d["champion_investigation_score"] = pd.to_numeric(d[f"{prefix}_investigation_score"], errors="coerce").fillna(0.0)
    d["candidate"] = d["champion_upper_exceedance"] & d["champion_anomaly_excess"].gt(0)
    return d


def _stable_random_score(date_value: object, dma_id: object) -> int:
    key = f"{pd.Timestamp(date_value).date()}|{dma_id}|water-utility-v0.6".encode("utf-8")
    return int.from_bytes(hashlib.blake2b(key, digest_size=8).digest(), "big", signed=False)


def add_policy_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute daily ranks once so capacity sweeps are vectorised."""
    d = frame.copy().reset_index(drop=True)
    d["_row_id"] = np.arange(len(d))
    d["random_score"] = [_stable_random_score(x, y) for x, y in zip(d["DATE"], d["DMA_ID"])]

    specs = {
        "random": ["DATE", "random_score", "DMA_ID", "_row_id"],
        "highest_flow": ["DATE", "target", "DMA_ID", "_row_id"],
        "anomaly_score": ["DATE", "champion_investigation_score", "champion_anomaly_excess", "DMA_ID", "_row_id"],
    }
    ascending = {
        "random": [True, False, True, True],
        "highest_flow": [True, False, True, True],
        "anomaly_score": [True, False, False, True, True],
    }
    for name, cols in specs.items():
        ordered = d.sort_values(cols, ascending=ascending[name], kind="mergesort")
        ranks = ordered.groupby("DATE", sort=False).cumcount() + 1
        d.loc[ordered.index, f"rank_{name}"] = ranks.to_numpy()

    d["rank_capacity_constrained"] = np.nan
    cand = d[d["candidate"]].sort_values(
        ["DATE", "champion_investigation_score", "champion_anomaly_excess", "DMA_ID", "_row_id"],
        ascending=[True, False, False, True, True],
        kind="mergesort",
    )
    d.loc[cand.index, "rank_capacity_constrained"] = (cand.groupby("DATE", sort=False).cumcount() + 1).to_numpy()
    return d


def selected_mask(ranked: pd.DataFrame, policy: str, capacity: int) -> pd.Series:
    if policy not in POLICIES:
        raise ValueError(f"Unknown policy: {policy}")
    if capacity < 1:
        raise ValueError("capacity must be positive")
    return ranked[f"rank_{policy}"].le(capacity).fillna(False)


def evaluate_policy_grid(
    ranked: pd.DataFrame,
    capacities: Iterable[int] = (5, 10, 20, 40),
    minutes_per_review: float = 20.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return compact policy summaries plus day-level workload/capture metrics."""
    capacities = tuple(sorted({int(x) for x in capacities}))
    dates = pd.Index(sorted(pd.to_datetime(ranked["DATE"]).unique()))
    total_signal = float(ranked["champion_anomaly_excess"].sum())
    total_candidates = int(ranked["candidate"].sum())
    n_days = int(len(dates))
    mean_candidates_day = total_candidates / n_days if n_days else np.nan

    rows: list[dict] = []
    daily_rows: list[dict] = []
    for capacity in capacities:
        for policy in POLICIES:
            sel = selected_mask(ranked, policy, capacity)
            selected = ranked[sel]
            selected_candidates = int(selected["candidate"].sum())
            captured_signal = float(selected["champion_anomaly_excess"].sum())

            daily_input = ranked[["DATE", "candidate", "champion_anomaly_excess"]].copy()
            daily_input["selected"] = sel.to_numpy()
            daily_input["selected_candidate"] = daily_input["selected"] & daily_input["candidate"]
            daily_input["captured_signal"] = daily_input["champion_anomaly_excess"].where(daily_input["selected"], 0.0)
            by_day = daily_input.groupby("DATE", sort=True).agg(
                candidate_count=("candidate", "sum"),
                selected_count=("selected", "sum"),
                selected_candidates=("selected_candidate", "sum"),
                total_signal=("champion_anomaly_excess", "sum"),
                captured_signal=("captured_signal", "sum"),
            ).reset_index()
            by_day["policy"] = policy
            by_day["capacity"] = capacity
            by_day["backlog_candidates"] = (by_day["candidate_count"] - by_day["selected_candidates"]).clip(lower=0)
            by_day["capacity_utilisation"] = by_day["selected_count"] / capacity
            by_day["analyst_hours"] = by_day["selected_count"] * minutes_per_review / 60.0
            daily_rows.extend(by_day.to_dict("records"))

            rows.append({
                "policy": policy,
                "capacity": capacity,
                "selected_rows": int(sel.sum()),
                "selected_candidates": selected_candidates,
                "signal_capture": captured_signal / total_signal if total_signal > 0 else np.nan,
                "candidate_precision": selected_candidates / int(sel.sum()) if int(sel.sum()) else np.nan,
                "candidate_recall": selected_candidates / total_candidates if total_candidates else np.nan,
                "mean_selected_per_day": float(by_day["selected_count"].mean()),
                "mean_candidates_per_day": mean_candidates_day,
                "mean_backlog_candidates": float(by_day["backlog_candidates"].mean()),
                "capacity_utilisation": float(by_day["capacity_utilisation"].mean()),
                "analyst_hours_per_day": float(by_day["analyst_hours"].mean()),
                "held_out_dates": n_days,
                "held_out_rows": int(len(ranked)),
                "total_candidates": total_candidates,
                "total_positive_residual_excess": total_signal,
            })
    return pd.DataFrame(rows), pd.DataFrame(daily_rows)

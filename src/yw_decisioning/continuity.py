from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def _ordered_candidates(day: pd.DataFrame) -> pd.DataFrame:
    return day[day["candidate"]].sort_values(
        ["champion_investigation_score", "champion_anomaly_excess", "DMA_ID"],
        ascending=[False, False, True],
        kind="mergesort",
    )


def continuity_queue(
    frame: pd.DataFrame,
    capacity: int = 20,
    carryover_fraction: float = 0.25,
) -> pd.DataFrame:
    """Build a candidate-only sequential queue with a bounded continuity reserve.

    A DMA can be carried over only if it is still a positive candidate today.
    The reserve is a maximum, not a quota: if fewer prior-queue DMAs remain
    candidates, the unused slots are immediately returned to current ranking.
    """
    if capacity < 1:
        raise ValueError("capacity must be positive")
    if not 0 <= carryover_fraction <= 1:
        raise ValueError("carryover_fraction must be between 0 and 1")

    d = frame.copy()
    d["DATE"] = pd.to_datetime(d["DATE"])
    reserve = int(np.floor(capacity * carryover_fraction + 1e-12))
    prev_queue: set[str] = set()
    selected_parts: list[pd.DataFrame] = []

    for date, day in d.groupby("DATE", sort=True):
        cand = _ordered_candidates(day).copy()
        if cand.empty:
            prev_queue = set()
            continue

        if reserve > 0 and prev_queue:
            carried = cand[cand["DMA_ID"].astype(str).isin(prev_queue)].head(reserve).copy()
        else:
            carried = cand.iloc[:0].copy()
        carried["selection_reason"] = "continuity"

        carried_ids = set(carried["DMA_ID"].astype(str))
        remaining = cand[~cand["DMA_ID"].astype(str).isin(carried_ids)]
        fill = remaining.head(max(0, capacity - len(carried))).copy()
        fill["selection_reason"] = "current_score"

        queue = pd.concat([carried, fill], ignore_index=True)
        if queue.empty:
            prev_queue = set()
            continue
        queue["queue_rank"] = np.arange(1, len(queue) + 1)
        queue["carryover_fraction"] = carryover_fraction
        queue["capacity"] = capacity
        queue["queue_date"] = pd.Timestamp(date)
        queue["was_in_previous_queue"] = queue["DMA_ID"].astype(str).isin(prev_queue)
        selected_parts.append(queue)
        prev_queue = set(queue["DMA_ID"].astype(str))

    if not selected_parts:
        return pd.DataFrame(columns=list(d.columns) + [
            "selection_reason", "queue_rank", "carryover_fraction", "capacity",
            "queue_date", "was_in_previous_queue",
        ])
    return pd.concat(selected_parts, ignore_index=True)


def continuity_sensitivity(
    frame: pd.DataFrame,
    capacity: int = 20,
    carryover_fractions: Iterable[float] = (0.0, 0.10, 0.25, 0.50),
    minutes_per_review: float = 20.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate continuity as a transparent policy sensitivity, not tuning."""
    d = frame.copy()
    d["DATE"] = pd.to_datetime(d["DATE"])
    total_signal = float(d["champion_anomaly_excess"].sum())
    total_candidates = int(d["candidate"].sum())
    all_dates = list(sorted(d["DATE"].unique()))
    candidate_by_day = d.groupby("DATE")["candidate"].sum().to_dict()

    summaries: list[dict] = []
    daily_rows: list[dict] = []
    base_capture = None

    for frac in [float(x) for x in carryover_fractions]:
        queue = continuity_queue(d, capacity=capacity, carryover_fraction=frac)
        sets = {
            pd.Timestamp(date): set(g["DMA_ID"].astype(str))
            for date, g in queue.groupby("queue_date", sort=True)
        }
        signal_by_day = queue.groupby("queue_date")["champion_anomaly_excess"].sum().to_dict()
        count_by_day = queue.groupby("queue_date").size().to_dict()
        carry_by_day = queue.groupby("queue_date")["selection_reason"].apply(lambda x: int((x == "continuity").sum())).to_dict()

        jaccards: list[float] = []
        retentions: list[float] = []
        for prev, curr in zip(all_dates[:-1], all_dates[1:]):
            a = sets.get(pd.Timestamp(prev), set())
            b = sets.get(pd.Timestamp(curr), set())
            inter = a & b
            union = a | b
            jaccards.append(len(inter) / len(union) if union else 1.0)
            retentions.append(len(inter) / len(a) if a else (1.0 if not b else 0.0))

        captured_signal = float(queue["champion_anomaly_excess"].sum())
        capture = captured_signal / total_signal if total_signal else np.nan
        if base_capture is None:
            base_capture = capture

        for date in all_dates:
            selected = int(count_by_day.get(pd.Timestamp(date), 0))
            candidates = int(candidate_by_day.get(pd.Timestamp(date), 0))
            daily_rows.append({
                "DATE": pd.Timestamp(date),
                "capacity": capacity,
                "carryover_fraction": frac,
                "candidate_count": candidates,
                "selected_count": selected,
                "continuity_selected": int(carry_by_day.get(pd.Timestamp(date), 0)),
                "captured_signal": float(signal_by_day.get(pd.Timestamp(date), 0.0)),
                "backlog_candidates": max(0, candidates - selected),
                "capacity_utilisation": selected / capacity,
                "analyst_hours": selected * minutes_per_review / 60.0,
            })

        counts = queue["DMA_ID"].astype(str).value_counts(normalize=True)
        summaries.append({
            "capacity": capacity,
            "carryover_fraction": frac,
            "selected_rows": int(len(queue)),
            "signal_capture": capture,
            "signal_capture_cost_pp_vs_zero": 100.0 * (base_capture - capture),
            "candidate_recall": int(len(queue)) / total_candidates if total_candidates else np.nan,
            "candidate_precision": 1.0 if len(queue) else np.nan,
            "mean_selected_per_day": len(queue) / len(all_dates) if all_dates else np.nan,
            "mean_backlog_candidates": float(np.mean([max(0, candidate_by_day.get(pd.Timestamp(x), 0) - count_by_day.get(pd.Timestamp(x), 0)) for x in all_dates])) if all_dates else np.nan,
            "capacity_utilisation": (len(queue) / len(all_dates) / capacity) if all_dates else np.nan,
            "analyst_hours_per_day": (len(queue) / len(all_dates) * minutes_per_review / 60.0) if all_dates else np.nan,
            "mean_consecutive_day_jaccard": float(np.mean(jaccards)) if jaccards else np.nan,
            "mean_previous_queue_retention": float(np.mean(retentions)) if retentions else np.nan,
            "mean_queue_churn": float(1.0 - np.mean(jaccards)) if jaccards else np.nan,
            "mean_continuity_selected_per_day": float(queue["selection_reason"].eq("continuity").sum() / len(all_dates)) if all_dates else np.nan,
            "unique_dmas_selected": int(queue["DMA_ID"].nunique()),
            "selection_hhi": float(np.square(counts.to_numpy()).sum()) if len(counts) else np.nan,
            "top_10_dma_share": float(counts.head(10).sum()) if len(counts) else np.nan,
            "held_out_dates": len(all_dates),
            "held_out_rows": len(d),
            "total_candidates": total_candidates,
        })

    return pd.DataFrame(summaries), pd.DataFrame(daily_rows)

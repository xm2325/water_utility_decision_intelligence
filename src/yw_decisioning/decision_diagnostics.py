from __future__ import annotations

from collections import Counter
from typing import Iterable

import numpy as np
import pandas as pd

from .decision_value import POLICIES, selected_mask


def queue_stability(ranked: pd.DataFrame, capacities: Iterable[int] = (5, 10, 20, 40)) -> pd.DataFrame:
    rows: list[dict] = []
    dates = sorted(pd.to_datetime(ranked["DATE"]).unique())
    for capacity in sorted({int(x) for x in capacities}):
        for policy in POLICIES:
            sel = selected_mask(ranked, policy, capacity)
            work = ranked.loc[sel, ["DATE", "DMA_ID"]].copy()
            sets = {pd.Timestamp(k): set(v["DMA_ID"].astype(str)) for k, v in work.groupby("DATE")}
            jaccards, retentions = [], []
            for prev_date, curr_date in zip(dates[:-1], dates[1:]):
                a = sets.get(pd.Timestamp(prev_date), set())
                b = sets.get(pd.Timestamp(curr_date), set())
                union = a | b
                inter = a & b
                jaccards.append(len(inter) / len(union) if union else 1.0)
                retentions.append(len(inter) / len(a) if a else (1.0 if not b else 0.0))
            rows.append({
                "policy": policy,
                "capacity": capacity,
                "mean_consecutive_day_jaccard": float(np.mean(jaccards)) if jaccards else np.nan,
                "mean_previous_queue_retention": float(np.mean(retentions)) if retentions else np.nan,
                "mean_queue_churn": float(1 - np.mean(jaccards)) if jaccards else np.nan,
                "date_transitions": len(jaccards),
            })
    return pd.DataFrame(rows)


def dma_concentration(ranked: pd.DataFrame, capacities: Iterable[int] = (5, 10, 20, 40)) -> pd.DataFrame:
    rows: list[dict] = []
    for capacity in sorted({int(x) for x in capacities}):
        for policy in POLICIES:
            sel = selected_mask(ranked, policy, capacity)
            counts = Counter(ranked.loc[sel, "DMA_ID"].astype(str))
            total = sum(counts.values())
            shares = np.array(list(counts.values()), dtype=float) / total if total else np.array([])
            ordered = np.sort(shares)[::-1]
            rows.append({
                "policy": policy,
                "capacity": capacity,
                "unique_dmas_selected": len(counts),
                "selection_hhi": float(np.square(shares).sum()) if total else np.nan,
                "top_10_dma_share": float(ordered[:10].sum()) if total else np.nan,
                "max_single_dma_share": float(ordered[0]) if total else np.nan,
            })
    return pd.DataFrame(rows)

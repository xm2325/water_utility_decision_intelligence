from __future__ import annotations

from collections.abc import Iterable
import numpy as np
import pandas as pd


REQUIRED = {"DATE", "policy", "capacity", "total_signal", "captured_signal"}


def moving_block_sample_indices(n: int, block_length: int, rng: np.random.Generator) -> np.ndarray:
    """Sample positions with replacement in contiguous moving blocks."""
    if n < 1:
        raise ValueError("n must be positive")
    if block_length < 1 or block_length > n:
        raise ValueError("block_length must be between 1 and n")
    idx: list[int] = []
    max_start = n - block_length
    while len(idx) < n:
        start = int(rng.integers(0, max_start + 1))
        idx.extend(range(start, start + block_length))
    return np.asarray(idx[:n], dtype=int)


def block_bootstrap_policy_capture(
    daily_metrics: pd.DataFrame,
    capacity: int = 20,
    policies: Iterable[str] = ("capacity_constrained", "highest_flow", "random"),
    reference_policy: str = "capacity_constrained",
    block_length: int = 7,
    n_bootstrap: int = 1000,
    seed: int = 20260821,
    alpha: float = 0.05,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Moving-block bootstrap for frozen-policy residual-signal capture.

    The procedure resamples contiguous date positions and therefore preserves
    short-run temporal structure within each sampled block. It is a robustness
    sensitivity conditional on the frozen model/policies, not a causal or leak-
    detection confidence interval.
    """
    missing = REQUIRED - set(daily_metrics.columns)
    if missing:
        raise ValueError(f"daily metrics missing columns: {sorted(missing)}")
    if n_bootstrap < 10:
        raise ValueError("n_bootstrap must be at least 10")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    d = daily_metrics[daily_metrics["capacity"] == capacity].copy()
    d["DATE"] = pd.to_datetime(d["DATE"])
    policies = tuple(policies)
    if reference_policy not in policies:
        raise ValueError("reference_policy must be included in policies")

    dates = sorted(d["DATE"].unique())
    if len(dates) < block_length:
        raise ValueError("not enough dates for requested block length")

    by_policy: dict[str, pd.DataFrame] = {}
    for policy in policies:
        x = d[d["policy"] == policy].set_index("DATE").reindex(dates)
        if x["captured_signal"].isna().any() or x["total_signal"].isna().any():
            raise ValueError(f"policy {policy!r} does not cover every held-out date")
        by_policy[policy] = x

    common_total = by_policy[reference_policy]["total_signal"].to_numpy(float)
    for policy, x in by_policy.items():
        if not np.allclose(x["total_signal"].to_numpy(float), common_total, rtol=0, atol=1e-10):
            raise ValueError(f"total_signal differs by policy for {policy!r}")

    point = {
        policy: float(x["captured_signal"].sum() / x["total_signal"].sum())
        for policy, x in by_policy.items()
    }
    boot = {policy: np.empty(n_bootstrap, dtype=float) for policy in policies}
    rng = np.random.default_rng(seed)
    for b in range(n_bootstrap):
        idx = moving_block_sample_indices(len(dates), block_length, rng)
        denominator = float(common_total[idx].sum())
        for policy, x in by_policy.items():
            numerator = float(x["captured_signal"].to_numpy(float)[idx].sum())
            boot[policy][b] = numerator / denominator if denominator else np.nan

    lo_q, hi_q = alpha / 2, 1 - alpha / 2
    summary_rows = []
    for policy in policies:
        arr = boot[policy]
        summary_rows.append({
            "policy": policy,
            "capacity": capacity,
            "point_signal_capture": point[policy],
            "bootstrap_mean": float(np.nanmean(arr)),
            "bootstrap_median": float(np.nanmedian(arr)),
            "ci_lower": float(np.nanquantile(arr, lo_q)),
            "ci_upper": float(np.nanquantile(arr, hi_q)),
            "block_length_days": block_length,
            "bootstrap_replicates": n_bootstrap,
            "seed": seed,
            "held_out_dates": len(dates),
        })

    comparison_rows = []
    ref_arr = boot[reference_policy]
    for policy in policies:
        if policy == reference_policy:
            continue
        diff = ref_arr - boot[policy]
        comparison_rows.append({
            "reference_policy": reference_policy,
            "comparison_policy": policy,
            "capacity": capacity,
            "point_capture_difference_pp": 100.0 * (point[reference_policy] - point[policy]),
            "bootstrap_difference_mean_pp": 100.0 * float(np.nanmean(diff)),
            "difference_ci_lower_pp": 100.0 * float(np.nanquantile(diff, lo_q)),
            "difference_ci_upper_pp": 100.0 * float(np.nanquantile(diff, hi_q)),
            "bootstrap_share_difference_positive": float(np.nanmean(diff > 0)),
            "block_length_days": block_length,
            "bootstrap_replicates": n_bootstrap,
            "seed": seed,
            "held_out_dates": len(dates),
        })

    return pd.DataFrame(summary_rows), pd.DataFrame(comparison_rows)

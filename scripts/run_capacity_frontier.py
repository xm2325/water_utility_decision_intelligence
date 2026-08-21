from pathlib import Path
import argparse
import json
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.capacity_frontier import build_capacity_frontier  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Build marginal capacity / residual-signal frontier")
    p.add_argument("--policy", default="capacity_constrained")
    return p.parse_args()


def main():
    args = parse_args()
    results = ROOT / "results"
    source = results / "nightflow_policy_capacity_summary.csv"
    if not source.exists():
        raise SystemExit("Run scripts/run_decision_value.py first.")

    summary = pd.read_csv(source)
    frontier = build_capacity_frontier(summary, policy=args.policy)
    frontier.to_csv(results / "nightflow_capacity_frontier.csv", index=False)

    increments = frontier.dropna(subset=["previous_capacity"]).copy()
    payload = {
        "policy": args.policy,
        "capacities": [int(x) for x in frontier["capacity"]],
        "points": frontier.to_dict(orient="records"),
        "marginal_steps": increments[[
            "previous_capacity", "capacity", "delta_selected_per_day",
            "delta_signal_capture_pp", "marginal_capture_pp_per_extra_review",
            "backlog_reduction_per_day", "backlog_reduction_per_extra_review",
        ]].to_dict(orient="records"),
        "interpretation": (
            "This frontier describes diminishing residual-signal returns across stated review-capacity scenarios. "
            "It does not identify an optimal staffing level because review cost, intervention success and verified leak outcomes are absent from the public data."
        ),
    }
    (results / "nightflow_capacity_frontier_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report_cols = [
        "capacity", "mean_selected_per_day", "signal_capture", "candidate_recall",
        "mean_backlog_candidates", "delta_selected_per_day", "delta_signal_capture_pp",
        "marginal_capture_pp_per_extra_review",
    ]
    report = f"""# Night-flow capacity marginal-value frontier — v0.8

Policy: **{args.policy}**. Marginal gains use actual mean reviews selected per day, not nominal capacity, because the candidate-only policy can leave slots unused.

{frontier[report_cols].to_markdown(index=False, floatfmt='.4f')}

The table is a residual-signal / review-burden frontier. It does not estimate avoided leaks, recovered water, staffing savings, financial return or an optimal daily capacity.
"""
    (results / "NIGHTFLOW_CAPACITY_FRONTIER.md").write_text(report, encoding="utf-8")

    fig_dir = results / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    ax = frontier.plot(x="mean_selected_per_day", y="signal_capture", marker="o", figsize=(7, 4.6), legend=False)
    for _, row in frontier.iterrows():
        ax.annotate(f"K={int(row['capacity'])}", (row["mean_selected_per_day"], row["signal_capture"]))
    ax.set_xlabel("Mean DMA reviews selected per day")
    ax.set_ylabel("Residual-signal capture")
    ax.set_title("Capacity / residual-signal frontier")
    plt.tight_layout()
    plt.savefig(fig_dir / "nightflow_capacity_frontier.png", dpi=180)
    plt.close()

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

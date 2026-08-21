from pathlib import Path
import argparse
import json
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.decision_uncertainty import block_bootstrap_policy_capture  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Moving-block bootstrap robustness for decision-policy signal capture")
    p.add_argument("--capacity", type=int, default=20)
    p.add_argument("--block-lengths", default="3,7,14")
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=20260821)
    return p.parse_args()


def main():
    args = parse_args()
    results = ROOT / "results"
    source = results / "nightflow_policy_daily_metrics.csv"
    if not source.exists():
        raise SystemExit("Run scripts/run_decision_value.py first.")
    daily = pd.read_csv(source, parse_dates=["DATE"])
    block_lengths = [int(x.strip()) for x in args.block_lengths.split(",") if x.strip()]
    summaries = []
    comparisons_all = []
    for block_length in block_lengths:
        summary_i, comparisons_i = block_bootstrap_policy_capture(
            daily,
            capacity=args.capacity,
            policies=("capacity_constrained", "highest_flow", "random"),
            reference_policy="capacity_constrained",
            block_length=block_length,
            n_bootstrap=args.bootstrap,
            seed=args.seed,
        )
        summaries.append(summary_i)
        comparisons_all.append(comparisons_i)
    summary = pd.concat(summaries, ignore_index=True)
    comparisons = pd.concat(comparisons_all, ignore_index=True)
    summary.to_csv(results / "nightflow_policy_bootstrap_summary.csv", index=False)
    comparisons.to_csv(results / "nightflow_policy_bootstrap_comparisons.csv", index=False)
    payload = {
        "capacity": args.capacity,
        "block_lengths_days": block_lengths,
        "bootstrap_replicates_per_block_length": args.bootstrap,
        "seed": args.seed,
        "policy_intervals": summary.to_dict(orient="records"),
        "policy_comparisons": comparisons.to_dict(orient="records"),
        "interpretation": (
            "Moving-block bootstrap intervals measure date-level robustness conditional on the frozen champion and policies. "
            "They are not verified-leak confidence intervals, causal effects, or guarantees for future operations."
        ),
    }
    (results / "nightflow_policy_bootstrap_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report = f"""# Decision-policy moving-block bootstrap robustness — v0.9

Capacity: **{args.capacity} DMA reviews/day**. Dates are resampled with **{args.bootstrap} deterministic replicates per block length** (seed {args.seed}) at block lengths **{', '.join(map(str, block_lengths))} days**.

## Signal-capture intervals

{summary[["block_length_days", "policy", "point_signal_capture", "ci_lower", "ci_upper"]].to_markdown(index=False, floatfmt='.4f')}

## Capacity-constrained differences

{comparisons[["block_length_days", "comparison_policy", "point_capture_difference_pp", "difference_ci_lower_pp", "difference_ci_upper_pp", "bootstrap_share_difference_positive"]].to_markdown(index=False, floatfmt='.4f')}

The bootstrap preserves short-run date dependence within sampled blocks, but it remains conditional on this historical public-data period, the frozen model and the selected policies. It is not a causal or leak-detection interval.
"""
    (results / "NIGHTFLOW_POLICY_ROBUSTNESS.md").write_text(report, encoding="utf-8")

    fig_dir = results / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plot = summary[summary["block_length_days"] == (7 if 7 in block_lengths else block_lengths[0])].copy()
    y = plot["point_signal_capture"].to_numpy()
    yerr = [y - plot["ci_lower"].to_numpy(), plot["ci_upper"].to_numpy() - y]
    ax = plot.plot(x="policy", y="point_signal_capture", kind="bar", yerr=yerr, legend=False, capsize=4, figsize=(7, 4.6))
    ax.set_ylabel("Residual-signal capture")
    ax.set_xlabel("")
    ax.set_title(f"{int(plot['block_length_days'].iloc[0])}-day moving-block bootstrap sensitivity")
    plt.tight_layout()
    plt.savefig(fig_dir / "nightflow_policy_bootstrap.png", dpi=180)
    plt.close()
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

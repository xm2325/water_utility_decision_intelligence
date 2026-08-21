from pathlib import Path
import argparse
import json
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.temporal_robustness import quarterly_policy_robustness, temporal_robustness_summary  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Calendar-quarter robustness for frozen decision policies")
    p.add_argument("--capacity", type=int, default=20)
    return p.parse_args()


def main():
    args = parse_args()
    results = ROOT / "results"
    source = results / "nightflow_policy_daily_metrics.csv"
    if not source.exists():
        raise SystemExit("Run scripts/run_decision_value.py first.")
    daily = pd.read_csv(source, parse_dates=["DATE"])
    summary, comparisons = quarterly_policy_robustness(daily, capacity=args.capacity)
    summary.to_csv(results / "nightflow_policy_quarterly_summary.csv", index=False)
    comparisons.to_csv(results / "nightflow_policy_quarterly_comparisons.csv", index=False)
    compact = temporal_robustness_summary(summary, comparisons)
    payload = {
        "capacity": args.capacity,
        "slice_definition": "calendar quarter; partial edge quarters retained and labelled by observed-day count",
        **compact,
        "interpretation": (
            "Quarterly slices test temporal heterogeneity of the frozen public-data policy. "
            "They are descriptive held-out robustness slices, not tuned regimes or guarantees for future periods."
        ),
    }
    (results / "nightflow_temporal_robustness_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    piv = summary.pivot(index="quarter", columns="policy", values="signal_capture")
    ax = piv.plot(marker="o", figsize=(8, 4.8))
    ax.set_ylabel("Residual-signal capture")
    ax.set_xlabel("Calendar quarter")
    ax.set_title("Frozen-policy signal capture by calendar quarter")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    fig_dir = results / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_dir / "nightflow_temporal_robustness.png", dpi=180)
    plt.close()

    report = f"""# Decision-policy temporal robustness — v0.10

Capacity: **{args.capacity} DMA reviews/day**. Calendar quarters are descriptive slices; partial edge quarters are retained and labelled by observed-day count.

## Quarterly signal capture

{summary[["quarter", "policy", "observed_days", "signal_capture", "mean_candidates_per_day", "mean_selected_per_day"]].to_markdown(index=False, floatfmt='.4f')}

## Capacity-constrained comparator gaps

{comparisons.to_markdown(index=False, floatfmt='.4f')}

The slice analysis keeps the champion, threshold, policy and capacity frozen. It does not tune a different rule per quarter and does not establish future performance, verified leak recall or causal benefit.
"""
    (results / "NIGHTFLOW_TEMPORAL_ROBUSTNESS.md").write_text(report, encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

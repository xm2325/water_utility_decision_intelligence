from pathlib import Path
import argparse
import json
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.decision_value import attach_champion_signal  # noqa: E402
from yw_decisioning.continuity import continuity_sensitivity  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate candidate-only queue continuity sensitivity")
    p.add_argument("--capacity", type=int, default=20)
    p.add_argument("--fractions", default="0,0.10,0.25,0.50")
    p.add_argument("--minutes-per-review", type=float, default=20.0)
    return p.parse_args()


def main():
    args = parse_args()
    fractions = tuple(float(x.strip()) for x in args.fractions.split(",") if x.strip())
    results = ROOT / "results"
    pred_path = results / "nightflow_backtest_predictions.csv"
    decision_path = results / "nightflow_promotion_decision.json"
    if not pred_path.exists() or not decision_path.exists():
        raise SystemExit("Run scripts/run_nightflow_model.py first.")

    pred = pd.read_csv(pred_path, parse_dates=["DATE"])
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    frame = attach_champion_signal(pred, decision)
    summary, daily = continuity_sensitivity(
        frame,
        capacity=args.capacity,
        carryover_fractions=fractions,
        minutes_per_review=args.minutes_per_review,
    )
    summary.to_csv(results / "nightflow_continuity_sensitivity.csv", index=False)
    daily.to_csv(results / "nightflow_continuity_daily_metrics.csv", index=False)

    payload = {
        "capacity": args.capacity,
        "fractions": fractions,
        "held_out_rows": int(len(frame)),
        "held_out_dates": int(pd.to_datetime(frame["DATE"]).nunique()),
        "results": summary.set_index("carryover_fraction").to_dict(orient="index"),
        "interpretation": (
            "Continuity is a sensitivity over current positive candidates only. "
            "No DMA is retained merely because it appeared yesterday. The public data do not contain verified leak outcomes."
        ),
    }
    (results / "nightflow_continuity_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    fig_dir = results / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    ax = summary.plot(x="mean_consecutive_day_jaccard", y="signal_capture", marker="o", figsize=(7, 4.6), legend=False)
    for _, row in summary.iterrows():
        ax.annotate(f"{100*row['carryover_fraction']:.0f}%", (row["mean_consecutive_day_jaccard"], row["signal_capture"]))
    ax.set_xlabel("Mean consecutive-day queue Jaccard")
    ax.set_ylabel("Residual-signal capture")
    ax.set_title("Continuity / signal-capture sensitivity")
    plt.tight_layout()
    plt.savefig(fig_dir / "nightflow_continuity_frontier.png", dpi=180)
    plt.close()

    report_rows = summary[[
        "carryover_fraction", "signal_capture", "signal_capture_cost_pp_vs_zero",
        "mean_consecutive_day_jaccard", "mean_previous_queue_retention",
        "mean_continuity_selected_per_day",
    ]]
    report = f"""# Night-flow queue continuity sensitivity — v0.7

The frozen forecasting champion and candidate definition are unchanged. Continuity can only select a DMA that is **still a positive upper-band candidate on the current date**. This is a sensitivity analysis, not a tuned production setting.

Capacity: **{args.capacity} DMA reviews/day**.

{report_rows.to_markdown(index=False, floatfmt='.4f')}

`signal_capture_cost_pp_vs_zero` measures the percentage-point loss relative to the zero-carryover anomaly queue. The comparison exposes the operational trade-off between current-day residual signal and day-to-day queue continuity. It does not measure leak recall, recovered water or field-team savings.
"""
    (results / "NIGHTFLOW_CONTINUITY.md").write_text(report, encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

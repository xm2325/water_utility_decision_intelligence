from pathlib import Path
import argparse
import json
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.decision_value import attach_champion_signal, add_policy_ranks, evaluate_policy_grid  # noqa: E402
from yw_decisioning.decision_diagnostics import queue_stability, dma_concentration  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate capacity-aware DMA review policies on held-out predictions")
    p.add_argument("--capacities", default="5,10,20,40")
    p.add_argument("--minutes-per-review", type=float, default=20.0)
    return p.parse_args()


def main():
    args = parse_args()
    capacities = tuple(int(x.strip()) for x in args.capacities.split(",") if x.strip())
    results = ROOT / "results"
    pred_path = results / "nightflow_backtest_predictions.csv"
    decision_path = results / "nightflow_promotion_decision.json"
    if not pred_path.exists() or not decision_path.exists():
        raise SystemExit("Run scripts/run_nightflow_model.py first.")

    pred = pd.read_csv(pred_path, parse_dates=["DATE"])
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    ranked = add_policy_ranks(attach_champion_signal(pred, decision))
    summary, daily = evaluate_policy_grid(ranked, capacities, args.minutes_per_review)
    stability = queue_stability(ranked, capacities)
    concentration = dma_concentration(ranked, capacities)

    summary = summary.merge(stability, on=["policy", "capacity"], how="left").merge(
        concentration, on=["policy", "capacity"], how="left"
    )
    summary.to_csv(results / "nightflow_policy_capacity_summary.csv", index=False)
    daily.to_csv(results / "nightflow_policy_daily_metrics.csv", index=False)
    stability.to_csv(results / "nightflow_policy_queue_stability.csv", index=False)
    concentration.to_csv(results / "nightflow_policy_dma_concentration.csv", index=False)

    default_capacity = 20 if 20 in capacities else capacities[0]
    cap = summary[summary["capacity"] == default_capacity].copy()
    payload = {
        "held_out_rows": int(len(ranked)),
        "held_out_dates": int(pd.to_datetime(ranked["DATE"]).nunique()),
        "champion": decision.get("champion"),
        "baseline_name": decision.get("baseline_name"),
        "total_candidates": int(ranked["candidate"].sum()),
        "candidate_rate": float(ranked["candidate"].mean()),
        "mean_candidates_per_day": float(ranked["candidate"].sum() / pd.to_datetime(ranked["DATE"]).nunique()),
        "total_positive_residual_excess": float(ranked["champion_anomaly_excess"].sum()),
        "default_capacity": default_capacity,
        "minutes_per_review_scenario": args.minutes_per_review,
        "policies_at_default_capacity": cap.set_index("policy").to_dict(orient="index"),
        "interpretation": (
            "Signal capture is the share of the frozen champion's positive upper-band residual excess retained by a review policy. "
            "It is not leak recall, recovered water, avoided incidents, ODI benefit or money saved."
        ),
    }
    (results / "nightflow_decision_value_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    fig = results / "figures"
    fig.mkdir(parents=True, exist_ok=True)
    for metric, filename, ylabel in [
        ("signal_capture", "nightflow_policy_signal_capture.png", "Residual-signal capture"),
        ("mean_consecutive_day_jaccard", "nightflow_policy_queue_stability.png", "Mean consecutive-day Jaccard"),
    ]:
        pivot = summary.pivot(index="capacity", columns="policy", values=metric)
        ax = pivot.plot(marker="o", figsize=(8, 4.8))
        ax.set_xlabel("Daily review capacity")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel + " by policy and capacity")
        ax.set_ylim(bottom=0)
        plt.tight_layout()
        plt.savefig(fig / filename, dpi=180)
        plt.close()

    table = cap[["policy", "signal_capture", "candidate_precision", "candidate_recall", "mean_consecutive_day_jaccard", "capacity_utilisation"]].copy()
    report = f"""# Night-flow decision-value evaluation — v0.6

## Evidence boundary

The forecasting champion is frozen before this evaluation. Public data do not include verified leak labels. **Signal capture** is the fraction of positive upper-band residual excess retained by a review rule; it is not leak recall or operational savings.

## Evaluation set

- Held-out observations: **{len(ranked):,}**
- Held-out dates: **{payload['held_out_dates']:,}**
- Positive upper-band candidates: **{payload['total_candidates']:,}** ({100*payload['candidate_rate']:.2f}% of observations)
- Mean candidates/day: **{payload['mean_candidates_per_day']:.1f}**
- Frozen champion: **{payload['champion']}**{(' (' + str(payload['baseline_name']) + ')') if payload['baseline_name'] else ''}

## Capacity {default_capacity}

{table.to_markdown(index=False, floatfmt='.4f')}

The `capacity_constrained` policy admits only positive candidates and leaves unused capacity empty. `anomaly_score` fills all slots, even when fewer than {default_capacity} positive candidates exist. `highest_flow` and deterministic `random` are comparison policies rather than proposed production rules.

## Operational trade-off

A policy can capture more residual signal while producing a less stable day-to-day field queue. Queue Jaccard, retention, capacity utilisation, backlog, analyst-hours scenario and DMA concentration are therefore reported alongside signal capture rather than hidden behind one score.
"""
    (results / "NIGHTFLOW_DECISION_VALUE.md").write_text(report, encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

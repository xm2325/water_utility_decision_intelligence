from pathlib import Path
import argparse
import json
import sys

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.nightflow import (  # noqa: E402
    DataContractPolicy,
    PromotionPolicy,
    data_quality_report,
    load_nightflow,
    rolling_origin_backtest,
    save_backtest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Yorkshire Water DMA night-flow rolling-origin validation")
    parser.add_argument("--splits", type=int, default=4, help="Number of expanding-window test folds")
    parser.add_argument("--capacity", type=int, default=20, help="Number of DMA investigations available in latest snapshot")
    parser.add_argument("--min-improvement", type=float, default=0.02, help="Minimum aggregate MAE improvement required to promote ML")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = sorted((ROOT / "data" / "raw" / "arcgis").glob("night_flow_*.csv"))
    if not paths:
        raise SystemExit("No night-flow CSVs found. Run scripts/download_arcgis.py first.")

    df = load_nightflow(paths)
    quality_summary, quality_by_dma = data_quality_report(df)
    predictions, folds, drift, summary = rolling_origin_backtest(df, n_splits=args.splits)
    policy = PromotionPolicy(min_relative_mae_improvement=args.min_improvement)
    decision = save_backtest(
        predictions,
        folds,
        drift,
        summary,
        ROOT / "results",
        quality_summary=quality_summary,
        quality_by_dma=quality_by_dma,
        policy=policy,
        data_contract_policy=DataContractPolicy(),
        capacity=args.capacity,
    )

    fig = ROOT / "results" / "figures"
    fig.mkdir(parents=True, exist_ok=True)

    # Fold-level champion/challenger comparison.
    p = folds[["fold", "mae_model", "mae_persistence"]].set_index("fold")
    ax = p.plot(kind="bar", figsize=(8, 4.8))
    ax.set_xlabel("Rolling-origin fold")
    ax.set_ylabel("Mean absolute error")
    ax.set_title("Night-flow forecast: ML versus persistence")
    plt.tight_layout()
    plt.savefig(fig / "nightflow_fold_mae.png", dpi=180)
    plt.close()

    # Latest operational snapshot: only information after observation is used for anomaly triage.
    priorities = pd.read_csv(ROOT / "results" / "nightflow_latest_priorities.csv")
    if len(priorities):
        top = priorities[priorities["champion_upper_exceedance"].astype(str).str.lower().isin(["true", "1"])].head(min(args.capacity, len(priorities))).sort_values("champion_investigation_score")
        plt.figure(figsize=(8, max(4.5, 0.28 * len(top))))
        plt.barh(top["DMA_ID"].astype(str), top["champion_investigation_score"])
        plt.xlabel("Investigation score (positive upper-band excess / recent variability)")
        plt.ylabel("DMA")
        plt.title(f"Latest DMA investigation queue — capacity {args.capacity}")
        plt.tight_layout()
        plt.savefig(fig / "nightflow_latest_priority_queue.png", dpi=180)
        plt.close()

    report = f"""# Night-flow ML validation — v0.4

## Evidence boundary

This report uses Yorkshire Water DMA night-flow records downloaded by the repository. The target is the observed minimum night flow at date *t*. Predictors use observations strictly before *t*. A positive upper-band exceedance is an **investigation signal**, not a verified leak label.

## Dataset

- Rows loaded: **{quality_summary['rows']:,}**
- Unique DMAs: **{quality_summary['unique_dmas']:,}**
- Date range: **{quality_summary['date_min']} to {quality_summary['date_max']}**
- Duplicate-key excess rows recorded before consolidation: **{quality_summary['duplicate_key_excess_rows']:,}**
- Reference-flow missing rate: **{100*quality_summary['reference_flow_missing_rate']:.2f}%**

## Rolling-origin validation

- Folds: **{summary['folds']}**
- Total held-out rows: **{summary['test_rows_total']:,}**
- ML MAE: **{summary['mae_model']:.4f}**
- Persistence MAE: **{summary['mae_persistence']:.4f}**
- Relative MAE improvement: **{100*summary['relative_mae_improvement']:.2f}%**
- ML upper-band coverage: **{100*summary['ml_upper_band_coverage']:.2f}%**
- Persistence upper-band coverage: **{100*summary['persistence_upper_band_coverage']:.2f}%**
- ML upper-band exceedance rate: **{100*summary['ml_upper_exceedance_rate']:.2f}%**
- Persistence upper-band exceedance rate: **{100*summary['persistence_upper_exceedance_rate']:.2f}%**
- Features with a drift flag in at least one fold: **{summary['drift_features_flagged']}**

## Champion / challenger gate

Decision: **{decision['status']}**  
Champion: **{decision['champion']}**

The ML model is promoted only if it clears the configured improvement, fold-stability and uncertainty-band checks. If it does not, the persistence baseline remains the operational champion. This avoids deploying a more complex model only because it exists.

## Operational output

`nightflow_latest_priorities.csv` ranks the latest observed DMA anomalies under a fixed investigation capacity. The score measures how far the observed night flow exceeds the **deployed champion's** calibrated upper band relative to recent DMA variability. If the ML challenger fails promotion, the operational queue uses persistence rather than ML. It supports triage after an observation arrives; it is not a statement that a leak has been confirmed.
"""
    (ROOT / "results" / "NIGHTFLOW_RESULTS.md").write_text(report, encoding="utf-8")

    print(json.dumps({"summary": summary, "promotion": decision}, indent=2))


if __name__ == "__main__":
    main()

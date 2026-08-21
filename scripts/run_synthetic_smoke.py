"""Offline integration smoke test for the night-flow pipeline.

Outputs are written under results/dev_validation and are NEVER CV evidence.
The script exists so the full ML/data-quality/governance path can be exercised
without network access.
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.nightflow import (  # noqa: E402
    data_quality_report,
    rolling_origin_backtest,
    save_backtest,
)


def build_synthetic(seed: int = 11, days: int = 365, dmas: int = 8) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=days, freq="D")
    rows = []
    for j in range(dmas):
        dma = f"S{j+1:03d}"
        base = 18 + 2.5 * j
        y = base
        for t, date in enumerate(dates):
            seasonal = 1.8 * np.sin(2 * np.pi * t / 28) + 0.8 * np.cos(2 * np.pi * t / 365)
            y = 0.65 * y + 0.35 * (base + seasonal) + rng.normal(0, 0.45)
            if (j, t) in {(0, 290), (2, 315), (4, 342)}:
                y += 5.5
            rows.append(
                {
                    "DATE": date,
                    "DMA_ID": dma,
                    "CENTROID_X": 420000 + 1200 * j,
                    "CENTROID_Y": 430000 + 700 * j,
                    "ACTUAL_MIN_NIGHT_FLOW": y,
                    "MIN_NIGHT_FLOW": base - 1.2,
                    "UNITS": "l/s",
                    "source_file": "synthetic_dev_only.csv",
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    out = ROOT / "results" / "dev_validation"
    out.mkdir(parents=True, exist_ok=True)
    df = build_synthetic()
    quality, by_dma = data_quality_report(df)
    pred, folds, drift, summary = rolling_origin_backtest(df, n_splits=4)
    decision = save_backtest(
        pred,
        folds,
        drift,
        summary,
        out,
        quality_summary=quality,
        quality_by_dma=by_dma,
        capacity=5,
    )
    (out / "README.md").write_text(
        "# Synthetic development validation\n\n"
        "These outputs validate that the pipeline executes offline. They are synthetic and must not be used as application evidence or CV metrics.\n",
        encoding="utf-8",
    )
    print(json.dumps({"summary": summary, "promotion": decision}, indent=2))


if __name__ == "__main__":
    main()

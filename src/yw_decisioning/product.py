from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import pandas as pd


RESULT_TABLES = {
    "common_pc_portfolio_2025_26.csv": "apr_common_pc_portfolio",
    "triage_capacity_curve.csv": "apr_triage_capacity_curve",
    "storm_overflow_spills_apr.csv": "apr_storm_overflow_spills",
    "nightflow_fold_metrics.csv": "nightflow_fold_metrics",
    "nightflow_drift_report.csv": "nightflow_drift_report",
    "nightflow_latest_priorities.csv": "nightflow_latest_priorities",
    "nightflow_data_quality_by_dma.csv": "nightflow_data_quality_by_dma",
    "nightflow_dma_performance.csv": "nightflow_dma_performance",
    "edm_apr_reconciliation.csv": "edm_apr_reconciliation",
    "watsit_resource_watch_2026.csv": "watsit_resource_watch_2026",
}


def build_operational_store(results_dir: str | Path, db_path: str | Path) -> dict:
    """Publish result tables into a small read-only-friendly SQLite product."""

    results_dir = Path(results_dir)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    loaded: dict[str, int] = {}
    with sqlite3.connect(db_path) as con:
        for filename, table in RESULT_TABLES.items():
            path = results_dir / filename
            if not path.exists():
                continue
            df = pd.read_csv(path)
            df.to_sql(table, con, if_exists="replace", index=False)
            loaded[table] = int(len(df))

        meta = pd.DataFrame(
            [
                {
                    "built_at_utc": datetime.now(timezone.utc).isoformat(),
                    "source_results_dir": str(results_dir.resolve()),
                    "tables_loaded": len(loaded),
                }
            ]
        )
        meta.to_sql("product_metadata", con, if_exists="replace", index=False)

        if "apr_common_pc_portfolio" in loaded:
            con.execute(
                """
                CREATE VIEW v_apr_negative_payment_priority AS
                SELECT rag_reference, line_description, pcl_met, payment_m,
                       underperformance_exposure_m, exposure_share
                FROM apr_common_pc_portfolio
                WHERE underperformance_exposure_m > 0
                ORDER BY underperformance_exposure_m DESC
                """
            )

        if "nightflow_latest_priorities" in loaded:
            con.execute(
                """
                CREATE VIEW v_current_dma_investigation_queue AS
                SELECT *
                FROM nightflow_latest_priorities
                WHERE within_capacity IN (1, 'True', 'true')
                ORDER BY priority_rank
                """
            )

        if "watsit_resource_watch_2026" in loaded:
            con.execute(
                """
                CREATE VIEW v_latest_resource_watch AS
                SELECT *
                FROM watsit_resource_watch_2026
                WHERE month_num = (SELECT MAX(month_num) FROM watsit_resource_watch_2026)
                """
            )

        if "edm_apr_reconciliation" in loaded:
            con.execute(
                """
                CREATE VIEW v_source_reconciliation_review AS
                SELECT *
                FROM edm_apr_reconciliation
                WHERE review_status <> 'matched'
                ORDER BY calendar_year DESC
                """
            )

        con.commit()

    return {"database": str(db_path), "tables": loaded}

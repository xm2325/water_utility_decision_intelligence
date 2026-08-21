import sqlite3

import pandas as pd

from yw_decisioning.governance import build_evidence_register
from yw_decisioning.live_provenance import build_live_provenance
from yw_decisioning.product import build_operational_store


def test_capacity_frontier_claims_fail_closed_after_metric_change(tmp_path):
    results = tmp_path / "results"
    arcgis = tmp_path / "data" / "raw" / "arcgis"
    results.mkdir(parents=True)
    arcgis.mkdir(parents=True)
    (arcgis / "night_flow_2026.csv").write_text("x\n1\n")
    (arcgis / "download_manifest.jsonl").write_text("{}\n")
    for name in [
        "nightflow_backtest_metrics.json", "nightflow_promotion_decision.json",
        "nightflow_decision_value_metrics.json", "nightflow_capacity_frontier_metrics.json",
    ]:
        (results / name).write_text("{}")
    for name in [
        "nightflow_policy_capacity_summary.csv", "nightflow_policy_queue_stability.csv",
        "nightflow_policy_dma_concentration.csv", "nightflow_capacity_frontier.csv",
    ]:
        (results / name).write_text("policy,capacity\na,20\n")
    build_live_provenance(tmp_path)
    register, summary = build_evidence_register(tmp_path)
    row = register[register["evidence_id"] == "nightflow_capacity_frontier"].iloc[0]
    assert row["status"] == "available"
    assert summary["capacity_frontier_claims_ready"] is True

    (results / "nightflow_capacity_frontier_metrics.json").write_text('{"changed": true}')
    _, summary2 = build_evidence_register(tmp_path)
    assert summary2["capacity_frontier_claims_ready"] is False


def test_build_operational_store_creates_capacity_marginal_view(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    pd.DataFrame({
        "policy": ["capacity_constrained", "capacity_constrained"],
        "capacity": [5, 10], "previous_capacity": [None, 5],
        "mean_selected_per_day": [5.0, 10.0], "signal_capture": [0.5, 0.7],
        "candidate_recall": [0.1, 0.2], "mean_backlog_candidates": [30.0, 25.0],
        "capacity_utilisation": [1.0, 1.0], "analyst_hours_per_day": [1.67, 3.33],
        "unused_capacity_per_day": [0.0, 0.0], "delta_nominal_capacity": [None, 5],
        "delta_selected_per_day": [None, 5.0], "delta_signal_capture_pp": [None, 20.0],
        "marginal_capture_pp_per_extra_review": [None, 4.0],
        "backlog_reduction_per_day": [None, 5.0],
        "backlog_reduction_per_extra_review": [None, 1.0],
        "incremental_analyst_hours_per_day": [None, 1.66],
        "unretained_signal_pct": [50.0, 30.0],
    }).to_csv(results / "nightflow_capacity_frontier.csv", index=False)
    db = tmp_path / "product.sqlite"
    build_operational_store(results, db)
    with sqlite3.connect(db) as con:
        rows = con.execute(
            "SELECT capacity, marginal_capture_pp_per_extra_review "
            "FROM v_nightflow_capacity_marginal_value ORDER BY capacity"
        ).fetchall()
    assert rows[1] == (10, 4.0)

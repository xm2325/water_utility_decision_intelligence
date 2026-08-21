import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.governance import build_evidence_register  # noqa: E402


def test_synthetic_metrics_are_not_accepted_as_live_evidence(tmp_path):
    (tmp_path / "results" / "dev_validation").mkdir(parents=True)
    (tmp_path / "results" / "dev_validation" / "nightflow_backtest_metrics.json").write_text("{}")
    register, summary = build_evidence_register(tmp_path)
    live = register[register["evidence_id"] == "nightflow_live_backtest"].iloc[0]
    smoke = register[register["evidence_id"] == "nightflow_synthetic_smoke"].iloc[0]
    assert live["status"] == "blocked_pending_network_run"
    assert smoke["evidence_type"] == "synthetic_validation"
    assert summary["live_nightflow_claims_ready"] is False


def test_decision_claims_require_matching_live_provenance(tmp_path):
    import json
    from yw_decisioning.live_provenance import build_live_provenance

    results = tmp_path / "results"
    arcgis = tmp_path / "data" / "raw" / "arcgis"
    results.mkdir(parents=True)
    arcgis.mkdir(parents=True)
    (arcgis / "night_flow_2026.csv").write_text("x\n1\n")
    (arcgis / "download_manifest.jsonl").write_text("{}\n")
    for name in [
        "nightflow_backtest_metrics.json",
        "nightflow_promotion_decision.json",
        "nightflow_decision_value_metrics.json",
    ]:
        (results / name).write_text("{}")
    for name in [
        "nightflow_policy_capacity_summary.csv",
        "nightflow_policy_queue_stability.csv",
        "nightflow_policy_dma_concentration.csv",
    ]:
        (results / name).write_text("policy,capacity\na,20\n")
    build_live_provenance(tmp_path)
    register, summary = build_evidence_register(tmp_path)
    decision = register[register["evidence_id"] == "nightflow_decision_value"].iloc[0]
    assert decision["status"] == "available"
    assert summary["decision_value_claims_ready"] is True

    (results / "nightflow_decision_value_metrics.json").write_text('{"changed": true}')
    _, summary2 = build_evidence_register(tmp_path)
    assert summary2["decision_value_claims_ready"] is False


def test_continuity_claims_fail_closed_after_compact_output_changes(tmp_path):
    from yw_decisioning.live_provenance import build_live_provenance

    results = tmp_path / "results"
    arcgis = tmp_path / "data" / "raw" / "arcgis"
    results.mkdir(parents=True)
    arcgis.mkdir(parents=True)
    (arcgis / "night_flow_2026.csv").write_text("x\n1\n")
    (arcgis / "download_manifest.jsonl").write_text("{}\n")
    for name in [
        "nightflow_backtest_metrics.json",
        "nightflow_promotion_decision.json",
        "nightflow_decision_value_metrics.json",
        "nightflow_continuity_metrics.json",
    ]:
        (results / name).write_text("{}")
    for name in [
        "nightflow_policy_capacity_summary.csv",
        "nightflow_policy_queue_stability.csv",
        "nightflow_policy_dma_concentration.csv",
        "nightflow_continuity_sensitivity.csv",
    ]:
        (results / name).write_text("policy,capacity\na,20\n")

    build_live_provenance(tmp_path)
    register, summary = build_evidence_register(tmp_path)
    continuity = register[register["evidence_id"] == "nightflow_queue_continuity"].iloc[0]
    assert continuity["status"] == "available"
    assert summary["continuity_claims_ready"] is True

    (results / "nightflow_continuity_metrics.json").write_text('{"changed": true}')
    register2, summary2 = build_evidence_register(tmp_path)
    continuity2 = register2[register2["evidence_id"] == "nightflow_queue_continuity"].iloc[0]
    assert continuity2["status"] == "blocked_pending_verified_live_run"
    assert summary2["continuity_claims_ready"] is False

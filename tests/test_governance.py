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

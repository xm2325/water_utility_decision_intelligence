from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from .live_provenance import CAPACITY_FRONTIER_FILES, CONTINUITY_FILES, DECISION_FILES, verify_live_provenance


def build_evidence_register(root: str | Path) -> tuple[pd.DataFrame, dict]:
    """Classify which repository outputs can support external claims."""
    root = Path(root)
    results = root / "results"
    arcgis = root / "data" / "raw" / "arcgis"
    rows: list[dict] = []

    def add(evidence_id, exists, source, artifact, allowed, prohibited, missing_status="missing"):
        rows.append({
            "evidence_id": evidence_id,
            "evidence_type": "executed_real_data" if exists else "missing",
            "status": "available" if exists else missing_status,
            "source": source,
            "artifact": artifact if exists else "",
            "allowed_claim": allowed,
            "prohibited_claim": prohibited,
        })

    apr = results / "apr_metrics.json"
    add("apr_2025_26", apr.exists(), "Yorkshire Water APR Open Data CSV", "results/apr_metrics.json",
        "APR portfolio statistics and observed payment exposure only", "avoided ODI payment or causal operational impact")

    edm = results / "edm_reconciliation_metrics.json"
    add("edm_apr_reconciliation", edm.exists(), "Yorkshire Water APR CSV + published EDM summary", "results/edm_reconciliation_metrics.json",
        "official-source agreement/mismatch statistics", "asserting which source is authoritative without reporting context")

    resource = results / "watsit_resource_watch_summary.json"
    add("watsit_resource_watch", resource.exists(), "Yorkshire Water Watsit published monthly resource data", "results/watsit_resource_watch_summary.json",
        "published rainfall/reservoir/demand context and transparent historical comparisons", "official drought classification, causal effect, or asset-failure probability")

    live_metrics = results / "nightflow_backtest_metrics.json"
    live_raw = list(arcgis.glob("night_flow_*.csv"))
    manifest = arcgis / "download_manifest.jsonl"
    has_live = live_metrics.exists() and bool(live_raw) and manifest.exists()
    rows.append({
        "evidence_id": "nightflow_live_backtest",
        "evidence_type": "executed_real_data" if has_live else "not_yet_executed",
        "status": "available" if has_live else "blocked_pending_network_run",
        "source": "Yorkshire Water ArcGIS DMA night-flow tables",
        "artifact": "results/nightflow_backtest_metrics.json" if has_live else "",
        "allowed_claim": "real rolling-backtest and champion decision metrics" if has_live else "pipeline design only",
        "prohibited_claim": "leak detection, avoided incidents, or unexecuted MAE improvement",
    })

    provenance_ok, provenance_detail = verify_live_provenance(root, required=DECISION_FILES)
    decision_metrics = results / "nightflow_decision_value_metrics.json"
    has_decision = has_live and decision_metrics.exists() and provenance_ok
    rows.append({
        "evidence_id": "nightflow_decision_value",
        "evidence_type": "executed_real_data" if has_decision else ("not_yet_executed" if not decision_metrics.exists() else "unverified_live_output"),
        "status": "available" if has_decision else "blocked_pending_verified_live_run",
        "source": "Held-out Yorkshire Water DMA night-flow predictions from the frozen champion",
        "artifact": "results/nightflow_decision_value_metrics.json" if has_decision else "",
        "allowed_claim": "residual-signal capture, candidate review burden, capacity utilisation, queue stability and DMA concentration" if has_decision else "decision-policy design only",
        "prohibited_claim": "verified leak recall, recovered water, avoided incidents, ODI recovery, staffing requirement or financial return",
    })

    frontier_metrics = results / "nightflow_capacity_frontier_metrics.json"
    frontier_required = (
        "nightflow_decision_value_metrics.json",
        "nightflow_policy_capacity_summary.csv",
        *CAPACITY_FRONTIER_FILES,
    )
    frontier_provenance_ok, frontier_provenance_detail = verify_live_provenance(root, required=frontier_required)
    has_frontier = has_live and frontier_metrics.exists() and frontier_provenance_ok
    rows.append({
        "evidence_id": "nightflow_capacity_frontier",
        "evidence_type": "executed_real_data" if has_frontier else ("not_yet_executed" if not frontier_metrics.exists() else "unverified_live_output"),
        "status": "available" if has_frontier else "blocked_pending_verified_live_run",
        "source": "Capacity-constrained policy outputs from held-out Yorkshire Water DMA night-flow predictions",
        "artifact": "results/nightflow_capacity_frontier_metrics.json" if has_frontier else "",
        "allowed_claim": "marginal residual-signal capture and candidate-backlog changes across stated capacity scenarios" if has_frontier else "capacity-frontier design only",
        "prohibited_claim": "optimal staffing, staffing savings, verified leak recall, avoided leakage, ROI or financial return",
    })

    continuity_metrics = results / "nightflow_continuity_metrics.json"
    continuity_required = (
        "nightflow_backtest_metrics.json",
        "nightflow_promotion_decision.json",
        *CONTINUITY_FILES,
    )
    continuity_provenance_ok, continuity_provenance_detail = verify_live_provenance(root, required=continuity_required)
    has_continuity = has_live and continuity_metrics.exists() and continuity_provenance_ok
    rows.append({
        "evidence_id": "nightflow_queue_continuity",
        "evidence_type": "executed_real_data" if has_continuity else ("not_yet_executed" if not continuity_metrics.exists() else "unverified_live_output"),
        "status": "available" if has_continuity else "blocked_pending_verified_live_run",
        "source": "Held-out Yorkshire Water DMA night-flow candidates from the frozen champion",
        "artifact": "results/nightflow_continuity_metrics.json" if has_continuity else "",
        "allowed_claim": "candidate-only continuity sensitivity, queue Jaccard/retention and residual-signal trade-off" if has_continuity else "continuity-policy design only",
        "prohibited_claim": "optimal continuity quota, verified leak recall, staffing savings, avoided incidents or financial return",
    })

    smoke = results / "dev_validation" / "nightflow_backtest_metrics.json"
    rows.append({
        "evidence_id": "nightflow_synthetic_smoke",
        "evidence_type": "synthetic_validation" if smoke.exists() else "missing",
        "status": "available" if smoke.exists() else "missing",
        "source": "repository-generated synthetic DMA time series",
        "artifact": "results/dev_validation/nightflow_backtest_metrics.json" if smoke.exists() else "",
        "allowed_claim": "software integration and gate-behaviour validation",
        "prohibited_claim": "CV performance metric or Yorkshire Water operational result",
    })

    register = pd.DataFrame(rows)
    summary = {
        "real_evidence_items_available": int(((register["evidence_type"] == "executed_real_data") & (register["status"] == "available")).sum()),
        "live_nightflow_claims_ready": bool(has_live),
        "decision_value_claims_ready": bool(has_decision),
        "capacity_frontier_claims_ready": bool(has_frontier),
        "continuity_claims_ready": bool(has_continuity),
        "live_provenance_verified": bool(provenance_ok),
        "live_provenance_detail": provenance_detail,
        "capacity_frontier_provenance_verified": bool(frontier_provenance_ok),
        "capacity_frontier_provenance_detail": frontier_provenance_detail,
        "continuity_provenance_verified": bool(continuity_provenance_ok),
        "continuity_provenance_detail": continuity_provenance_detail,
        "application_claim_boundary": (
            "Executed public-data claims may cover APR portfolio statistics, source reconciliation, Watsit context, "
            "night-flow backtest/governance metrics and, when provenance verifies, residual-signal capture, review-workload, marginal capacity-frontier and candidate-only queue-continuity sensitivity metrics. "
            "Do not describe anomaly signals as confirmed leaks, call a capacity or continuity setting optimal, or convert signals into avoided incidents, recovered water, ODI recovery or financial return."
        ),
    }
    return register, summary


def save_evidence_register(root: str | Path) -> dict:
    root = Path(root)
    register, summary = build_evidence_register(root)
    out = root / "results"
    out.mkdir(parents=True, exist_ok=True)
    register.to_csv(out / "EVIDENCE_REGISTER.csv", index=False)
    (out / "evidence_register_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    status = "READY" if (
        summary["live_nightflow_claims_ready"]
        and (not (out / "nightflow_decision_value_metrics.json").exists() or summary["decision_value_claims_ready"])
        and (not (out / "nightflow_capacity_frontier_metrics.json").exists() or summary["capacity_frontier_claims_ready"])
        and (not (out / "nightflow_continuity_metrics.json").exists() or summary["continuity_claims_ready"])
    ) else "BLOCKED FOR UNVERIFIED LIVE CLAIMS"
    report = f"""# Release readiness — v0.8

**Status: {status}**

This register separates executed public-data evidence from synthetic development validation and unverified compact outputs.

- Real evidence items available: **{summary['real_evidence_items_available']}**
- Live night-flow claims ready: **{summary['live_nightflow_claims_ready']}**
- Decision-value claims ready: **{summary['decision_value_claims_ready']}**
- Capacity-frontier claims ready: **{summary['capacity_frontier_claims_ready']}**
- Continuity claims ready: **{summary['continuity_claims_ready']}**
- Live provenance verified: **{summary['live_provenance_verified']}**
- Capacity-frontier provenance verified: **{summary['capacity_frontier_provenance_verified']}**
- Continuity provenance verified: **{summary['continuity_provenance_verified']}**

## Application boundary

{summary['application_claim_boundary']}

`EVIDENCE_REGISTER.csv` records what can and cannot be claimed externally. `live_validation_provenance.json` binds compact live metrics to an executed run without committing the large raw ArcGIS tables or held-out prediction file to Git.
"""
    (out / "RELEASE_READINESS.md").write_text(report, encoding="utf-8")
    return summary

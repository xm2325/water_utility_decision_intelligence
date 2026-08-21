from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


def build_evidence_register(root: str | Path) -> tuple[pd.DataFrame, dict]:
    """Classify which repository outputs can support external claims."""

    root = Path(root)
    results = root / "results"
    arcgis = root / "data" / "raw" / "arcgis"
    rows: list[dict] = []

    apr_metrics = results / "apr_metrics.json"
    rows.append(
        {
            "evidence_id": "apr_2025_26",
            "evidence_type": "executed_real_data" if apr_metrics.exists() else "missing",
            "status": "available" if apr_metrics.exists() else "missing",
            "source": "Yorkshire Water APR Open Data CSV",
            "artifact": str(apr_metrics.relative_to(root)) if apr_metrics.exists() else "",
            "allowed_claim": "APR portfolio statistics and observed payment exposure only",
            "prohibited_claim": "avoided ODI payment or causal operational impact",
        }
    )

    edm_metrics = results / "edm_reconciliation_metrics.json"
    rows.append(
        {
            "evidence_id": "edm_apr_reconciliation",
            "evidence_type": "executed_real_data" if edm_metrics.exists() else "missing",
            "status": "available" if edm_metrics.exists() else "missing",
            "source": "Yorkshire Water APR CSV + published EDM summary",
            "artifact": str(edm_metrics.relative_to(root)) if edm_metrics.exists() else "",
            "allowed_claim": "official-source agreement/mismatch statistics",
            "prohibited_claim": "asserting which source is authoritative without reporting context",
        }
    )

    resource_metrics = results / "watsit_resource_watch_summary.json"
    rows.append(
        {
            "evidence_id": "watsit_resource_watch",
            "evidence_type": "executed_real_data" if resource_metrics.exists() else "missing",
            "status": "available" if resource_metrics.exists() else "missing",
            "source": "Yorkshire Water Watsit published monthly resource data",
            "artifact": str(resource_metrics.relative_to(root)) if resource_metrics.exists() else "",
            "allowed_claim": "published rainfall/reservoir/demand context and transparent historical comparisons",
            "prohibited_claim": "official drought classification, causal effect, or asset-failure probability",
        }
    )

    live_metrics = results / "nightflow_backtest_metrics.json"
    live_raw = list(arcgis.glob("night_flow_*.csv"))
    manifest = arcgis / "download_manifest.jsonl"
    has_live = live_metrics.exists() and len(live_raw) >= 1 and manifest.exists()
    rows.append(
        {
            "evidence_id": "nightflow_live_backtest",
            "evidence_type": "executed_real_data" if has_live else "not_yet_executed",
            "status": "available" if has_live else "blocked_pending_network_run",
            "source": "Yorkshire Water ArcGIS DMA night-flow tables",
            "artifact": str(live_metrics.relative_to(root)) if has_live else "",
            "allowed_claim": "real rolling-backtest and champion decision metrics" if has_live else "pipeline design only",
            "prohibited_claim": "leak detection, avoided incidents, or unexecuted MAE improvement",
        }
    )

    smoke = results / "dev_validation" / "nightflow_backtest_metrics.json"
    rows.append(
        {
            "evidence_id": "nightflow_synthetic_smoke",
            "evidence_type": "synthetic_validation" if smoke.exists() else "missing",
            "status": "available" if smoke.exists() else "missing",
            "source": "repository-generated synthetic DMA time series",
            "artifact": str(smoke.relative_to(root)) if smoke.exists() else "",
            "allowed_claim": "software integration and gate-behaviour validation",
            "prohibited_claim": "CV performance metric or Yorkshire Water operational result",
        }
    )

    register = pd.DataFrame(rows)
    summary = {
        "real_evidence_items_available": int(
            ((register["evidence_type"] == "executed_real_data") & (register["status"] == "available")).sum()
        ),
        "live_nightflow_claims_ready": bool(has_live),
        "application_claim_boundary": (
            "APR, source-reconciliation and Watsit resource-watch statistics are currently usable. "
            "Night-flow performance metrics remain blocked until a network-enabled real-data run produces "
            "raw ArcGIS files, provenance manifest and root-level backtest metrics."
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

    status = "READY" if summary["live_nightflow_claims_ready"] else "BLOCKED FOR LIVE NIGHT-FLOW CLAIMS"
    report = f"""# Release readiness — v0.4

**Status: {status}**

This register separates executed official-data evidence from synthetic development validation.

- Real evidence items available: **{summary['real_evidence_items_available']}**
- Live night-flow claims ready: **{summary['live_nightflow_claims_ready']}**

## Application boundary

{summary['application_claim_boundary']}

`EVIDENCE_REGISTER.csv` records, for each output, what can and cannot be claimed externally. This prevents synthetic smoke-test metrics or unexecuted live-data designs from leaking into the CV or interview evidence.
"""
    (out / "RELEASE_READINESS.md").write_text(report, encoding="utf-8")
    return summary

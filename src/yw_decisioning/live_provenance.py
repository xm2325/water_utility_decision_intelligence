from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

DECISION_FILES = (
    "nightflow_backtest_metrics.json",
    "nightflow_promotion_decision.json",
    "nightflow_policy_capacity_summary.csv",
    "nightflow_policy_queue_stability.csv",
    "nightflow_policy_dma_concentration.csv",
    "nightflow_decision_value_metrics.json",
)

CONTINUITY_FILES = (
    "nightflow_continuity_sensitivity.csv",
    "nightflow_continuity_metrics.json",
)

LIVE_FILES = DECISION_FILES + CONTINUITY_FILES


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_live_provenance(root: str | Path) -> dict:
    root = Path(root)
    results = root / "results"
    files = {}
    for name in LIVE_FILES:
        path = results / name
        if path.exists():
            files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "interpretation": "Hashes bind compact live outputs to one executed run; raw ArcGIS records remain workflow artifacts rather than Git-tracked evidence.",
    }
    (results / "live_validation_provenance.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def verify_live_provenance(root: str | Path, required: tuple[str, ...] = LIVE_FILES) -> tuple[bool, dict]:
    root = Path(root)
    path = root / "results" / "live_validation_provenance.json"
    if not path.exists():
        return False, {"reason": "provenance_missing"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    for name in required:
        target = root / "results" / name
        recorded = payload.get("files", {}).get(name, {}).get("sha256")
        if not target.exists() or not recorded:
            problems.append(f"missing:{name}")
        elif sha256_file(target) != recorded:
            problems.append(f"hash_mismatch:{name}")
    return not problems, {"problems": problems, "files_checked": len(required)}

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_tests() -> int:
    total = 0
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        total += sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_") for n in ast.walk(tree))
    return total

key_paths = [
    ROOT / "README.md",
    RESULTS / "apr_metrics.json",
    RESULTS / "edm_reconciliation_metrics.json",
    RESULTS / "watsit_resource_watch_summary.json",
    RESULTS / "EVIDENCE_REGISTER.csv",
    RESULTS / "operational_decision_product.sqlite",
]
manifest = {
    "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
    "built_at_utc": datetime.now(timezone.utc).isoformat(),
    "automated_test_functions": count_tests(),
    "live_nightflow_claims_ready": json.loads((RESULTS / "evidence_register_summary.json").read_text())["live_nightflow_claims_ready"],
    "artifacts": [
        {
            "path": str(p.relative_to(ROOT)),
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
        for p in key_paths if p.exists()
    ],
}
(RESULTS / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest, indent=2))

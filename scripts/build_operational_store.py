from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.product import build_operational_store  # noqa: E402


if __name__ == "__main__":
    out = build_operational_store(ROOT / "results", ROOT / "results" / "operational_decision_product.sqlite")
    print(json.dumps(out, indent=2))

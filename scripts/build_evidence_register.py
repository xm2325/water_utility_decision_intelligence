from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.governance import save_evidence_register  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(save_evidence_register(ROOT), indent=2))

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.live_provenance import build_live_provenance  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(build_live_provenance(ROOT), indent=2))

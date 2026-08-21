from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.resource_watch import save_resource_watch

summary = save_resource_watch(
    ROOT / "data" / "raw" / "watsit" / "watsit_monthly_snapshot.csv",
    ROOT / "results",
    ROOT / "data" / "raw" / "watsit" / "current_status_2026_07.json",
)
print(summary)

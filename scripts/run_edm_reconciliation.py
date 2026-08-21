from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.apr import extract_storm_overflow_spills, read_apr_csv  # noqa: E402
from yw_decisioning.edm import read_edm_summary, reconcile_apr_spills, save_reconciliation  # noqa: E402


def main() -> None:
    apr_paths = sorted((ROOT / "data" / "raw" / "apr").glob("apr_*.csv"))
    if not apr_paths:
        raise SystemExit("No APR CSV files found")
    apr_parts = [extract_storm_overflow_spills(read_apr_csv(p)) for p in apr_paths]
    import pandas as pd

    apr = pd.concat(apr_parts, ignore_index=True).drop_duplicates()
    edm = read_edm_summary(ROOT / "data" / "raw" / "edm" / "edm_published_summary.csv")
    table, metrics = reconcile_apr_spills(apr, edm)
    save_reconciliation(table, metrics, ROOT / "results")

    report = f"""# Official source reconciliation — APR vs EDM

The APR spill-count line and Yorkshire Water's current EDM summary are both official publications, but they are versioned through different reporting processes. This check does not silently overwrite one with the other.

- Comparable years: **{metrics['comparable_years']}**
- Exact matches: **{metrics['matched_years']}**
- Years requiring review: **{metrics['years_requiring_review']}**
- Largest absolute difference: **{metrics['max_absolute_difference']:.0f} spills**
- Largest relative difference: **{100*metrics['max_absolute_relative_difference']:.3f}%**

A mismatch is treated as a data-governance event, not a modelling error. The pipeline keeps both values, source identifiers and retrieval date so downstream users can choose the appropriate publication for their decision context.
"""
    (ROOT / "results" / "EDM_RECONCILIATION.md").write_text(report, encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


def read_edm_summary(path: str | Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    required = {
        "year",
        "storm_overflows_with_data",
        "total_discharges",
        "total_duration_hours",
        "source_url",
        "retrieved_date",
    }
    missing = required - set(d.columns)
    if missing:
        raise ValueError(f"EDM summary missing columns: {sorted(missing)}")
    d["year"] = pd.to_numeric(d["year"], errors="raise").astype(int)
    for c in ["storm_overflows_with_data", "total_discharges", "total_duration_hours"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.sort_values("year").reset_index(drop=True)


def reconcile_apr_spills(apr_spills: pd.DataFrame, edm: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Compare APR-reported annual spill counts with the current EDM summary.

    A mismatch is not auto-corrected. The output is a source-reconciliation
    queue for human review because publication timing and assurance status can
    differ across official sources.
    """

    a = apr_spills.copy()
    a["apr_year_end"] = a["year"].astype(str).str.extract(r"(20\d{2})").iloc[:, 0]
    # APR labels are financial years such as 2025/26 but the line itself states
    # that spills cover 1 Jan to 31 Dec; use the starting calendar year.
    a["calendar_year"] = pd.to_numeric(a["apr_year_end"], errors="coerce").astype("Int64")
    a = a.rename(columns={"spills": "apr_total_discharges"})

    e = edm.rename(columns={"year": "calendar_year", "total_discharges": "edm_total_discharges"}).copy()
    merged = a.merge(
        e[
            [
                "calendar_year",
                "edm_total_discharges",
                "storm_overflows_with_data",
                "total_duration_hours",
                "source_url",
                "retrieved_date",
            ]
        ],
        on="calendar_year",
        how="outer",
    ).sort_values("calendar_year")

    merged["absolute_difference"] = merged["edm_total_discharges"] - merged["apr_total_discharges"]
    merged["relative_difference"] = merged["absolute_difference"] / merged["apr_total_discharges"].replace(0, pd.NA)
    merged["match"] = merged["absolute_difference"].fillna(float("inf")).eq(0)
    merged["review_status"] = merged["match"].map({True: "matched", False: "review"})
    merged.loc[merged["apr_total_discharges"].isna() | merged["edm_total_discharges"].isna(), "review_status"] = "source_missing"

    comparable = merged.dropna(subset=["apr_total_discharges", "edm_total_discharges"])
    mismatches = comparable[~comparable["match"]]
    metrics = {
        "comparable_years": int(len(comparable)),
        "matched_years": int(comparable["match"].sum()),
        "mismatched_years": int((~comparable["match"]).sum()),
        "max_absolute_difference": float(comparable["absolute_difference"].abs().max()) if len(comparable) else None,
        "max_absolute_relative_difference": float(comparable["relative_difference"].abs().max()) if len(comparable) else None,
        "years_requiring_review": [int(x) for x in mismatches["calendar_year"].tolist()],
        "interpretation": (
            "Official-source mismatches are surfaced for review and are not automatically reconciled. "
            "A mismatch does not by itself identify which publication is authoritative for a given use."
        ),
    }
    return merged.reset_index(drop=True), metrics


def save_reconciliation(table: pd.DataFrame, metrics: dict, output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "edm_apr_reconciliation.csv", index=False)
    (out / "edm_reconciliation_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

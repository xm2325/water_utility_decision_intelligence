from __future__ import annotations

from pathlib import Path
import re
import pandas as pd


def _canonical_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {}
    for c in df.columns:
        key = re.sub(r"\s+", " ", c.strip().lower())
        if key == "line description":
            mapping[c] = "line_description"
        elif key == "rag 4 reference":
            mapping[c] = "rag_reference"
        elif key == "item reference":
            mapping[c] = "item_reference"
        else:
            mapping[c] = key.replace(" ", "_")
    return df.rename(columns=mapping)


def read_apr_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df = _canonical_columns(df)
    required = {"company", "year", "line_description", "attribute", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"APR file {path} missing required columns: {sorted(missing)}")
    return df


def extract_common_pc_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    """Extract PR24 common 3A performance-commitment rows.

    One row is returned per RAG 3A reference. Values are kept as reported;
    only payment is coerced to numeric for portfolio calculations.
    """
    d = df[df["rag_reference"].astype(str).str.match(r"^3A\.\d+$", na=False)].copy()
    if d.empty:
        return pd.DataFrame()
    idx = ["rag_reference", "line_description", "units"]
    p = d.pivot_table(index=idx, columns="attribute", values="value", aggfunc="first").reset_index()
    p.columns.name = None

    payment_col = "Outperformance or underperformance payment"
    total_col = "Total 2025-30 outperformance or underperformance payment"
    pcl_col = "PCL met? (Yes/No)"
    actual_col = "Performance level - actual"

    p["actual_reported"] = p[actual_col] if actual_col in p.columns else pd.NA
    p["pcl_met"] = p[pcl_col] if pcl_col in p.columns else pd.NA
    p["payment_m"] = pd.to_numeric(p[payment_col], errors="coerce") if payment_col in p.columns else pd.NA
    p["total_2025_30_payment_m"] = (
        pd.to_numeric(p[total_col], errors="coerce") if total_col in p.columns else pd.NA
    )
    p["underperformance_exposure_m"] = (-p["payment_m"]).clip(lower=0)
    total_exposure = p["underperformance_exposure_m"].sum(skipna=True)
    p["exposure_share"] = (
        p["underperformance_exposure_m"] / total_exposure if total_exposure > 0 else 0.0
    )
    return p.sort_values(["underperformance_exposure_m", "rag_reference"], ascending=[False, True])


def capacity_curve(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Observed exposure covered by investigating top-k negatively paid PCs.

    This is a triage curve, not an estimate of avoidable payment. It assumes only
    that a team can focus on k workstreams and asks what share of already observed
    negative-payment exposure those workstreams account for.
    """
    p = portfolio[portfolio["underperformance_exposure_m"] > 0].copy()
    p = p.sort_values("underperformance_exposure_m", ascending=False).reset_index(drop=True)
    gross = p["underperformance_exposure_m"].sum()
    rows = []
    cumulative = 0.0
    for i, r in p.iterrows():
        cumulative += float(r["underperformance_exposure_m"])
        rows.append(
            {
                "capacity_workstreams": i + 1,
                "cumulative_observed_exposure_m": cumulative,
                "observed_exposure_share": cumulative / gross if gross else 0.0,
                "last_added_pc": r["line_description"],
                "last_added_reference": r["rag_reference"],
            }
        )
    return pd.DataFrame(rows)


def extract_storm_overflow_spills(df: pd.DataFrame) -> pd.DataFrame:
    target = "Number of spills from storm overflows (from 1 January to 31 December)"
    d = df[df["line_description"].astype(str).str.strip().eq(target)].copy()
    if d.empty:
        return pd.DataFrame(columns=["year", "spills"])
    d["spills"] = pd.to_numeric(d["value"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    return d[["year", "spills"]].dropna().drop_duplicates()

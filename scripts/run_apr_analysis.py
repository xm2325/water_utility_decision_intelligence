from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.apr import read_apr_csv, extract_common_pc_portfolio, capacity_curve, extract_storm_overflow_spills

APR = ROOT / "data" / "raw" / "apr"
RESULTS = ROOT / "results"
FIG = RESULTS / "figures"
RESULTS.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

files = [APR / "apr_2023_24.csv", APR / "apr_2024_25.csv", APR / "apr_2025_26.csv"]
frames = {p.stem.replace("apr_", "").replace("_", "-"): read_apr_csv(p) for p in files}

latest = frames["2025-26"]
portfolio = extract_common_pc_portfolio(latest)
portfolio.to_csv(RESULTS / "common_pc_portfolio_2025_26.csv", index=False)
curve = capacity_curve(portfolio)
curve.to_csv(RESULTS / "triage_capacity_curve.csv", index=False)

spills = pd.concat([extract_storm_overflow_spills(df) for df in frames.values()], ignore_index=True)
spills = spills.sort_values("year")
spills.to_csv(RESULTS / "storm_overflow_spills_apr.csv", index=False)

neg = portfolio[portfolio["underperformance_exposure_m"] > 0].copy()
gross = neg["underperformance_exposure_m"].sum()
pos = portfolio.loc[portfolio["payment_m"] > 0, "payment_m"].sum()
net = portfolio["payment_m"].sum(skipna=True)
not_met = int((portfolio["pcl_met"].astype(str).str.strip().str.lower() == "no").sum())
with_payment = int(portfolio["payment_m"].notna().sum())
top3 = neg.head(3)["underperformance_exposure_m"].sum()

# Plot 1: negative payment exposure
plot_df = neg.sort_values("underperformance_exposure_m")
plt.figure(figsize=(9, 6))
plt.barh(plot_df["line_description"], plot_df["underperformance_exposure_m"])
plt.xlabel("Observed underperformance payment exposure (£m)")
plt.ylabel("")
plt.title("Yorkshire Water 2025/26 common performance commitments")
plt.tight_layout()
plt.savefig(FIG / "underperformance_exposure.png", dpi=180)
plt.close()

# Plot 2: capacity curve
plt.figure(figsize=(7, 4.5))
plt.plot(curve["capacity_workstreams"], 100 * curve["observed_exposure_share"], marker="o")
plt.xlabel("Number of workstreams prioritised")
plt.ylabel("Share of observed negative-payment exposure (%)")
plt.title("Triage concentration curve")
plt.ylim(0, 105)
plt.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(FIG / "triage_capacity_curve.png", dpi=180)
plt.close()

# Plot 3: storm overflow spills across APR files
if len(spills) >= 2:
    plt.figure(figsize=(6, 4.5))
    plt.plot(spills["year"], spills["spills"], marker="o")
    plt.ylabel("Reported number of spills")
    plt.xlabel("APR reporting year")
    plt.title("Storm-overflow spill count reported in APR open data")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(FIG / "storm_overflow_spills.png", dpi=180)
    plt.close()

spill_change = None
if len(spills) >= 2 and spills.iloc[0]["spills"]:
    spill_change = (spills.iloc[-1]["spills"] - spills.iloc[0]["spills"]) / spills.iloc[0]["spills"]

summary = f"""# Yorkshire Water ODI / Regulatory Decision Product — v0.4 results

## Data actually used

The analysis ran on Yorkshire Water official APR Open Data CSV files for 2023/24, 2024/25 and 2025/26. The latest file contains **{len(latest):,} rows**.

## 2025/26 common performance-commitment portfolio

The parser found **{len(portfolio)}** common 3A rows, including **{with_payment}** with a numeric outperformance/underperformance payment. Across all common 3A rows, **{not_met}** were explicitly reported as not meeting their PCL; **{int(((portfolio["payment_m"].notna()) & (portfolio["pcl_met"].astype(str).str.strip().str.lower() == "no")).sum())}** of those PCL misses also had a numeric payment in this extract.

Gross observed negative-payment exposure across the parsed common 3A measures is **£{gross:.2f}m**. Positive payments across those measures total **£{pos:.2f}m**, giving a net parsed payment of **£{net:.2f}m**. This is a deliberately narrow extract of common 3A measures and must not be presented as Yorkshire Water's total company ODI position.

The three largest observed negative-payment workstreams are:

1. **{neg.iloc[0]['line_description']}** — £{neg.iloc[0]['underperformance_exposure_m']:.2f}m
2. **{neg.iloc[1]['line_description']}** — £{neg.iloc[1]['underperformance_exposure_m']:.2f}m
3. **{neg.iloc[2]['line_description']}** — £{neg.iloc[2]['underperformance_exposure_m']:.2f}m

Together these account for **{100*top3/gross:.1f}%** of observed negative-payment exposure in the extracted portfolio. This is useful for triage under limited team capacity, but it is **not** an estimate that these payments are avoidable.

## Storm-overflow reporting signal

The same APR line, `Number of spills from storm overflows (from 1 January to 31 December)`, is present in all three files. Reported values are:

{spills.to_markdown(index=False)}

The first-to-latest change is **{100*spill_change:.1f}%**. This is a descriptive reporting trend only; the project does not infer causality from it.

## Next real-data layer

The repository includes an ArcGIS FeatureServer downloader and a temporal night-flow ML backtest. Yorkshire Water's 2026 night-flow layer exposes `DATE`, `DMA_ID`, `ACTUAL_MIN_NIGHT_FLOW`, `MIN_NIGHT_FLOW` and coordinates. The model forecasts each dated minimum-night-flow observation from strictly prior DMA history and ranks upper-band exceedances for investigation. Such residuals are an operational signal, **not a confirmed leak label**.
"""
(RESULTS / "RESULTS.md").write_text(summary, encoding="utf-8")

import json
apr_metrics = {
    "latest_rows": int(len(latest)),
    "common_3a_rows": int(len(portfolio)),
    "common_3a_with_numeric_payment": with_payment,
    "common_3a_pcl_not_met": not_met,
    "common_3a_pcl_not_met_with_numeric_payment": int(((portfolio["payment_m"].notna()) & (portfolio["pcl_met"].astype(str).str.strip().str.lower() == "no")).sum()),
    "gross_negative_payment_exposure_m": float(gross),
    "positive_payments_m": float(pos),
    "net_parsed_payment_m": float(net),
    "top3_negative_payment_share": float(top3 / gross) if gross else None,
    "storm_overflow_first_to_latest_change": float(spill_change) if spill_change is not None else None,
    "evidence_boundary": "Common 3A extract only; not Yorkshire Water's total company ODI position and not an estimate of avoidable payments.",
}
(RESULTS / "apr_metrics.json").write_text(json.dumps(apr_metrics, indent=2), encoding="utf-8")
print(summary)

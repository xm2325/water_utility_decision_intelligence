# CV bullets — v0.5 evidence rules

## Recommended version — executed Yorkshire Water public data

**Water Utility Decision Intelligence | Python, ML, SQL, Decision Modelling**

- Built a reproducible decision-support product over **121,937 rows of Yorkshire Water's official 2025/26 APR open data**, parsing **36 common performance-commitment rows** and **18 numeric payment measures** with explicit source and evidence controls.
- Quantified **£76.75m gross negative-payment exposure** within the extracted common-3A payment portfolio and built a capacity-aware triage curve; serious pollution, total pollution and internal sewer flooding represented **66.8%** of observed negative-payment exposure.
- Validated **424,695 official DMA night-flow records across 345 DMAs** using four rolling-origin folds: HistGradientBoosting reduced aggregate MAE from **0.15931 to 0.15747 (1.15%)** and improved **83.8% of DMAs**, but the governance gate retained the simple baseline because the improvement was below the 2% promotion margin and the worst fold was **5.24% worse**.
- Built a champion-consistent operational queue with calibrated upper-band exceedances and a fixed field-team capacity; on the latest **19 August 2026** snapshot, **46 DMA observations** were investigation candidates and only the top **20** entered the capacity-limited action queue. These are review signals, not confirmed leak labels.
- Added cross-source assurance and operational context: reconciled APR spill counts against Yorkshire Water's published EDM series, surfacing a **156-event (0.303%) 2025 source-version difference** for review rather than silently overwriting it, and built a monthly rainfall/reservoir/demand watch layer.
- Published compact outputs through tested Python pipelines and a **SQLite operational layer**, with source pinning, data contracts, drift checks, champion/challenger rules and an evidence register that separates real-data results from synthetic development validation.

For a one-page CV, the strongest three bullets for the Yorkshire Water Senior Data Scientist role are the first, third and sixth. Add the second if ODI/regulatory prioritisation is central to the application; add the fourth if operational product ownership is central.

## Evidence boundary

The night-flow figures above are from the successful GitHub Actions real-data run on 21 August 2026. The v0.5 baseline-selection refactor retains these ML predictions and will rerun the full workflow before merge. Do not claim that the project detected leaks, prevented pollution incidents, saved ODI penalties, implemented an official drought classifier, or deployed Azure/Databricks. Numerical metrics from `results/dev_validation/` remain synthetic development evidence and must not be used as Yorkshire Water operational results.

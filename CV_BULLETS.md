# CV bullets — v0.4 evidence rules

## Recommended version now — executed real Yorkshire Water data only

**Yorkshire Water Operational Decision Intelligence | Python, ML, SQL, Decision Modelling**

- Built a reproducible decision-support product over **121,937 rows of Yorkshire Water's official 2025/26 APR open data**, parsing **36 common performance-commitment rows** and **18 numeric payment measures** with explicit source and evidence controls.
- Quantified **£76.75m gross negative-payment exposure** within the extracted common-3A payment portfolio and built a capacity-aware triage curve; serious pollution, total pollution and internal sewer flooding represented **66.8%** of observed negative-payment exposure.
- Added **cross-source assurance and operational context**: reconciled APR spill counts against Yorkshire Water's published EDM series, surfacing a **156-event (0.303%) 2025 source-version difference** for review rather than silently overwriting it, and built a monthly rainfall/reservoir/demand watch layer for analyst use.
- Published results through tested Python pipelines and a **SQLite operational layer** with stable SQL views, plus data-contract, source-provenance and release-readiness controls that prevent synthetic or unexecuted model metrics from entering external claims.

For a one-page CV, use the first, second and fourth bullets. Use the third when the role places high weight on model/data governance or operational assurance.

## Use only after the network-enabled real-data workflow has completed

Replace bracketed values only from root-level `results/nightflow_backtest_metrics.json`, `nightflow_dma_performance.csv`, `nightflow_promotion_decision.json` and `data/raw/arcgis/download_manifest.jsonl`:

- Built a time-aware forecasting and anomaly-triage pipeline over **[real row count] Yorkshire Water DMA night-flow records across [date range / N DMAs]**, using calendar-time lagged features and expanding-window validation against a persistence baseline.
- **[Improved MAE by X% and promoted ML / retained persistence because ML did not pass the production gate]** across **[N] rolling folds**, with aggregate, worst-fold, per-DMA, uncertainty-coverage and data-contract checks.
- Generated a capacity-constrained **DMA investigation queue** from the deployed champion's calibrated upper-band exceedances and recent variability, treating alerts as operational review signals rather than confirmed leak labels.

## Evidence boundary

Do not claim that the project detected leaks, prevented pollution incidents, saved ODI penalties, implemented an official drought classifier, or deployed Azure/Databricks. Do not use numerical metrics from `results/dev_validation/`; those are synthetic integration tests.

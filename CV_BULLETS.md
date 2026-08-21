# CV bullets — v0.6 evidence rules

## Recommended Yorkshire Water / utility Senior Data Scientist version

**Water Utility Decision Intelligence | Python, ML, SQL, Decision Modelling**

- Built a reproducible decision-support product over **121,937 rows of Yorkshire Water's official 2025/26 APR open data**, extracting 36 common performance-commitment rows and quantifying **£76.75m gross negative-payment exposure** within the parsed common-3A payment portfolio.
- Validated **424,695 official DMA night-flow records across 345 DMAs** with four rolling-origin folds; HistGradientBoosting reduced MAE from **0.15931 to 0.15747 (1.15%)** and improved **83.8% of DMAs**, but a pre-set governance gate retained persistence because the gain was below 2% and the worst fold was **5.24% worse**.
- Converted the frozen champion into a capacity-aware review product over **210,841 held-out observations**: at **20 DMA reviews/day**, the constrained anomaly queue selected **52.6% of candidate alerts while retaining 85.3% of positive residual-excess signal**, versus **38.9%** for highest-flow and **5.5%** for deterministic random selection.
- Added operational assurance through source pinning, data contracts, drift checks, APR↔EDM reconciliation, queue-stability and DMA-concentration monitoring, and published compact outputs through a **SQLite decision layer** and evidence register.

Until v0.6 live verification completes, use bullets 1, 2 and 4. After verification, replace bullet 3 with the executed capacity-policy figures from the evidence register and then use bullets 1–3. Add bullet 4 when the role stresses product ownership, governance or SQL/data-product delivery.

## Optional regulatory bullet

- Reconciled APR spill counts against Yorkshire Water's published EDM series, surfacing a **156-event (0.303%) 2025 source-version difference** for review rather than silently overwriting it; also built a rainfall/reservoir/demand operational-context layer.

## Evidence boundary

The night-flow model figures above come from a successful GitHub Actions run against Yorkshire Water's public ArcGIS DMA data. The v0.6 policy figures are pre-release replay results until the v0.6 network workflow reproduces them and the evidence register marks decision-value claims as available. "Positive residual-excess signal" is a model-residual proxy, not a verified leak label or recovered water volume. Do not claim detected leaks, avoided incidents, saved ODI penalties, an official drought classifier, or an executed Azure/Databricks deployment.

# CV bullets — v1.0 verified evidence

## Recommended three bullets

**Water Utility Decision Intelligence | Python, ML, SQL, Decision Modelling**

- Built a reproducible decision-support pipeline over **424,695 Yorkshire Water DMA night-flow records across 345 DMAs**, using four rolling-origin folds and **210,841 held-out predictions**; a pre-set governance gate retained persistence after HistGradientBoosting improved MAE by only **1.15%** and was **5.24% worse in the weakest fold**.
- Converted the frozen champion into a capacity-aware review product: at **20 DMA reviews/day**, the candidate-constrained queue reviewed **52.6% of candidate alerts while retaining 85.3% of positive residual-excess signal**, versus **38.9%** for highest-flow selection; 7-day moving-block bootstrap placed the 95% capture interval at **82.4%–88.2%**.
- Tested decision robustness rather than relying on a single average: the same frozen policy beat highest-flow in **8/8 calendar-quarter slices** while absolute capture ranged from **76.9% to 95.1%**; added capacity-return, queue-continuity, data-contract and provenance controls in a tested Python/SQLite product.

## Optional regulatory/data-assurance bullet

- Parsed **121,937 rows** of official 2025/26 APR open data and quantified **£76.75m gross negative-payment exposure** within a narrow common-3A numeric-payment extract; reconciled APR and EDM spill totals and routed a **156-event (0.303%) 2025 source-version difference** to review rather than silently overwriting it.

## Claim boundary

“Positive residual-excess signal” is a model-residual proxy, not verified leak recall or recovered water. Do not claim detected leaks, avoided incidents, saved ODI penalties, optimal staffing, an official drought classification, or an executed Azure/Databricks deployment.

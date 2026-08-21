# Water Utility Decision Intelligence — v1.0

**Independent portfolio project using publicly available Yorkshire Water data; not affiliated with or endorsed by Yorkshire Water.**

A reproducible decision-support case study for a Senior Data Scientist role in a regulated utility. The project starts with reported regulatory outcomes, then moves to DMA night-flow forecasting, model governance, capacity-aware review queues and operational assurance. It treats a model as one component of a decision product rather than the end result.

## Verified results at a glance

All figures below were reproduced by GitHub Actions on 21 August 2026 from the public-data pipeline. Compact outputs are tied to the live run by SHA-256 hashes; large raw ArcGIS tables remain workflow artifacts rather than Git-tracked files.

| Layer | Verified result |
|---|---|
| APR regulatory triage | 121,937 rows in the official 2025/26 APR release; £76.75m gross negative-payment exposure in the narrow parsed common-3A numeric-payment portfolio |
| Night-flow data | 424,695 records, 345 DMAs, 7 Apr 2023–19 Aug 2026 |
| Forecast validation | 210,841 held-out predictions over 4 rolling-origin folds |
| Model governance | HistGradientBoosting MAE 0.15747 vs persistence 0.15931 (+1.15%); ML not promoted because the gain was below the pre-set 2% margin and the worst fold was 5.24% worse |
| Capacity-20 review policy | 52.6% of candidate alerts reviewed while retaining 85.3% of positive residual-excess signal; highest-flow retained 38.9%, deterministic random 5.5% |
| Capacity frontier | Marginal capture gain fell from 3.38 to 1.70 to 0.86 percentage points per extra actual review across 5→10→20→40 capacity steps |
| Queue continuity | 10% candidate-only carry-over reserve increased mean daily queue Jaccard 45.7% with a 0.059pp signal-capture cost; reported as sensitivity, not an optimum |
| Block-bootstrap robustness | 7-day moving-block 95% interval for capacity-20 capture: 82.4%–88.2%; advantage over highest-flow: 41.93–52.92pp |
| Temporal robustness | Capacity-constrained policy beat highest-flow in 8/8 calendar-quarter slices; absolute capture ranged from 76.9% to 95.1% |

`positive residual-excess signal` is a model-residual proxy. It is **not** verified leak recall, recovered water, avoided incidents or financial value.

## Why the simple model remained champion

Each rolling fold selected the strongest simple comparator from persistence, 7-day seasonal and trailing-28-day median using calibration data only. Persistence won in all four folds.

The promotion gate required at least 2% aggregate MAE improvement and no rolling fold more than 5% worse than the selected baseline. The challenger improved aggregate MAE by 1.15% but its worst fold was 5.24% worse, so persistence remained the operational champion. The downstream queue then used the champion forecast and champion uncertainty band, keeping model governance and operational ranking consistent.

## Decision layer

The frozen champion generates a one-sided upper-band exceedance. Only positive exceedances are investigation candidates. Four review rules are evaluated at capacities 5, 10, 20 and 40: deterministic random, highest observed flow, anomaly-score ranking, and a capacity-constrained candidate queue that leaves unused slots empty when there are too few candidates.

At capacity 20, the constrained queue retained 85.3% of observed positive residual-excess signal while selecting 52.6% of candidate alerts. The project also reports queue churn, backlog, capacity utilisation, DMA concentration and a transparent analyst-time scenario rather than presenting signal capture alone.

## Robustness and limitations

The capacity result is checked in three ways. Moving-block bootstrap resamples contiguous held-out dates using 3-, 7- and 14-day blocks. Calendar-quarter slices keep the same champion, threshold, capacity and review rule frozen. Candidate-only continuity sensitivity tests whether modest carry-over can improve field-team continuity without retaining a DMA that is no longer a current candidate.

The public data do not include confirmed leak labels, intervention success, repair cost, staffing cost or recovered water. The project therefore does not call any capacity or carry-over setting optimal and does not translate residual signals into financial return.

## Other verified public-data products

The 2025/26 APR parser identifies 36 common performance-commitment rows and 18 numeric payment measures. Serious pollution incidents, total pollution incidents and internal sewer flooding account for 66.8% of observed negative-payment exposure in this narrow extract. This is a concentration statistic, not an estimate of avoidable penalties.

APR storm-overflow totals are reconciled against the current published EDM series. 2023 and 2024 match; for 2025 the APR file reports 51,560 and the current EDM publication reports 51,404, a difference of 156 (0.303%). The difference is routed to review rather than silently overwritten.

The Watsit layer adds published rainfall, reservoir and demand context. Its rules are descriptive analyst signals, not an official drought classification.

## Repository structure

```text
src/yw_decisioning/      ingestion, modelling, governance and decision logic
scripts/                 reproducible CLI entry points
results/                 compact public-data outputs and evidence reports
tests/                   regression, governance and product tests
sql/                     operational queries
config/                  pinned source metadata
docs/                    case study, architecture, data/model cards and JD mapping
.github/workflows/       clean CI and network-enabled public-data validation
```

## Reproduce

For the pinned APR analysis:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt
make bootstrap
make all
```

For the full public-data network run:

```bash
make live
```

The GitHub Actions workflow is the release authority for live claims. `results/EVIDENCE_REGISTER.csv`, `results/RELEASE_READINESS.md`, `results/live_validation_provenance.json` and `results/RELEASE_MANIFEST.json` define the claim boundary and hashes. `requirements-lock.txt` and the workflow-generated `results/environment_snapshot.txt` record the verified Python environment.

## Cloud boundary

The repository includes a reference Azure/Databricks architecture in `docs/ARCHITECTURE.md`, but this public portfolio version is **not** an executed Azure or Databricks deployment.

## Application material

- `docs/CASE_STUDY.md` — short interview walkthrough
- `docs/JD_TRACEABILITY.md` — evidence-to-role mapping and remaining gaps
- `CV_BULLETS.md` — concise application bullets with verified figures
- `docs/MODEL_CARD.md` and `docs/DATA_CARD.md` — model/data limitations and controls

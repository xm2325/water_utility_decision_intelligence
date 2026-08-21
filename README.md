# Water Utility Decision Intelligence — v0.7

**Independent portfolio project using publicly available Yorkshire Water data; not affiliated with or endorsed by Yorkshire Water.**

Application project for a Senior Data Scientist role in a regulated utility. The repository treats modelling as one part of an operational Data/AI product: source provenance, source reconciliation, data contracts, time-aware validation, baseline selection, champion/challenger rules, capacity-aware review, SQL publication and evidence controls are explicit.

## v0.7 in one view

v0.7 keeps the verified v0.6 decision-value layer and adds a **candidate-only queue-continuity sensitivity**. The forecasting champion, candidate threshold and capacity rule remain frozen; continuity can only prioritise a DMA if it is still a positive candidate on the current date.

The decision layer compares four rules at capacities 5, 10, 20 and 40:

1. deterministic random selection;
2. highest observed absolute night flow;
3. anomaly-score ranking that fills the available slots;
4. capacity-constrained anomaly ranking that admits only positive upper-band candidates and leaves unused slots empty.

The public data do not contain verified leak labels. Therefore, "signal capture" means the share of the deployed champion's **positive upper-band residual excess** retained by a review policy. It is not leak recall, recovered water, an avoided incident, ODI benefit or money saved.

## Latest executed real-data results

### DMA night-flow model governance

The GitHub Actions live-data workflow downloaded **424,695 Yorkshire Water DMA night-flow records** across **345 DMAs**, covering **7 April 2023 to 19 August 2026**. After point-in-time feature construction, the rolling validation produced **210,841 held-out predictions** across four folds.

Data-contract checks passed. HistGradientBoosting achieved MAE **0.15747** versus **0.15931** for the calibration-selected simple baseline, a **1.15%** improvement. The challenger improved **83.8% of evaluated DMAs**, but it was not promoted because:

- the aggregate gain was below the pre-set 2% threshold; and
- the worst fold was **5.24% worse** than the selected baseline, outside the 5% tolerance.

All four calibration blocks selected **persistence** over the 7-day seasonal and trailing-28-day median comparators. The operational champion therefore remains persistence rather than forcing ML into production.

### Capacity-aware review policy — verified live evidence

The v0.6 GitHub Actions network workflow reproduced these figures from the public ArcGIS source and the evidence register verified the compact-output hashes.

Across the **615 held-out dates**, the champion produced **23,120 positive upper-band candidates**: **10.97%** of held-out observations, with a mean **37.6 candidates/day**.

At daily capacity **20**:

| Policy | Residual-signal capture | Candidate precision | Candidate recall | Mean queue Jaccard |
|---|---:|---:|---:|---:|
| random | 5.5% | 11.2% | 5.9% | 0.030 |
| highest_flow | 38.9% | 30.9% | 16.4% | 0.793 |
| anomaly_score | 85.3% | 98.9% | 52.6% | 0.029 |
| capacity_constrained | **85.3%** | **100.0%** | **52.6%** | 0.026 |

At capacity 20, the constrained anomaly queue reviews 52.6% of candidate alerts while retaining 85.3% of the observed positive residual-excess signal. The same result also exposes a limitation: the anomaly queue changes sharply from day to day. A production workflow may therefore need queue hysteresis or continuity constraints for field teams.

The default workload scenario assumes 20 minutes per selected DMA only to make policies comparable. It is not a Yorkshire Water staffing estimate.

### v0.7 queue-continuity sensitivity — verified live evidence

The v0.6 result exposes a practical issue: high residual-signal capture comes with a rapidly changing daily queue. v0.7 tests bounded continuity reserves of 0%, 10%, 25% and 50% at capacity 20. A DMA can receive continuity priority **only when it is still a positive upper-band candidate today**; yesterday's queue alone can never keep a DMA active.

The v0.7 GitHub Actions network workflow reproduced the following sensitivity over the same **210,841 held-out predictions**:

| Carry-over reserve | Signal capture | Capture cost vs 0% | Mean queue Jaccard | Previous-queue retention |
|---:|---:|---:|---:|---:|
| 0% | 85.30% | 0.000 pp | 0.0262 | 5.01% |
| 10% | 85.24% | 0.059 pp | 0.0381 | 7.27% |
| 25% | 85.07% | 0.236 pp | 0.0487 | 9.08% |
| 50% | 84.99% | 0.311 pp | 0.0505 | 9.34% |

The 10–50% settings are **sensitivity points, not tuned recommendations**. The v0.7 live provenance check passed, so these figures are available as continuity evidence; no carry-over fraction is described as optimal.

### Capacity frontier

For the capacity-constrained policy, signal capture rises with review capacity but with diminishing marginal gain:

| Daily capacity | Signal capture | Candidate recall | Mean backlog/day | Mean selected/day |
|---:|---:|---:|---:|---:|
| 5 | 51.8% | 13.3% | 32.6 | 5.0 |
| 10 | 68.7% | 26.6% | 27.6 | 10.0 |
| 20 | 85.3% | 52.6% | 17.8 | 19.8 |
| 40 | 96.8% | 88.2% | 4.4 | 33.1 |

This is a decision frontier, not a recommendation that capacity should be 20 or 40. Actual staffing cost and operational value are not present in the public data.


## Regulatory and operational context

### APR decision-support product

`make bootstrap` downloads and verifies pinned official APR releases for 2023/24, 2024/25 and 2025/26 using URL, SHA-256, byte-size and row-count checks.

The 2025/26 file contains **121,937 rows**. The parser extracts **36 common 3A performance-commitment rows** and **18 numeric payment measures**. Within the numeric common-3A payment extract:

- gross observed negative-payment exposure: **£76.75m**;
- positive payments: **£15.86m**;
- net parsed payment: **-£60.89m**;
- serious pollution, total pollution and internal sewer flooding account for **66.8%** of observed negative-payment exposure.

These are portfolio and triage statistics, not Yorkshire Water's total ODI position or estimates of avoidable payments.

### APR ↔ EDM reconciliation

The pipeline compares the APR storm-overflow count with Yorkshire Water's published EDM summary:

- 2023: 77,761 vs 77,761 — matched;
- 2024: 68,164 vs 68,164 — matched;
- 2025: APR 51,560 vs current EDM publication 51,404 — **156 difference (0.303%)**.

The difference is routed to a review table instead of being silently overwritten.

### Watsit resource context

For July 2026 the stored Yorkshire Water source snapshot reports:

- provisional rainfall: **19.4% of long-term average**;
- reservoir monthly table: **65%**, 3 percentage points below the July 2023–2025 median;
- demand: **1,382 Ml/day**, 7.1% above the July 2023–2025 median;
- **3/3 project watch signals** active.

These are transparent project rules, not an official drought classification.

## Night-flow pipeline

```text
Yorkshire Water ArcGIS annual DMA tables
    -> retrying paginated download
    -> schema + timestamp + SHA-256 manifest
    -> data contract / duplicate consolidation
    -> calendar-time point-in-time features
    -> expanding-window rolling validation
    -> calibration-only simple-baseline selection
    -> ML + baseline uncertainty bands
    -> aggregate + per-DMA champion/challenger gate
    -> frozen champion
    -> four review policies x capacity sensitivity
    -> candidate-only queue-continuity sensitivity
    -> workload + signal capture + queue stability + DMA concentration
    -> SQLite operational product + evidence register
```

For date `t`, the target is `ACTUAL_MIN_NIGHT_FLOW(t)`. Flow-derived predictors use only earlier observations. Calendar-time `lag7d`, trailing 7-day and trailing 28-day features avoid treating "seven observations" as "seven days" when records are missing.

## Model promotion gate

The ML challenger is promoted only if all default checks pass:

1. aggregate MAE improves on the calibration-selected simple baseline by at least 2%;
2. no rolling fold is more than 5% worse than the selected baseline;
3. ML one-sided upper-band coverage lies between 85% and 97%;
4. at least 50% of evaluated DMAs have lower ML MAE;
5. the 10th percentile of DMA-level relative improvement is no worse than -25%;
6. the data contract passes.

The thresholds are not changed after viewing the result.

## SQL operational product

```bash
make product
```

This creates `results/operational_decision_product.sqlite`. Views include:

- `v_apr_negative_payment_priority`;
- `v_source_reconciliation_review`;
- `v_latest_resource_watch`;
- `v_current_dma_investigation_queue` after a live run;
- `v_nightflow_capacity_tradeoff`;
- `v_nightflow_policy_capacity20`;
- `v_nightflow_continuity_frontier`.

Example queries are in `sql/operational_queries.sql`.

## Evidence controls

`results/EVIDENCE_REGISTER.csv` separates executed real-data evidence from synthetic development checks and blocked claims. A compact live-data snapshot remains valid only when its metrics SHA-256 matches `results/live_validation_provenance.json`.

The live evidence boundary allows claims about:

- observed forecast error and promotion decisions;
- residual-signal capture under stated capacity rules;
- candidate review burden, queue stability and DMA concentration;
- candidate-only continuity sensitivity when compact hashes match the live-run provenance.

It blocks claims about confirmed leak detection, avoided leakage, prevented incidents, ODI recovery or financial return.

## Reproduction

Offline/pinned-data build:

```bash
make bootstrap
make all
```

Network-enabled live build:

```bash
make live
```

`make live` downloads the ArcGIS data, runs rolling validation, evaluates decision policies, records live provenance, builds the SQLite product, updates the evidence register and builds the release manifest.

## Tests

v0.7 has **34 automated tests** covering source pins, ArcGIS pagination, time semantics, data contracts, baseline selection, champion routing, decision-policy capacity rules, deterministic random benchmarking, candidate-only continuity, fail-closed continuity provenance, SQL views and source reconciliation.

## Cloud design boundary

`docs/ARCHITECTURE.md` maps the product to Azure Data Lake, Databricks/Delta, MLflow and Power BI/API consumption. That file is a production design only. This repository does **not** claim an executed Azure or Databricks deployment.

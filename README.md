# Water Utility Decision Intelligence — v0.6

**Independent portfolio project using publicly available Yorkshire Water data; not affiliated with or endorsed by Yorkshire Water.**

Application project for a Senior Data Scientist role in a regulated utility. The repository treats modelling as one part of an operational Data/AI product: source provenance, source reconciliation, data contracts, time-aware validation, baseline selection, champion/challenger rules, capacity-aware review, SQL publication and evidence controls are explicit.

## v0.6 in one view

v0.6 adds a downstream **decision-value layer** after the forecasting champion is frozen. The question is no longer only whether ML predicts better; it is also whether a finite daily review budget is allocated to the most informative DMA signals.

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

### Capacity-aware review policy — pre-release replay

The numbers below are a deterministic local replay over the already verified v0.5 GitHub Actions artifact. They are **not yet released as v0.6 application evidence**; the v0.6 network workflow must reproduce them and bind the compact outputs to provenance hashes first.

Across the **615 held-out dates**, the champion produced **23,120 positive upper-band candidates**: **10.97%** of held-out observations, with a mean **37.6 candidates/day**.

At daily capacity **20**:

| Policy | Residual-signal capture | Candidate precision | Candidate recall | Mean queue Jaccard |
|---|---:|---:|---:|---:|
| random | 5.5% | 11.2% | 5.9% | 0.030 |
| highest_flow | 38.9% | 30.9% | 16.4% | 0.793 |
| anomaly_score | 85.3% | 98.9% | 52.6% | 0.029 |
| capacity_constrained | **85.3%** | **100.0%** | **52.6%** | 0.026 |

The constrained anomaly queue reviews only about half of candidate alerts while retaining 85.3% of the observed positive residual-excess signal. The same result also exposes a limitation: the anomaly queue changes sharply from day to day. A production workflow may therefore need queue hysteresis or continuity constraints for field teams.

The default workload scenario assumes 20 minutes per selected DMA only to make policies comparable. It is not a Yorkshire Water staffing estimate.

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
- `v_nightflow_policy_capacity20`.

Example queries are in `sql/operational_queries.sql`.

## Evidence controls

`results/EVIDENCE_REGISTER.csv` separates executed real-data evidence from synthetic development checks and blocked claims. A compact live-data snapshot remains valid only when its metrics SHA-256 matches `results/live_validation_provenance.json`.

The live evidence boundary allows claims about:

- observed forecast error and promotion decisions;
- residual-signal capture under stated capacity rules;
- candidate review burden, queue stability and DMA concentration.

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

v0.6 has **28 automated tests** covering source pins, ArcGIS pagination, time semantics, data contracts, baseline selection, champion routing, decision-policy capacity rules, deterministic random benchmarking, evidence hashes, SQL views and source reconciliation.

## Cloud design boundary

`docs/ARCHITECTURE.md` maps the product to Azure Data Lake, Databricks/Delta, MLflow and Power BI/API consumption. That file is a production design only. This repository does **not** claim an executed Azure or Databricks deployment.

# Water Utility Decision Intelligence — v0.4

**Independent portfolio project using publicly available Yorkshire Water data; not affiliated with or endorsed by Yorkshire Water.**

Application project for the Yorkshire Water **Senior Data Scientist** role. The project treats modelling as one part of an operational Data/AI product: source provenance, source reconciliation, data contracts, time-aware validation, simple baselines, champion/challenger rules, uncertainty, capacity-aware triage, SQL outputs and evidence controls are explicit.

## v0.4 in one view

v0.4 keeps the v0.3 modelling/governance work and adds release-grade source pinning and reproducibility controls for a public GitHub repository.


1. **Pinned APR source bootstrap:** large raw APR CSV files are no longer stored in Git. `make bootstrap` retrieves the three official releases and verifies SHA-256, byte size and row count against reviewed pins.
2. **Fail-closed source drift:** a changed upstream APR file stops the default build instead of silently changing portfolio results; changed bytes can be downloaded for review without auto-updating the pin.
3. **PR live-data validation:** the network-enabled workflow now runs on pull requests as well as manual/scheduled execution so the real ArcGIS chain is exercised before merge.
4. **Public-repo boundary:** the README now states clearly that this is an independent portfolio project, not an official Yorkshire Water system.

### Retained v0.3 modelling and governance controls

1. **Calendar-time features:** `lag7d`, trailing 7-day and trailing 28-day features are now defined by calendar time, not by a fixed number of observations. This matters when DMA observations are missing or irregular.
2. **Champion-consistent queue:** if the ML challenger fails the production gate, persistence remains champion and the live investigation queue uses the persistence forecast and its calibrated upper band. v0.2 could retain persistence in governance while still ranking the latest queue from ML outputs.
3. **Per-DMA stability and data contract:** promotion now checks aggregate error, worst fold, uncertainty coverage, share of DMAs improved and the lower tail of per-DMA relative improvement. A data contract can block promotion before model metrics are considered.
4. **Official-source reconciliation:** the APR spill-count line is reconciled against Yorkshire Water's published EDM summary. Differences are reported for review and are never silently overwritten.
5. **Multi-signal resource context:** a Watsit layer compares 2026 rainfall, reservoir stocks and demand with same-month 2023–2025 values using transparent watch rules. It is analyst context, not an official drought classification.
6. **Evidence register:** every result is marked as executed real data, synthetic validation or not yet executed. Synthetic metrics and unexecuted live-data claims are blocked from CV evidence.
7. **20 automated tests** now cover modelling, calendar-time features, baseline routing, data contracts, source reconciliation, evidence controls, ArcGIS ingestion and SQL publication.

## Executed real-data evidence

### 1. APR regulatory decision product

Yorkshire Water APR Open Data CSVs for 2023/24, 2024/25 and 2025/26 are pinned to reviewed official releases. After cloning, download and verify them with:

```bash
make bootstrap
```

Then rebuild the APR analysis with:

```bash
make apr
```

The 2025/26 file contains **121,937 rows**. The parser extracts **36 common 3A performance-commitment rows**, including **18 numeric payment measures**. Across the full common 3A set, **12 rows report `PCL met? = No`**; **11** of those also have a numeric payment.

Within the numeric common-3A payment extract:

- gross observed negative-payment exposure: **£76.75m**;
- positive payments: **£15.86m**;
- net parsed payment: **-£60.89m**;
- serious pollution, total pollution and internal sewer flooding account for **66.8%** of observed negative-payment exposure.

These are portfolio and triage statistics. They are not Yorkshire Water's total ODI position and are not estimates of avoidable payments.

### 2. APR ↔ EDM source reconciliation

```bash
make edm
```

For the three calendar years shared by the local APR extracts and the published EDM summary:

- **2023:** 77,761 vs 77,761 — matched;
- **2024:** 68,164 vs 68,164 — matched;
- **2025:** APR 51,560 vs current EDM publication 51,404 — **156 difference (0.303%)**, routed to review.

The pipeline records the mismatch rather than choosing a source automatically. This is useful because published operational data can be updated after validation and assurance.

### 3. Watsit multi-signal resource context

```bash
make resource
```

The local source snapshot reproduces Yorkshire Water's published monthly reservoir, demand and rainfall values retrieved on 21 August 2026. For **July 2026**:

- provisional rainfall: **19.4% of long-term average (LTA)**;
- monthly reservoir table: **65%**, **3 percentage points below** the July 2023–2025 median of 68%;
- demand: **1,382 Ml/day**, **7.1% above** the July 2023–2025 median and above the maximum of those three historical July values;
- **3/3 transparent project watch signals** are active.

The source page's current headline reports reservoir stocks of **64.9%** and states that some rivers are below critical level. The 75% rainfall rule used here is a project watch threshold, not a Yorkshire Water or regulatory drought threshold.

## Network-enabled DMA night-flow ML

Yorkshire Water publishes annual DMA night-flow tables through ArcGIS. The official layer estimates checked on 21 August 2026 report:

| Year | Public records |
|---|---:|
| 2023 | 92,805 |
| 2024 | 126,270 |
| 2025 | 125,925 |
| 2026 | 79,695 |
| **Total** | **424,695** |

The 2026 layer exposes `DATE`, `DMA_ID`, `ACTUAL_MIN_NIGHT_FLOW`, `MIN_NIGHT_FLOW`, coordinates and units, and was last edited on 20 August 2026.

The live workflow is:

```bash
make live
```

```text
ArcGIS annual night-flow tables
    -> retrying paginated download
    -> schema + timestamp + SHA-256 manifest
    -> data contract / duplicate consolidation
    -> calendar-time lagged features
    -> expanding-window rolling validation
    -> ML and persistence uncertainty bands
    -> aggregate + per-DMA champion/challenger gate
    -> champion-consistent investigation queue
    -> drift report + SQL product + evidence register
```

### Forecast semantics

For DMA observation date `t`, the target is `ACTUAL_MIN_NIGHT_FLOW(t)`.

- `lag1`: most recent earlier observation, also used by the persistence baseline;
- `lag7d`: most recent observation available at or before `t - 7 days`;
- `rolling7d`: earlier observations in the previous 7 calendar days;
- `rolling28d`: earlier observations in the previous 28 calendar days;
- current `ACTUAL_MIN_NIGHT_FLOW(t)` is never used as a predictor for itself.

The calendar-time definition avoids turning a nominal seven-day feature into an unknown period when records are missing.

### Production gate

The ML challenger is promoted only when all default checks pass:

1. aggregate MAE improves on persistence by at least 2%;
2. no rolling fold is more than 5% worse than persistence;
3. ML one-sided upper-band coverage lies between 85% and 97%;
4. at least 50% of evaluated DMAs have lower ML MAE than persistence;
5. the 10th percentile of DMA-level relative improvement is no worse than -25%;
6. the data contract passes.

If any required check fails, persistence remains champion. The latest operational queue then uses the persistence expectation and persistence uncertainty band.

### Investigation output

After a new observed value arrives, only observations above the deployed champion's calibrated upper band can enter the queue. Capacity is a ceiling, not a quota. An exceedance is an **investigation signal**, not a confirmed leak label.

## SQL operational product

```bash
make product
```

This creates `results/operational_decision_product.sqlite`. Current executed-real-data views include:

- `v_apr_negative_payment_priority`;
- `v_source_reconciliation_review`;
- `v_latest_resource_watch`.

After a live night-flow run it also exposes `v_current_dma_investigation_queue` and the validation/drift tables.

Example SQL is in `sql/operational_queries.sql`.

## Evidence controls

```bash
make evidence
```

`results/EVIDENCE_REGISTER.csv` and `results/RELEASE_READINESS.md` separate:

- **executed real data** — safe for the stated measured claims;
- **synthetic validation** — software/gate testing only;
- **not yet executed** — design claims only.

The current build has **3 executed real-data evidence items**. Live DMA performance claims remain blocked until the network-enabled ArcGIS run creates raw files, a provenance manifest and root-level backtest metrics.

## Offline integration test

```bash
make smoke
```

Synthetic outputs are isolated under `results/dev_validation/`. They prove that the full pipeline and governance logic run, including the case where persistence remains champion. Their numerical metrics must not be used on the CV.

## Full local rebuild

```bash
make bootstrap
make all
```

`make bootstrap` downloads the pinned official APR releases. `make all` then verifies the pins before running tests, APR analysis, source reconciliation, Watsit context, synthetic integration validation, SQL publication and evidence classification.

## Cloud design boundary

`docs/ARCHITECTURE.md` maps the product to Azure Data Lake, Databricks/Delta, MLflow and Power BI/API consumption. That document is a production design. The repository does **not** claim an executed Azure or Databricks deployment.

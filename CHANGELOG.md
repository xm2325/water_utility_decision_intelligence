# Changelog

## v0.5.0 — 2026-08-21

- Replaced the single fixed persistence comparator with a leakage-safe simple-baseline set: persistence, 7-day seasonal and trailing-28-day median.
- Selects the baseline from the calibration block only before each held-out rolling-origin fold; the test block cannot choose its own comparator.
- Promotion now requires ML to beat the selected simple baseline, not merely persistence.
- Added selected-baseline uncertainty bands and champion-consistent operational routing when ML is rejected.
- Retained persistence metrics separately for auditability and easier interpretation.
- Added fold-level baseline-selection outputs and one additional regression test; local suite is now 21/21.

## v0.4.0 — 2026-08-21

- Moved the three large APR raw CSV releases out of Git and added `make bootstrap` for official-source retrieval.
- Added reviewed URL, SHA-256, byte-size and row-count pins for 2023/24, 2024/25 and 2025/26 APR releases.
- Added fail-closed source-drift handling: a republished upstream file cannot silently alter portfolio results.
- Added a retrieval manifest for APR downloads.
- Added source-pin tests and raised the local test count from 18 to 20.
- Added pull-request triggering to the network-enabled real-data workflow so the ArcGIS live chain can be validated before merge.
- Added an explicit public-repository disclaimer: this is an independent portfolio project, not a Yorkshire Water system.

## 0.3.0 — 2026-08-21

### Forecast correctness

- Replaced observation-count `lag7`/rolling windows with calendar-time `lag7d`, trailing 7-day and trailing 28-day features.
- Added lag staleness and time-gap features for irregular observation schedules.
- Kept the current target outside every flow-derived predictor.
- Made the latest investigation queue use the **deployed champion**. If persistence wins the gate, its forecast, upper band and exceedance signal drive the queue.

### Model assurance

- Added a pre-model data contract covering date span, DMA count, actual/reference missingness, duplicate-key rate, negative-flow rate and units.
- Added per-DMA model-vs-persistence evaluation.
- Extended promotion rules with the share of DMAs improved and a lower-tail DMA performance check.
- Calibrated and reported separate one-sided uncertainty bands for ML and persistence.

### Official-source reconciliation

- Added a cached Yorkshire Water EDM published-summary snapshot and APR↔EDM reconciliation.
- 2023 and 2024 spill counts match across the two sources.
- The current 2025 EDM publication reports 51,404 versus 51,560 in the local 2025/26 APR line: a 156-event (0.303%) source-version difference.
- The difference is routed to a review table; the code does not silently replace either value.

### Multi-signal resource context

- Added a Watsit monthly snapshot with rainfall, reservoir and demand data.
- Added same-calendar-month comparisons against 2023–2025 history.
- Added three transparent analyst watch rules without treating them as official drought definitions.
- Added `v_latest_resource_watch` to the SQLite product.

### Evidence governance

- Added `EVIDENCE_REGISTER.csv` and `RELEASE_READINESS.md`.
- Executed real-data, synthetic validation and pending live-data claims are classified separately.
- Root-level live DMA claims require raw ArcGIS files, a download manifest and real backtest outputs.

### Testing and product

- Expanded the automated test suite from 12 to **18 passing tests**.
- Added source-reconciliation, resource-watch, calendar-window, champion-routing, data-contract and evidence-leakage tests.
- Added SQL tables/views for source review and resource context.

## 0.2.0 — 2026-08-21

- Fixed the v0.1 target/persistence forecast-horizon mismatch.
- Replaced a single split with expanding-window rolling validation.
- Added ML vs persistence promotion rules, uncertainty bands, drift checks, source provenance, SQLite outputs and synthetic integration testing.
- Expanded the test suite to 12 tests.

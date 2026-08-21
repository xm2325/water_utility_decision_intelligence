# Changelog

## v1.0.0 — 2026-08-21

- Promoted the portfolio to an application-ready release after GitHub Actions verified the full v0.10 public-data chain.
- Added an executive-first README, interview case study, JD traceability and a clear current/reference architecture boundary.
- Added a fully pinned Python dependency lock from the verified GitHub Python 3.11 environment and made CI/live workflows install from that lock.
- Upgraded `actions/checkout` and `actions/setup-python` to Node-24-compatible majors and added `pip check` plus a live environment snapshot.
- Deduplicated provenance requirements before verification so `files_checked` counts unique evidence inputs.
- Added dependency-lock/runtime metadata to the release manifest.
- Kept the model and policies frozen: persistence remains champion; capacity and continuity values remain reported sensitivities rather than claimed optima.

## v0.10.0 — 2026-08-21

- Added frozen-policy calendar-quarter robustness without quarter-specific retraining or threshold tuning.
- GitHub real-data validation confirmed the capacity-constrained policy beat highest-flow in all 8 held-out calendar-quarter slices.
- Absolute constrained-policy capture ranged from 76.9% to 95.1%, exposing time heterogeneity rather than hiding it behind the 85.3% aggregate result.
- Added quarter-level compact outputs, provenance/evidence checks and SQLite publication.
- GitHub clean CI passed 53 tests.

## v0.9.0 — 2026-08-21

- Added moving-block bootstrap robustness for the frozen capacity-20 decision policies using 3-, 7- and 14-day blocks.
- The 7-day 95% interval for constrained-policy residual-signal capture was 82.4%–88.2%; the advantage over highest-flow was 41.93–52.92 percentage points.
- Bound the daily policy input and bootstrap outputs to the same live-run provenance and added fail-closed evidence controls.

## v0.8.0 — 2026-08-21

- Added a marginal capacity / residual-signal frontier for the candidate-only constrained review policy.
- Marginal gains use actual reviews selected per day rather than nominal capacity because unused slots are allowed.
- Verified marginal capture gain fell from 3.38 to 1.70 to 0.86 percentage points per extra actual review across 5→10→20→40 capacity steps.
- Added frontier provenance/evidence controls and a SQLite marginal-value view.

## v0.7.0 — 2026-08-21

- Added candidate-only queue-continuity sensitivity after the forecasting champion and anomaly threshold are frozen.
- A previous queue can prioritise a DMA only if it remains a positive current candidate.
- GitHub real-data validation confirmed mean queue Jaccard rising from 0.0262 at 0% to 0.0381 / 0.0487 / 0.0505 while signal capture remains 85.24% / 85.07% / 84.99% at 10% / 25% / 50% carry-over.
- Added continuity metrics to live provenance and the SQLite operational product.

## v0.6.0 — 2026-08-21

- Added downstream capacity-aware DMA review evaluation after the forecasting champion is frozen.
- Compared deterministic random, highest-flow, anomaly-score and capacity-constrained policies at capacities 5, 10, 20 and 40.
- GitHub real-data validation confirmed that capacity 20 retained 85.3% of positive residual-excess signal while reviewing 52.6% of candidate alerts; highest-flow retained 38.9% and deterministic random 5.5%.
- Added workload, queue-stability and DMA-concentration metrics plus live-run provenance.

## v0.5.0 — 2026-08-21

- Replaced the single fixed persistence comparator with a calibration-only simple-baseline set: persistence, 7-day seasonal and trailing-28-day median.
- Promotion requires ML to beat the selected simple baseline rather than choosing the comparator from the test period.
- All four real-data folds selected persistence; the operational champion remained the simple baseline.

## v0.4.0 — 2026-08-21

- Moved large APR raw CSV releases out of Git and added `make bootstrap` for official-source retrieval.
- Added reviewed URL, SHA-256, byte-size and row-count pins and fail-closed source-drift handling.
- Added pull-request triggering to the network-enabled real-data workflow and an explicit public-project disclaimer.

## v0.3.0 — 2026-08-21

- Replaced observation-count windows with calendar-time lag/rolling features and added staleness/gap features.
- Added data contracts, per-DMA evaluation, separate uncertainty bands, champion-consistent queue routing, APR↔EDM reconciliation, Watsit resource context and evidence governance.

## v0.2.0 — 2026-08-21

- Fixed the original target/persistence horizon mismatch.
- Replaced a single split with expanding-window rolling validation.
- Added ML-vs-baseline promotion rules, uncertainty bands, drift checks, source provenance, SQLite outputs and synthetic integration testing.

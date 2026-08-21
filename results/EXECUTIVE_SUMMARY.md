# Executive summary — v0.4

## Executed real-data evidence

The repository now has three independent executed real-data products.

**APR regulatory triage.** The official 2025/26 APR file contains 121,937 rows. The parser extracts 36 common-3A performance-commitment rows and 18 numeric payment measures. Gross negative-payment exposure in that narrow numeric extract is £76.75m; serious pollution, total pollution and internal sewer flooding account for 66.8% of observed negative-payment exposure. This is a portfolio concentration measure, not an estimate of avoidable payment.

**APR ↔ EDM source reconciliation.** The APR and current published EDM spill totals match for 2023 and 2024. For 2025, APR reports 51,560 and the current EDM publication reports 51,404, a difference of 156 (0.303%). v0.4 writes that difference to a review queue rather than silently choosing one source.

**Watsit resource context.** For July 2026, the published Watsit data give 19.4% provisional rainfall versus LTA, 65% in the monthly reservoir table and 1,382 Ml/day demand. Relative to the same month in 2023–2025, reservoir stocks are 3 percentage points below the median and demand is 7.1% above the median and above the historical maximum. Three transparent project watch rules are active. These rules are analyst context, not an official drought classification.

## Night-flow model status

The night-flow pipeline is fully implemented and locally tested with calendar-time features, rolling-origin validation, separate ML/persistence uncertainty bands, a data contract, per-DMA stability checks, drift monitoring and a champion-consistent capacity queue.

Official ArcGIS layer estimates show 424,695 public records across the 2023–2026 annual night-flow tables. This local build does not contain the raw ArcGIS record payloads, so the evidence register blocks real night-flow MAE, DMA counts and model-promotion claims until a network-enabled run creates raw files, the download manifest and root-level backtest outputs.

## Production rule

ML is not selected because it is more complex. If the challenger fails any required aggregate, fold, per-DMA, uncertainty or data-contract check, persistence remains champion and the operational queue uses persistence outputs.

## Release status

The current build has **3 executed real-data evidence items** and **20 passing automated tests**. Live night-flow performance claims remain blocked pending the network-enabled ArcGIS run.

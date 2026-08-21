# Executive summary — v0.5

## Executed real-data evidence

**APR regulatory triage.** The official 2025/26 APR file contains 121,937 rows. The parser extracts 36 common-3A performance-commitment rows and 18 numeric payment measures. Gross negative-payment exposure in that narrow numeric extract is £76.75m; serious pollution, total pollution and internal sewer flooding account for 66.8% of observed negative-payment exposure. This is a portfolio concentration measure, not an estimate of avoidable payment.

**APR ↔ EDM source reconciliation.** The APR and current published EDM spill totals match for 2023 and 2024. For 2025, APR reports 51,560 and the current EDM publication reports 51,404, a difference of 156 (0.303%). The difference is routed to review rather than silently resolved.

**Watsit resource context.** For July 2026, published Watsit data give 19.4% provisional rainfall versus LTA, 65% in the monthly reservoir table and 1,382 Ml/day demand. The project uses transparent historical comparisons as analyst context rather than an official drought classification.

**DMA night-flow validation.** The successful network-enabled workflow downloaded 424,695 Yorkshire Water night-flow records across 345 DMAs covering 7 April 2023 to 19 August 2026. The data contract passed: actual-flow missingness was 0.704%, reference-flow missingness 0.716%, duplicate-key rate 0%, and all rows used one unit (`l/s`). Four rolling-origin folds produced 210,841 held-out predictions. HistGradientBoosting achieved MAE 0.15747 versus persistence 0.15931, a 1.15% aggregate reduction; 289 of 345 evaluated DMAs (83.8%) had lower ML MAE. The ML challenger was nevertheless not promoted because the aggregate gain was below the configured 2% margin and the worst fold was 5.24% worse than persistence. Retaining the baseline is therefore the governed result, not a failed experiment.

On the latest 19 August 2026 snapshot, the deployed persistence champion produced 46 upper-band exceedance candidates; the capacity ceiling admitted the top 20 to the investigation queue. These are anomaly-review signals, not confirmed leak labels.

## v0.5 evaluation upgrade

v0.5 strengthens the comparator design. Before each held-out fold, the calibration block selects among persistence, a 7-day seasonal baseline and a trailing-28-day median. The held-out outcomes never choose their comparator. An audit calculation on the executed data selected persistence in all four folds, so the stronger baseline-selection rule does not weaken the existing conclusion; the full v0.5 workflow is rerun before merge.

## Production rule

ML is promoted only when it clears aggregate improvement, worst-fold stability, per-DMA performance, uncertainty coverage and data-contract checks against a comparator selected without test leakage. If it fails, the selected simple baseline drives the operational queue.

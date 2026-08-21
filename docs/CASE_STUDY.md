# Application case study — operational decision intelligence for a water utility

## Decision problem

A utility data-science team may need to answer several related but different questions: where regulatory pressure is concentrated, whether official sources agree, what current water-resource context looks unusual, and which DMAs should be inspected after new telemetry arrives. v0.4 keeps those decisions separate and publishes them through one governed data product.

## Regulatory triage

The executed APR pipeline processes 121,937 rows in the 2025/26 official open-data file. It extracts the common 3A performance-commitment section and separates reported outcomes from counterfactual impact claims.

Within the numeric payment extract, serious pollution, total pollution and internal sewer flooding account for 66.8% of observed negative-payment exposure. The capacity curve answers a prioritisation question under limited analytical capacity; it does not say that the payment can be recovered.

## Source reconciliation as a QA decision

The project compares the APR storm-overflow line with Yorkshire Water's published EDM yearly series. 2023 and 2024 agree exactly. For 2025, the current EDM publication reports 51,404 and the local APR row reports 51,560.

Instead of hiding the difference, v0.4 produces a review item with absolute and relative difference. This makes source version and assurance state visible to downstream users.

## Resource context without an arbitrary composite risk score

Watsit rainfall, reservoir and demand values are compared with the same calendar month in 2023–2025. For July 2026, provisional rainfall is 19.4% LTA, the monthly reservoir value is 65% versus a 68% historical median, and demand is 1,382 Ml/day versus a 1,290.1 Ml/day historical median.

Three simple watch rules are active, but the project does not combine them into a claimed drought probability. The output gives an analyst context for interpretation and escalation.

## DMA night-flow investigation

The live design forecasts each dated DMA observation using only earlier history. v0.4 uses calendar-time lag and rolling features so that missing observations do not change the meaning of a seven-day window.

The challenger model is compared with persistence through rolling folds and at DMA level. Data quality can block promotion before model performance is considered. If persistence stays champion, the operational queue uses the persistence expectation and persistence uncertainty band; the governance decision and operational output cannot disagree.

Only champion upper-band exceedances enter the queue, and field-team capacity is a ceiling rather than a quota.

## What additional internal data would change

With internal access, verified incident/work-order labels, pressure and rainfall telemetry at the correct network unit, asset type/age, maintenance history and intervention records could support evaluation of incident recall at fixed capacity, false-alert load, lead time and intervention effects. None of those outcomes are claimed from the current public data.

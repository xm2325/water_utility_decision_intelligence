# v0.5 real-data audit

The first successful network-enabled validation run on 21 August 2026 downloaded **424,695** Yorkshire Water DMA night-flow records covering **345 DMAs** from 7 April 2023 to 19 August 2026.

The v0.4 challenger achieved MAE **0.15747** versus persistence **0.15931**, an aggregate reduction of **1.15%**. ML had lower MAE for **289/345 DMAs (83.8%)**, but the configured gate retained persistence because the aggregate gain was below 2% and the worst rolling fold was **5.24% worse** than persistence. The data contract passed.

Before implementing v0.5, the same executed data were used to audit three simple comparators on each fold's calibration block: persistence, a 7-day seasonal baseline and a trailing-28-day median. Persistence had the lowest calibration MAE in all four folds. Therefore the v0.5 leakage-safe comparator rule strengthens the evaluation design without changing the substantive champion decision.

These values are forecasting/model-governance results. Upper-band exceedances are investigation candidates, not verified leak labels, and no avoided incident or financial benefit is inferred from them.

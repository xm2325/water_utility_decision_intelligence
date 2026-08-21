# Night-flow queue continuity sensitivity — v0.7

The frozen forecasting champion and candidate definition are unchanged. Continuity can only select a DMA that is **still a positive upper-band candidate on the current date**. This is a sensitivity analysis, not a tuned production setting.

Capacity: **20 DMA reviews/day**.

|   carryover_fraction |   signal_capture |   signal_capture_cost_pp_vs_zero |   mean_consecutive_day_jaccard |   mean_previous_queue_retention |   mean_continuity_selected_per_day |
|---------------------:|-----------------:|---------------------------------:|-------------------------------:|--------------------------------:|-----------------------------------:|
|               0.0000 |           0.8530 |                           0.0000 |                         0.0262 |                          0.0501 |                             0.0000 |
|               0.1000 |           0.8524 |                           0.0592 |                         0.0381 |                          0.0727 |                             1.3203 |
|               0.2500 |           0.8507 |                           0.2355 |                         0.0487 |                          0.0908 |                             1.7854 |
|               0.5000 |           0.8499 |                           0.3115 |                         0.0505 |                          0.0934 |                             1.8358 |

`signal_capture_cost_pp_vs_zero` measures the percentage-point loss relative to the zero-carryover anomaly queue. The comparison exposes the operational trade-off between current-day residual signal and day-to-day queue continuity. It does not measure leak recall, recovered water or field-team savings.

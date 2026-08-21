# Model card — DMA night-flow investigation model v0.5

## Intended decision

Support a daily question: **which district metered areas (DMAs) should an analyst or field team inspect first after new night-flow observations arrive?**

The output is an investigation queue. It is not a leak diagnosis and it is not an estimate of avoided ODI payment.

## Target and information cutoff

For observation date `t`, the target is `ACTUAL_MIN_NIGHT_FLOW(t)`. Flow-derived predictors use only earlier information:

- `lag1`: most recent previous observation;
- `lag7d`: most recent observation at or before `t - 7 calendar days`;
- `lag7d_staleness_days`: distance between that selected observation and the seven-day reference time;
- `rolling7d`: prior observations in the previous seven calendar days;
- `rolling28d`, `rolling28d_std`, `rolling28d_count`: prior observations in the previous 28 calendar days;
- previous published `MIN_NIGHT_FLOW` reference;
- days since previous observation and rate-of-change terms;
- calendar terms;
- published DMA centroid coordinates where present.

Time windows are calendar based and closed before the target time. This prevents irregular sampling from changing a nominal seven-day feature into a variable-length history.

## Champion and challenger

**Simple baseline set:** previous observed flow (persistence), a 7-day seasonal value and a trailing-28-day median. One baseline is selected on calibration data only for each fold; held-out outcomes are not used to choose the comparator.

**Challenger:** `HistGradientBoostingRegressor` with median imputation and absolute-error loss.

The default production gate requires all of the following:

1. at least 2% aggregate MAE improvement over the calibration-selected simple baseline;
2. no rolling fold more than 5% worse than the selected baseline;
3. ML one-sided upper-band coverage between 85% and 97%;
4. at least half of evaluated DMAs improve against the selected baseline;
5. the 10th percentile of DMA-level relative improvement is no worse than -25%;
6. the data contract passes.

If a check fails, the calibration-selected simple baseline remains champion.

## Champion-consistent operational output

The challenger, selected simple baseline and persistence reference each get empirical one-sided residual bands. After the gate is evaluated, the deployed champion selects:

- expected flow;
- upper uncertainty band;
- exceedance indicator;
- excess above the band;
- investigation score.

This prevents a governance inconsistency where a simple baseline is declared champion but an ML-derived queue is still used operationally.

## Validation

Validation uses expanding-window rolling-origin folds. The tail of each training window is used to estimate model-specific upper residual quantiles. The project does not claim formal exchangeable conformal coverage for this dependent time series.

Outputs include aggregate and fold metrics, per-DMA MAE comparison, uncertainty coverage/exceedance, drift checks and the final promotion decision.

## Data contract

The default pre-model checks cover:

- at least 3 DMAs;
- at least 90 calendar days of coverage;
- actual-flow missing rate no greater than 10%;
- reference-flow missing rate no greater than 50%;
- duplicate DMA/date rate no greater than 2%;
- negative actual-flow rate no greater than 1%;
- at most one unit value.

Thresholds are project defaults and should be agreed with data owners before production use.

## Investigation score

For the deployed champion:

`anomaly_excess = max(0, observed_flow - champion_upper_band)`

`investigation_score = anomaly_excess / recent_28d_std`

Only upper-band exceedances can enter the latest queue. Field-team capacity is a maximum number of queued candidates, not a target count.

## Known limitations

- No verified leak-event label is present in the public night-flow table.
- Rainfall, pressure, work orders and asset condition are not joined to the DMA predictor without a tested key.
- DMA definition changes and sensor maintenance can create distribution shifts.
- The investigation score is not a failure probability.
- A flagged DMA needs operational review before field action.

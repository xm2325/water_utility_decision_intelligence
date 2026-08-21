-- Highest observed negative-payment exposure in the extracted APR portfolio.
SELECT rag_reference,
       line_description,
       ROUND(underperformance_exposure_m, 2) AS exposure_gbp_m,
       ROUND(100.0 * exposure_share, 1) AS exposure_share_pct
FROM v_apr_negative_payment_priority
LIMIT 10;

-- Current capacity-constrained DMA queue (available after a live night-flow run).
SELECT DATE,
       DMA_ID,
       priority_rank,
       ROUND(target, 3) AS observed_flow,
       ROUND(prediction, 3) AS expected_flow,
       ROUND(upper_band, 3) AS upper_band,
       ROUND(investigation_score, 3) AS investigation_score
FROM v_current_dma_investigation_queue
ORDER BY priority_rank;

-- Model stability across rolling-origin folds (available after a live night-flow run).
SELECT fold,
       ROUND(mae_model, 4) AS mae_model,
       ROUND(mae_persistence, 4) AS mae_persistence,
       ROUND(100.0 * relative_mae_improvement, 2) AS relative_improvement_pct,
       ROUND(100.0 * upper_band_coverage, 2) AS upper_band_coverage_pct
FROM nightflow_fold_metrics
ORDER BY fold;

-- Official-source mismatches that require human review rather than silent overwrite.
SELECT calendar_year,
       apr_total_discharges,
       edm_total_discharges,
       absolute_difference,
       relative_difference,
       retrieved_date
FROM v_source_reconciliation_review;

-- DMAs where the ML challenger materially underperforms persistence.
SELECT DMA_ID,
       test_rows,
       mae_model,
       mae_persistence,
       relative_mae_improvement
FROM nightflow_dma_performance
WHERE relative_mae_improvement < 0
ORDER BY relative_mae_improvement ASC;

-- Current multi-signal resource context. These are project watch rules, not an official drought classification.
SELECT month, year,
       rainfall_provisional_pct_lta,
       reservoir_pct, reservoir_hist_median_pct, reservoir_vs_hist_median_pp,
       demand_ml_day, demand_hist_median_ml_day, demand_vs_hist_median_pct,
       active_watch_signals
FROM v_latest_resource_watch;

-- v0.6: compare review policies at the default daily capacity.
SELECT policy, signal_capture, candidate_precision, candidate_recall,
       mean_backlog_candidates, capacity_utilisation,
       mean_consecutive_day_jaccard, selection_hhi
FROM v_nightflow_policy_capacity20;

-- v0.6: inspect signal-capture / workload / continuity trade-offs by capacity.
SELECT *
FROM v_nightflow_capacity_tradeoff
ORDER BY capacity, signal_capture DESC;

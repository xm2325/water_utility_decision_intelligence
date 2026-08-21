# Interview case study — Water Utility Decision Intelligence

## 60-second version

I built a public-data decision product around two utility problems: how to prioritise reported regulatory pressure and how to turn DMA night-flow signals into a review queue under limited capacity. The night-flow pipeline used 424,695 public records across 345 DMAs and 210,841 held-out predictions over four rolling-origin folds. HistGradientBoosting improved aggregate MAE by 1.15%, but it failed my pre-set promotion gate because the gain was below 2% and its weakest fold was 5.24% worse, so I retained persistence. I then evaluated the operational policy rather than stopping at forecast error: at 20 reviews per day the constrained queue reviewed 52.6% of candidate alerts while retaining 85.3% of positive residual-excess signal. I added block-bootstrap, quarter-level robustness, queue-continuity, source-reconciliation and evidence-provenance checks so every application claim is tied to an executed public-data run.

## Five-minute walkthrough

### 1. Business question

A utility data-science team does not have unlimited analyst or field-review capacity. The useful question is therefore not only “can I forecast night flow?”, but also “which signals should be reviewed first, how stable is that queue, and how do I know the evidence is reliable?”

### 2. Data and controls

The project downloads Yorkshire Water public DMA night-flow data through ArcGIS and pins APR releases by URL, bytes, row count and SHA-256. Data-contract checks cover DMA count, time span, missingness, duplicate keys, negative flows and units. Compact live outputs are hashed into a provenance file; large raw tables remain Actions artifacts.

### 3. Forecast governance

Features use strictly prior calendar-time history. Each rolling fold selects a simple comparator using calibration data only. Persistence won all four real-data folds. The ML challenger improved overall MAE from 0.15931 to 0.15747, but that 1.15% gain was below the 2% promotion margin and the weakest fold was 5.24% worse. I therefore retained the simpler champion rather than changing the rule after seeing the result.

### 4. Decision policy

Only positive upper-band exceedances become investigation candidates. At capacity 20, the constrained queue selected 52.6% of candidate alerts and retained 85.3% of positive residual-excess signal. Highest-flow selection retained 38.9%; deterministic random retained 5.5%. These are residual-signal metrics, not confirmed leak outcomes.

### 5. Operational trade-offs

The project reports diminishing return as capacity rises, daily queue churn, candidate backlog, capacity utilisation and DMA concentration. A 10% candidate-only continuity reserve increased daily queue Jaccard by 45.7% for a 0.059 percentage-point capture cost. I report this as a sensitivity point, not a recommendation.

### 6. Robustness

A 7-day moving-block bootstrap gives an 82.4%–88.2% 95% interval for capacity-20 residual-signal capture. The same frozen policy beats highest-flow in all 8 calendar-quarter slices, while its own capture varies from 76.9% to 95.1%. That distinction matters: the comparative ranking is consistent in the observed slices, but absolute performance still changes through time.

## What I would add with internal utility data

With access to internal systems I would link candidates to confirmed investigations, repairs, asset condition, work-order outcome, response time and cost. That would allow the decision target to move from residual-signal capture to an operational outcome such as confirmed issue yield or expected intervention value. I would also add spatial/network topology, rainfall and pressure context at the correct operational grain, then monitor both model performance and queue outcomes after deployment.

## What I deliberately do not claim

The public dataset does not contain verified leak labels, intervention success or recovered water. The repository therefore does not claim detected leaks, avoided incidents, financial savings, optimal staffing, recovered ODI payments or an executed Azure/Databricks deployment.

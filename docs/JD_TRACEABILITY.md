# Senior Data Scientist role traceability

This table maps repository evidence to the Yorkshire Water Senior Data Scientist requirements that the project can reasonably demonstrate. It also states where the repository is only partial evidence or no evidence at all.

| Role area | Evidence in this repository | Strength |
|---|---|---|
| Python / data science / ML | Reproducible Python pipelines, rolling-origin forecasting, baseline selection, uncertainty bands, bootstrap and temporal robustness | Strong |
| SQL / operational data product | SQLite publication layer with stable decision, capacity, continuity, reconciliation and robustness views | Strong |
| Translate data into action | Forecast outputs are converted into a candidate-only, capacity-constrained review queue with backlog and workload metrics | Strong |
| Technical assurance / QA | Source pins, data contracts, source reconciliation, drift checks, champion/challenger gates, provenance hashes and evidence register | Strong |
| Model performance evaluation | Aggregate, fold-level, DMA-level, block-bootstrap and calendar-quarter evaluation; simple model retained when ML failed the gate | Strong |
| Data engineering / pipelines | Official-source retrieval, ArcGIS pagination, retry/backoff, schema checks, manifests, reproducible CLI and GitHub Actions | Strong |
| Open data | APR, EDM, Watsit and ArcGIS public-data layers with explicit source boundaries | Strong |
| Product ownership / prioritisation | Capacity frontier, queue continuity, evidence release gate and SQL product show end-to-end decision-product thinking | Strong portfolio evidence |
| Water / wastewater domain | Uses water-utility performance, storm-overflow, resource and DMA night-flow data | Partial: public-data case study, not internal operational experience |
| Asset management | DMA-level signals and operational prioritisation are relevant, but the public project has no asset register, failure history or work-order data | Partial |
| Azure / Databricks | `docs/ARCHITECTURE.md` maps the current pipeline to a reference cloud design | Partial: architecture only; no executed cloud deployment claimed |
| R | Not used in this repository | Gap in this project |
| Agile delivery | Repository history shows iterative releases and automated validation, but it does not evidence work within an Agile team | Gap / use professional examples |
| Coaching / supporting data scientists | Cannot be demonstrated by repository code | Gap / use professional examples |
| Senior stakeholder communication | README, case study and explicit decision/claim boundaries demonstrate communication design, but real stakeholder influence must come from professional experience | Partial |

## Best interview linkage

The strongest story for this role is not “I trained an ML model.” It is: I defined a decision problem, built a reproducible public-data pipeline, used a pre-set promotion rule, kept the simpler champion when ML did not clear the bar, converted the champion into a capacity-aware operational queue, and then tested workload, continuity and time robustness.

## Claims to avoid

Do not present this as a Yorkshire Water internal system. Do not claim confirmed leak detection, asset failure prediction, field-team savings, optimal staffing, prevented incidents, recovered water, avoided ODI payments or executed Azure/Databricks production deployment.

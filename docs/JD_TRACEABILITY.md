# Yorkshire Water Senior Data Scientist — project traceability

This file maps the public job description to evidence in this project. It also states gaps rather than treating architecture or source availability as completed experience.

| Job-description area | Project evidence | Evidence level / gap |
|---|---|---|
| Own Data & AI products and prioritise delivery | Separate regulatory triage, source-review, resource-watch and DMA queue outputs; SQL product; release-readiness register | Executed locally for APR/EDM/Watsit; DMA live metrics pending |
| Develop actionable insight and decision models | Capacity-aware APR triage; DMA investigation ranking under capacity | APR executed; DMA design tested synthetically, real live run pending |
| Python / SQL | Python package, scripts, tests, SQLite tables/views and operational SQL | Executed |
| R | Not used in this repository | Gap; do not claim from this project |
| Azure / Databricks / cloud | `ARCHITECTURE.md` maps raw/validated zones, Databricks/Delta, MLflow and monitoring | Design only; no executed cloud deployment claimed |
| Data engineering and pipelines | ArcGIS pagination/retry, provenance manifest, schema capture, hashes, deterministic transformations | Code and tests executed; full remote data pull pending |
| Technical assurance / QA / model evaluation | Data contract, rolling validation, persistence baseline, per-DMA gate, drift, source reconciliation, evidence register | Executed code/tests; live DMA metrics pending |
| ODI / reactive prioritisation | Official APR common-performance-commitment triage and exposure concentration | Executed official data |
| Utilities / water context | APR, EDM, Watsit and DMA night-flow public sources | Executed for first three; DMA source availability verified |
| Asset management | DMA investigation workflow is asset/network-oriented, but no internal asset registry/work-order history is available | Partial; do not claim internal asset-management delivery |
| Senior stakeholder communication / visualisation | Executive/result reports, SQL views and decision boundaries designed for operational review | Demonstrated project output; not evidence of Yorkshire Water stakeholder delivery |
| Coaching / Agile delivery | Not demonstrated by this repository | Gap; use only separate real work experience if applicable |

## Why this project is useful for the application

The strongest link to the role is not the gradient-boosting estimator. It is the combination of a defined operational decision, a cheap baseline, data/source QA, explicit model promotion, capacity limits, stable downstream outputs and clear claim boundaries. That structure matches a senior role where the data scientist is expected to own a Data/AI product rather than only train a model.

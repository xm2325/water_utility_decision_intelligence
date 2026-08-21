# Architecture

## Current executed public-repository architecture

```text
Official public sources
  ├─ Yorkshire Water APR CSV releases
  ├─ published EDM summary
  ├─ Watsit monthly resource data
  └─ ArcGIS FeatureServer layers
          |
          v
Source retrieval + provenance
  ├─ URL / SHA-256 / bytes / row pins for APR
  ├─ ArcGIS pagination + retry/backoff
  └─ download manifests
          |
          v
Validation + feature layer
  ├─ schema and data-contract checks
  ├─ calendar-time lag / rolling features
  └─ strictly prior information at prediction time
          |
          v
Forecast governance
  ├─ calibration-only simple-baseline selection
  ├─ rolling-origin ML evaluation
  ├─ uncertainty bands
  └─ champion/challenger promotion gate
          |
          v
Decision layer
  ├─ current positive candidates only
  ├─ capacity-constrained ranking
  ├─ marginal capacity frontier
  ├─ queue-continuity sensitivity
  ├─ moving-block robustness
  └─ calendar-quarter robustness
          |
          v
Publication + assurance
  ├─ CSV / JSON compact outputs
  ├─ SQLite operational views
  ├─ evidence register
  ├─ SHA-256 live provenance
  └─ GitHub Actions artifacts
```

This is the architecture actually executed in the public project.

## Reference Azure / Databricks production mapping

The following is a design mapping only. It has **not** been deployed by this repository.

| Current component | Possible production service |
|---|---|
| Public-source landing / raw snapshots | Azure Data Lake Storage Gen2, Bronze Delta tables |
| Schema and data-quality processing | Azure Databricks / Delta Live Tables or equivalent quality jobs |
| Curated DMA / regulatory tables | Silver/Gold Delta tables |
| Feature construction and training | Databricks jobs or Azure Machine Learning pipelines |
| Experiment and model tracking | MLflow / managed model registry |
| Batch review queue | Scheduled Databricks/AML job writing governed Gold decision tables |
| Operational reporting | Power BI / governed SQL endpoint |
| Monitoring | Azure Monitor plus data/model/queue-quality tables |
| Secrets / service access | Managed identities and Key Vault |

## Production controls I would add

A real deployment would need environment-specific infrastructure-as-code, service identities, network/security controls, dataset and model access policies, job-level SLAs, alerting, lineage, rollback procedures, model approval ownership, and a feedback loop from investigations/work orders into model and policy evaluation.

## Boundary

The reference table is included because the target role asks for cloud and modern data-platform skills. It must not be described as an executed Azure, Databricks or production deployment in CV or interview material.

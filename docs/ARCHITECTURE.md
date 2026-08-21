# Architecture — v0.4

```mermaid
flowchart LR
    A[APR Open Data CSV] --> B[Schema normalisation]
    B --> C[Performance-commitment portfolio]
    C --> D[Capacity triage]

    E[EDM published summary] --> F[Cross-source reconciliation]
    C --> F

    G[Watsit rainfall / reservoir / demand] --> H[Transparent resource watch]

    I[ArcGIS DMA night flow] --> J[Retrying paginated downloader]
    J --> K[Manifest + SHA-256 + schema]
    K --> L[Data contract / QA]
    L --> M[Calendar-time feature pipeline]
    M --> N[Rolling validation]
    N --> O[ML vs persistence gate]
    O --> P[Champion-consistent investigation queue]

    D --> Q[SQLite operational product]
    F --> Q
    H --> Q
    P --> Q
    N --> Q
    Q --> R[Analyst / dashboard / API]

    Q --> S[Evidence register / release readiness]
```

## Cloud production design

A production implementation could use:

- Azure Data Lake Storage for immutable raw and validated zones;
- Databricks jobs and Delta tables for ingestion, validation and features;
- MLflow for run tracking and champion/challenger registration;
- Azure Monitor or equivalent for pipeline and data checks;
- Power BI or a small API for operational queues and review tables.

This is a design mapping only. The current repository does not claim an executed Azure or Databricks deployment.

## Data-product contracts

The system exposes separate SQL outputs for three decision types rather than forcing unrelated data into one model:

1. regulatory workstream priority;
2. source reconciliation review;
3. resource context;
4. DMA investigation queue after a live ArcGIS run.

This separation reduces the risk of treating correlated public signals as if they were verified asset-level causal features.

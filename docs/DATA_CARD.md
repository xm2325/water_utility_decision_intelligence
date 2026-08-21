# Data card — v0.4

## APR regulatory data — executed

The regulatory analysis uses Yorkshire Water APR Open Data CSV files for 2023/24, 2024/25 and 2025/26. The latest file contains **121,937 rows**.

For 2025/26 the parser finds:

- 36 common `3A.*` rows;
- 18 rows with a numeric payment;
- 12 rows with `PCL met? = No` across the full common set;
- 11 rows with both `PCL met? = No` and a numeric payment.

The **£76.75m** gross negative-payment figure is a narrow common-3A payment extract, not the company's full ODI result and not an estimate of avoidable payment.

## EDM published summary — executed reconciliation

`data/raw/edm/edm_published_summary.csv` stores the yearly spill totals displayed on Yorkshire Water's EDM page as retrieved on 21 August 2026. The APR line explicitly describes January–December spill counts, so the project compares its calendar-year value with the EDM calendar-year summary.

The code reports differences without auto-correction. Current comparison:

- 2023: exact match;
- 2024: exact match;
- 2025: APR 51,560 versus EDM 51,404, difference 156 (0.303%).

The mismatch is a source-version/assurance review item; this project does not decide which publication should replace the other.

## Watsit monthly resource snapshot — executed

`data/raw/watsit/watsit_monthly_snapshot.csv` stores the monthly reservoir and demand series shown for 2023–2026 and rainfall values shown for 2025–2026, retrieved on 21 August 2026.

The resource-watch layer uses only same-calendar-month historical comparisons. The rainfall threshold of 75% LTA is a project watch rule, not an official drought threshold.

The source page gives July 2026 as 19.4% provisional rainfall versus LTA, 64.9% current regional reservoir stocks and 1,382 Ml/day demand. The monthly reservoir table rounds July 2026 to 65%.

## DMA night-flow — live workflow pending in this local build

Official annual ArcGIS layers expose:

`DATE`, `DMA_ID`, `CENTROID_X`, `CENTROID_Y`, `ACTUAL_MIN_NIGHT_FLOW`, `MIN_NIGHT_FLOW`, `UNITS`, `OBJECTID`.

Official layer record estimates checked on 21 August 2026 are 92,805 (2023), 126,270 (2024), 125,925 (2025) and 79,695 (2026), totalling 424,695 available public records.

The downloader records URL, retrieval time, schema, row count and SHA-256 hash in `download_manifest.jsonl`. Source availability is not treated as executed model evidence until the raw files and root-level live backtest outputs exist.

## Join policy

APR, EDM, Watsit, reservoir, drinking-water-quality and DMA sources are not merged merely because they share a date. Any future feature join must state a spatial and temporal key and test whether that key represents the intended operational unit.

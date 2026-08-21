# Data sources

## APR Open Data CSVs

Official Yorkshire Water reports page:
https://www.yorkshirewater.com/about-us/reports/

The large APR CSV releases are **not stored in Git**. The repository pins the reviewed official URLs, SHA-256 hashes, byte sizes and row counts in `config/source_pins.json`.

After cloning, run:

```bash
make bootstrap
```

This retrieves and verifies the 2023/24, 2024/25 and 2025/26 APR Open Data CSVs before any APR analysis runs.

## ArcGIS sources downloaded by the workflow

Yorkshire Water ArcGIS REST directory:
https://services-eu1.arcgis.com/1WqkK5cDKUbF0CkH/arcgis/rest/services

The network-enabled workflow uses:
- YW Night-flow monitoring 2023–2026
- Yorkshire Water Reservoir Levels 2026
- Yorkshire Water Drinking Water Quality 2026

The 2026 night-flow schema includes DATE, DMA_ID, ACTUAL_MIN_NIGHT_FLOW, MIN_NIGHT_FLOW, CENTROID_X and CENTROID_Y. The model treats elevated forecast residuals only as investigation signals, not confirmed leaks.

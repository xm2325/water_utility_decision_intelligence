# Source inventory

This project uses public Yorkshire Water sources only. It is an independent portfolio project and is not affiliated with Yorkshire Water.

## 1. APR Open Data CSV releases

The repository does **not** commit the large APR raw CSV files. `config/source_pins.json` records the reviewed official release URL, SHA-256, byte size and row count for each of:

- 2023/24 APR Open Data CSV
- 2024/25 APR Open Data CSV
- 2025/26 APR Open Data CSV

Run `make bootstrap` to retrieve and verify the pinned releases. A changed upstream file fails closed and must be reviewed before a pin is updated.

Used for performance-commitment extraction, payment exposure analysis and the storm-overflow APR series.

## 2. Published EDM summary snapshot

`data/raw/edm/edm_published_summary.csv` stores a small, reviewable snapshot of Yorkshire Water's published annual Event Duration Monitoring summary, with source URL and retrieval date. It is used only for cross-source reconciliation against APR spill counts.

## 3. Watsit monthly resource snapshot

`data/raw/watsit/` stores small source snapshots derived from Yorkshire Water's Watsit report page for rainfall, reservoir stocks and demand. These are used as transparent analyst context, not as an official drought classification.

## 4. ArcGIS operational tables

The network-enabled workflow retrieves Yorkshire Water ArcGIS layers for:

- DMA night-flow monitoring, 2023–2026;
- reservoir levels, 2026;
- drinking-water quality, 2026.

Downloaded ArcGIS CSVs are not committed. Each live run records retrieval metadata and SHA-256 values in `data/raw/arcgis/download_manifest.jsonl`.

## Evidence rule

A numerical claim is allowed into application material only when the corresponding source and executed result are present and classified as executed real-data evidence in `results/EVIDENCE_REGISTER.csv`. Synthetic validation metrics are never external evidence.

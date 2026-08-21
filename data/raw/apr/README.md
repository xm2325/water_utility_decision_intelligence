# APR raw files

The three APR CSV releases are intentionally not committed to Git.

Run:

```bash
make bootstrap
```

The downloader retrieves Yorkshire Water's official 2023/24, 2024/25 and 2025/26 Open Data CSV releases and checks SHA-256, byte size and row count against `config/source_pins.json`.

If Yorkshire Water republishes a file, the default command fails closed. Review the upstream change before updating a pin; `--allow-source-drift` downloads changed bytes for review but never rewrites the pinned metadata automatically.

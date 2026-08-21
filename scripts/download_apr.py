from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.source_pins import load_source_pins, sha256_file

PINS = ROOT / "config" / "source_pins.json"
MANIFEST = ROOT / "data" / "raw" / "apr" / "download_manifest.json"


def download_one(name: str, pin: dict, allow_source_drift: bool = False) -> dict:
    target = ROOT / pin["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    headers = {"User-Agent": "water-utility-decision-intelligence/0.4 (+public-data-reproducibility)"}
    with requests.get(pin["url"], stream=True, timeout=(15, 120), headers=headers) as response:
        response.raise_for_status()
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    actual_sha = sha256_file(tmp)
    actual_bytes = tmp.stat().st_size
    df = pd.read_csv(tmp, low_memory=False)
    actual_rows = len(df)
    matches_pin = (
        actual_sha == pin["sha256"]
        and actual_bytes == int(pin["bytes"])
        and actual_rows == int(pin["rows"])
    )
    if not matches_pin and not allow_source_drift:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Pinned source {name} changed: sha={actual_sha}, bytes={actual_bytes}, rows={actual_rows}. "
            "Review the upstream change before accepting a new pin."
        )
    os.replace(tmp, target)
    return {
        "source": name,
        "url": pin["url"],
        "path": pin["path"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": actual_sha,
        "bytes": actual_bytes,
        "rows": actual_rows,
        "matches_pin": matches_pin,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Download pinned Yorkshire Water APR CSV releases")
    parser.add_argument("--allow-source-drift", action="store_true", help="Download changed upstream bytes for review; never updates pins automatically")
    args = parser.parse_args()
    payload = load_source_pins(PINS)
    records = [download_one(name, pin, args.allow_source_drift) for name, pin in payload["sources"].items()]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"schema_version": 1, "downloads": records}, indent=2), encoding="utf-8")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(frozen=True)
class ArcGISLayer:
    name: str
    url: str
    return_geometry: bool = False


LAYERS = {
    "night_flow_2023": ArcGISLayer(
        "night_flow_2023",
        "https://services-eu1.arcgis.com/1WqkK5cDKUbF0CkH/ArcGIS/rest/services/YW%20Night-flow%20monitoring%202023/FeatureServer/0",
    ),
    "night_flow_2024": ArcGISLayer(
        "night_flow_2024",
        "https://services-eu1.arcgis.com/1WqkK5cDKUbF0CkH/ArcGIS/rest/services/YW%20Night-flow%20monitoring%202024/FeatureServer/0",
    ),
    "night_flow_2025": ArcGISLayer(
        "night_flow_2025",
        "https://services-eu1.arcgis.com/1WqkK5cDKUbF0CkH/ArcGIS/rest/services/YW%20Night-flow%20monitoring%202025/FeatureServer/0",
    ),
    "night_flow_2026": ArcGISLayer(
        "night_flow_2026",
        "https://services-eu1.arcgis.com/1WqkK5cDKUbF0CkH/ArcGIS/rest/services/YW%20Night-flow%20monitoring%202026/FeatureServer/0",
    ),
    "reservoir_2026": ArcGISLayer(
        "reservoir_2026",
        "https://services-eu1.arcgis.com/1WqkK5cDKUbF0CkH/ArcGIS/rest/services/Yorkshire%20Water%20Reservoir%20Levels%202026/FeatureServer/0",
        return_geometry=True,
    ),
    "dwq_2026": ArcGISLayer(
        "dwq_2026",
        "https://services-eu1.arcgis.com/1WqkK5cDKUbF0CkH/ArcGIS/rest/services/Yorkshire%20Water%20Drinking%20Water%20Quality%202026/FeatureServer/0",
    ),
}


def retry_session(total: int = 5, backoff_factor: float = 0.8) -> requests.Session:
    retry = Retry(
        total=total,
        connect=total,
        read=total,
        status=total,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "water-utility-decision-intelligence/0.4 (+public-open-data-validation)"})
    return session


def _get_json(session: Any, url: str, params: dict[str, Any], timeout: int) -> dict[str, Any]:
    response = session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"ArcGIS error: {payload['error']}")
    return payload


def fetch_metadata(layer: ArcGISLayer, session: Any = requests, timeout: int = 60) -> dict[str, Any]:
    return _get_json(session, layer.url, {"f": "json"}, timeout)


def fetch_layer(
    layer: ArcGISLayer,
    session: Any = requests,
    timeout: int = 60,
    *,
    metadata: dict[str, Any] | None = None,
) -> pd.DataFrame:
    meta = metadata or fetch_metadata(layer, session=session, timeout=timeout)
    page_size = int(meta.get("maxRecordCount", 2000))
    query_url = layer.url.rstrip("/") + "/query"
    rows: list[dict[str, Any]] = []
    offset = 0

    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": str(layer.return_geometry).lower(),
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "orderByFields": str(meta.get("objectIdField", "OBJECTID")) + " ASC",
            "f": "json",
        }
        payload = _get_json(session, query_url, params, timeout)
        features = payload.get("features", [])
        for feature in features:
            row = dict(feature.get("attributes", {}))
            if layer.return_geometry and feature.get("geometry") is not None:
                row["_geometry"] = json.dumps(feature["geometry"], sort_keys=True)
            rows.append(row)

        if not features:
            break
        if len(features) < page_size and not payload.get("exceededTransferLimit", False):
            break
        offset += len(features)

    return pd.DataFrame(rows)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _field_schema(meta: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for f in meta.get("fields", []):
        out.append({"name": f.get("name"), "type": f.get("type"), "nullable": f.get("nullable")})
    return out


def download_layer(
    name: str,
    output_dir: str | Path,
    *,
    manifest_path: str | Path | None = None,
    session: Any | None = None,
    timeout: int = 60,
) -> Path:
    if name not in LAYERS:
        raise KeyError(f"Unknown layer: {name}. Choices: {sorted(LAYERS)}")

    layer = LAYERS[name]
    session = session or retry_session()
    meta = fetch_metadata(layer, session=session, timeout=timeout)
    df = fetch_layer(layer, session=session, timeout=timeout, metadata=meta)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.csv"
    df.to_csv(out, index=False)

    manifest = {
        "dataset": name,
        "source_url": layer.url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "sha256": sha256_file(out),
        "service_item_id": meta.get("serviceItemId"),
        "max_record_count": meta.get("maxRecordCount"),
        "object_id_field": meta.get("objectIdField"),
        "editing_info": meta.get("editingInfo", {}),
        "fields": _field_schema(meta),
    }

    manifest_path = Path(manifest_path) if manifest_path else out_dir / "download_manifest.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(manifest, sort_keys=True) + "\n")

    return out

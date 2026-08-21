from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_source_pins(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported source pin schema version")
    sources = payload.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise ValueError("Source pin file must contain at least one source")
    required = {"url", "path", "sha256", "bytes", "rows"}
    for name, pin in sources.items():
        missing = required - set(pin)
        if missing:
            raise ValueError(f"Source pin {name!r} missing fields: {sorted(missing)}")
    return payload


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def validate_file_against_pin(path: str | Path, pin: dict[str, Any]) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"exists": False, "ok": False, "reason": "missing"}
    actual_bytes = p.stat().st_size
    actual_sha = sha256_file(p)
    ok = actual_bytes == int(pin["bytes"]) and actual_sha == str(pin["sha256"])
    return {
        "exists": True,
        "ok": ok,
        "actual_bytes": actual_bytes,
        "expected_bytes": int(pin["bytes"]),
        "actual_sha256": actual_sha,
        "expected_sha256": str(pin["sha256"]),
        "reason": "match" if ok else "source_drift",
    }

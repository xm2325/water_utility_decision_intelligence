import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.arcgis import ArcGISLayer, download_layer, fetch_layer, sha256_file  # noqa: E402


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Session:
    def __init__(self):
        self.query_calls = 0

    def get(self, url, params=None, timeout=60):
        if url.endswith("/query"):
            self.query_calls += 1
            if self.query_calls == 1:
                return Response(
                    {
                        "features": [
                            {"attributes": {"OBJECTID": 1, "A": 1}},
                            {"attributes": {"OBJECTID": 2, "A": 2}},
                        ],
                        "exceededTransferLimit": True,
                    }
                )
            return Response(
                {
                    "features": [{"attributes": {"OBJECTID": 3, "A": 3}}],
                    "exceededTransferLimit": False,
                }
            )
        return Response(
            {
                "maxRecordCount": 2,
                "objectIdField": "OBJECTID",
                "serviceItemId": "abc",
                "fields": [
                    {"name": "OBJECTID", "type": "esriFieldTypeOID", "nullable": False},
                    {"name": "A", "type": "esriFieldTypeInteger", "nullable": True},
                ],
            }
        )


def test_arcgis_pagination():
    session = Session()
    layer = ArcGISLayer("x", "https://example.test/FeatureServer/0")
    d = fetch_layer(layer, session=session)
    assert d["A"].tolist() == [1, 2, 3]
    assert session.query_calls == 2


def test_sha256_is_deterministic(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("abc", encoding="utf-8")
    assert sha256_file(p) == sha256_file(p)
    assert len(sha256_file(p)) == 64


def test_download_layer_writes_manifest(tmp_path, monkeypatch):
    import yw_decisioning.arcgis as arcgis

    layer = ArcGISLayer("fake", "https://example.test/FeatureServer/0")
    monkeypatch.setitem(arcgis.LAYERS, "fake", layer)
    out = download_layer("fake", tmp_path, session=Session())
    assert out.exists()
    manifest = tmp_path / "download_manifest.jsonl"
    record = json.loads(manifest.read_text(encoding="utf-8").strip())
    assert record["dataset"] == "fake"
    assert record["rows"] == 3
    assert record["sha256"] == sha256_file(out)
    assert record["fields"][0]["name"] == "OBJECTID"

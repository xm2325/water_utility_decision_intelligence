from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.source_pins import load_source_pins, sha256_file, validate_file_against_pin


def test_load_source_pins_has_three_apr_releases():
    pins = load_source_pins(ROOT / "config" / "source_pins.json")
    assert set(pins["sources"]) == {"apr_2023_24", "apr_2024_25", "apr_2025_26"}


def test_validate_file_against_pin_detects_match_and_drift(tmp_path):
    p = tmp_path / "x.csv"
    p.write_bytes(b"abc")
    pin = {"bytes": 3, "sha256": sha256_file(p)}
    assert validate_file_against_pin(p, pin)["ok"] is True
    p.write_bytes(b"abcd")
    result = validate_file_against_pin(p, pin)
    assert result["ok"] is False
    assert result["reason"] == "source_drift"

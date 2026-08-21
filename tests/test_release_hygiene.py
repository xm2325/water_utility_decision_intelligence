from pathlib import Path
import re

from yw_decisioning.live_provenance import build_live_provenance, verify_live_provenance


ROOT = Path(__file__).resolve().parents[1]


def _req_name(line: str) -> str:
    return re.split(r"[<>=!~\[]", line.strip(), maxsplit=1)[0].lower().replace("_", "-")


def test_provenance_deduplicates_required_paths(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    name = "nightflow_backtest_metrics.json"
    (results / name).write_text("{}", encoding="utf-8")
    build_live_provenance(tmp_path)
    ok, detail = verify_live_provenance(tmp_path, required=(name, name))
    assert ok is True
    assert detail["files_checked"] == 1


def test_dependency_lock_covers_direct_requirements():
    direct = {
        _req_name(line)
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    lock_lines = [
        line.strip()
        for line in (ROOT / "requirements-lock.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    locked = {_req_name(line) for line in lock_lines}
    assert direct <= locked
    assert all("==" in line for line in lock_lines)
    assert len(locked) == len(lock_lines)


def test_workflows_use_locked_node24_actions():
    for rel in (".github/workflows/ci.yml", ".github/workflows/real-data.yml"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "actions/checkout@v5" in text
        assert "actions/setup-python@v6" in text
        assert "pip install -r requirements-lock.txt" in text
        assert "cache-dependency-path: requirements-lock.txt" in text

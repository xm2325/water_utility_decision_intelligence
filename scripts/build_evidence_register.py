from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yw_decisioning.governance import save_evidence_register  # noqa: E402


def main():
    summary = save_evidence_register(ROOT)
    report_path = ROOT / "results" / "RELEASE_READINESS.md"
    if report_path.exists():
        lines = report_path.read_text(encoding="utf-8").splitlines()
        if lines:
            version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
            lines[0] = f"# Release readiness — v{version}"
            report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

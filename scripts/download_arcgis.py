from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from yw_decisioning.arcgis import LAYERS, download_layer  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Yorkshire Water ArcGIS open-data layers")
    parser.add_argument("layers", nargs="+", choices=sorted(LAYERS))
    parser.add_argument("--output-dir", default=str(ROOT / "data" / "raw" / "arcgis"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    manifest = output_dir / "download_manifest.jsonl"
    if manifest.exists():
        manifest.unlink()  # one deterministic manifest per refresh run

    for name in args.layers:
        path = download_layer(name, output_dir, manifest_path=manifest)
        print(path)


if __name__ == "__main__":
    main()

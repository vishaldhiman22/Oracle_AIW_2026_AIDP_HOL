"""Package authored labs; record hashes without duplicating original assets."""
import ast
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    "source-data_suppliers_supplier_extract.csv",
    "source-data_assets_financial_assets.csv",
    "source-data_purchasing_purchase_orders.csv",
    "source-data_schedules_project_milestones.csv",
    "source-data_inspections_inspection_findings.csv",
    "documents_atlas_supplier_framework_agreement.pdf",
    "documents_austin_receiving_inspection_report.pdf",
    "documents_austin_structural_engineering_specification.pdf",
]


def main():
    learner_files = sorted((ROOT / "notebooks").iterdir())
    assert len(learner_files) == 4 and all(p.suffix == ".ipynb" for p in learner_files), "Only the four IPYNB notebooks belong in notebooks/"
    for source in ROOT.rglob("*.py"):
        ast.parse(source.read_text(), filename=str(source))
    manifest = []
    for name in ASSETS:
        path = ROOT.parent / name
        checksum = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(block)
        manifest.append({"filename": name, "bytes": path.stat().st_size, "sha256": checksum.hexdigest()})
    (ROOT / "reference/source-assets.json").write_text(json.dumps(manifest, indent=2) + "\n")
    target = ROOT.parent / "aidp-livelabs.zip"
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if not path.is_file() or any(part in {"__pycache__", "deployment", "validation", "local-store", "executed"} for part in relative.parts):
                continue
            if path.name == "config.local.json" or path.name.endswith(".rendered.json"):
                continue
            archive.write(path, "aidp-livelabs/" + relative.as_posix())
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        print(f"Created {target}: {len(archive.namelist())} files; {target.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

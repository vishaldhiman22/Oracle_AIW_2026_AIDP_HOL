# Oracle_AIW_2026_AIDP_HOL

Hands-on Oracle AI Data Platform labs for a sample construction-project lakehouse and MLflow model lifecycle.

## Labs

1. [Lab 1A: Bronze ingestion](aidp-livelabs/notebooks/Lab1A_Bronze_Ingestion.ipynb): load five CSV feeds into Delta tables.
2. [Lab 1B: Silver transformations](aidp-livelabs/notebooks/Lab1B_Silver_Transformations.ipynb): standardize suppliers and reconcile project data.
3. [Lab 1C: Gold project data](aidp-livelabs/notebooks/Lab1C_Gold_Project_Data.ipynb): build project context with Spark SQL and milestone features.
4. [Lab 2: MLflow lifecycle](aidp-livelabs/notebooks/Lab2_Predict_Investigate_and_Operationalize.ipynb): train six candidates, compare runs, register the winner, reload its version, and score Gold data. Task 11 stages three PDFs; Tasks 12 onward have been removed.

Start with the [setup guide](aidp-livelabs/docs/00-setup.md), then follow the [Lab 1](aidp-livelabs/docs/01-lab1.md) and [Lab 2](aidp-livelabs/docs/02-lab2.md) instructions. The [workflow](aidp-livelabs/docs/workflow.md) and [knowledge-base](aidp-livelabs/docs/knowledge-base.md) guides are separate optional extensions.

## Bring your own AIDP environment

- Create a dedicated catalog, workspace, Spark cluster, schemas and volumes. No cloud resources or credentials are supplied by this repository.
- The sample catalog/workspace name is `seer_livelabs_20260922`. Either create that name in your own environment or update it consistently in all notebook setup cells, `aidp-livelabs/config/workshop.json`, and instructions.
- Upload the five root-level CSV files and three sample PDFs into the source volume. Upload the four notebooks and required config/reference JSON files under `/Workspace/Shared/seer-aidp-livelabs` as described in the setup guide.
- Keep AIDP's integrated MLflow package. Training runs use scikit-learn Gradient Boosting and Decision Tree models; the unused ONNX model is not included or required.

**Reset warning:** Lab 1 drops and recreates its 12 named tables without backups. Use only a dedicated learning environment. Lab 2 keeps experiment/model history and replaces its predictions table. See [rerun guidance](aidp-livelabs/docs/reruns.md).

Training history is synthetic and the supplied source data is a teaching fixture. Metrics and predictions are not production forecasts. Learner logic is inline in the notebooks; `tools/test_support` contains historical authoring-test references, not AIDP dependencies.

## Public distribution and checks

This repository contains source notebooks, sample CSV/PDF inputs, support JSON, workflow templates, text guides, and authoring tools. Private deployment receipts, resource OCIDs, executed notebooks, logs, personal filesystem paths, screenshots with account details, generated PDF/ZIP exports, virtual environments, and caches are excluded. The original private workspace is unchanged.

From `aidp-livelabs`, use Python 3 with NumPy and pandas:

```bash
python tools/validate_lab1_structure.py
python tools/validate_maintenance.py
python tools/validate_lab2_independence.py
```

Optional HTML generation requires Pandoc and Pillow: `python tools/build_guide.py`, then `python tools/validate_guide.py`. To build a PDF, install ReportLab, pypdf and Pillow, provide DejaVu fonts via `AIDP_GUIDE_FONT_DIR`, and run `python tools/build_pdf.py`. Authoring packages are local tools; do not install them over AIDP's managed MLflow runtime.

Adapted from Oracle LiveLabs material by Eli Schilling and the LiveLabs/ONA Lab Experience teams. See [source mapping and attribution](aidp-livelabs/docs/conversion-map.md). This independently maintained repository is not an Oracle-published replacement.

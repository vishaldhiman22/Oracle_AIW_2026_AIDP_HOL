# Oracle AI World 2026: AIDP Hands-on Labs

Hands-on Oracle AI Data Platform labs for a sample construction-project lakehouse and MLflow model lifecycle.

## Labs

1. [Lab 1A: Bronze ingestion](aidp-livelabs/notebooks/Lab1A_Bronze_Ingestion.ipynb): load five CSV feeds into Delta tables.
2. [Lab 1B: Silver transformations](aidp-livelabs/notebooks/Lab1B_Silver_Transformations.ipynb): standardize suppliers and reconcile project data.
3. [Lab 1C: Gold project data](aidp-livelabs/notebooks/Lab1C_Gold_Project_Data.ipynb): build project context with Spark SQL and milestone features.
4. [Lab 2: MLflow lifecycle](aidp-livelabs/notebooks/Lab2_Predict_Investigate_and_Operationalize.ipynb): train six candidates, compare runs, register the winner, reload its version, and score Gold data. The lab ends at Task 11, which stages three PDFs.

Start with the [setup guide](aidp-livelabs/docs/00-setup.md), then follow the [Lab 1](aidp-livelabs/docs/01-lab1.md) and [Lab 2](aidp-livelabs/docs/02-lab2.md) instructions. The [workflow](aidp-livelabs/docs/workflow.md) and [knowledge-base](aidp-livelabs/docs/knowledge-base.md) guides are separate optional extensions.

## Quick start

```bash
git clone https://github.com/vishaldhiman22/Oracle_AIW_2026_AIDP_HOL.git
cd Oracle_AIW_2026_AIDP_HOL
```

1. Follow the setup guide to prepare your own AIDP environment and upload the source files below. Keep their filenames unchanged.
2. Import the four `.ipynb` files from `aidp-livelabs/notebooks/` as AIDP notebooks, and upload the configuration and reference JSON files to the corresponding workspace folders.
3. Attach your Spark cluster and run **Lab 1A → Lab 1B → Lab 1C → Lab 2**. These are AIDP/Spark notebooks, not standalone local Python scripts.
4. In Lab 2, run one cell at a time and pause after Task 6 to compare the first three runs before training the next three. Run each training round once per comparison session.
5. Register the selected model, reload its explicit version, score the Gold milestones, and finish with PDF staging in Task 11. Knowledge-base creation and agent testing are not required for the MLflow lab.

## Included sample inputs

All five CSV files and three project PDFs are included at the repository root. No separate bucket download is required for these inputs.

| Input | Purpose |
| --- | --- |
| [Supplier extract](source-data_suppliers_supplier_extract.csv) | Supplier standardization and reconciliation |
| [Financial assets](source-data_assets_financial_assets.csv) | Asset and project context |
| [Purchase orders](source-data_purchasing_purchase_orders.csv) | Procurement status and committed costs |
| [Project milestones](source-data_schedules_project_milestones.csv) | Milestone dates and status |
| [Inspection findings](source-data_inspections_inspection_findings.csv) | Inspection context |
| [Supplier framework agreement](documents_atlas_supplier_framework_agreement.pdf) | Project document staged in Task 11 |
| [Austin receiving inspection report](documents_austin_receiving_inspection_report.pdf) | Project document staged in Task 11 |
| [Austin structural specification](documents_austin_structural_engineering_specification.pdf) | Project document staged in Task 11 |

The classifier is trained on generated synthetic history, not on these PDFs or the three current Gold rows. It then scores the Gold feature rows produced by Lab 1C. Task 11 checks the PDFs against [the PDF manifest](aidp-livelabs/reference/pdf-manifest.json).

## Bring your own AIDP environment

- Create a dedicated catalog, workspace, Spark cluster, schemas and volumes. No cloud resources or credentials are supplied by this repository.
- The sample catalog/workspace name is `seer_livelabs_20260922`. Either create that name in your own environment or update it consistently in all notebook setup cells, `aidp-livelabs/config/workshop.json`, and instructions.
- Upload the five root-level CSV files and three sample PDFs into the source volume. Upload the four notebooks and required config/reference JSON files under `/Workspace/Shared/seer-aidp-livelabs` as described in the setup guide.
- Keep AIDP's integrated MLflow package. Training runs use scikit-learn Gradient Boosting and Decision Tree models; the unused ONNX model is not included or required.

**Reset warning:** Lab 1 drops and recreates its 12 named tables without backups. Use only a dedicated learning environment. Lab 2 keeps experiment/model history and replaces its predictions table. See [rerun guidance](aidp-livelabs/docs/reruns.md).

Training history is synthetic and the supplied source data is a teaching fixture. Metrics and predictions are not production forecasts. All learner logic is inline in the notebooks; no support Python libraries or authoring tools are required.

## Required runtime files

Upload only these files to the corresponding AIDP workspace folders:

- The four `.ipynb` files in `aidp-livelabs/notebooks/`.
- `aidp-livelabs/config/workshop.json`, read by all four notebooks.
- `aidp-livelabs/reference/pdf-manifest.json`, read only by Lab 2 Task 11.

Upload the five CSVs and three PDFs separately to the source volume. Instructions and the optional workflow template are provided for learners; they are not notebook runtime dependencies.

The authoring tools, historical test helpers, unused reference files and unused evidence configuration have been removed from this learner package. Private deployment receipts, resource OCIDs, executed notebooks, logs, personal filesystem paths, account screenshots, generated PDF/ZIP exports, virtual environments and caches are also excluded.

Adapted from Oracle LiveLabs material by Eli Schilling and the LiveLabs/ONA Lab Experience teams. See [source mapping and attribution](aidp-livelabs/docs/conversion-map.md). This independently maintained repository is not an Oracle-published replacement.

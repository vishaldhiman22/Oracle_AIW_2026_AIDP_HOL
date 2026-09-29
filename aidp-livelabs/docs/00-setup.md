# Before you begin: prepare the AIDP workshop

[Workshop home](../README.md) · Next: [Lab 1](01-lab1.md)

## Introduction

In this workshop, you play Alex, the data engineer at Seer Construction. Your project manager needs a consistent view of suppliers, purchase orders, inspections and upcoming milestones. You will build that foundation in Lab 1, then train a demonstration classifier and investigate PDF evidence in Lab 2.

**Estimated time:** 20–30 minutes to verify the prepared environment; allow additional provisioning time for a fresh environment. Lab 1 takes approximately 45–60 minutes when following all checkpoints. Lab 2 takes approximately 90–120 minutes including the UI exercises, excluding service startup and ingestion wait time.

**What you will learn**

- Navigate a dedicated catalog, workspace, Spark cluster and managed volumes.
- Run Python notebook cells in sequence and inspect managed Bronze, Silver and Gold tables.
- Trace model predictions to the selected experiment run and registered model version.
- Execute four notebooks as dependent tasks in an AIDP workflow.

> **Current edition:** Lab 1 is split into Bronze, Silver and Gold notebooks. Lab 2 is the fourth notebook. The catalog/schema locations are unchanged; the four-task workflow completed with native Success. Earlier screenshots show previous notebook/task names where noted.

## Your workshop values

Use these exact values in the prepared environment. If an instructor gives you a separate learner environment, replace the catalog/workspace and paths consistently.

| Setting | Value |
| --- | --- |
| OCI region | US Midwest (Chicago), `us-chicago-1` |
| Workbench display name | Your AIDP workbench |
| Catalog and workspace | `seer_livelabs_20260922` |
| Spark cluster | `seer_livelabs_spark` |
| Schemas | `seer_bronze`, `seer_silver`, `seer_gold` |
| Source volume | `seer_livelabs_20260922.seer_bronze.source_files` |
| Output volume | `seer_livelabs_20260922.seer_gold.workshop_outputs` |
| Package filesystem root | `/Workspace/Shared/seer-aidp-livelabs` |
| Workflow display name | `seer_aidp_labs` |

Use the workbench OCID, workspace key and cluster key from your own AIDP environment. This public repository supplies no live connection details. Create the example resource names above, or replace them consistently throughout the notebook setup cells and configuration.

## Prerequisites

1. Sign in to the supplied OCI tenancy and open its AIDP workbench in Chrome.
2. Confirm that your identity can read the source volume, create/update tables in the three workshop schemas, write the output volume, and use the dedicated workspace/cluster.
3. Knowledge-base and agent permissions are not required for Lab 2 Tasks 1–11. The separate optional PDF knowledge-base guide has additional prerequisites.
4. The five CSVs and three sample PDFs are included at the repository root. Keep them available locally for upload to your source volume.
5. Obtain approval for your environment's compute usage before starting it. A 30-minute idle timeout reduces unattended runtime; it is not a spending cap.

No ALH database login, ONNX runtime or GPU is required. Lab 1 uses Spark DataFrames and Spark SQL. Lab 2 uses the platform's MLflow integration and scikit-learn to train Gradient Boosting and Decision Tree classifiers on the driver, compare six experiment runs, register the winner, and reload its explicit version for batch scoring through a Spark UDF. It saves only predictions as a Gold table; no quality/freshness review or summary-generation task is included. Do not apply this bounded driver-side training implementation to production-scale data.

## Task 1: Confirm the catalog and schemas

1. In the workbench's left navigation, click **Master catalog**.
2. In the catalog list, click **seer_livelabs_20260922**.
3. On **Schemas**, find **seer_bronze**, **seer_silver** and **seer_gold**.
4. Check that each schema is Active. The automatically created `default` schema is not used by these notebooks.
5. Leave existing unrelated catalogs unchanged.



**Checkpoint:** You can open all three schemas. An empty Tables listing before Lab 1 is expected.

## Task 2: Verify the eight source files

1. From the catalog, open **seer_bronze**.
2. In **Types**, click **Volumes**, then **source_files**.
3. Select **Folders and Files**.
4. Verify these eight flat filenames. Do not rename them or add a second nested copy.

| Filename | Expected contents |
| --- | --- |
| `source-data_suppliers_supplier_extract.csv` | 8 supplier records |
| `source-data_assets_financial_assets.csv` | 3 asset records |
| `source-data_purchasing_purchase_orders.csv` | 4 purchase orders |
| `source-data_schedules_project_milestones.csv` | 4 milestones |
| `source-data_inspections_inspection_findings.csv` | 4 inspection records |
| `documents_atlas_supplier_framework_agreement.pdf` | 1 page |
| `documents_austin_receiving_inspection_report.pdf` | 1 page |
| `documents_austin_structural_engineering_specification.pdf` | 3 pages |



5. If a file is missing in a fresh environment, use the volume's **Actions** upload option and select that original file. Inspect the destination before submitting. Do not replace an existing different version without review.
6. Compare names and hashes with [source-assets.json](../reference/source-assets.json). Lab 1 no longer includes a source-inventory task.
7. Leave `models_all_MiniLM_L12_v2.onnx` local. The native knowledge base handles embeddings; this edition does not upload that model.

The notebook filesystem path is:

```text
/Volumes/seer_livelabs_20260922/seer_bronze/source_files
```

**Checkpoint:** Eight files, five CSV feeds, 23 total CSV rows, five PDF pages. Do not count the header as a data row.

## Task 3: Locate the notebooks and support files

1. Click **Workspaces** and open **seer_livelabs_20260922**.
2. Open **Shared → seer-aidp-livelabs → notebooks**.
3. Confirm that all four rows have Type **Notebook**, not simply File.
4. Keep this folder available; you will open Lab 1 from here.



5. Return one folder level to **seer-aidp-livelabs**. Verify the support folders:

```text
seer-aidp-livelabs/
  config/
    workshop.json
  reference/
    project_context_contract.json
    pdf-manifest.json
  notebooks/
    Lab1A_Bronze_Ingestion.ipynb
    Lab1B_Silver_Transformations.ipynb
    Lab1C_Gold_Project_Data.ipynb
    Lab2_Predict_Investigate_and_Operationalize.ipynb
  seer_aidp_labs.job
```

For a fresh import, create the folders first, upload ordinary support files into their matching folders, and import the IPYNBs as notebooks. Keep the folder structure intact. The native notebook metadata may report `Workspace/Shared/...` without the leading slash; Python filesystem reads use `/Workspace/Shared/...`.

**Checkpoint:** All four notebooks open with multiple Markdown/code cells: Bronze has 7 code cells, Silver 7, Gold 3, and Lab 2 has 12. All contain their own Python logic, without workspace library imports. An empty text editor or one large JSON cell indicates an incorrect import.

## Task 4: Inspect compute and dependencies

1. Confirm the workspace selector in the left navigation shows **seer_livelabs_20260922**.
2. Click **Compute**, then the **Clusters** tab.
3. Open **seer_livelabs_spark**.
4. On **Details**, verify Spark 3.5.0, an AMD driver with 2 OCPUs/16 GB, one AMD worker with 2 OCPUs/16 GB, and idle timeout 30 minutes.
5. If the cluster is stopped, start it only when you are ready to execute the lab and authorized to incur runtime charges. Wait for Active before running notebook cells.



6. For Lab 2, check MLflow, scikit-learn, pandas and NumPy. Keep AIDP's integrated MLflow package and authentication. The checked runtime provides MLflow 3.12.0, scikit-learn 1.8.0, pandas 2.2.3 and NumPy 2.4.6. No learner requirements file or XGBoost package is needed. PDF staging needs no PDF parser.
7. If a package is absent, use your administrator-approved cluster library installation method. Apply the requirements to the runtime used by both interactive notebooks and workflow tasks, and restart only if the library installer requires it.
8. In the first notebook, use a temporary Python cell to check the runtime after attaching compute:

```python
import sys
import pandas, numpy, sklearn, mlflow
from pathlib import Path

print(sys.version)
print("pandas", pandas.__version__)
print("numpy", numpy.__version__)
print("scikit-learn", sklearn.__version__)
print("MLflow", mlflow.__version__)
root = Path("/Workspace/Shared/seer-aidp-livelabs")
assert (root / "reference/pdf-manifest.json").is_file()
assert (root / "config/workshop.json").is_file()
assert (root / "reference/pdf-manifest.json").is_file()
assert Path("/Volumes/seer_livelabs_20260922/seer_bronze/source_files").is_dir()
assert "spark" in globals(), "Attach the dedicated Spark cluster."
```

Do not set `SEER_LOCAL_TEST=1` in AIDP. That flag bypasses Spark persistence and is only for offline package tests. Do not put credentials in a notebook cell.

## Task 5: Attach compute and learn the notebook controls

1. Open **Lab1A_Bronze_Ingestion.ipynb**.
2. At the upper right, click **Cluster → Attach existing cluster**.
3. Choose **seer_livelabs_spark**. Verify the attached-cluster label changes from **No cluster attached** to the workshop cluster.
4. If the cluster is missing, check the selected workspace and your compute permissions before creating another cluster.



5. Read each Markdown task, select its following Python code cell, and use **Run → Run selected cell(s)**. The cell-level play control is also available when the cell is selected. Wait for output or an error before moving on.
6. Use **Run all** only after understanding the notebook. In Lab 2's first interactive pass, pause after Task 6 to compare the first round, and finish after Task 11. The code does not pause automatically.
7. Do not run later cells after an earlier failure. For Lab 1, fix the root cause and rebuild the affected target and downstream dependencies. For a partially completed Lab 2 training round, start a fresh session from Task 1 and run both rounds once; blindly repeating the round can create extra candidates. Before repeating registration, check whether it already created a version.
8. Gold and Lab 2 default to run ID `interactive`. Workflow tasks receive the shared native job run ID. There is no `Lab` object in the learner notebooks.



## Task 6: Review configuration and choose your route

1. Open [config/workshop.json](../config/workshop.json) or its uploaded workspace copy.
2. Verify catalog, schema names and both volume paths against this guide.
3. Retain `source_layout: "flat"`. Use `"nested"` only for the original bucket's nested directory layout, with matching files.
4. Keep the historical fixture clock `2026-07-14T01:00:00+00:00`. It controls which upcoming milestones are selected; it does not make the sources current.
5. Training and evaluation remain synthetic demonstrations; the current labs do not use the legacy `fail_on_not_ready` setting.
6. No KB attestation file is required. Inspect ingestion status directly in AIDP during Lab 2.

Follow this sequence:

1. Complete [Lab 1](01-lab1.md), running Bronze, Silver and both Gold writes.
2. Complete Lab 2 Tasks 1–11.
3. Complete Lab 2 after Task 11 stages the PDFs. No KB, quality/freshness or readiness tasks are required.
4. Optionally use the separate [workflow execution guide](workflow.md) to automate the four notebooks. It is not a Lab 2 task.

## Optional: recreate the environment for a new learner

This is not necessary to repeat the labs. Reuse the prepared environment and follow [rerun guidance for Lab 1 and Lab 2](reruns.md); do not delete existing experiments or model versions first.

Skip this section in the prepared workspace. Use unique instructor-approved names; do not overwrite the existing catalog.

1. In **Master catalog**, choose **Create catalog**, select a standard catalog, and create your learner catalog.
2. Open it and use **Create schema** for the Bronze, Silver and Gold schema names above.
3. Within Bronze, use **Add to schema** to create a managed volume named `source_files`. In Gold, create a managed volume named `workshop_outputs`.
4. In **Workspaces**, create a workspace and select your new standard catalog as its default catalog.
5. Select that workspace, open **Compute**, and create a Spark cluster using the sizing and idle timeout in Task 4. Record the new cluster key rather than reusing the prepared key.
6. Upload/import the data and code using Tasks 2–3. Update `config/workshop.json` and the cluster environment variable `SEER_LAB_HOME` if your package root differs.
7. Create the four-task job using the [workflow guide](workflow.md), with your notebook paths and cluster.
8. Repeat all setup checkpoints before running Lab 1. Ask an administrator for missing privileges; do not grant broad access as a shortcut.

For UI variations, consult Oracle's [notebook guide](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/notebooks.html), [volume guide](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/volumes.html), and [AI prerequisites](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/get-started-oracle-ai-data-platform.html).

## Troubleshooting and completion

| Symptom | Check and next action |
| --- | --- |
| Cluster not listed in attachment menu | Select the dedicated workspace; inspect Compute and permissions. |
| `ModuleNotFoundError: seer_runtime` | Reopen the updated notebook: neither current lab imports workshop libraries. Configuration/reference files are still required. |
| Missing MLflow/scikit-learn/pandas/NumPy | Complete the runtime check; use approved cluster libraries. Preserve AIDP's integrated MLflow; do not replace it with a local file tracker. |
| File not found under `/Volumes` | Compare catalog/schema/volume, flat filename and source layout. |
| Tables not visible | Finish the producing cell, then refresh the schema's Tables listing. |
| Permission denied | Request the specific missing read/write/use privilege; don't switch to unrelated privileged resources. |
| AI features unavailable | Complete the data/ML path and record KB/agent steps as not performed. |

You are ready for [Lab 1](01-lab1.md) when all four notebooks, all support files, eight source files, three schemas and the dedicated runtime are accessible. Review the [workshop checkpoints](learner-evidence.md).

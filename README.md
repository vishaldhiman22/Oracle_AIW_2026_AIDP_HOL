# Oracle AI World 2026: AIDP Hands-on Labs

Build a construction-project lakehouse, then train and use a milestone-delay classifier with Oracle AI Data Platform (AIDP) and MLflow.

This README is the single learner guide. Detailed explanations and task instructions are also embedded in the four notebooks. No separate `docs/`, `tools/`, or support Python library is required.

## Contents

- [What you will build](#what-you-will-build)
- [Get the files](#get-the-files)
- [Prepare your AIDP environment](#prepare-your-aidp-environment)
- [Lab 1: Bronze, Silver and Gold](#lab-1-bronze-silver-and-gold)
- [Lab 2: MLflow model lifecycle](#lab-2-mlflow-model-lifecycle)
- [Reruns and recovery](#reruns-and-recovery)
- [Optional workflow](#optional-workflow)
- [Troubleshooting](#troubleshooting)
- [Attribution](#attribution)

## What you will build

Run the notebooks in this order:

| Notebook | Purpose | Output |
| --- | --- | --- |
| [Lab 1A: Bronze ingestion](aidp-livelabs/notebooks/Lab1A_Bronze_Ingestion.ipynb) | Import five source CSVs | Five Bronze Delta tables |
| [Lab 1B: Silver transformations](aidp-livelabs/notebooks/Lab1B_Silver_Transformations.ipynb) | Standardize suppliers and reconcile project data | Five Silver Delta tables |
| [Lab 1C: Gold project data](aidp-livelabs/notebooks/Lab1C_Gold_Project_Data.ipynb) | Build project context with Spark SQL and milestone features with PySpark | Two Gold Delta tables |
| [Lab 2: MLflow lifecycle](aidp-livelabs/notebooks/Lab2_Predict_Investigate_and_Operationalize.ipynb) | Train six candidates, compare, register, reload, score and stage PDFs | One experiment, model versions, one predictions table and staged PDFs |

Lab 1 takes approximately 45–60 minutes and Lab 2 approximately 60–90 minutes, excluding provisioning and compute startup.

**Use a dedicated learning environment. Lab 1 drops and recreates its 12 named tables without backups.** Do not point the notebooks at production tables or run concurrent writers.

The source files are teaching fixtures. Lab 2 generates synthetic labeled history for training; it does not train on the PDFs or the three current Gold rows. Metrics and predictions are educational, not production forecasts.

## Get the files

```bash
git clone https://github.com/vishaldhiman22/Oracle_AIW_2026_AIDP_HOL.git
cd Oracle_AIW_2026_AIDP_HOL
```

Alternatively, use GitHub's **Code → Download ZIP** and extract it.

### Included source inputs

All eight files below are at the repository root. No separate bucket download is required. Keep their filenames unchanged when uploading.

| Input | Purpose |
| --- | --- |
| [Supplier extract](source-data_suppliers_supplier_extract.csv) | Supplier standardization and reconciliation |
| [Financial assets](source-data_assets_financial_assets.csv) | Asset and project context |
| [Purchase orders](source-data_purchasing_purchase_orders.csv) | Procurement status and committed costs |
| [Project milestones](source-data_schedules_project_milestones.csv) | Milestone dates and status |
| [Inspection findings](source-data_inspections_inspection_findings.csv) | Inspection context |
| [Supplier framework agreement](documents_atlas_supplier_framework_agreement.pdf) | Project document staged in Lab 2 Task 11 |
| [Austin receiving inspection report](documents_austin_receiving_inspection_report.pdf) | Project document staged in Lab 2 Task 11 |
| [Austin structural specification](documents_austin_structural_engineering_specification.pdf) | Project document staged in Lab 2 Task 11 |

The CSVs contain 23 data rows in total; the three PDFs contain five pages in total.

### Required workspace files

Only six files are needed in the AIDP workspace: the four notebooks and these two support files:

- [config/workshop.json](aidp-livelabs/config/workshop.json): configuration read by every notebook.
- [reference/pdf-manifest.json](aidp-livelabs/reference/pdf-manifest.json): PDF names and hashes read only by Lab 2 Task 11.

The CSV/PDF inputs belong in a **volume**, not in the notebook folder. The optional [workflow template](aidp-livelabs/workflows/seer-labs.template.json) is not a notebook runtime dependency.

## Prepare your AIDP environment

### 1. Confirm access and create dedicated resources

Sign in to your authorized AIDP workbench. You need permission to use a workspace and Spark cluster, create/read/write the lab schemas and volumes, use experiments, and register model versions.

Use the following example names or update them consistently in the notebook setup cells and `config/workshop.json`:

| Resource | Example name |
| --- | --- |
| Catalog | `seer_livelabs_20260922` |
| Workspace | `seer_livelabs_20260922` |
| Spark cluster | `seer_livelabs_spark` |
| Schemas | `seer_bronze`, `seer_silver`, `seer_gold` |
| Source volume | `seer_livelabs_20260922.seer_bronze.source_files` |
| Output volume | `seer_livelabs_20260922.seer_gold.workshop_outputs` |

In **Master catalog**, create the dedicated catalog and the Bronze/Gold schemas needed for the volumes. Create managed volumes named **source_files** under Bronze and **workshop_outputs** under Gold. Each Lab 1 notebook also runs `CREATE SCHEMA IF NOT EXISTS` for its target schema.

All layers remain in this standard catalog. No external database or vector catalog is required. This repository supplies no live workbench OCID, credentials, cluster key or other connection details.

Create the workspace and Spark cluster. The prepared workshop used Spark 3.5.0 on AMD compute, with a 2-OCPU/16-GB driver, one 2-OCPU/16-GB worker, and a 30-minute idle timeout. Use a compatible administrator-approved runtime; compute incurs charges.

### 2. Upload the source data

1. Open **Master catalog → your catalog → seer_bronze → Volumes → source_files**.
2. Use the volume's upload action to upload all five CSVs and three PDFs at the volume root. Do not rename them or add a second nesting folder.
3. Confirm there are eight files.
4. In `config/workshop.json`, confirm `source_layout` is `flat` and the paths match your volumes:
   - `source_root`: `/Volumes/seer_livelabs_20260922/seer_bronze/source_files`
   - `output_root`: `/Volumes/seer_livelabs_20260922/seer_gold/workshop_outputs`

Keep the supplied historical `fixture_as_of` date for reproducible results. Do not substitute today's date merely to make source data look fresh.

### 3. Import the notebooks and support files

In your workspace, create this folder structure:

```text
/Workspace/Shared/seer-aidp-livelabs/
  config/
    workshop.json
  reference/
    pdf-manifest.json
  notebooks/
    Lab1A_Bronze_Ingestion.ipynb
    Lab1B_Silver_Transformations.ipynb
    Lab1C_Gold_Project_Data.ipynb
    Lab2_Predict_Investigate_and_Operationalize.ipynb
```

Upload the two JSON files as ordinary workspace files. Import the four IPYNB files as **notebooks**, not text files. Each must open with separate Markdown and Python cells.

Keep the default workspace path unless you also change every affected notebook setup path and workflow parameter. The native workspace metadata may omit the leading slash; Python filesystem reads use `/Workspace/...`.

### 4. Attach compute

1. Open each notebook and choose **Cluster → Attach existing cluster**.
2. Select your dedicated Spark cluster and wait for it to be ready.
3. Confirm Spark is available and MLflow, scikit-learn, pandas and NumPy import successfully.
4. Keep AIDP's platform-provided MLflow integration and authentication. Do not replace it with a separately installed MLflow package or point tracking at a local folder.

No ONNX model, XGBoost package, GPU, workspace `lib/`, or learner `requirements.txt` is required. If libraries are missing, use your administrator-approved runtime/library process.

## Lab 1: Bronze, Silver and Gold

Run each notebook's setup first, then its remaining cells in order. Task numbers are Markdown headings, not execution-counter numbers.

### Lab 1A: Load Bronze

Open the Bronze notebook and run its seven code cells: setup, five imports, and a final table-count display.

Each import reads one CSV with headers, keeps source fields as strings, recreates its named Delta table, and displays the first five rows. The source file is unchanged.

| Feed | Bronze table | Expected rows |
| --- | --- | --- |
| Suppliers | `suppliers_raw` | 8 |
| Assets | `assets_raw` | 3 |
| Purchase orders | `purchasing_raw` | 4 |
| Milestones | `schedules_raw` | 4 |
| Inspections | `inspections_raw` | 4 |

Run the last cell to see the Bronze table names and counts. Refresh the catalog and confirm five tables containing 23 rows in total.

### Lab 1B: Transform Silver

Run setup and the five commented transformation tasks, followed by the table-count cell:

| Task | Silver table | Transformation |
| --- | --- | --- |
| Suppliers | `suppliers` | Standardize names, qualifications, certifications and locations; group duplicates, assign stable IDs, and retain source records/conflicts |
| Assets | `assets` | Apply the fixture's one-asset-per-project mapping and join project names |
| Purchase orders | `purchase_orders` | Resolve asset/supplier references, retain unmatched suppliers, normalize status and convert currency to integer USD cents |
| Inspections | `inspections` | Join project/asset identifiers and normalize inspection status |
| Milestones | `milestones` | Join project/asset identifiers and normalize status while retaining source dates |

Expected counts are six suppliers, three assets, four purchase orders, four inspections and four milestones. Inspections and milestones also display their first five rows. The final cell lists every Silver table and its count.

Each transformation writes one table in one step. There is no separate Silver validation, quarantine, or summary-table task. Known source issues remain visible rather than being silently corrected.

### Lab 1C: Build Gold

Run the three code cells:

1. **Setup:** read configuration and create the Gold schema if absent.
2. **Build project context:** use `spark.sql()` with CTEs to aggregate purchase orders, supplier status and inspections before joining to assets and milestones. Preaggregation avoids multiplying costs.
3. **Build milestone features:** use PySpark DataFrame functions to select unfinished milestones due 1–30 days after the fixture date and compute nine numeric model inputs.

Browse `seer_gold.project_context` and `seer_gold.milestone_features`; each should contain three rows. The supplied fixture has Austin committed cost of 167,390,000 cents and total committed cost of 473,090,000 cents.

Gold remains in the same catalog. Source extraction dates and notebook refresh timestamps represent different things.

### Inspect lineage

Refresh the catalog, open `milestone_features`, and choose **Actions → Lineage (Preview)**. Trace Gold inputs through Silver to Bronze. Task/process nodes between tables are expected. Inspect the actual graph after execution; successful table writes alone do not prove lineage capture.

At the end of Lab 1, there are five Bronze, five Silver and two Gold tables.

## Lab 2: MLflow model lifecycle

Complete Lab 1 first. Open the Lab 2 notebook, attach the same cluster, and run its 11 tasks in order. For your first walkthrough, **run one cell at a time** and pause after Task 6; **Run all** does not pause for the first-round comparison.

| Task | Action | What to inspect |
| --- | --- | --- |
| 1 | Create or reuse `seer_milestone_delay` | Experiment ID, new comparison `SESSION_ID`, library versions |
| 2 | Generate 1,800 labeled synthetic examples | Sample milestone IDs, dates and `late_flag`; no PDFs are used for training |
| 3 | Make chronological train/validation/test splits | 1,140 training, 391 validation, 183 test and 86 excluded rows |
| 4 | Define explicit MLflow run logging | Parameters, metrics, model signature and probability-prediction interface |
| 5 | Train three Gradient Boosting candidates | Three distinct run IDs and validation metrics |
| 6 | Compare round one | Exactly three rows in the notebook's session-filtered comparison |
| 7 | Train three Decision Tree candidates | Three more runs in the same experiment and session |
| 8 | Compare all six and select the winner | Rank by validation average precision, then Brier score and run ID; evaluate only the winner on the held-out test set |
| 9 | Register the selected artifact | Fully qualified catalog model name, returned version and originating run |
| 10 | Reload that registered version and score Gold | Three persisted predictions and their model/run identifiers |
| 11 | Stage the three project PDFs | Verified files under the output volume's `austin-project` folder |

### Inspect experiments and models

- Open **Experiments → seer_milestone_delay**. Inspect run parameters, metrics and artifacts; use **Compare** for charts.
- On repeat exercises, the UI can show old runs with the same names. Use run IDs and the notebook's session-filtered comparison to identify this walkthrough.
- Register once in Task 9. Do not also register through the UI unless you intentionally want another model version.
- Open **Master catalog → your catalog → seer_gold → Models → milestone_delay_classifier**. Inspect **Versions** and follow the source-run link.
- Task 10 reloads `models:/<catalog>.seer_gold.milestone_delay_classifier/<version>`, not an unversioned “latest” model. An MLflow Spark UDF scores the saved Gold features.
- Inspect `seer_gold.milestone_delay_predictions`: three rows with `delay_probability`, `predicted_late`, `risk_band`, `model_name`, `model_version`, `model_run_id`, source `run_id` and `scoring_run_id`.
- Task 10 compares persisted probabilities with predictions from the loaded model. A successful comparison verifies that read-back check, not production accuracy.

The probability threshold is 0.5. Risk bands are workshop conventions: LOW below 0.4, MEDIUM from 0.4 to below 0.7, and HIGH at or above 0.7. Model artifacts belong to MLflow/catalog storage, not extra Gold Delta tables.

### PDF staging and completion

Task 11 reads `reference/pdf-manifest.json`, verifies the source PDF hashes and copies missing files to:

```text
/Volumes/seer_livelabs_20260922/seer_gold/workshop_outputs/austin-project
```

Identical existing PDFs are reused. Differing bytes or unexpected destination files stop the cell for review.

**Lab 2 ends at Task 11.** Staging PDFs does not create a knowledge base or train the classifier on documents. Knowledge-base ingestion, agent testing, quality/freshness review and readiness assessment are not required lab tasks.

Completion means six candidate runs in one experiment, a registered winner, three predictions scored using its explicit registered version, and three staged PDFs. The Gold schema now has three tables: `project_context`, `milestone_features` and `milestone_delay_predictions`.

## Reruns and recovery

**Do not delete experiments, runs, model versions, source files or schemas before an ordinary rerun.**

| What you rerun | Effect |
| --- | --- |
| Lab 1A | Recreates its five named Bronze tables without backups |
| Lab 1B | Recreates its five named Silver tables without backups |
| Lab 1C | Recreates `project_context` and `milestone_features` without backups |
| Full Lab 2, beginning at Task 1 | Starts a new comparison session, retains history, adds six runs and a model version, overwrites predictions, and stages PDFs |
| Lab 2 Task 10 only | Reloads the selected registered version and overwrites predictions, without training or registration |
| Lab 2 Task 11 only | Reuses identical PDFs and copies missing files |
| Full workflow | Repeats all three Lab 1 notebooks, then Lab 2 |

Lab 1's drops discard target-table history and table-specific metadata. A failure between drop and write can leave a table absent; the multi-table rebuild is not atomic. Source files, volumes, models and unrelated tables are not reset.

### Where to restart

- Source CSVs or Bronze changed: **Lab 1A → Lab 1B → Lab 1C → Lab 2**.
- Silver transformation changed and Bronze is current: **Lab 1B → Lab 1C → Lab 2**.
- Gold transformation changed and Silver is current: **Lab 1C → Lab 2**.
- Lab 2 only: run from Task 1; Lab 1 tables are read, not reset.

Always start the chosen notebook with its setup and run subsequent cells in order. Upstream changes do not automatically refresh downstream data or predictions.

### Training or registration fails

Run Task 1 once per walkthrough and each training round once. Do not rerun Task 1 between rounds. Repeating a partially successful Task 5 or 7 in the same session can add extra candidates and fail the six-run check. Fix the cause and restart a complete walkthrough at Task 1; retain previous runs for troubleshooting.

Before retrying Task 9, inspect the model's **Versions** list: registration may already have succeeded. Every additional registration creates another version.

Task 10 alone works only in the **same active notebook session** with variables such as `REGISTERED_URI`, `MODEL_NAME`, `MODEL_VERSION` and `best_run_id` available. It is not a standalone fresh-session inference script. If the session is lost, follow a full walkthrough or obtain a separate inference setup with an explicit model version and source run; do not guess them.

Run only one notebook/workflow writer at a time. Retained artifacts consume storage; cleanup is optional housekeeping, not a prerequisite. Keep model versions and source runs needed for traceability.

## Optional workflow

After completing the interactive labs, optionally automate the four notebooks in **Workflow → Jobs**:

1. Create a job named `seer_aidp_labs` in your workspace.
2. Add four **Notebook task** entries using **Workspace** source and the same Spark cluster:

| Task key | Notebook | Depends on |
| --- | --- | --- |
| `lab1_bronze` | Lab 1A | None |
| `lab1_silver` | Lab 1B | `lab1_bronze` |
| `lab1_gold` | Lab 1C | `lab1_silver` |
| `lab2_predict_and_assess` | Lab 2 | `lab1_gold` |

3. Use **All success** dependency conditions, **Max concurrent runs = 1**, no schedule, and a 90-minute job timeout.
4. Set each Lab 1 task timeout to 30 minutes and Lab 2 to 60 minutes. Keep Lab 2 automatic retries disabled.
5. Pass `run_id = {{job.run_id}}` to all tasks. Set job parameter `config_path` to `/Workspace/Shared/seer-aidp-livelabs/config/workshop.json`.
6. Save, reopen and verify every notebook path, parameter and dependency.
7. Stop interactive writers, choose **Run now** once, and inspect each task's output. All four tasks must reach **Success**.
8. Verify table counts, model registration, predictions and actual lineage in your environment.

Workflow concurrency does not block simultaneous interactive notebook writes. A complete workflow run repeats the Lab 1 resets and Lab 2 training/registration; it is not equivalent to scoring only. It does not pause for comparisons or ingest a knowledge base.

For API-based job creation, the optional [workflow template](aidp-livelabs/workflows/seer-labs.template.json) contains the same task configuration. Replace `__CLUSTER_KEY__`, `__CLUSTER_NAME__`, `__WORKSPACE_FOLDER__` and `__CONFIG_PATH__` with your values before submitting it through your approved AIDP tooling. Editing the file does not create or execute a job.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Notebook opens as raw JSON or one text cell | Import the IPYNB as a notebook, not a plain file |
| Missing `spark` or no attached cluster | Select the correct workspace, attach the cluster and wait for readiness |
| Missing configuration or PDF manifest | Verify the six required workspace files and exact folder paths |
| Source file not found | Verify volume permissions, the eight filenames and `source_layout = flat` |
| Gold tables missing | Finish Lab 1A, 1B and 1C in order in the same catalog |
| Missing MLflow/scikit-learn | Use the approved runtime; do not replace AIDP's integrated MLflow |
| Comparison empty or not exactly six candidates | Check run status and session ID; restart a full walkthrough after a partial/repeated training round |
| More runs visible in the UI | Historical runs are retained; compare current run IDs/session tags |
| Model version is not 1 | Expected on a rerun; use the actual version returned by Task 9 |
| Permission denied | Request the specific missing permission; do not switch catalogs to bypass controls |
| Lineage loading or unexpected relationships | Refresh and inspect the current table after successful execution; do not assume an earlier graph validates the latest run |

Stop compute when finished, or rely on the configured idle timeout according to your organization's cost policy. Do not delete shared catalogs or source volumes as a reset shortcut.

## Attribution

Adapted from Oracle LiveLabs material by Eli Schilling and the LiveLabs/ONA Lab Experience teams: [original Lab 1](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=1-unified-lakehouse-foundation), [original Lab 2](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=2-unify-data-for-ai), and [original Lab 3](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=3-trusted-data-products).

This independently maintained repository is not an Oracle-published replacement. It excludes credentials, private deployment receipts, executed notebooks, logs and screenshots containing account details.

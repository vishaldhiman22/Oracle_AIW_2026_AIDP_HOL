# Oracle AI World 2026: AIDP Hands-on Labs

Build a construction-project lakehouse, then train and use a milestone-delay classifier with Oracle AI Data Platform (AIDP) and MLflow.

Notebook source was synchronized from the workbench on **September 30, 2026**. This is a source export, not a new successful execution claim.

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
| [Lab 1C: Gold project data](aidp-livelabs/notebooks/Lab1C_Gold_Project_Data.ipynb) | Build project context, features, known outcomes and training rows | Four Gold Delta tables |
| [Lab 2: MLflow lifecycle](aidp-livelabs/notebooks/Lab2_Predict_Investigate_and_Operationalize.ipynb) | Train six candidates, compare, register, reload and score | One experiment, model versions and displayed predictions |

Lab 1 takes approximately 45–60 minutes and Lab 2 approximately 60–90 minutes, excluding provisioning and compute startup.

**Use a dedicated learning environment. Lab 1 drops and recreates its 14 named tables without backups.** Do not point the notebooks at production tables or run concurrent writers.

The source files are teaching fixtures. Lab 2 now trains from `seer_gold.milestone_training`, not generated synthetic history or PDFs. Gold training combines status-derived proxy labels with available completion outcomes. Metrics and predictions demonstrate MLflow functionality, not validated delay forecasting.

## Get the files

```bash
git clone https://github.com/vishaldhiman22/Oracle_AIW_2026_AIDP_HOL.git
cd Oracle_AIW_2026_AIDP_HOL
```

Alternatively, use GitHub's **Code → Download ZIP** and extract it.

### Included source inputs

All five CSV inputs are in the [`data/`](data/) folder. No separate bucket download is required. Keep their filenames unchanged when uploading.

| Input | Purpose |
| --- | --- |
| [Supplier extract](data/source-data_suppliers_supplier_extract.csv) | Supplier standardization and reconciliation |
| [Financial assets](data/source-data_assets_financial_assets.csv) | Asset and project context |
| [Purchase orders](data/source-data_purchasing_purchase_orders.csv) | Procurement status and committed costs |
| [Project milestones](data/source-data_schedules_project_milestones.csv) | Milestone dates and status |
| [Inspection findings](data/source-data_inspections_inspection_findings.csv) | Inspection context |

The CSVs contain 23 data rows in total.

### Required workspace files

Only five files are required in the AIDP workspace: the four notebooks and [config/workshop.json](aidp-livelabs/config/workshop.json), read by every notebook.

The CSV inputs belong in a **volume**, not in the notebook folder. The notebooks do not require PDFs, a reference folder or a workflow template.

## Prepare your AIDP environment

### 1. Confirm access and create dedicated resources

Sign in to your authorized AIDP workbench. You need permission to use a workspace and Spark cluster, create/read/write the lab schemas and volumes, use experiments, and register model versions.

Use the following example names or update them consistently in the notebook setup cells and `config/workshop.json`:

| Resource | Example name |
| --- | --- |
| Catalog | `seer_livelabs` |
| Workspace | `seer_livelabs` |
| Spark cluster | `seer_livelabs_spark` |
| Schemas | `seer_bronze`, `seer_silver`, `seer_gold` |
| Source volume | `seer_livelabs.seer_bronze.source_files` |
| Optional document volume | `seer_livelabs.seer_gold.workshop_outputs` |

In **Master catalog**, create the dedicated catalog and Bronze schema, then create a managed volume named **source_files** under Bronze. The Gold `workshop_outputs` volume is only needed if you separately use the optional document assets. Each Lab 1 notebook runs `CREATE SCHEMA IF NOT EXISTS` for its target schema.

All layers remain in this standard catalog. No external database or vector catalog is required. This repository supplies no live workbench OCID, credentials, cluster key or other connection details.

Create the workspace and Spark cluster. The prepared workshop used Spark 3.5.0 on AMD compute, with a 2-OCPU/16-GB driver, one 2-OCPU/16-GB worker, and a 30-minute idle timeout. Use a compatible administrator-approved runtime; compute incurs charges.

### 2. Upload the source data

1. Open **Master catalog → your catalog → seer_bronze → Volumes → source_files**.
2. Upload the five CSV files from the repository's `data/` folder directly to the volume root. Do not upload the `data` folder itself, rename files, or add a second nesting folder.
3. Confirm all five CSV filenames match the repository.
4. In `config/workshop.json`, confirm `source_layout` is `flat` and the paths match your volumes:
   - `source_root`: `/Volumes/seer_livelabs/seer_bronze/source_files`
   - `output_root`: `/Volumes/seer_livelabs/seer_gold/workshop_outputs`

Keep the supplied historical `fixture_as_of` date for reproducible results. Do not substitute today's date merely to make source data look fresh.

### 3. Import the notebooks and support files

In your workspace, create this folder structure:

```text
/Workspace/Shared/seer-aidp-livelabs/
  config/
    workshop.json
  notebooks/
    Lab1A_Bronze_Ingestion.ipynb
    Lab1B_Silver_Transformations.ipynb
    Lab1C_Gold_Project_Data.ipynb
    Lab2_Predict_Investigate_and_Operationalize.ipynb
```

Upload `config/workshop.json` as an ordinary workspace file. Import the four IPYNB files as **notebooks**, not text files. Each must open with separate Markdown and Python cells.

Keep the default workspace path unless you also change every affected notebook setup path and workflow parameter. The native workspace metadata may omit the leading slash; Python filesystem reads use `/Workspace/...`.

All four notebooks accept an optional `config_path` workflow parameter. Use it to test a separate configuration without overwriting the shared `config/workshop.json`. Interactive runs use the default workspace path above.

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
| Milestones | `milestones` | Join identifiers, normalize status, cast planned/actual dates and derive `late_flag` only for completed work |

Expected counts are six suppliers, three assets, four purchase orders, four inspections and four milestones. Inspections display sample rows; milestones display activity IDs, planned/actual dates, status and `late_flag`. The final cell lists every Silver table and its count.

Each transformation writes one table in one step. There is no separate Silver validation, quarantine, or summary-table task. Known source issues remain visible rather than being silently corrected.

### Lab 1C: Build Gold

Run the five code cells in order:

1. **Setup:** read configuration and create the Gold schema if absent.
2. **Task 1 — Build project context:** use Spark SQL CTEs to aggregate purchase orders, supplier status and inspections before joining. Preaggregation avoids multiplying costs.
3. **Task 2 — Build milestone features:** select unfinished milestones due 1–30 days after the fixture date and compute nine numeric inputs.
4. **Task 3 — Publish known milestone outcomes:** save completed milestones with known `late_flag` values in `milestone_outcomes`. Unknown outcomes are excluded.
5. **Task 4 — Build milestone training data:** create `milestone_training` from feature rows, status-derived proxy labels, and completion-outcome rows joined by project and asset.

Each write drops and recreates its target: `project_context`, `milestone_features`, `milestone_outcomes` or `milestone_training`.

The supplied fixture has three current feature milestones and one known completed milestone. The context has Austin committed cost of 167,390,000 cents and total cost of 473,090,000 cents. Verify actual outputs in your environment; this synchronization did not execute Spark.

**Training-data limitation:** the proxy target is copied from `milestone_at_risk_flag`, which is also an input feature. Completion outcomes are joined by project/asset rather than by an identical historical milestone snapshot. This is a small lifecycle demonstration with target leakage and temporal-alignment limitations, not a valid predictive evaluation.

Some workbench Markdown still describes the earlier two-table Gold version; the current code writes four Gold tables. Exported code is preserved as authored.

### Inspect lineage

Refresh the catalog, open `milestone_features`, and choose **Actions → Lineage (Preview)**. Trace Gold inputs through Silver to Bronze. Task/process nodes between tables are expected. Inspect the actual graph after execution; successful table writes alone do not prove lineage capture.

At the end of Lab 1, the current code creates five Bronze, five Silver and four Gold tables.

## Lab 2: MLflow model lifecycle

Complete Lab 1, including its Gold training-table task. Open Lab 2, attach the cluster and run its **10 Python tasks** in order. Run one cell at a time and pause after Task 6 to compare the first model family.

| Task | Action | What to inspect |
| --- | --- | --- |
| 1 | Create or reuse `seer_milestone_delay` | Experiment and new comparison `SESSION_ID` |
| 2 | Load Gold training data | Read `milestone_training` into pandas; inspect row/class counts |
| 3 | Split training and validation | 50/50 stratified split with `random_state=42`; every candidate uses the same split |
| 4 | Define MLflow helpers | Run tags, parameters, validation metrics and artifacts |
| 5 | Train three Decision Trees | Runs `dt_r1_1` to `dt_r1_3` |
| 6 | Compare round one | Inspect three finished runs in the notebook and Experiments UI |
| 7 | Train three Gradient Boosting models | Runs `gb_r2_1` to `gb_r2_3` in the same experiment/session |
| 8 | Compare and select | Highest validation F1, then lowest Brier score, then run name |
| 9 | Register the selected model | Catalog model `<catalog>.seer_gold.milestone_delay_classifier` and explicit version |
| 10 | Reload and score | Load that version, score `milestone_features` and display predictions |

There is no synthetic-data generator, held-out test partition, PDF-staging task or persisted prediction-table write in this version.

### Compare, register and score

1. Open **Experiments → seer_milestone_delay**. Inspect run parameters, metrics and artifacts. Use **Compare** to view F1 and Brier score.
2. Identify this walkthrough by its session tag/run IDs. Historical runs remain visible.
3. Use Task 8's ranking to select the winner. The helper includes finished runs for the current session; the former exact-six-run guard is absent, so run both rounds once and verify the intended six candidates yourself.
4. For an uninterrupted notebook walkthrough, run Task 9's registration cell once. It defines `MODEL_VERSION` and `REGISTERED_URI` for Task 10.
5. The workbench instructions also allow **Experiments → selected run → Register**. If choosing this UI-only route, Task 10 still needs those variables set to the actual registered version. The current notebook does not resolve UI registration automatically. Do not use both routes unless you intend another version.
6. Browse **Master catalog → your catalog → seer_gold → Models → milestone_delay_classifier → Versions** and follow the source-run link.
7. Task 10 loads `models:/<catalog>.seer_gold.milestone_delay_classifier/<version>` and uses an MLflow Spark UDF to display milestone ID, project/milestone names, planned date, delay probability, predicted class and model version.

The threshold is 0.5. Task 10 displays scores only: it does not save a Delta predictions table, create risk bands or perform the old persisted-score read-back check. A `milestone_delay_predictions` table left from an earlier version is not refreshed by this code.

### Data prerequisites and limitations

The stratified split needs enough examples of each class in both partitions; ROC AUC needs both classes in validation. The entire Gold training table is collected to pandas on the driver, so use a bounded teaching dataset.

The tiny fixture, status-derived labels and absence of an independent test set cannot support meaningful real-world accuracy claims. Use sufficient independent historical snapshots with trustworthy outcomes for real predictive modeling.

**Lab 2 ends at Task 10.** PDFs, their manifest, a document output volume, knowledge-base ingestion and agent testing are not required by the current Lab 2.

## Reruns and recovery

**Do not delete experiments, runs, model versions, source files or schemas before an ordinary rerun.**

| What you rerun | Effect |
| --- | --- |
| Lab 1A | Recreates its five named Bronze tables without backups |
| Lab 1B | Recreates its five named Silver tables without backups |
| Lab 1C | Recreates context, features, outcomes and training tables without backups |
| Full Lab 2, beginning at Task 1 | Starts a new session, retains history, adds six runs and a model version, and displays scores |
| Lab 2 Task 10 only | Reloads the selected version and displays scores without training, registration or table writes |
| Full workflow | Repeats all three Lab 1 notebooks, then Lab 2 |

Lab 1's drops discard target-table history and table-specific metadata. A failure between drop and write can leave a table absent; the multi-table rebuild is not atomic. Source files, volumes, models and unrelated tables are not reset.

### Where to restart

- Source CSVs or Bronze changed: **Lab 1A → Lab 1B → Lab 1C → Lab 2**.
- Silver transformation changed and Bronze is current: **Lab 1B → Lab 1C → Lab 2**.
- Gold transformation changed and Silver is current: **Lab 1C → Lab 2**.
- Lab 2 only: run from Task 1; Lab 1 tables are read, not reset.

Always start the chosen notebook with its setup and run subsequent cells in order. Upstream changes do not automatically refresh downstream tables. Rerun scoring to display updated scores; legacy prediction tables are not updated by current Lab 2.

### Training or registration fails

Run Task 1 once per walkthrough and each training round once. Do not rerun Task 1 between rounds. Repeating a partially successful Task 5 or 7 can add extra candidates to the comparison; there is no exact-six-run guard in this version. Fix the cause and restart a complete walkthrough at Task 1; retain previous runs for troubleshooting.

Before retrying Task 9, inspect the model's **Versions** list: registration may already have succeeded. Every additional registration creates another version.

Task 10 alone works only in the **same active notebook session** with variables such as `REGISTERED_URI`, `MODEL_VERSION`, `SCORING_TABLE`, `FEATURES` and `threshold` available. It is not a standalone fresh-session inference script. If the session is lost, follow a full walkthrough or obtain a separate inference setup with an explicit model version and source run; do not guess them.

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

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Notebook opens as raw JSON or one text cell | Import the IPYNB as a notebook, not a plain file |
| Missing `spark` or no attached cluster | Select the correct workspace, attach the cluster and wait for readiness |
| Missing configuration | Verify the five required workspace files and exact paths |
| Source file not found | Verify volume permissions, the five CSV filenames and `source_layout = flat` |
| Gold training table missing | Complete Lab 1C through Task 4 in the same catalog |
| Missing MLflow/scikit-learn | Use the approved runtime; do not replace AIDP's integrated MLflow |
| Comparison empty or has extra candidates | Check run status and session ID; restart after a partial/repeated round |
| Stratified split or ROC AUC fails | Inspect class counts and ensure both partitions have both classes |
| `REGISTERED_URI` missing after UI registration | Define the exact registered URI/version for Task 10; do not register twice |
| More runs visible in the UI | Historical runs are retained; compare current run IDs/session tags |
| Model version is not 1 | Expected on a rerun; use the actual version returned by Task 9 |
| Permission denied | Request the specific missing permission; do not switch catalogs to bypass controls |
| Lineage loading or unexpected relationships | Refresh and inspect the current table after successful execution; do not assume an earlier graph validates the latest run |

Stop compute when finished, or rely on the configured idle timeout according to your organization's cost policy. Do not delete shared catalogs or source volumes as a reset shortcut.

## Attribution

Adapted from Oracle LiveLabs material by Eli Schilling and the LiveLabs/ONA Lab Experience teams: [original Lab 1](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=1-unified-lakehouse-foundation), [original Lab 2](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=2-unify-data-for-ai), and [original Lab 3](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=3-trusted-data-products).

This independently maintained repository is not an Oracle-published replacement. It excludes credentials, private deployment receipts, executed notebooks, logs and screenshots containing account details.

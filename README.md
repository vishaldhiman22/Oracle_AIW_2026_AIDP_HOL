# Oracle AI World 2026 AIDP Hands-on Lab

Build a Bronze–Silver–Gold lakehouse, then train, compare, register and reload a milestone-delay model using AIDP and MLflow. Follow the numbered steps below. Run Python cells individually, in notebook order.

**Before you begin:** your instructor must provide access to an AIDP workbench, a workspace (example: `HOL_Workspace`), a compatible Spark cluster, and permission to create lab schemas/tables and register models in the `default` catalog. Do not use production tables. Different workspaces in the same instance can share catalog tables: use instructor-assigned schema names if multiple learners share the same catalog.

**Credential safety:** this public repository never contains a personal access token (PAT). Obtain an authorized, short-lived credential privately from your instructor, or use your own account and token. Never paste tokens into notebooks, JSON, screenshots or Git commits. Revoke any token accidentally shared publicly.

## Lab sequence

| Notebook | Code cells | Result |
| --- | ---: | --- |
| [Lab 1A](aidp-livelabs/notebooks/Lab1A_Bronze_Ingestion.ipynb) | 7 | Five Bronze Delta tables |
| [Lab 1B](aidp-livelabs/notebooks/Lab1B_Silver_Transformations.ipynb) | 7 | Five Silver Delta tables |
| [Lab 1C](aidp-livelabs/notebooks/Lab1C_Gold_Project_Data.ipynb) | 5 | Four Gold Delta tables |
| [Lab 2](aidp-livelabs/notebooks/Lab2_Predict_Investigate_and_Operationalize.ipynb) | 10 | Six MLflow runs, a registered model version, displayed predictions |

Allow approximately 45–60 minutes for Lab 1 and 60–90 minutes for Lab 2, plus compute startup. All CSVs are included. No bucket download, volume upload, PDFs, support library, or requirements file is needed.

## Step 1 Download everything from GitHub

Open [the public workshop repository](https://github.com/vishaldhiman22/Oracle_AIW_2026_AIDP_HOL). Select branch **main**, click the green **Code** button, then **Download ZIP**. Extract the downloaded archive on your computer. It contains all four notebooks, the configuration, five CSVs, and this guide.

Keep the extracted files for reference. **Do not upload the ZIP to AIDP or run notebooks from your laptop.** In Steps 4–5, AIDP will fetch the same repository into a Git folder for execution. A ZIP download and an AIDP Git clone are separate copies.

## Step 2 Open Git credential settings

Sign in to the workbench URL supplied by your instructor. In the left navigation, click **Settings**, then **Git linked accounts**, then **Add credential**. This is the Git-linked account setting, not the general **Credential store**.

## Step 3 Add the GitHub credential

Fill the dialog using the table below, then click **Add**. Confirm the credential appears in Git linked accounts.

| Field | Value |
| --- | --- |
| Git provider | `GitHub` |
| Credential name | `aiw_hol_github`, or any unique name you choose |
| Git provider email | `vishal.dhiman@oracle.com` for the instructor-provided workshop identity |
| Personal access token | Paste the authorized token supplied **privately** by the instructor; no token is published in this guide |

If using your own GitHub PAT, enter **your own GitHub email** instead. Do not combine your own PAT with the workshop account's email. Use only the repository-read access required by your approved workshop setup; pushing changes is not part of this lab.

Keep the token hidden when entering it.

## Step 4 Open the workspace root

Click **Workspaces**, open your assigned workspace (for example **HOL_Workspace**), and select the workspace's **top-level/root folder** in the tree. The breadcrumb should end at the workspace name.

**Do not enter Shared or another child folder.** From the workspace root, click **Create → Git folder (Preview)**.

## Step 5 Create the aiw_hol Git folder

Enter these values in **Create Git folder**, then click **Create**:

| Field | Value |
| --- | --- |
| Select GIT credentials | The credential you saved in Step 3, for example `aiw_hol_github` |
| Git Repository URL | `https://github.com/vishaldhiman22/Oracle_AIW_2026_AIDP_HOL.git` |
| Git folder name | `aiw_hol` |
| Branch name | `main` |

Wait for cloning to finish. Open **aiw_hol → Content** and confirm that `data`, `aidp-livelabs` and `README.md` are present. Creating this Git folder downloads the files into AIDP; no manual CSV upload is required. If the clone fails, check the credential and repository URL with the instructor before retrying.

This is the [Oracle-documented Git folder workflow](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/git-integration.html). If `aiw_hol` already exists, inspect it rather than deleting it; obtain instructor guidance before replacing or pulling over local edits.

## Step 6 Verify workshop.json and the workspace path

In the AIDP Git folder, navigate to:

**aiw_hol → aidp-livelabs → config → workshop.json**

Click `workshop.json` to open its editor. Verify these settings; the committed file already contains them:

| Setting | Required value for this layout |
| --- | --- |
| `workspace_name` | `HOL_Workspace`, or your assigned workspace's display name |
| `catalog` | `default` |
| `source_root` | `/Workspace/aiw_hol/data` |
| `schemas.bronze` | `seer_bronze` |
| `schemas.silver` | `seer_silver` |
| `schemas.gold` | `seer_gold` |

If you change anything, preserve valid JSON and choose **File → Save**. Verify the saved indicator before proceeding. Do not replace the whole configuration with just these fields; retain the other supplied settings and historical `fixture_as_of` date.

**Important path rules**

- A Git folder at the workspace root named `aiw_hol` uses `/Workspace/aiw_hol`. Do not insert `HOL_Workspace` into that filesystem path.
- `workspace_name` is descriptive; it does not create or rename a workspace and does not control file resolution.
- If you intentionally used a different folder/location, change `source_root` to its actual `data` folder. Also change `config_path` in **Lab 1B, Lab 1C and Lab 2** to that checkout's `aidp-livelabs/config/workshop.json`.
- **Lab 1A** uses `config_path = "../config/workshop.json"`. Keep its relative path and the supplied directory structure.

Your workspace tree should be:

```text
HOL_Workspace (workspace root)
└── aiw_hol (Git folder, branch main)
    ├── README.md
    ├── data/
    │   ├── source-data_suppliers_supplier_extract.csv
    │   ├── source-data_assets_financial_assets.csv
    │   ├── source-data_purchasing_purchase_orders.csv
    │   ├── source-data_schedules_project_milestones.csv
    │   └── source-data_inspections_inspection_findings.csv
    └── aidp-livelabs/
        ├── config/workshop.json
        └── notebooks/
            ├── Lab1A_Bronze_Ingestion.ipynb
            ├── Lab1B_Silver_Transformations.ipynb
            ├── Lab1C_Gold_Project_Data.ipynb
            └── Lab2_Predict_Investigate_and_Operationalize.ipynb
```

## Step 7 Open Lab 1A

Navigate to **aiw_hol → aidp-livelabs → notebooks**. Click **Lab1A_Bronze_Ingestion.ipynb**. It should open as a notebook with separate explanatory Markdown cells and Python code cells—not as raw JSON.

Use the four notebooks in the order shown below. Do not make another copy in `Shared`.

## Step 8 Attach a Spark cluster

In the notebook's upper-right corner, click **Cluster → Attach existing cluster**, then select your instructor-assigned cluster, for example **seer_livelabs_spark**.

Wait until the cluster is running/ready and the notebook shows the intended cluster. Repeat this attachment check when opening **each** of the other three notebooks. Attaching compute does not run the cells.

If the menu says **No clusters available**, or the badge says **Stopped**, ask the instructor to start/provision the assigned cluster through **Compute** and confirm your permissions. Do not run code while compute is unavailable. The prepared workshop used Spark 3.5.0 on AMD compute (2-OCPU/16-GB driver and worker); use the approved workshop runtime, including AIDP's MLflow integration. No GPU or XGBoost installation is needed.

## Step 9 Learn how to run one cell

Click inside the **first Python code cell** so only that cell is selected. Open the notebook menu **Run → Run selected cell(s)**. The menu also displays the platform-specific keyboard shortcut.

Wait for completion before selecting the next Python cell. Inspect its output below the cell. A setup cell may return `DataFrame[]` or no output; that alone is not a failure. If a red traceback appears, stop and resolve it before continuing.

**Do not click Run all** during the walkthrough. Do not choose **Run selected text**, and do not select multiple cells. Markdown cells explain the task; select the Python cell below the explanation. A bracketed number such as `[8]` is an execution counter, not the task number and not necessarily its first execution.

For every checklist below, run **one row's code cell, wait, review, then proceed to the next row**.

## Step 10 Complete Lab 1A Bronze ingestion

Run all seven code cells in this order using Step 9:

| Code cell order | What to run | What to check |
| ---: | --- | --- |
| 1 | Setup under Task 1 | Reads `../config/workshop.json`; creates `default.seer_bronze` if absent |
| 2 | `suppliers_raw` load | Reads the supplier CSV and displays up to five saved rows |
| 3 | `assets_raw` load | Displays the three asset rows |
| 4 | `purchasing_raw` load | Displays four purchase-order rows |
| 5 | `schedules_raw` load | Displays four milestone rows |
| 6 | `inspections_raw` load | Displays four inspection rows |
| 7 | Review Bronze tables and row counts | Lists all five saved tables and their counts |

Every load reads from `/Workspace/aiw_hol/data`, preserves fields as strings, replaces only its named Bronze table, and displays a sample. Source CSVs are unchanged.

Expected counts in `default.seer_bronze`: **suppliers_raw 8, assets_raw 3, purchasing_raw 4, schedules_raw 4, inspections_raw 4**—23 rows in total. Your output should begin with `default.seer_bronze`.

**Stop if a load fails or a count differs.** Resolve it before starting Silver.

## Step 11 Complete Lab 1B Silver transformations

Return to the notebook folder and open **Lab1B_Silver_Transformations.ipynb**. Attach the cluster as in Step 8. Run these seven code cells individually:

| Code cell order | Task | Transformation and checkpoint |
| ---: | --- | --- |
| 1 | Setup | Reads config and creates `default.seer_silver` if absent |
| 2 | Task 1 Suppliers | Standardizes supplier names, status, certifications and locations; reconciles duplicates |
| 3 | Task 2 Assets | Reconciles project/asset references and adds project names |
| 4 | Task 3 Purchase orders | Resolves supplier/asset references, normalizes status and converts amounts to USD cents |
| 5 | Task 4 Inspections | Normalizes inspection results; inspect the first five records |
| 6 | Task 5 Milestones | Casts dates, normalizes status and derives `late_flag` for completed milestones; inspect sample records |
| 7 | Review Silver tables and row counts | Confirms the five saved Silver tables |

Read the comments before running each transformation. Each task produces one table from saved upstream tables; there is no separate Silver validation or quarantine task.

Expected counts in `default.seer_silver`: **suppliers 6, assets 3, purchase_orders 4, inspections 4, milestones 4**. Stop on errors or unexpected counts.

## Step 12 Complete Lab 1C Gold data

Open **Lab1C_Gold_Project_Data.ipynb**, attach the cluster, and run its five Python code cells individually:

| Code cell order | Task | Output |
| ---: | --- | --- |
| 1 | Setup | Creates `default.seer_gold` if absent |
| 2 | Task 1 Build project context | Spark SQL aggregates purchasing, supplier and inspection context into `project_context` |
| 3 | Task 2 Build milestone features | Creates `milestone_features` with nine numeric inputs for unfinished milestones |
| 4 | Task 3 Publish known milestone outcomes | Creates `milestone_outcomes` from completed milestones with known lateness |
| 5 | Task 4 Build milestone training data | Creates `milestone_training` for Lab 2 |

Task 1 aggregates before joining to avoid multiplying purchase-order costs. Tasks 2–4 consume saved tables. Inspect the displayed outputs after each cell; the fixture has three current feature milestones and one completed milestone with a known outcome.

Refresh **Master catalog → default → seer_gold → Tables** and confirm all four table names. Lab 1 now has **5 Bronze + 5 Silver + 4 Gold tables**. The notebook's final lineage section has no additional Python cell: open a Gold table's **Actions → Lineage (Preview)** if you want to inspect its relationships.

## Step 13 Start Lab 2 and prepare the experiment

Open **Lab2_Predict_Investigate_and_Operationalize.ipynb** and attach the cluster. Complete these four Python tasks, one at a time:

| Notebook task | What to do | Checkpoint |
| ---: | --- | --- |
| 1 | Create/reuse the experiment and initialize variables | Record experiment `seer_milestone_delay` and the printed `SESSION_ID` |
| 2 | Load Gold training history | Inspect the training rows, nine inputs and class counts |
| 3 | Create the train/validation split | Uses the same stratified 50/50 split with seed 42 for every candidate |
| 4 | Define MLflow helpers | Defines training/logging and comparison functions; no candidate runs yet |

Do not rerun Task 1 between training rounds: that starts another comparison session. The split requires enough rows from both classes. If data is missing, finish Lab 1C first.

**Learning limitation:** this tiny fixture uses status-derived proxy labels; an input feature also reveals the proxy target. This demonstrates the MLflow lifecycle, not a scientifically valid forecast evaluation. Do not interpret the displayed metrics as production model accuracy.

## Step 14 Train and compare the first model family

Run **Task 5** once. It trains three Decision Tree candidates and logs three separate runs to the same experiment. Wait for the cell to finish. Then run **Task 6** once to display the first comparison.

| Run name | max_depth | min_samples_leaf |
| --- | ---: | ---: |
| `dt_r1_1` | 3 | 10 |
| `dt_r1_2` | 5 | 20 |
| `dt_r1_3` | 8 | 30 |

Check that the Task 6 comparison contains the three intended completed runs. Record their run IDs. **Pause here** to inspect them in the UI before adding the second model family.

## Step 15 Inspect the first comparison in the UI

Open **Experiments → seer_milestone_delay** from the workspace navigation. In **List**, filter run names with `dt_r1`. Use the run IDs printed in Task 6 to identify the three runs from **your current session**; names repeat on reruns.

Select their checkboxes and click **Compare**. Inspect the parameter/metric information and scroll to the **validation_f1** and **validation_brier_score** charts. Higher F1 and lower Brier are preferred. Do not register a winner yet.

The experiment retains run history. A name filter alone does not isolate a session; use current run IDs. Return to the same Lab 2 notebook/session when finished.

## Step 16 Train the second family and choose the best of all six

Run **Task 7** once. It adds three Gradient Boosting candidates to the **same experiment and session**:

| Run name | max_depth | learning_rate | n_estimators |
| --- | ---: | ---: | ---: |
| `gb_r2_1` | 2 | 0.05 | 60 |
| `gb_r2_2` | 3 | 0.10 | 100 |
| `gb_r2_3` | 4 | 0.05 | 120 |

After completion, run **Task 8** once. Verify that the notebook compares six completed candidates from this walkthrough. The selection rule is **highest validation F1, then lowest validation Brier score**, then run name to break a remaining tie. Record the selected run ID and metrics.

To repeat the visual comparison, return to **Experiments → seer_milestone_delay → List**, clear the name filter, select the six current run IDs and choose **Compare**. Historical runs stay in the experiment. If you accidentally reran a training cell, the current session may contain extra candidates; start a clean walkthrough at Task 1 rather than silently comparing the wrong set.

## Step 17 Register the selected model

Return to Lab 2 and run **Task 9 exactly once**. Use the notebook route for this walkthrough; do not also register the same selection through the UI.

Confirm the output reports:

- Model: `default.seer_gold.milestone_delay_classifier`
- A model version number
- The selected source run ID
- A URI such as `models:/default.seer_gold.milestone_delay_classifier/1` (use the actual returned version, which may not be 1)

Browse **Master catalog → default → seer_gold → Models → milestone_delay_classifier → Versions** to inspect the registered version and its source-run link. Each registration creates a new version. If the cell appears to fail, check the Versions list before retrying.

## Step 18 Reload the registered model and score

Run **Task 10** in the **same active notebook session**. It loads the exact registered version from Task 9 and scores the current `default.seer_gold.milestone_features` rows.

Inspect the displayed milestone ID, project/milestone names, planned date, `delay_probability`, `predicted_late` and `model_version`. The classification threshold is 0.5. Expect three scoring rows with the supplied fixture.

**Lab 2 ends here.** Scores are displayed, not written to a predictions table. No PDF ingestion, knowledge base, document volume or additional workflow is required. Stop your dedicated cluster through **Compute** when finished, in accordance with instructor guidance; do not stop shared compute used by other learners.

## Reruns and recovery

Do not delete experiments, runs, model versions or source files before a normal rerun.

| Action | Effect |
| --- | --- |
| Rerun Lab 1A | Drops/recreates its five named Bronze tables without backups |
| Rerun Lab 1B | Drops/recreates its five named Silver tables without backups |
| Rerun Lab 1C | Drops/recreates its four named Gold tables without backups |
| Rerun Lab 2 from Task 1 | New session; adds runs and a model version; keeps previous history |
| Rerun Task 10 alone in the same session | Reloads the selected version and displays scores; no new training or registration |

Run only one writer at a time. A failed write after a drop can leave the target table absent; resolve the failure before continuing. Table history and table-specific metadata are not preserved by the rebuild.

If sources change, rerun **Lab 1A → Lab 1B → Lab 1C → Lab 2**. If only Silver changes, start at Lab 1B; if only Gold changes, start at Lab 1C. Always begin with the chosen notebook's setup. Upstream changes do not automatically refresh downstream tables.

A lost Lab 2 session also loses variables such as `REGISTERED_URI`, `MODEL_VERSION` and `FEATURES`. Task 10 is not a standalone fresh-session inference script. Restart the complete walkthrough or obtain an instructor-provided inference setup.

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| Git credential is missing from the dropdown | Verify it was added under Settings → Git linked accounts for the current identity |
| Git clone fails | Check URL, branch `main`, authorized credential, expiry and approved network access |
| `aiw_hol` already exists | Inspect the existing folder; do not delete uncommitted work |
| Configuration not found | Open the notebook from `aiw_hol/aidp-livelabs/notebooks`; preserve the sibling `config` folder |
| CSV not found | Confirm `source_root = /Workspace/aiw_hol/data` and all five CSV filenames |
| Permission denied on schema/table/model | Ask the instructor for the required permission; do not bypass access controls |
| No cluster or missing `spark` | Attach the assigned cluster and wait for readiness |
| Missing MLflow or scikit-learn | Use the approved runtime; do not replace AIDP's integrated MLflow installation |
| Gold training table missing | Finish Lab 1C Task 4 in the same configured catalog/schema |
| Stratified split or ROC AUC fails | Inspect class counts; both train/validation partitions need both classes |
| More than six candidates | A training cell was repeated in the same session; restart at Task 1 |
| Model version is greater than 1 | Normal after reruns; use the version returned by Task 9 |
| Lineage is empty/loading | Refresh after execution and inspect current table identities; successful writes alone do not prove lineage capture |

## Included data and verification scope

The five CSVs under [data](data/) contain 23 input rows. Keep their filenames unchanged. The notebook code is self-contained.

Lab 1A's seven code cells were successfully executed on AIDP on October 5, 2026 using the existing demonstration catalog and workspace data folder. This guide update changes the checkout path to `/Workspace/aiw_hol` and keeps the requested `default` catalog setting. These new environment settings were statically checked but not re-executed on AIDP as part of the documentation update.

## Attribution

Adapted from Oracle LiveLabs material by Eli Schilling and the LiveLabs/ONA Lab Experience teams: [original Lab 1](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=1-unified-lakehouse-foundation), [original Lab 2](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=2-unify-data-for-ai), and [original Lab 3](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=3-trusted-data-products).

This independently maintained repository is not an Oracle-published replacement. It contains no PATs, live workbench OCIDs, private deployment receipts or execution logs.

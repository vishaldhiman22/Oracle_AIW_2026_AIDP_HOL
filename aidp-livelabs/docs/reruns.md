# Rerunning Lab 1 and Lab 2

[Workshop home](../README.md) · [Lab 1](01-lab1.md) · [Lab 2](02-lab2.md)

You can repeat both labs sequentially in this dedicated workshop environment. **Do not delete experiments, training runs, model versions, source files or schemas before an ordinary rerun.** The notebooks handle their own target writes, but their effects differ.

## What each rerun changes

| What you run | Reused or retained | Replaced or added |
| --- | --- | --- |
| Lab 1A — Bronze | Source CSVs, schemas and volumes | Drops and recreates five named Bronze tables; no backups |
| Lab 1B — Silver | Bronze inputs and unrelated objects | Drops and recreates five named Silver tables; no backups |
| Lab 1C — Gold | Silver inputs, models and volumes | Drops and recreates `project_context` and `milestone_features`; no backups |
| Lab 2, starting at Task 1 | Existing experiment, earlier runs/model versions and Lab 1 tables | Adds six training runs and a registered model version; overwrites `milestone_delay_predictions` |
| Lab 2 Task 10 only | Selected registered model/version | Overwrites predictions without retraining or registering another version |
| Lab 2 Task 11 | Identical existing PDFs | Copies missing PDFs; stops for review if existing bytes differ |
| Full four-task workflow | Source files, experiment history, models and KB objects | Performs all three Lab 1 resets, then the complete Lab 2 training/registration/scoring path |

Lab 1 recreations discard the existing target table's history and table-specific metadata. A failure between drop and write can leave that target absent. These operations are not an atomic multi-table update. Do not run other readers or writers that require a consistent workshop snapshot while rebuilding it.

## Lab 1: choose where to restart

1. If source CSVs or Bronze ingestion changed, run **Lab 1A → Lab 1B → Lab 1C → Lab 2**.
2. If only Silver transformations changed and Bronze is current, run **Lab 1B → Lab 1C → Lab 2**.
3. If only Gold transformations changed and Silver is current, run **Lab 1C → Lab 2**.
4. Start each notebook at its setup cell, then run the remaining cells in order. Silver also has dependencies between its table transformations.
5. After a failed Lab 1 write, resolve the cause, recreate the affected target by rerunning its cell, and complete dependent cells/notebooks before using the results.
6. Refresh the catalog and recheck row counts, outputs and native lineage. Do not assume an old graph or a previous successful run describes newly recreated tables.

An upstream rerun does **not** refresh downstream tables automatically. Existing Gold predictions can remain visible but be out of date until Lab 2 scores the refreshed Gold data. Lab 1C does not delete the prediction table or registered model.

## Lab 2: repeat a complete walkthrough

1. Confirm Lab 1's Gold inputs exist and no competing writer is running.
2. Start at **Task 1**. It reuses `seer_milestone_delay` and generates a new comparison `SESSION_ID`.
3. Run Tasks 2–8 in order, executing the Task 5 and Task 7 training rounds once each.
4. Do not rerun Task 1 between rounds. Doing so changes the session and excludes earlier candidates from the comparison.
5. Inspect the current notebook's three-run and six-run comparisons. The UI retains older runs, sometimes with identical names; identify current runs by run ID and session tag.
6. Run Task 9 once to register the selected artifact, then Task 10 to load that returned version and overwrite the predictions table.
7. Run Task 11 to stage the PDFs, reusing identical existing files. This completes Lab 2; there are no subsequent quality, readiness or knowledge-base tasks.

**No prior deletion is required.** The new session isolates model selection from earlier walkthroughs. Training still consumes compute, and retained run artifacts/model versions accumulate storage.

### If a training round fails or was repeated

Stop and fix the cause. If Task 5 or Task 7 created any runs, repeating the entire cell in the same session can leave extra completed candidates and fail Task 8's exact-six-run check. The simplest learner recovery is a fresh walkthrough from Task 1, running both rounds once. Previous partial/failed runs may remain for troubleshooting; do not delete them to force the comparison to pass.

### If you only want to score again

In the same active notebook session, rerun Task 10 with its required variables still defined, including `REGISTERED_URI`, `MODEL_NAME`, `MODEL_VERSION` and `best_run_id`. It reloads the selected version and overwrites the batch predictions. Do not rerun Task 9: registration would create another version.

Task 10 is not a standalone fresh-session notebook. If the session was lost, follow the complete walkthrough, or have the instructor provide a separate inference-only setup with an explicit existing model version and its originating run. Do not substitute “latest” or guess missing values.

### If registration or scoring fails

Check the catalog's Models → Versions list before repeating Task 9: registration might have completed even if a later step failed. If registration succeeded and its variables remain available, fix the scoring issue and rerun Task 10. Keep the model version and source-run identifiers together.

## Separate optional knowledge-base exercise

Reuse the Austin KB and assistant when the same PDFs and retrieval setup are intended. A new classifier version alone does not require PDF re-ingestion. Review changed documents or retrieval settings and ingest as needed; inspect the actual ingestion result. Do not repeat the creation steps for every model-training run.

## Concurrency and optional cleanup

- Run one notebook/workflow writer at a time. Workflow concurrency of one does not prevent an interactive notebook from writing simultaneously.
- Keep automatic Lab 2 retries disabled. A full retry can create another group of runs and another registered version.
- Cleanup is optional storage/history housekeeping, not part of the normal rerun procedure. Keep versions and source runs needed by predictions or comparisons.
- Before any cleanup, identify exact lab-owned objects and their dependencies. Do not delete the catalog, schemas, source volumes, active model artifacts or unrelated resources as a reset shortcut.
- Stopping between exercises does not require deleting data. Follow the setup guide's compute and idle-timeout guidance.

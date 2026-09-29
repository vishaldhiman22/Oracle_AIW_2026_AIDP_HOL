# Run the four-notebook workflow

[Back to Lab 2](02-lab2.md)

## Prerequisites and deployment status

The workflow uses four notebook tasks. All three layers remain in the standard catalog `seer_livelabs_20260922`. Complete [Lab 1](01-lab1.md) setup and stop concurrent writers before a run.

## Task 1: Deploy the four notebooks

1. Open workspace **seer_livelabs_20260922**.
2. Import the four IPYNB files into **Shared → seer-aidp-livelabs → notebooks**.
3. Verify `config/workshop.json`: the catalog and all three schema names are unchanged.
4. Confirm each notebook opens with separate Markdown and Python cells.
5. Keep the PDF volume and source volume at their existing standard-catalog locations.
6. Use the split notebooks rather than the superseded monolithic Lab 1 notebook.

## Task 2: Update the existing job

Open **Workflow → Jobs → seer_aidp_labs.job → Tasks**. Replace the single Lab 1 task with the following three tasks and change Lab 2's dependency.

| Task key | Notebook | Depends on |
| --- | --- | --- |
| `lab1_bronze` | `Lab1A_Bronze_Ingestion.ipynb` | None |
| `lab1_silver` | `Lab1B_Silver_Transformations.ipynb` | `lab1_bronze` |
| `lab1_gold` | `Lab1C_Gold_Project_Data.ipynb` | `lab1_silver` |
| `lab2_predict_and_assess` | `Lab2_Predict_Investigate_and_Operationalize.ipynb` | `lab1_gold` |


1. Use **Notebook task**, **Workspace** source and **seer_livelabs_spark** for every task.
2. Set each dependency condition to **All success**.
3. Keep **Max concurrent runs = 1**, no schedule, and a 90-minute job timeout.
4. Give the Lab 1 tasks 30-minute timeouts and Lab 2 a 60-minute timeout.
5. Pass `run_id = {{job.run_id}}` to all tasks. Gold and Lab 2 stamp persisted rows with this value.
6. Set job parameter `config_path` to `/Workspace/Shared/seer-aidp-livelabs/config/workshop.json`. The Bronze/Silver setup cells use this default path directly; Gold and Lab 2 also accept the parameter.
7. Save, reopen the job and verify every notebook path and dependency.

The [native request template](../workflows/seer-labs.template.json) can be rendered for the existing cluster:

```bash
python tools/render_workflow.py \
  --cluster-key "<your-cluster-key>" \
  --cluster-name seer_livelabs_spark
```

Rendering prepares JSON only; it does not update or run the live job. The deployed request (private deployment record; not distributed) records the four tasks.

## Task 3: Execute and verify

1. Stop concurrent interactive writes.
2. Choose **Run now** once and open the new run.
3. Check tasks execute Bronze → Silver → Gold → Lab 2.
4. Inspect each task's notebook output. All four must reach **Success**.
5. Confirm two Lab 1 Gold tables and Lab 2's predictions are in `seer_livelabs_20260922.seer_gold`.
6. Compare project counts and costs with the local reference checks. For Lab 2, verify both three-run rounds, the six-run comparison, the registered model/version, and the notebook's registered-model score read-back check.
7. Open Gold lineage and verify upstream Silver/Bronze relationships through all three layers.
8. Run KB ingestion separately after PDF staging; the workflow does not ingest the KB or wait for the UI exercise.

If Gold fails on schema visibility, object creation or write permissions, stop and resolve that specific issue before rerunning downstream tasks. Do not change catalogs to work around a permissions failure.

## Reruns

No prior experiment, model or table deletion is needed. **Run now on the full workflow repeats both Lab 1 and Lab 2**, whereas running the Lab 2 notebook alone reads the existing Lab 1 tables. Follow [rerun guidance](reruns.md) to choose the appropriate restart point.

Bronze, Silver, and Gold each recreate one named Delta table per write cell; prior Delta history/table-specific metadata are not preserved. These are not atomic multi-table publications.

The fixture should continue to yield three context rows, three eligible milestones, Austin committed cost 167,390,000 cents, and total cost 473,090,000 cents. Classification probabilities are synthetic demonstration outputs, not validated operational predictions.

Lab 2 adds six runs to the same experiment and registers another version of the selected model on each complete execution. Its session tag keeps each two-round comparison separate. Do not enable automatic Lab 2 retries: a retry can create extra experiment runs/model versions. Model artifacts remain in MLOps storage, not extra Gold Delta tables.

Do not run an interactive writer alongside the workflow; max concurrency one only limits workflow runs. If a Lab 2 task partially fails, inspect its outputs and the model Versions list before retrying. Another complete Lab 2 execution starts a new comparison session; it need not delete partial history. The KB and document assistant are reused separately and are not automatically ingested or tested.

Return to [Lab 2](02-lab2.md).

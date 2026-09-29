# Workshop checkpoints

[Workshop home](../README.md)

No evidence worksheet, generated summary, or attestation file is required.

## Lab 1

- Five Bronze tables contain 23 source rows.
- Five Silver business tables have the expected counts and keys.
- Supplier standardization and reconciliation are explained by comments in the Silver notebook; there is no learner answer-key validation task.
- Three supplier-source issues, one unresolved PO reference and the retained supplier conflict are visible.
- Gold context and features each have three rows; costs are correct.
- Native lineage shows source-to-target relationships across schemas.

## Lab 2

- Confirm three Gradient Boosting runs and three Decision Tree runs in one experiment, with a common session tag.
- Compare validation metrics, select the winning run and evaluate it on the reserved test partition.
- Register its artifact, reload the returned model version and check all three persisted predictions against that loaded model.
- Stage three Austin PDFs in the Gold output volume; Lab 2 ends at Task 11.
- Successful execution and model registration are not production approval.

## Repeated exercises

- Lab 1 requires no manual deletion: it recreates its 12 target tables without backups. Rerun downstream notebooks after upstream changes.
- Lab 2 requires no experiment/model cleanup: it adds six runs and a version, while overwriting predictions. Use a fresh Task 1 session and execute each training round once.
- Reuse identical PDFs; no KB or assistant is required for Lab 2.
- Keep one writer active. Cleanup is optional; preserve artifacts needed for traceability. See [rerun guidance](reruns.md).

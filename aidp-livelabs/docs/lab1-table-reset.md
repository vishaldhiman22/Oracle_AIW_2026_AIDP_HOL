# Lab 1 rerun behavior

[Back to Lab 1](01-lab1.md)

There is no global reset or optional recreation section. Each Bronze, Silver, and Gold write cell recreates only its target Delta table immediately before writing its new result. Twelve explicit tables are affected, without backups. CSVs, PDFs, schemas, volumes and unrelated tables remain unchanged.

Lab 1 uses SQL for table recreation and Spark SQL for Gold project context; the other business transformations use PySpark DataFrame expressions. Lab 2 overwrites its predictions when explicitly run after Gold is refreshed; Lab 1 alone does not refresh or remove existing predictions.

Run Bronze → Silver → Gold → Lab 2 after changing sources. Do not run concurrent writers. The catalog remains `seer_livelabs_20260922` and the Gold schema remains `seer_gold`.

No manual deletion is required before rerunning. A failed drop/write sequence can leave a target absent; fix the cause and rerun its producing cell, then its dependents. Resetting tables does not reset experiment history, registered models or the knowledge base. See [rerunning both labs](reruns.md) for restart points and optional cleanup.

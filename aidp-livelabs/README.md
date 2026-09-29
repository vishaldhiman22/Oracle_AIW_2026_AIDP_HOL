# Seer Construction: lakehouse data and milestone predictions

Build project context from five CSV feeds, train and compare six milestone-delay classifiers with AIDP MLOps, register and reload the winning model for batch predictions, and stage the project PDFs in a volume.

## Start here

1. Complete [environment setup](docs/00-setup.md).
2. Run [Lab 1](docs/01-lab1.md): Bronze → Silver → Gold.
3. Run [Lab 2](docs/02-lab2.md): create an experiment, train, compare, register, reload, score, and stage PDFs (Tasks 1–11).
4. Optionally execute the separate [four-task workflow](docs/workflow.md).
5. Before repeating either lab, read [rerun and cleanup guidance](docs/reruns.md). Ordinary reruns require no prior experiment/model deletion; Lab 1 recreates its target tables and Lab 2 retains model history while replacing predictions.

| Notebook | Purpose |
| --- | --- |
| [Lab 1A — Bronze](notebooks/Lab1A_Bronze_Ingestion.ipynb) | Five CSV imports; minimal setup |
| [Lab 1B — Silver](notebooks/Lab1B_Silver_Transformations.ipynb) | Five commented transformations; no validation task |
| [Lab 1C — Gold](notebooks/Lab1C_Gold_Project_Data.ipynb) | PySpark project context and milestone features |
| [Lab 2](notebooks/Lab2_Predict_Investigate_and_Operationalize.ipynb) | Experiment → two training rounds → compare → register → reload → batch score → PDF staging |

All tables remain in `seer_livelabs_20260922`: five Bronze, five Silver, and three Gold after Lab 2. No tables are moved to the vector catalog. Gold remains `seer_gold`.

The four notebooks are authoritative learner sources. No duplicate lab Python scripts or workspace `lib` folder are needed. Configuration and Lab 2 reference JSON files remain required. Authoring-only reference helpers are isolated under `tools/test_support` and must not be uploaded to AIDP.

Lab 1 recreates each named target immediately before its write, without backups. Its business transformations use PySpark DataFrames and Spark SQL. No learner evidence files, summary tables, or Silver validation task are produced. Lab 2 intentionally retains MLflow runs and model artifacts; rerunning creates six new runs and a new model version. [Reset scope](docs/lab1-table-reset.md).

The model learns from synthetic training data, not from PDFs. PDFs are staged to a volume in Task 11. Native knowledge-base ingestion and agent testing are available only as a separate optional guide, not as Lab 2 tasks. Successful execution does not establish production readiness.

## Package and verification

Validate with `python tools/validate_local.py`, build the HTML reader with `python tools/build_guide.py` (Pandoc required), and package with `python tools/package_workshop.py`. Original assets are not duplicated in the ZIP; their hashes are listed in [source-assets.json](reference/source-assets.json).

See [validation guidance](validation/README.md) and [source-to-AIDP mapping](docs/conversion-map.md). Supply your own AIDP resource identifiers; private deployment records and screenshots are not distributed. The generated HTML guides open locally without a web server.

Adapted from Oracle LiveLabs material by Eli Schilling and the LiveLabs/ONA Lab Experience teams. This locally authored workshop is not an Oracle-published replacement. The Ask AIDP skill informed notebook structure, deployment, and native workflow verification.

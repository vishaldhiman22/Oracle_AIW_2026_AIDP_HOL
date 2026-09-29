# Original-to-AIDP conversion

| Original content | Two-lab AIDP edition |
| --- | --- |
| Lab 1 seeded Bronze/Silver/Gold inventory | Lab 1 builds actual exercise Delta snapshots from five CSVs. |
| Cloud link/external supplier table | Volume read and materialized Bronze table; not a live external view. |
| SQL supplier standardization | Commented PySpark transformations in the Silver notebook, without a learner validation task. |
| Canonical events/quality/lineage | Five Silver business tables, direct preaggregated Gold context, and native table/column lineage. |
| Lab 2 seeded structured/JSON/graph products | Replaced by a focused milestone-feature product and supervised-learning lifecycle. |
| Lab 2 embedded model/vector search/chunks | PDF staging remains in Task 11. Native knowledge-base/RAG instructions are a separate optional extension. |
| Lab 2 semantic context | Not part of the MLflow lab; the separate optional document guide can use Gold predictions. |
| Lab 3 seeded pipeline history | Four AIDP notebook tasks: Bronze, Silver, Gold and Lab 2, with native run inspection. |
| Lab 3 contracts, freshness, consumer readiness | Removed from Lab 2. The retained MLflow tasks check model inputs and persisted scores; there is no readiness assessment. |

Additional authored assets: 1,800 synthetic training examples, stochastic labels, six Gradient Boosting/Decision Tree experiment runs, validation-based comparison, catalog model registration, registered-version batch scoring, historical upcoming-milestone features and native KB ingestion review. Synthetic performance is not real project accuracy. Gold source quality is not silently corrected. Document coverage remains Austin-only. PDF provenance uses file hashes, not invented OCI object-version IDs.

Repeated execution is documented in [rerun guidance](reruns.md): Lab 1 replaces its named table snapshots, while Lab 2 keeps experiment/model history and replaces batch predictions. No prior experiment or model deletion is required.

Original Oracle LiveLabs sources: [Lab 1](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=1-unified-lakehouse-foundation), [Lab 2](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=2-unify-data-for-ai), [Lab 3](https://livelabs.oracle.com/cdn/analytics-ai/alh-implement-unified-data-layer/workshops/sandbox/index.html?lab=3-trusted-data-products). Reviewed September 22, 2026. The old authored edition is preserved in the versioned ZIP outside this package.

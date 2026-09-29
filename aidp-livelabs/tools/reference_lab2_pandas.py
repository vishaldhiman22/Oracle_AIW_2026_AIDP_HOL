# %% [markdown]
# # Lab 2: Predict, investigate and operationalize
# **Time:** 75-90 minutes plus compute/ingestion startup. Complete Lab 1 first.
# Train a milestone-delay classifier using explicitly synthetic historical Gold
# data, score the three upcoming milestones from Lab 1, and use a native PDF
# knowledge base to investigate project requirements. Finish with a two-task
# workflow, quality/freshness checks and readiness assessment.
#
# Use the AIDP interface to create and ingest the knowledge base, then test a
# document assistant with a RAG tool. Pause after PDF staging to complete those
# steps. This notebook records their evidence separately from model results.

# %% [markdown]
# ## Task 1: Read Gold features and verify the foundation
# Attach the dedicated Spark cluster before running this notebook.
# For interactive work, run both notebooks with the same explicit SEER_RUN_ID
# (the default is `interactive`). Workflow tasks receive the real job run ID.

# %%
import os, sys, json
from pathlib import Path
import numpy as np
import pandas as pd
LAB_HOME = Path(os.environ.get("SEER_LAB_HOME", "/Workspace/Shared/seer-aidp-livelabs"))
sys.path.insert(0, str(LAB_HOME / "tools/test_support"))
from seer_runtime import Lab, digest, now
from seer_predictions import (FEATURES, synthetic_history, chronological_split,
    fit_classifier, predict, metrics, reason_signals, stage_documents, kb_evidence_status, feature_matrix)
lab = Lab("Lab2_Predict_Investigate_and_Operationalize", globals().get("spark"), globals().get("oidlUtils"))
context = lab.read("gold", "project_context")
features = lab.read("gold", "milestone_features")
inventory = lab.read("bronze", "source_record_inventory")
quality = lab.read("gold", "data_quality_results")
quarantine = lab.read("silver", "quarantined_records")
task_evidence = lab.read("gold", "workflow_task_evidence")
for frame in [context, features, inventory, quality]:
    assert frame.run_id.eq(lab.run_id).all(), "Mixed run snapshots: run Lab 1 first in the same workflow/interactive run"
assert ((task_evidence.run_id == lab.run_id) & (task_evidence.notebook == "Lab1_Unified_Lakehouse_Foundation") & (task_evidence.status == "SUCCEEDED")).any()
assert all(digest(lab.path(row.source_object)) == row.source_sha256 for _, row in inventory.iterrows()), "Source changed since Lab 1"
feature_matrix(features)
print("Native upstream state:", lab.parameter("upstream_lab1_state", "INTERACTIVE"))
display(features[["project_id", "milestone_id", "planned_date"] + FEATURES])

# %% [markdown]
# ## Task 2: Create a labeled Gold training product
# The workshop source data has three projects and no historical outcome training
# set. Generate 1,800 SYNTHETIC examples to teach the lifecycle, not to claim real
# accuracy. Each row is one unfinished milestone 1-30 days before its due date.
# `late_flag = actual_completion_date > planned_date`. The generator samples
# noisy outcomes, rather than copying the rule-based supplier risk label.
# Only the nine explicit FEATURES enter training. Outcome dates, IDs and labels
# are excluded. Synthetic data, current fixture data and predictions stay separate.

# %%
history = synthetic_history(lab.config["synthetic_seed"], lab.config["synthetic_rows"])
assert len(history) <= lab.config["max_driver_rows"]
history_types = {c: "double" for c in FEATURES}
history_types.update(late_flag="long", generator_seed="long")
lab.write("gold", "milestone_training_data", history.assign(run_id=lab.run_id), history_types)
history = lab.read("gold", "milestone_training_data").drop(columns="run_id")
display(history[["milestone_id", "prediction_as_of", "planned_date", "actual_completion_date", "late_flag", "data_origin"]].head())
print("Synthetic rows:", len(history), "late fraction:", float(history.late_flag.mean()))

# %% [markdown]
# ## Task 3: Split chronologically and train a classifier
# Train only on snapshots AND labels available before 2026-01-01. Later
# snapshots form the untouched test set. Exclude unresolved training-cutoff
# outcomes; no repeated milestone appears across splits. Fit normalization only
# on training rows. The model is L2 logistic regression implemented transparently
# with NumPy so no additional ML library or external service is needed.
# The helper optimizes binary log-loss; it is not a rules-to-probabilities lookup.

# %%
train, test, excluded_rows = chronological_split(history, lab.config["training_cutoff"])
assert pd.to_datetime(test.label_available_at, utc=True).max() < pd.Timestamp(lab.config["fixture_as_of"])
model = fit_classifier(train)
model_path = lab.evidence("milestone-delay-model.json", model)
loaded_model = json.loads(Path(model_path).read_text())
assert np.allclose(predict(model, test), predict(loaded_model, test))
print({"train_rows": len(train), "test_rows": len(test), "cutoff_gap_rows": excluded_rows,
       "model_version": model["model_version"], "iterations": model["iterations"], "model_artifact": model_path})

# %% [markdown]
# ## Task 4: Evaluate against a baseline
# The baseline predicts the TRAINING late rate for everyone. Compare ROC AUC,
# Brier score (lower is better), precision, recall and the confusion matrix.
# The 0.5 classification threshold is fixed before looking at held-out outcomes.
# These are measured results on SYNTHETIC data, not production accuracy or
# calibrated real-world likelihoods. No minimum accuracy is fabricated as PASS.

# %%
threshold = lab.config["classification_threshold"]
assert 0 < threshold < 1
test_probabilities = predict(model, test)
baseline_probabilities = np.full(len(test), float(train.late_flag.mean()))
evaluation = pd.DataFrame([
    dict(model_name="logistic_regression", **metrics(test.late_flag, test_probabilities, threshold)),
    dict(model_name="training_prevalence_baseline", **metrics(test.late_flag, baseline_probabilities, threshold))])
evaluation["evaluation_scope"], evaluation["model_version"], evaluation["run_id"] = "SYNTHETIC_HOLDOUT_ONLY", model["model_version"], lab.run_id
evaluation["evaluated_at"] = now()
evaluation_types = {c: "double" for c in ["roc_auc", "brier_score", "accuracy", "precision", "recall", "threshold"]}
evaluation_types.update({c: "long" for c in ["rows", "true_positive", "false_positive", "false_negative", "true_negative"]})
lab.write("gold", "model_evaluation", evaluation, evaluation_types)
display(evaluation)
print("Compare rather than assume improvement. Do not tune on this test set.")

# %% [markdown]
# ## Task 5: Make predictions from Lab 1's Gold data
# Score Austin frame erection, Houston podium release and Harbor brace approval.
# The completed Austin delivery is excluded. These are historical fixture
# demonstrations at July 14, NOT live project forecasts at today's date.
# LOW/MEDIUM/HIGH bands (<0.4 / <0.7 / >=0.7) are workshop triage conventions,
# independent of the 0.5 evaluation threshold, not business-approved decisions.
# Context signals below are observed evidence, not causal model explanations.

# %%
predictions = features[["project_id", "asset_id", "milestone_id", "project_name", "milestone_name",
                        "planned_date", "prediction_as_of", "committed_cost_cents"]].copy()
predictions["delay_probability"] = predict(loaded_model, features)
predictions["predicted_late"] = predictions.delay_probability.ge(threshold)
predictions["risk_band"] = pd.cut(predictions.delay_probability, [-np.inf, .4, .7, np.inf], right=False, labels=["LOW", "MEDIUM", "HIGH"]).astype(str)
predictions["observed_context_signals"] = features.apply(reason_signals, axis=1)
predictions["model_version"] = model["model_version"]
predictions["model_training_origin"] = "SYNTHETIC_TRAINING_ONLY"
predictions["prediction_scope"] = "HISTORICAL_FIXTURE_DEMONSTRATION_NOT_OPERATIONAL"
predictions["scored_at"], predictions["run_id"] = now(), lab.run_id
assert predictions.delay_probability.between(0, 1).all()
lab.write("gold", "milestone_delay_predictions", predictions,
    {"delay_probability": "double", "predicted_late": "boolean", "committed_cost_cents": "long"})
display(predictions.sort_values("delay_probability", ascending=False))

# %% [markdown]
# ## Task 6: Stage PDFs in a volume and create a native knowledge base
# Run the next cell to copy the three PDFs into `workshop_outputs/austin-project`.
# Original files remain untouched. The notebook records hashes and page counts;
# it does not extract chunks or generate embeddings. Unexpected files or changed
# existing versions stop staging for review, preventing silent KB scope changes.
#
# Follow `docs/knowledge-base.md`: create a KB, add THIS folder, ingest now, inspect
# native job results, then attach a RAG tool to an agent and test supported and
# unsupported questions. The KB contains Austin evidence only. A high Harbor or
# Houston risk score does NOT imply their documents are present in this KB.

# %%
documents, manifest_sha256, kb_source_folder = stage_documents(lab)
lab.write("gold", "document_catalog", documents, {"page_count": "long"})
lab.evidence("knowledge-base-source-manifest.json", dict(source_folder=str(kb_source_folder),
    source_manifest_sha256=manifest_sha256, documents=documents[["document_name", "content_sha256"]].to_dict("records")))
print({"kb_source_folder": str(kb_source_folder), "source_manifest_sha256": manifest_sha256})
display(documents)

# %% [markdown]
# ## Task 7: Record actual knowledge-base ingestion evidence
# In an interactive run, pause here to do the UI exercise. Copy the evidence
# template to your output volume, fill ACTUAL identifiers/status/timestamps and
# the manifest hash printed above, then configure `kb_evidence_path`.
# Rerun this cell after editing. A workflow never pauses for a person: absent
# evidence is recorded as NOT_RECORDED, not a fabricated successful ingestion.
# This is a manual UI attestation, not an API-verified native status check.

# %%
kb_evidence_path = lab.parameter("kb_evidence_path", lab.config.get("kb_evidence_path", ""))
kb_evidence = json.loads(Path(kb_evidence_path).read_text()) if kb_evidence_path else {}
kb_status = kb_evidence_status(kb_evidence, manifest_sha256, kb_source_folder)
lab.write("gold", "knowledge_base_evidence", pd.DataFrame([dict(
    knowledge_base_key=kb_evidence.get("knowledge_base_key"), ingestion_run_id=kb_evidence.get("ingestion_run_id"),
    status=kb_status["status"], verification_method=kb_status["verification_method"],
    source_manifest_sha256=manifest_sha256, reasons=json.dumps(kb_status["reasons"]), evaluated_at=now(), run_id=lab.run_id)]))
display(kb_status)

# %% [markdown]
# ## Task 8: Run quality, contract, source-freshness and coverage checks
# Fresh processing timestamps do not refresh the July source data. The supplier
# extract has no timestamp. Inspect known-source age and complete-feed freshness
# separately. A three-document KB only covers Austin, not all three projects.

# %%
contract = json.loads((LAB_HOME / "reference/project_context_contract.json").read_text())
assert list(context.columns) == [c["name"] for c in contract["columns"]]
for c in contract["columns"]:
    if not c["nullable"]:
        assert context[c["name"]].notna().all(), c["name"]
    if c["type"] == "LONG":
        assert pd.api.types.is_integer_dtype(context[c["name"]]), c["name"]
key_columns = ["project_id", "asset_id", "milestone_id"]
keys_valid = not predictions.duplicated(key_columns).any() and predictions[key_columns].notna().all().all()
assert keys_valid and len(predictions) == len(features) == 3
assert documents.page_count.sum() == 5 and len(documents) == 3
coverage = predictions[key_columns].merge(documents.groupby(["project_id", "asset_id"]).size().rename("document_count").reset_index(),
    on=["project_id", "asset_id"], how="left", validate="many_to_one")
coverage["document_count"] = coverage.document_count.fillna(0).astype(int)
lab.write("gold", "prediction_document_coverage", coverage, {"document_count": "long"})
source_times = pd.to_datetime(inventory.source_extracted_at, utc=True, errors="coerce")
source_age = (pd.Timestamp(now()) - source_times.min()).total_seconds() / 60
fixture_age = (pd.Timestamp(lab.config["fixture_as_of"]) - source_times.min()).total_seconds() / 60
freshness = pd.DataFrame([dict(product_name="milestone_delay_predictions", oldest_known_source=source_times.min().isoformat(),
    known_source_age_minutes=source_age, known_source_status="FRESH" if 0 <= source_age <= lab.config["freshness_sla_minutes"] else "STALE",
    complete_feed_freshness="UNKNOWN" if source_times.isna().any() else "KNOWN",
    historical_fixture_age_minutes=fixture_age, prediction_as_of=lab.config["fixture_as_of"],
    measured_at=now(), run_id=lab.run_id)])
lab.write("gold", "data_product_freshness", freshness, {"known_source_age_minutes": "double", "historical_fixture_age_minutes": "double"})
display(quality)
display(quarantine)
display(coverage)
display(freshness)

# %% [markdown]
# ## Task 9: Assess readiness without confusing it with execution success
# Structural checks can PASS while business readiness remains NOT_READY.
# Production model validation is deliberately false: synthetic evaluation cannot
# establish it. Metadata does not grant permissions. Security/owner labels need
# an actual review; they cannot override the synthetic model restriction.

# %%
readiness_checks = [
    ("unique_prediction_keys", bool(keys_valid), "Measured keys and prediction coverage"),
    ("valid_probabilities", bool(predictions.delay_probability.between(0, 1).all()), "Finite model outputs in [0,1]"),
    ("source_quality", len(quarantine) == 0, f"{len(quarantine)} unresolved source exceptions"),
    ("current_complete_source_freshness", bool(0 <= source_age <= lab.config["freshness_sla_minutes"] and source_times.notna().all()), "Source dates, not processing timestamps"),
    ("real_world_model_validation", False, "Synthetic training/holdout only; real model validation not performed"),
    ("knowledge_base_ingestion_evidence", bool(kb_status["check_passed"]), kb_status["status"] + "; manual attestation only"),
    ("document_scope_coverage", bool(coverage.document_count.gt(0).all()), "Only Austin has supplied PDFs"),
    ("security_review", lab.config["security_review"] == "APPROVED", "Configuration attestation; not permission enforcement"),
    ("accountable_owner", bool(lab.config["owner"].strip()) and "assign before publication" not in lab.config["owner"], lab.config["owner"])]
readiness = pd.DataFrame([dict(check_name=name, check_passed=bool(passed), evidence=reason,
    overall_readiness="NOT_READY", evaluated_at=now(), run_id=lab.run_id) for name, passed, reason in readiness_checks])
lab.write("gold", "ai_readiness_assessment", readiness, {"check_passed": "boolean"})
catalog = pd.DataFrame([dict(product_name=name, accountable_owner=lab.config["owner"], classification=lab.config["classification"],
    publication_status="WORKSHOP_REVIEW_ONLY", contract_version=lab.config["contract_version"], purpose=purpose) for name, purpose in [
    ("project_context", "Reconciled project/asset context"), ("milestone_features", "Historical unfinished milestone features"),
    ("milestone_training_data", "Synthetic labeled training demonstration"), ("milestone_delay_predictions", "Synthetic-model demonstration, not operational advice"),
    ("document_catalog", "Austin-only PDF provenance; knowledge base lives in Catalog")]])
lab.write("gold", "data_product_catalog", catalog)
lab.evidence("readiness-assessment.json", readiness.to_dict("records"))
display(readiness)
if lab.config["fail_on_not_ready"] and not readiness.check_passed.all():
    raise RuntimeError("Publication gate blocked. Assessment saved; do not relabel unresolved evidence as approved.")
lab.finish()

# %% [markdown]
# ## Task 10: Execute the two-task AIDP workflow
# Follow `docs/workflow.md` to run Lab1 -> Lab2, passing the same native run ID.
# Inspect actual job/task status and logs; notebook evidence is supplementary.
# Rerun to check stable business keys, model version and probabilities. Changing
# timestamps/attempt IDs is expected. Workflows rebuild data and stage PDFs, but
# do NOT trigger knowledge-base ingestion. If documents change, explicitly ingest
# in the KB UI again and replace the attestation with the actual new evidence.
#
# Test `fail_on_not_ready=true`: the final task must retain its assessment and
# fail. The synthetic-only model means production publication remains blocked.
# A successful default workflow means the assessment ran, not that the products
# are approved for use. No production agent deployment or schedule is activated.

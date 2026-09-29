"""Test the pandas business references; statically check both Spark notebooks.

Real Spark Lab 1 execution is verified separately from exported AIDP run output.
"""
import ast
import contextlib
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/test_support"))
from render_workflow import render
from local_spark_stub import LocalSparkStub


def main():
    import numpy as np
    import pandas as pd
    from seer_predictions import FEATURES, feature_matrix, fit_classifier, predict, metrics, kb_evidence_status
    from pypdf import PdfReader
    import hashlib
    for item in json.loads((ROOT / "reference/pdf-manifest.json").read_text()):
        pdf = ROOT.parent / ("documents_" + item["document_name"])
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == item["sha256"]
        assert len(PdfReader(pdf).pages) == item["page_count"]
    os.environ.update(SEER_LOCAL_TEST="1", SEER_LAB_HOME=str(ROOT), SEER_SOURCE_ROOT=str(ROOT.parent), SEER_RUN_ID="LOCAL_TWO_LAB_VALIDATION")
    from validate_lab1_structure import main as validate_lab1_structure
    from validate_maintenance import main as validate_maintenance
    validate_lab1_structure()
    validate_maintenance()
    report = {"scope": "Lab 1 business references and historical logistic-classifier reference executed. Historical classifier checks do not validate the current MLOps models. Current Lab 2 has separate data-split/static checks; cloud model execution has separate evidence.", "passed": [], "not_run": []}
    scripts = sorted((ROOT / "notebooks").glob("Lab*.ipynb"))
    assert len(scripts) == 4
    assert not list((ROOT / "notebooks").glob("*.py")), "Learner folder must contain notebooks only"
    for source in ROOT.rglob("*.py"):
        ast.parse(source.read_text(), filename=str(source))
    notebooks, states = [], []
    reference_executed = False
    log = io.StringIO()
    for path in scripts:
        nb = json.loads(path.read_text())
        assert nb["nbformat"] == 4 and nb["nbformat_minor"] == 5
        assert len({c["id"] for c in nb["cells"]}) == len(nb["cells"])
        for c in nb["cells"]:
            if c["cell_type"] == "code":
                ast.parse("".join(c["source"]), filename=str(path) + ":" + c["id"])
                assert c["execution_count"] is None and c["outputs"] == []
        state = {"display": lambda value: None, "spark": LocalSparkStub(ROOT / "validation/local-store")}
        with contextlib.redirect_stdout(log):
            business_code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
            if path.name.startswith("Lab1"):
                if not reference_executed:
                    exec(compile((ROOT / "tools/reference_lab1_pandas.py").read_text(), "reference_lab1_pandas.py", "exec"), state)
                    states.append(state)
                    reference_executed = True
            else:
                assert business_code.count("saveAsTable(") == 1
                assert '.write.format("delta")' in business_code
                exec(compile((ROOT / "tools/reference_lab2_pandas.py").read_text(), "reference_lab2_pandas.py", "exec"), state)
                states.append(state)
            # Historical reference programs above are authoring-only comparison
            # fixtures, not the learner notebooks or deployed workflow.
            for forbidden in ["lab.evidence(", "lab.finish(", "write_text(",
                              "workflow_task_evidence", "lineage_summary", "source_record_inventory",
                              "milestone_investigation_packet", "ai_readiness_assessment"]:
                assert forbidden not in business_code, (path, forbidden)
        notebooks.append(nb)
        report["passed"].append(path.name + ": static structure checked; business reference tested separately")
    one, two = states
    assert len(one["spark"].writes) == 5
    assert sum(item["rows"] for item in one["spark"].writes) == 23
    assert {item["table"].rsplit(".", 1)[-1] for item in one["spark"].writes} == {
        "suppliers_raw", "assets_raw", "purchasing_raw", "schedules_raw", "inspections_raw"}
    from seer_runtime import FILES
    for entity, (relative, _) in FILES.items():
        expected_raw = pd.read_csv(ROOT.parent / relative.replace("/", "_"), dtype=str, keep_default_na=False)
        pd.testing.assert_frame_equal(one["raw"][entity], expected_raw)
    report["passed"].append("Pandas reference's Bronze cell exercised with a local API test double: five overwrite targets, 23 rows; not current Spark Lab 1 execution")
    for nb in notebooks:
        narrative = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
        assert not re.search(r"original lab|original delivery story|temporary ALH|translated into Python|This edition|Lab 3|No hand-built", narrative, re.I)
    report["passed"].append("Both notebook narratives are standalone; no migration/back-reference wording")
    assert one["context"].committed_cost_cents.sum() == 473090000
    assert one["comparison"].validation_status.eq("MATCH").sum() == 8
    assert len(one["quarantine"]) == 4 and len(one["suppliers"]) == 6
    assert set(one["features"].milestone_id) == {"A44022", "A33011", "A22007"}
    report["passed"].append("Source controls: 23 rows, 8 standardization matches, 6 suppliers, 4 exceptions, 3 upcoming milestones; no completed activity scored")
    assert set(FEATURES).isdisjoint({"late_flag", "actual_completion_date", "label_available_at", "milestone_id"})
    assert pd.to_datetime(two["train"].label_available_at, utc=True).max() < pd.Timestamp(two["lab"].config["training_cutoff"])
    assert set(two["train"].milestone_id).isdisjoint(two["test"].milestone_id)
    assert np.allclose(two["model"]["mean"], feature_matrix(two["train"]).mean(axis=0))
    assert len(two["train"]) + len(two["test"]) + two["excluded_rows"] == len(two["history"]) == 1800
    assert two["history"].data_origin.eq("SYNTHETIC_TRAINING_ONLY").all()
    model2 = fit_classifier(two["train"])
    assert model2["model_version"] == two["model"]["model_version"]
    assert np.allclose(predict(model2, two["features"]), two["predictions"].delay_probability)
    report["passed"].append("Synthetic labels/origin, temporal split/label availability, train-only normalization, deterministic model fit and JSON reload")
    assert metrics([0, 1], [.1, .9])["roc_auc"] == 1
    assert metrics([0, 1], [.5, .5])["roc_auc"] == .5
    assert metrics([0, 1], [.9, .1])["roc_auc"] == 0
    bad = two["features"].copy()
    bad.loc[0, FEATURES[0]] = np.nan
    try:
        feature_matrix(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("Nonfinite features accepted")
    report["passed"].append("ROC AUC perfect/tied/reversed unit tests and rejection of nonfinite features")
    assert two["documents"].page_count.sum() == 5
    assert two["coverage"].document_count.tolist() == [3, 0, 0]
    assert two["kb_status"]["status"] == "NOT_RECORDED"
    assert not kb_evidence_status({"normalized_status": "SUCCEEDED"}, two["manifest_sha256"], two["kb_source_folder"])["check_passed"]
    assert two["readiness"].overall_readiness.eq("NOT_READY").all()
    assert not two["readiness"].set_index("check_name").loc["real_world_model_validation", "check_passed"]
    report["passed"].append("PDF staging: 3 files/5 pages, Austin-only coverage; absent and incomplete KB attestations do not pass; production readiness stays blocked")
    from reference_cells import parse_cells
    final_cell = next("".join(c["source"]) for c in parse_cells((ROOT / "tools/reference_lab2_pandas.py").read_text()) if c["cell_type"] == "code" and "readiness_checks =" in "".join(c["source"]))
    two["lab"].config["fail_on_not_ready"] = True
    try:
        with contextlib.redirect_stdout(log):
            exec(final_cell, two)
    except RuntimeError as error:
        assert "Publication gate blocked" in str(error)
    else:
        raise AssertionError("Publication gate failed open")
    report["passed"].append("Fail-closed publication gate raises after saving NOT_READY evidence")
    from validate_lab2_independence import main as validate_lab2_independence
    validate_lab2_independence()
    report["passed"].append("Current Lab 2 synthetic generation/splits execute without workshop-library imports; MLOps calls checked statically")
    payload = render("TEST_CLUSTER_KEY", "Validation cluster")
    assert [t["taskKey"] for t in payload["tasks"]] == ["lab1_bronze", "lab1_silver", "lab1_gold", "lab2_predict_and_assess"]
    assert [t["dependsOn"] for t in payload["tasks"]] == [[], [{"taskKey": "lab1_bronze"}], [{"taskKey": "lab1_silver"}], [{"taskKey": "lab1_gold"}]]
    assert all(t["runIf"] == "ALL_SUCCESS" for t in payload["tasks"])
    assert "{{job.run_id}}" in json.dumps(payload) and "__CLUSTER" not in json.dumps(payload)
    report["passed"].append("Four-task native workflow request renders with dependency and dynamic run parameters")
    before = one["context"].drop(columns="last_successful_refresh")
    replay = {"display": lambda value: None, "spark": LocalSparkStub(ROOT / "validation/local-store")}
    with contextlib.redirect_stdout(log):
        exec((ROOT / "tools/reference_lab1_pandas.py").read_text(), replay)
    pd.testing.assert_frame_equal(before, replay["context"].drop(columns="last_successful_refresh"))
    report["passed"].append("Pandas business-reference replay preserves outputs; not a Spark notebook replay")
    for path in ROOT.rglob("*.md"):
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" not in link and not link.startswith("#"):
                assert (path.parent / link.split("#")[0]).exists(), (path, link)
    report["passed"].append("All relative Markdown links resolve")
    report["training_split"] = {"train": len(two["train"]), "test": len(two["test"]), "cutoff_gap_excluded": two["excluded_rows"]}
    report["synthetic_holdout_metrics"] = two["evaluation"].drop(columns=["run_id", "evaluated_at"]).to_dict("records")
    report["not_run"] = ["This local test does not execute either Spark notebook or verify native lineage; see separate cloud evidence", "Native KB creation/ingestion and agent/RAG answer tests", "Real-world model training, calibration or production validation"]
    (ROOT / "validation/report.json").write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "validation/local-execution.log").write_text(log.getvalue())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

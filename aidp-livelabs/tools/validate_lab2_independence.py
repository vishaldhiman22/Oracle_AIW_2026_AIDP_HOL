"""Validate the self-contained MLOps notebook without simulating AIDP/MLflow."""
import ast
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def main():
    nb = json.loads((ROOT / "notebooks/Lab2_Predict_Investigate_and_Operationalize.ipynb").read_text())
    cells = {c["id"]: "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"}
    code = "\n".join(cells.values())
    tree = ast.parse(code)
    assert len(cells) == 11
    headings = ["".join(c["source"]).splitlines()[0] for c in nb["cells"] if c["cell_type"] == "markdown" and "".join(c["source"]).startswith("## Task ")]
    assert len(headings) == 11 and headings[-1].startswith("## Task 11:")
    assert "project_context_contract.json" not in code
    assert "known_source_status" not in code
    assert "sys.path" not in code and "seer_predictions" not in code and "seer_runtime" not in code
    assert code.count("saveAsTable(") == 1
    assert "mlflow.set_experiment" in cells["experiment-setup"]
    assert 'experiment_id=experiment.experiment_id' in cells["log-training-run"]
    assert 'pyfunc_predict_fn="predict_proba"' in cells["log-training-run"]
    assert "X_test" not in cells["log-training-run"]
    assert 'round_number=1' in cells["initial-comparison"]
    assert "validation_average_precision" in cells["log-training-run"]
    assert "mlflow.register_model" in cells["register-model"]
    assert 'models:/{MODEL_NAME}/{MODEL_VERSION}' in cells["register-model"]
    assert "model_uri=REGISTERED_URI" in cells["score-registered-model"]
    assert "spark.table" in cells["score-registered-model"] and "createDataFrame" not in cells["score-registered-model"]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("seer_")
    namespace = {"np": np, "pd": pd}
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in
                   {"feature_matrix", "sigmoid", "synthetic_history", "chronological_split"} or
                   isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "FEATURES" for t in n.targets)]
    exec(compile(ast.Module(body=definitions, type_ignores=[]), "notebook-data", "exec"), namespace)
    history = namespace["synthetic_history"]()
    repeated = namespace["synthetic_history"]()
    pd.testing.assert_frame_equal(history, repeated)
    train, validation, test = namespace["chronological_split"](history)
    assert len(history) == 1800
    assert history.milestone_id.is_unique
    assert history.data_origin.eq("SYNTHETIC_TRAINING_ONLY").all()
    assert set(train.milestone_id).isdisjoint(validation.milestone_id)
    assert set(train.milestone_id).isdisjoint(test.milestone_id)
    assert set(validation.milestone_id).isdisjoint(test.milestone_id)
    assert pd.to_datetime(train.label_available_at, utc=True).max() < pd.Timestamp("2025-07-01", tz="UTC")
    assert pd.to_datetime(validation.label_available_at, utc=True).max() < pd.Timestamp("2026-01-01", tz="UTC")
    assert pd.to_datetime(test.prediction_as_of, utc=True).min() >= pd.Timestamp("2026-01-01", tz="UTC")
    assert set(namespace["FEATURES"]).isdisjoint({"late_flag", "actual_completion_date", "label_available_at", "milestone_id"})
    labels = (pd.to_datetime(history.actual_completion_date) > pd.to_datetime(history.planned_date)).astype(int)
    assert labels.equals(history.late_flag)
    counts = {"train": len(train), "validation": len(validation), "test": len(test),
              "excluded": len(history) - len(train) - len(validation) - len(test)}
    report = {"scope": "Local data-generation and split tests plus static MLOps contract checks; not cloud model execution",
              "code_cells": len(cells), "splits": counts, "result": "PASS"}
    (ROOT / "validation/mlops-local.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()

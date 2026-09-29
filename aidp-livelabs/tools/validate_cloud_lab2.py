"""Validate exported MLOps output; the old logistic-model reference does not apply."""
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "validation/executed/Lab2-mlops-run.ipynb"
    nb = json.loads(path.read_text())
    cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    # Eleven cells in the current lab; twelve in the archived pre-trim execution.
    assert len(cells) in (11, 12)
    charts, texts = [], []
    for cell in cells:
        assert cell["metadata"]["command_metadata"]["end_time"] is not None, cell["id"]
        for output in cell["outputs"]:
            assert output["output_type"] != "error", output
            data = output.get("data", {})
            assert not any("error" in key for key in data), output
            texts.append(str(data.get("text/plain", "")))
            value = data.get("application/vnd.chart+json")
            if value:
                frame = pd.DataFrame(json.loads(value) if isinstance(value, str) else value)
                # The first native run predates the friendly display-column patch.
                if "run_id" in frame and "_8" in frame:
                    frame = frame.rename(columns={"_1": "runName", "_2": "round", "_3": "algorithm",
                        "_4": "validation_average_precision", "_5": "validation_recall",
                        "_6": "validation_precision", "_7": "validation_f1", "_8": "validation_brier_score"})
                charts.append(frame)
    comparisons = [x for x in charts if "validation_average_precision" in x]
    assert sorted(len(x) for x in comparisons) == [3, 6]
    final = next(x for x in comparisons if len(x) == 6)
    assert final.run_id.nunique() == 6
    assert set(final["algorithm"]) == {"Gradient Boosting", "DecisionTree"}
    assert final["validation_average_precision"].between(0, 1).all()
    predictions = next(x for x in charts if "delay_probability" in x and "model_name" in x)
    assert len(predictions) == 3 and predictions.milestone_id.nunique() == 3
    assert predictions.delay_probability.between(0, 1).all()
    assert predictions.model_version.nunique() == 1
    assert predictions.model_run_id.eq(final.iloc[0].run_id).all()
    assert predictions.model_name.eq("seer_livelabs_20260922.seer_gold.milestone_delay_classifier").all()
    assert "Loaded registered version:" in "\n".join(texts)
    if len(cells) == 12:
        freshness = next(x for x in charts if "known_source_status" in x)
        assert len(freshness) == 3
    report = {
        "scope": "Actual AIDP MLOps outputs; inline persisted-score comparison completed",
        "code_cells": len(cells), "selected_run": final.iloc[0].run_id,
        "model_name": predictions.model_name.iloc[0],
        "model_version": str(predictions.model_version.iloc[0]),
        "scoring_run_id": predictions.scoring_run_id.iloc[0],
        "comparisons": [3, 6],
        "predictions": predictions[["milestone_id", "delay_probability", "risk_band"]].to_dict("records"),
        "result": "PASS",
        "not_verified": ["Native scoring lineage graph", "KB ingestion and agent citations", "Real-world model accuracy"],
    }
    (ROOT / "validation/cloud-lab2-mlops-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

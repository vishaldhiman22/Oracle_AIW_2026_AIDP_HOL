"""Check exported real AIDP Lab 1 output against the independent pandas reference.

Run validate_local.py first; then supply executed Lab1C exported from AIDP.
This script does not run Spark and does not substitute for native lineage inspection.
"""
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "validation/executed/Lab1C-split-run.ipynb"
    notebook = json.loads(path.read_text())
    cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    assert len(cells) == 3
    charts = []
    for cell in cells:
        assert cell["metadata"]["command_metadata"]["end_time"] is not None
        assert not any(o["output_type"] == "error" for o in cell["outputs"])
        for output in cell["outputs"]:
            assert not any("error" in key for key in output.get("data", {})), output
            value = output.get("data", {}).get("application/vnd.chart+json")
            if value:
                charts.append(pd.DataFrame(json.loads(value) if isinstance(value, str) else value))
    context = next(x for x in charts if "decision_readiness" in x)
    features = next(x for x in charts if "log_committed_cost" in x)
    config = json.loads((ROOT / "config/workshop.json").read_text())
    catalog = config["catalog"]
    gold_schema = config["schemas"]["gold"]
    for name, actual, keys in [("project_context", context, ["project_id", "asset_id"]),
                               ("milestone_features", features, ["project_id", "milestone_id"])]:
        snapshot = json.loads((ROOT / f"validation/local-store/{catalog}.{gold_schema}.{name}.json").read_text())
        expected = pd.DataFrame(snapshot["rows"])
        columns = [c for c in actual if c not in {"last_successful_refresh", "run_id"}]
        pd.testing.assert_frame_equal(actual[columns].sort_values(keys).reset_index(drop=True),
            expected[columns].sort_values(keys).reset_index(drop=True), check_dtype=False,
            check_exact=False, rtol=1e-12)
    assert len(context) == len(features) == 3
    assert context.committed_cost_cents.sum() == 473090000
    report = {
        "scope": "Exported AIDP execution output compared with independent pandas business reference",
        "run_id": context.run_id.iloc[0], "completed_code_cells": len(cells),
        "gold_context_rows": len(context), "gold_feature_rows": len(features),
        "all_project_committed_cost_cents": int(context.committed_cost_cents.sum()),
        "passed": [f"All {len(cells)} cloud code cells completed without error",
                   "All Gold context business fields equal the pandas reference",
                   "All nine Gold model features and displayed milestone keys/dates equal the pandas reference",
                   "Independent exported-output checks passed; the learner Silver validation task is removed"],
        "native_lineage": "Requires separate native catalog graph inspection; not inferred from this comparison"
    }
    (ROOT / "validation/cloud-lab1-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

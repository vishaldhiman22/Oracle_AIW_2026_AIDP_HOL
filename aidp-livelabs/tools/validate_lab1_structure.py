"""Check the three learner notebooks without executing Spark."""
import ast
import builtins
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["Lab1A_Bronze_Ingestion", "Lab1B_Silver_Transformations", "Lab1C_Gold_Project_Data"]


def main():
    targets, counts = [], {}
    for name, expected in zip(NAMES, [5, 5, 2]):
        nb = json.loads((ROOT / "notebooks" / (name + ".ipynb")).read_text())
        cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        counts[name] = len(cells)
        setup = ast.parse("".join(cells[0]["source"]))
        shared = set(dir(builtins)) | {"spark", "display"}
        shared |= {n.id for n in ast.walk(setup) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        for n in ast.walk(setup):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                shared |= {a.asname or a.name.split(".")[0] for a in n.names}
        local_targets = []
        for cell in cells:
            source = "".join(cell["source"])
            tree = ast.parse(source)
            assert "from seer_" not in source and "sys.path" not in source
            assert "toPandas(" not in source and "createDataFrame(" not in source
            assert "assert " not in source, "No learner validation/assertion tasks in Lab 1"
            if name.startswith("Lab1C") and cell["id"] != "gold-project-context":
                assert not any(token in source for token in ["SELECT ", "WITH ", "selectExpr(", "F.expr("])
            if cell["id"] == "gold-project-context":
                assert 'context = spark.sql(f"""' in source and "WITH orders_by_asset AS" in source
                assert "F." not in source
            if cell != cells[0]:
                bound = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
                used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
                assert not (used - bound - shared), (name, cell["id"], used - bound - shared)
            writes = [ast.unparse(n.args[0]) for n in ast.walk(tree)
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                      and n.func.attr == "saveAsTable"]
            assert len(writes) <= 1
            local_targets.extend(writes)
        assert len(local_targets) == len(set(local_targets)) == expected
        targets.extend(local_targets)
    assert len(targets) == 12
    report = {"scope": "Static only; native execution is verified separately",
              "code_cells": counts, "table_writes": 12, "silver_validation_task": False,
              "gold_transformations": "Task 1 Spark SQL CTEs; Task 2 PySpark DataFrame API; Delta writers"}
    (ROOT / "validation/lab1-structure.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

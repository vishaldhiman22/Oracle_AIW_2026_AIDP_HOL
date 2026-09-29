"""Check per-table Bronze/Silver reset scope; never connects to AIDP."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    targets = []
    for filename, prefix, names in [
        ("Lab1A_Bronze_Ingestion.ipynb", "BRONZE",
         ["suppliers_raw", "assets_raw", "purchasing_raw", "schedules_raw", "inspections_raw"]),
        ("Lab1B_Silver_Transformations.ipynb", "SILVER",
         ["suppliers", "assets", "purchase_orders", "inspections", "milestones"]),
        ("Lab1C_Gold_Project_Data.ipynb", "GOLD", ["project_context", "milestone_features"]),
    ]:
        nb = json.loads((ROOT / "notebooks" / filename).read_text())
        found = []
        schemas_created = 0
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            tree = ast.parse("".join(cell["source"]))
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                     and n.func.value.id == "spark" and n.func.attr == "sql"]
            for call in calls:
                arg = call.args[0]
                assert isinstance(arg, ast.JoinedStr)
                ddl = "".join(n.value if isinstance(n, ast.Constant) else
                              "{" + ast.unparse(n.value) + "}" for n in arg.values)
                if cell.get("id") == "gold-project-context" and ddl.lstrip().startswith("WITH orders_by_asset AS"):
                    continue  # Read-only Spark SQL transformation; not a reset operation.
                if ddl == "CREATE SCHEMA IF NOT EXISTS {" + prefix + "}":
                    schemas_created += 1
                    continue
                assert ddl.startswith("DROP TABLE IF EXISTS {" + prefix + "}.")
                assert "CASCADE" not in ddl and "PURGE" not in ddl
                found.append(ddl.rsplit(".", 1)[-1])
        assert found == names
        assert schemas_created == 1
        targets.extend(found)
    assert len(targets) == 12
    print("PASS: twelve explicit per-cell Bronze/Silver/Gold resets")


if __name__ == "__main__":
    main()

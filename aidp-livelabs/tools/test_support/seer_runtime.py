"""Authoring-test I/O only; neither learner notebook imports this module.

The fixture is tiny. All driver-side reads have an explicit row limit. AIDP
persists managed Delta tables via Spark. Local validation persists JSON records.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

FILES = {
    "suppliers": ("source-data/suppliers/supplier_extract.csv", 8),
    "assets": ("source-data/assets/financial_assets.csv", 3),
    "purchasing": ("source-data/purchasing/purchase_orders.csv", 4),
    "schedules": ("source-data/schedules/project_milestones.csv", 4),
    "inspections": ("source-data/inspections/inspection_findings.csv", 4),
}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    checksum = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def clean_records(df):
    # JSON round trip normalizes numpy scalars and pandas missing values.
    return json.loads(df.to_json(orient="records", date_format="iso"))


class Lab:
    def __init__(self, name, spark=None, utilities=None):
        self.name, self.spark, self.utilities = name, spark, utilities
        self.local = os.environ.get("SEER_LOCAL_TEST") == "1"
        if not self.local and spark is None:
            raise RuntimeError("Attach AIDP Spark compute. Local tests require SEER_LOCAL_TEST=1.")
        default_root = "/Workspace/Shared/seer-aidp-livelabs"
        self.root = Path(os.environ.get("SEER_LAB_HOME", default_root))
        self.config = json.loads((self.root / "config/workshop.json").read_text())
        if utilities is not None:
            config_path = utilities.parameters.getParameter("config_path", str(self.root / "config/workshop.json"))
            self.config = json.loads(Path(config_path).read_text())
        if self.local:
            self.config["source_root"] = os.environ["SEER_SOURCE_ROOT"]
            self.config["output_root"] = str(self.root / "validation/local-store")
        self.out = Path(self.config["output_root"])
        self.out.mkdir(parents=True, exist_ok=True)
        self.run_id = self.parameter("run_id", os.environ.get("SEER_RUN_ID", "interactive"))
        self.attempt_id = str(uuid.uuid4())
        self.started_at = now()
        self.read_count, self.write_count = 0, 0
        for identifier in [self.config["catalog"], *self.config["schemas"].values()]:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", identifier):
                raise ValueError(f"Invalid catalog/schema identifier: {identifier}")

    def parameter(self, name, default):
        if self.utilities is None:
            return default
        return self.utilities.parameters.getParameter(name, default)

    def path(self, relative):
        name = relative.replace("/", "_") if self.config["source_layout"] == "flat" else relative
        return Path(self.config["source_root"]) / name

    def table_name(self, layer, name):
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError(name)
        catalog = self.config["catalog"]
        return f"{catalog}.{self.config['schemas'][layer]}.{name}"

    def csv(self, relative):
        path = self.path(relative)
        if self.local:
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            # Retain source spelling and headers. No inferred numeric types in Bronze.
            sdf = self.spark.read.option("header", True).option("inferSchema", False).option("mode", "FAILFAST").csv(str(path))
            df = sdf.limit(self.config["max_driver_rows"] + 1).toPandas().fillna("")
        if len(df) > self.config["max_driver_rows"]:
            raise ValueError("Driver row limit exceeded. Port this transformation to distributed Spark before using larger data.")
        self.read_count += len(df)
        return df

    def write(self, layer, name, df, types=None, append=False):
        """Stable tables with explicit scalar contracts. Dates use ISO-8601 strings.

        Supply numeric/boolean/vector fields in types; remaining fields are strings.
        This avoids empty-array, all-null, and implicit pandas-to-Spark type inference.
        """
        df = df.copy()
        types = types or {}
        rows = clean_records(df)
        table = self.table_name(layer, name)
        if self.local:
            target = self.out / (table + ".json")
            if append and target.exists():
                old = json.loads(target.read_text())
                rows = old["rows"] + rows
            target.write_text(json.dumps({"columns": list(df.columns), "types": types, "rows": rows}, indent=2))
        else:
            from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, BooleanType, ArrayType
            type_map = {"long": LongType(), "double": DoubleType(), "boolean": BooleanType(), "vector": ArrayType(DoubleType(), False)}
            schema = StructType([StructField(c, type_map.get(types.get(c), StringType()), True) for c in df.columns])
            for row in rows:
                for c in df.columns:
                    value = row.get(c)
                    if value is None:
                        continue
                    kind = types.get(c, "string")
                    row[c] = {"long": int, "double": float, "boolean": bool, "vector": lambda x: [float(v) for v in x], "string": str}[kind](value)
            sdf = self.spark.createDataFrame(rows, schema=schema)
            # Each notebook owns its targets. Reruns replace snapshots, not source files.
            writer = sdf.write.format("delta").mode("append" if append else "overwrite")
            writer.saveAsTable(table)
        self.write_count += len(df)
        return df

    def read(self, layer, name):
        table = self.table_name(layer, name)
        if self.local:
            data = json.loads((self.out / (table + ".json")).read_text())
            df = pd.DataFrame(data["rows"], columns=data["columns"])
        else:
            df = self.spark.table(table).limit(self.config["max_driver_rows"] + 1).toPandas()
        if len(df) > self.config["max_driver_rows"]:
            raise ValueError(f"{table} exceeds this workshop's driver row limit")
        self.read_count += len(df)
        return df

    def evidence(self, filename, payload):
        # Attempt-specific evidence, including reruns and failed checks, is retained.
        folder = self.out / "evidence" / self.attempt_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_text(json.dumps(payload, indent=2, default=str))
        return str(path)

    def finish(self, extra=None):
        result = dict(notebook=self.name, run_id=self.run_id, attempt_id=self.attempt_id,
                      execution_engine="LOCAL_VALIDATION" if self.local else "AIDP_NOTEBOOK",
                      started_at=self.started_at, completed_at=now(), status="SUCCEEDED",
                      records_read=self.read_count, records_written=self.write_count,
                      **(extra or {}))
        self.evidence("task-result.json", result)
        self.write("gold", "workflow_task_evidence", pd.DataFrame([result]),
                   types={"records_read": "long", "records_written": "long"}, append=True)
        print(json.dumps(result, indent=2))
        # Native job/task status is authoritative for exceptions before this final cell.
        return result


def standardize_suppliers(raw):
    result = raw[["source_record_id", "source_system", "ingestion_batch_id"]].copy()
    names = raw.supplier_name.str.strip()
    result["canonical_supplier_name"] = names.str.title()
    result.loc[names.str.upper().isin(["ATLAS STRUCTURAL FAB.", "ATLAS STRUCTURAL FABRICATION"]), "canonical_supplier_name"] = "Atlas Structural Fabrication"
    result["qualification_status"] = raw.source_status.str.strip().str.upper().map({"A": "APPROVED", "APPROVED": "APPROVED", "PENDING_INFO": "REQUEST_INFORMATION"}).fillna("REVIEW_REQUIRED")
    cert = raw.certification.fillna("").str.strip().str.upper()
    result["normalized_certification"] = cert.mask(cert.eq(""), "MISSING").mask(cert.str.contains("AISC", regex=False), "AISC")
    result["normalized_location"] = raw.location.str.strip().str.upper().str.replace(", TEXAS", ", TX", regex=False)
    return result

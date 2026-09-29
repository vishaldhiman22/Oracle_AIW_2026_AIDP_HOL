"""Narrow CSV/write test double. This does not validate Spark or Delta behavior.

Only implements the direct Bronze cell's API chain; all other operations fail.
Writes the local JSON format consumed by the workshop's offline adapter.
"""
import json
from pathlib import Path
import pandas as pd


class LocalSparkStub:
    def __init__(self, output):
        self.output = Path(output)
        self.writes = []
        self.read = self

    def csv(self, path, *, header, inferSchema, mode):
        assert header is True and inferSchema is False and mode == "FAILFAST"
        return LocalFrame(pd.read_csv(path, dtype=str, keep_default_na=False), self)


class LocalFrame:
    def __init__(self, frame, owner):
        self.frame, self.owner = frame, owner

    def fillna(self, value):
        assert value == ""
        return LocalFrame(self.frame.fillna(value), self.owner)

    @property
    def write(self):
        return LocalWriter(self.frame, self.owner)


class LocalWriter:
    def __init__(self, frame, owner):
        self.frame, self.owner = frame, owner
        self.file_format = self.write_mode = None

    def format(self, value):
        assert value == "delta"
        self.file_format = value
        return self

    def mode(self, value):
        assert value == "overwrite"
        self.write_mode = value
        return self

    def saveAsTable(self, table):
        assert self.file_format == "delta" and self.write_mode == "overwrite"
        assert table.startswith("seer_livelabs_20260922.seer_bronze.")
        assert table.endswith("_raw")
        self.owner.output.mkdir(parents=True, exist_ok=True)
        data = {"columns": list(self.frame.columns), "types": {},
                "rows": json.loads(self.frame.to_json(orient="records"))}
        (self.owner.output / (table + ".json")).write_text(json.dumps(data, indent=2))
        self.owner.writes.append({"table": table, "rows": len(self.frame)})

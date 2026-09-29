"""Parse validation-only reference scripts; never generate learner notebooks."""
import hashlib


def parse_cells(text):
    cells, kind, lines = [], None, []
    def flush():
        if kind is None:
            return
        source = "\n".join(lines).strip() + "\n"
        cell = {"cell_type": kind, "id": hashlib.sha256((str(len(cells)) + source).encode()).hexdigest()[:12], "metadata": {}, "source": source.splitlines(keepends=True)}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    for line in text.splitlines():
        if line.startswith("# %%"):
            flush()
            kind, lines = ("markdown" if "[markdown]" in line else "code"), []
        elif kind == "markdown":
            lines.append(line[2:] if line.startswith("# ") else "" if line == "#" else line)
        elif kind:
            lines.append(line)
    flush()
    return cells

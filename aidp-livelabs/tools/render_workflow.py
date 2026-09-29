"""Render a native AIDP create-job body. Does not connect, create resources or run jobs."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(cluster_key, cluster_name, folder="/Workspace/Shared/seer-aidp-livelabs"):
    if not cluster_key or not cluster_name or not folder.startswith("/"):
        raise ValueError("Supply an existing cluster key/name and absolute notebook folder from the workspace")
    config_folder = folder if folder.startswith("/Workspace/") else "/Workspace" + folder
    mapping = {"__CLUSTER_KEY__": cluster_key, "__CLUSTER_NAME__": cluster_name,
               "__WORKSPACE_FOLDER__": folder.rstrip("/"), "__CONFIG_PATH__": config_folder.rstrip("/") + "/config/workshop.json"}
    def walk(value):
        if isinstance(value, str):
            for key, replacement in mapping.items():
                value = value.replace(key, replacement)
            return value
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value
    return walk(json.loads((ROOT / "workflows/seer-labs.template.json").read_text()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster-key", required=True)
    parser.add_argument("--cluster-name", required=True)
    parser.add_argument("--workspace-folder", default="/Workspace/Shared/seer-aidp-livelabs")
    parser.add_argument("--output", type=Path, default=ROOT / "workflows/seer-labs.rendered.json")
    args = parser.parse_args()
    payload = render(args.cluster_key, args.cluster_name, args.workspace_folder)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(args.output)

import argparse
import json
import os
import sys

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schema")
SCHEMA_BY_FORMAT = {
    "scene": "scene.schema.json",
    "trajectories": "trajectories.schema.json",
    "scene_traj": "combined.schema.json",
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    try:
        import jsonschema
    except ImportError:
        print("jsonschema not installed: pip install jsonschema", file=sys.stderr)
        sys.exit(2)
    ok = True
    for path in a.files:
        doc = load(path)
        fmt = doc.get("format")
        schema_name = SCHEMA_BY_FORMAT.get(fmt)
        if not schema_name:
            print(f"{path}: UNKNOWN format={fmt!r}")
            ok = False
            continue
        schema = load(os.path.join(SCHEMA_DIR, schema_name))
        try:
            jsonschema.validate(doc, schema)
            print(f"{path}: OK ({fmt})")
        except jsonschema.ValidationError as e:
            ok = False
            print(f"{path}: INVALID ({fmt}) -> {e.message} at {list(e.path)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

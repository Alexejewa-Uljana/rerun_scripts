import argparse
import json


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def scene_objects(doc):
    if "objects" in doc:
        return doc["objects"]
    if "scene" in doc and isinstance(doc["scene"], dict):
        return doc["scene"].get("objects", [])
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--traj", nargs="+", required=True)
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    scene = load(a.scene)
    out = {"format": "scene_traj", "version": 1,
           "cell_size": scene.get("cell_size", 1.0),
           "angle_units": "rad",
           "scene": {"objects": scene_objects(scene)},
           "agents": []}
    names = set()
    for p in a.traj:
        td = load(p)
        out["angle_units"] = td.get("angle_units", out["angle_units"])
        for ag in td.get("agents", []):
            nm = ag["name"]
            while nm in names:
                nm += "_2"
            ag = dict(ag); ag["name"] = nm
            names.add(nm); out["agents"].append(ag)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"merged -> {a.out}: objects={len(out['scene']['objects'])} agents={len(out['agents'])}")


if __name__ == "__main__":
    main()

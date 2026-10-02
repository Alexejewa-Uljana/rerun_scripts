import argparse
import json

import rerunlib as rl


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compose(scene_doc, traj_docs):
    out = {"format": "scene_traj", "version": 1,
           "cell_size": scene_doc.get("cell_size", 1.0),
           "angle_units": "rad",
           "scene": {"objects": scene_doc.get("objects", scene_doc.get("scene", {}).get("objects", []))},
           "agents": []}
    for td in traj_docs:
        out["angle_units"] = td.get("angle_units", out["angle_units"])
        out["agents"] += td.get("agents", [])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc", nargs="?", help="combined scene_traj JSON")
    ap.add_argument("--scene")
    ap.add_argument("--traj", nargs="*", default=[])
    ap.add_argument("--save")
    ap.add_argument("--name", default="scene_traj")
    ap.add_argument("--dt", type=float, default=None)
    ap.add_argument("--fps", type=float, default=None)
    a = ap.parse_args()
    densify_dt = a.dt if a.dt is not None else (1.0 / a.fps if a.fps else None)
    if a.doc:
        doc = load(a.doc)
    elif a.scene:
        doc = compose(load(a.scene), [load(p) for p in a.traj])
    else:
        ap.error("pass a combined JSON or --scene SCENE.json [--traj T.json ...]")
    rl.render_document(doc, name=a.name, save=a.save, densify_dt=densify_dt)
    nobj = len(doc["scene"]["objects"]) if isinstance(doc.get("scene"), dict) else len(doc.get("objects", []))
    print(f"agents={len(doc.get('agents', []))} objects={nobj}"
          + (f" saved={a.save}" if a.save else " (spawned viewer)"))


if __name__ == "__main__":
    main()

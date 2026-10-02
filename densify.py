import argparse
import json

import numpy as np

import rerunlib as rl


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def agents_of(doc):
    return doc.get("agents", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("-o", "--out", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dt", type=float)
    g.add_argument("--fps", type=float)
    ap.add_argument("--round", type=int, default=3)
    a = ap.parse_args()
    dt = a.dt if a.dt is not None else 1.0 / a.fps
    doc = load(a.inp)
    for ag in agents_of(doc):
        rows = ag.get("trajectory", ag.get("traj"))
        n0 = len(rows)
        dense = rl.densify_rows(rows, dt)
        ag.pop("traj", None)
        ag["trajectory"] = np.round(dense, a.round).tolist()
        print(f"{ag.get('name', '?')}: {n0} -> {len(ag['trajectory'])} точек (dt={dt:.3f})")
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()

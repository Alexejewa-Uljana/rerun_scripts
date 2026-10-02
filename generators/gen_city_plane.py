import json
import os

import numpy as np
from scipy.interpolate import CubicSpline

WPTS = np.array([
    [5, 14, 4], [9, 5, 5], [15, 2, 5], [22, 4, 5], [26, 12, 13],
    [28, 22, 23], [28, 27, 23], [32, 31, 19], [34, 28, 9], [39, 28, 7], [45, 24, 6],
], float)
SPEEDS = [3.5, 2.0, 2.0, 3.0, 4.5, 4.5, 4.5, 3.0, 2.2, 2.5]

OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "trajectories", "city_plane.json")


def build_path():
    u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(WPTS, axis=0), axis=1))]
    un = u / u[-1]
    cs = CubicSpline(un, WPTS, axis=0)
    s = np.linspace(0, 1, 420)
    P = cs(s)
    seg = np.clip(np.searchsorted(un, s, side="right") - 1, 0, len(SPEEDS) - 1)
    v = np.array(SPEEDS)[seg]
    ds = np.r_[0, np.linalg.norm(np.diff(P, axis=0), axis=1)]
    t = np.cumsum(ds / v)
    return np.column_stack([t, P])


def main():
    tr = np.round(build_path(), 3)
    doc = {"format": "trajectories", "version": 1, "cell_size": 1.0, "angle_units": "rad",
           "agents": [{"name": "plane", "color": [220, 35, 35], "radius": 1.6, "body": "plane",
                       "trajectory": tr.tolist()}]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()

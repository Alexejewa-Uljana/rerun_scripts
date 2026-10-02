import json
import os

import numpy as np

Y, T, STEPS = 24, 22.0, 220
OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "trajectories", "overtake.json")


def main():
    ts = np.linspace(0, T, STEPS)
    xr = np.clip(12 + 1.0 * ts, 0, 44)
    xb = np.clip(2 + 2.1 * ts, 0, 44)
    yb = Y + 5.0 * np.exp(-((xb - xr) / 4.0) ** 2)
    red = np.round(np.column_stack([ts, xr, np.full_like(ts, Y), np.zeros_like(ts)]), 3)
    blue = np.round(np.column_stack([ts, xb, yb, np.zeros_like(ts)]), 3)
    doc = {"format": "trajectories", "version": 1, "cell_size": 1.0, "angle_units": "rad",
           "agents": [{"name": "red", "color": [220, 70, 60], "radius": 0.9, "body": "ball",
                       "trajectory": red.tolist()},
                      {"name": "blue", "color": [60, 120, 230], "radius": 0.9, "body": "ball",
                       "trajectory": blue.tolist()}]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()

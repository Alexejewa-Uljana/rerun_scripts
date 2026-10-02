import json
import os

import numpy as np

STEPS = 200
LANES = [("slow", 1.0, [200, 80, 80]), ("mid", 1.8, [200, 170, 60]), ("fast", 3.0, [80, 190, 120])]
OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "trajectories", "speeds.json")


def straight_speed(start, goal, speed):
    a, b = np.asarray(start, float), np.asarray(goal, float)
    T = np.linalg.norm(b - a) / speed
    ts = np.linspace(0, T, STEPS)
    s = np.linspace(0, 1, STEPS)
    p = (1 - s)[:, None] * a + s[:, None] * b
    return np.column_stack([ts, p])


def main():
    agents = []
    for k, (nm, v, col) in enumerate(LANES):
        tr = np.round(straight_speed([6, 12 + k * 5, 0], [42, 12 + k * 5, 0], v), 3)
        agents.append({"name": nm, "color": col, "radius": 0.9, "body": "ball", "trajectory": tr.tolist()})
    doc = {"format": "trajectories", "version": 1, "cell_size": 1.0, "angle_units": "rad", "agents": agents}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()

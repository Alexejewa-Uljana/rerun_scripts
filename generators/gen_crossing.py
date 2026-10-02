import json
import os

import numpy as np

C = 24
A_S, A_G = [4, C, 0], [44, C, 0]
B_S, B_G = [C, 4, 0], [C, 44, 0]
V0, M, STEPS, T = 2.0, 0.7, 240, 22.0

OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "trajectories", "crossing.json")


def motion(start, goal, sign):
    start, goal = np.array(start, float), np.array(goal, float)
    L = np.linalg.norm(goal - start)
    ts = np.linspace(0, T, STEPS)
    dt = ts[1] - ts[0]
    tc = (L / 2) / V0
    W = np.exp(-((ts - tc) / 2.5) ** 2)
    v = V0 * (1 + sign * M * W)
    dist = np.clip(np.cumsum(v) * dt, 0, L)
    s = dist / L
    p = start + s[:, None] * (goal - start)
    return np.column_stack([ts, p])


def main():
    A = np.round(motion(A_S, A_G, +1), 3)
    B = np.round(motion(B_S, B_G, -1), 3)
    doc = {"format": "trajectories", "version": 1, "cell_size": 1.0, "angle_units": "rad",
           "agents": [{"name": "A", "color": [230, 80, 60], "radius": 0.9, "body": "ball",
                       "trajectory": A.tolist()},
                      {"name": "B", "color": [60, 120, 230], "radius": 0.9, "body": "ball",
                       "trajectory": B.tolist()}]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()

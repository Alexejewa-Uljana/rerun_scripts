import json
import os

import numpy as np

OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "scenes", "occupancy.json")


def main():
    g = np.zeros((20, 20), int)
    g[3:6, 3:6] = 1
    g[10:13, 2:4] = 1
    g[14:16, 8:16] = 1
    g[5:8, 13:16] = 1
    doc = {"format": "scene", "version": 1, "cell_size": 1.0, "up": "z",
           "objects": [{"type": "ground", "n": 22, "color": [92, 132, 92]},
                       {"type": "occupancy", "name": "map", "grid": g.tolist(),
                        "origin": [1, 1, 0], "cell": 1.0, "color": [150, 155, 170]}]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()

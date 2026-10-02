import json
import os

BUILDINGS = [
    (14, 14, 5, 5, 12),
    (26, 24, 5, 5, 16),
    (34, 20, 5, 5, 11),
    (34, 36, 5, 5, 9),
    (18, 34, 5, 5, 10),
]
COLORS = [[205, 207, 212], [195, 198, 205], [210, 206, 200], [198, 203, 205], [202, 200, 208]]

OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "scenes", "city.json")


def main():
    objects = [{"type": "ground", "n": 49, "color": [92, 132, 92]},
               {"type": "border", "n": 49, "color": [140, 190, 140]}]
    for (x, y, w, d, h), col in zip(BUILDINGS, COLORS):
        objects.append({"type": "building", "x": x, "y": y, "w": w, "d": d, "h": h, "color": col, "detail": True})
    doc = {"format": "scene", "version": 1, "cell_size": 1.0, "up": "z", "objects": objects}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()

import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "scenes", "arena.json")


def main():
    doc = {"format": "scene", "version": 1, "cell_size": 1.0, "up": "z",
           "objects": [{"type": "border", "n": 49, "color": [140, 190, 140]}]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print("wrote", os.path.abspath(OUT))


if __name__ == "__main__":
    main()

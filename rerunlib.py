from __future__ import annotations

import json

import numpy as np
import rerun as rr

DEFAULT_RADIUS = 0.9
AXIS_LEN = 2.0
PLAN_COLOR = [240, 150, 30]
AXIS_COLORS = {"x": [235, 60, 60], "y": [60, 200, 90], "z": [70, 130, 240]}


def load_json(path_or_dict):
    if isinstance(path_or_dict, dict):
        return path_or_dict
    with open(path_or_dict, encoding="utf-8") as f:
        return json.load(f)


def set_time(t, timeline="sim_time"):
    if hasattr(rr, "set_time"):
        rr.set_time(timeline, duration=float(t))
    else:
        rr.set_time_seconds(timeline, float(t))


def rot_matrix(roll, pitch, yaw):
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, -sp], [0, 1, 0], [sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def normalize_rows(rows, angle_units="rad"):
    a = np.asarray(rows, dtype=float)
    if a.ndim != 2 or a.shape[1] < 3:
        raise ValueError("trajectory row needs at least [t, x, y]")
    n, w = a.shape
    out = np.zeros((n, 7))
    out[:, 0] = a[:, 0]
    out[:, 1:3] = a[:, 1:3]
    if w >= 4:
        out[:, 3] = a[:, 3]
    if w == 5:
        out[:, 6] = a[:, 4]
    elif w >= 7:
        out[:, 4:7] = a[:, 4:7]
    if angle_units == "deg":
        out[:, 4:7] = np.radians(out[:, 4:7])
    return out, w


def densify_rows(rows, dt):
    a = np.asarray(rows, dtype=float)
    if a.ndim != 2 or a.shape[1] < 3 or dt is None or dt <= 0 or len(a) < 2:
        return a
    b = a.copy()
    if b.shape[1] >= 5:
        b[:, 4:] = np.unwrap(b[:, 4:], axis=0)
    t = b[:, 0]
    out = [b[0]]
    for i in range(1, len(b)):
        gap = t[i] - t[i - 1]
        k = int(np.ceil(gap / dt)) if gap > dt else 1
        for j in range(1, k):
            f = j / k
            out.append(b[i - 1] + f * (b[i] - b[i - 1]))
        out.append(b[i])
    return np.array(out)


def _smooth(a, k=5):
    a = np.asarray(a, float)
    n = len(a)
    if k <= 1 or n < 3:
        return a
    k = min(k, n if n % 2 else n - 1)
    if k % 2 == 0:
        k -= 1
    if k < 3:
        return a
    pad = k // 2
    ap = np.pad(a, (pad, pad), mode="edge")
    ker = np.ones(k) / k
    return np.convolve(ap, ker, mode="valid")


def orientation_from_path(traj_xyz, bank=4.0, smooth=5):
    t = traj_xyz[:, 0]
    xyz = traj_xyz[:, 1:4]
    sm = np.column_stack([_smooth(xyz[:, i], smooth) for i in range(3)])
    d = np.gradient(sm, axis=0)
    speed = np.linalg.norm(d, axis=1) + 1e-9
    yaw = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    pitch = np.arctan2(d[:, 2], np.linalg.norm(d[:, :2], axis=1))
    yaw = _smooth(yaw, smooth)
    pitch = _smooth(pitch, smooth)
    roll = _smooth(np.clip(-bank * np.gradient(yaw) / speed, -0.5, 0.5), smooth)
    return np.column_stack([t, xyz, roll, pitch, yaw])


def plane_meshes(radius=DEFAULT_RADIUS):
    nose = [1.0, 0, 0]; tail = [-1.0, 0, 0]
    mt = [0, 0, 0.13]; mb = [0, 0, -0.11]; ml = [0, 0.1, 0]; mr = [0, -0.1, 0]
    fv = [nose, tail, mt, mb, ml, mr]
    ff = [[0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2],
          [1, 4, 2], [1, 3, 4], [1, 5, 3], [1, 2, 5]]
    rf = [0.3, 0, 0]; rb = [-0.3, 0, 0]
    ltf = [0.05, 1.0, 0.02]; ltb = [-0.2, 1.0, 0.02]
    rtf = [0.05, -1.0, 0.02]; rtb = [-0.2, -1.0, 0.02]
    fb0 = [-0.8, 0, 0.05]; ft = [-0.9, 0, 0.42]; fb1 = [-1.0, 0, 0.05]
    sc = [-0.78, 0, 0.04]; sl = [-0.95, 0.3, 0.05]; sr = [-0.95, -0.3, 0.05]
    wv = [rf, rb, ltf, ltb, rtf, rtb, fb0, ft, fb1, sc, sl, sr]
    wf = [[0, 1, 3], [0, 3, 2], [0, 5, 1], [0, 4, 5], [6, 7, 8], [9, 10, 11]]
    fv = np.array(fv, float); wv = np.array(wv, float)
    scale = radius / np.linalg.norm(np.vstack([fv, wv]), axis=1).max()
    return (fv * scale, np.array(ff, int)), (wv * scale, np.array(wf, int))


def _border_cells(n):
    cells = set()
    for i in range(0, n, 2):
        cells |= {(i, 0, 0), (i, n - 1, 0), (0, i, 0), (n - 1, i, 0)}
    return np.array(sorted(cells), float)


def log_ground(n=49, z=0.0, color=(90, 130, 90)):
    rr.log("world/scene/ground",
           rr.Boxes3D(centers=[[n / 2, n / 2, z - 0.2]], half_sizes=[[n / 2, n / 2, 0.15]],
                      colors=[list(color)], fill_mode="solid"), static=True)


def log_border(n=49, color=(140, 190, 140), size_frac=0.9):
    cells = _border_cells(n)
    if not len(cells):
        return
    half = size_frac / 2
    centers = cells.copy(); centers[:, 2] += half
    rr.log("world/scene/border", rr.Boxes3D(centers=centers, half_sizes=np.full((len(cells), 3), half),
           colors=[list(color)], fill_mode="solid"), static=True)


def _building_windows(x, y, w, d, z0, z1, frac):
    cen, hs = [], []
    wt, dt = w * frac, d * frac
    floors = np.arange(z0 + 1.1, z1 - 0.6, 2.2)
    colsx = np.linspace(-wt / 2 + 0.9, wt / 2 - 0.9, max(2, int(wt // 1.6)))
    colsy = np.linspace(-dt / 2 + 0.9, dt / 2 - 0.9, max(2, int(dt // 1.6)))
    oy, ox = dt / 2 - 0.06, wt / 2 - 0.06
    for z in floors:
        for cx in colsx:
            cen += [[x + cx, y - oy, z], [x + cx, y + oy, z]]
            hs += [[0.4, 0.06, 0.6]] * 2
        for cy in colsy:
            cen += [[x - ox, y + cy, z], [x + ox, y + cy, z]]
            hs += [[0.06, 0.4, 0.6]] * 2
    return cen, hs


def log_buildings(buildings):
    body_c, body_h, body_col, win_c, win_h = [], [], [], [], []
    tiers = [(0.0, 0.52, 1.0), (0.48, 0.82, 0.82), (0.78, 1.0, 0.64)]
    inset = 0.06
    for b in buildings:
        x, y, w, d, h = b["x"], b["y"], b["w"], b["d"], b["h"]
        col = list(b.get("color", [205, 207, 212]))
        if not b.get("detail", True):
            body_c.append([x, y, h / 2]); body_h.append([w / 2, d / 2, h / 2]); body_col.append(col)
            continue
        for z0f, z1f, frac in tiers:
            z0, z1 = z0f * h, z1f * h
            body_c.append([x, y, (z0 + z1) / 2])
            body_h.append([frac * w / 2 - inset, frac * d / 2 - inset, (z1 - z0) / 2]); body_col.append(col)
        for z0f, z1f, frac in tiers[:2]:
            wc, wh = _building_windows(x, y, w, d, z0f * h, z1f * h, frac)
            win_c += wc; win_h += wh
    if body_c:
        rr.log("world/scene/buildings/bodies", rr.Boxes3D(centers=body_c, half_sizes=body_h,
               colors=body_col, fill_mode="solid"), static=True)
    if win_c:
        rr.log("world/scene/buildings/windows", rr.Boxes3D(centers=win_c, half_sizes=win_h,
               colors=[[60, 85, 120]], fill_mode="solid"), static=True)


def log_occupancy(o, cell=1.0):
    grid = np.asarray(o["grid"])
    origin = np.asarray(o.get("origin", [0, 0, 0]), float)
    gc = float(o.get("cell", 1.0)) * cell
    color = o.get("color", [150, 155, 170])
    if grid.ndim == 2:
        ys, xs = np.nonzero(grid)
        cells = np.column_stack([xs, ys, np.zeros_like(xs)]).astype(float)
    else:
        xs, ys, zs = np.nonzero(grid)
        cells = np.column_stack([xs, ys, zs]).astype(float)
    if not len(cells):
        return
    half = gc * 0.46
    centers = (cells + 0.5) * gc + origin
    rr.log(f"world/scene/occupancy/{o.get('name', 'grid')}",
           rr.Boxes3D(centers=centers, half_sizes=np.full((len(cells), 3), half),
                      colors=[list(color)], fill_mode="solid"), static=True)


def log_cylinders(objects, cell=1.0):
    lengths, radii, centers, colors = [], [], [], []
    for o in objects:
        col = o.get("color", [180, 160, 140])
        for it in o.get("items", []):
            cx, cy, cz = (np.asarray(it["center"], float) * cell).tolist()
            h = float(it["height"]) * cell
            r = float(it["radius"]) * cell
            lengths.append(h)
            radii.append(r)
            centers.append([cx, cy, cz + h / 2])
            colors.append(list(it.get("color", col)))
    if not lengths:
        return
    rr.log("world/scene/cylinders", rr.Cylinders3D(lengths=lengths, radii=radii, centers=centers,
           colors=colors, fill_mode="solid"), static=True)


def log_scene(objects, cell=1.0):
    buildings, boxes_c, boxes_h, boxes_col, cylinders = [], [], [], [], []
    for o in objects:
        t = o["type"]
        if t == "ground":
            log_ground(o.get("n", 49), o.get("z", 0.0), o.get("color", (90, 130, 90)))
        elif t == "border":
            log_border(o.get("n", 49), o.get("color", (140, 190, 140)), o.get("size_frac", 0.9))
        elif t == "building":
            buildings.append(o)
        elif t == "box":
            c = np.asarray(o["center"], float) * cell
            s = np.asarray(o["size"], float) * cell / 2
            boxes_c.append(c.tolist()); boxes_h.append(s.tolist()); boxes_col.append(o.get("color", [150, 155, 170]))
        elif t == "mesh":
            rr.log(f"world/scene/mesh/{o.get('name', 'm')}",
                   rr.Mesh3D(vertex_positions=np.asarray(o["vertices"], float),
                             triangle_indices=np.asarray(o["faces"], int),
                             albedo_factor=o.get("color", [150, 150, 200])), static=True)
        elif t == "occupancy":
            log_occupancy(o, cell)
        elif t == "cylinders":
            cylinders.append(o)
    if buildings:
        log_buildings(buildings)
    if boxes_c:
        rr.log("world/scene/boxes", rr.Boxes3D(centers=boxes_c, half_sizes=boxes_h,
               colors=[list(c) for c in boxes_col], fill_mode="solid"), static=True)
    if cylinders:
        log_cylinders(cylinders, cell)


def dash_strips(points, dash_len=0.6, gap_len=0.4):
    P = np.asarray(points, float)
    if len(P) < 2:
        return [P.tolist()] if len(P) else []
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.r_[0.0, np.cumsum(seg)]
    total = float(s[-1])
    if total == 0:
        return [P[:1].tolist()]

    def at(d):
        i = int(np.clip(np.searchsorted(s, d) - 1, 0, len(seg) - 1))
        f = 0.0 if seg[i] == 0 else (d - s[i]) / seg[i]
        return P[i] + f * (P[i + 1] - P[i])

    strips, pos, on = [], 0.0, True
    while pos < total:
        step = dash_len if on else gap_len
        if on:
            strips.append([at(pos).tolist(), at(min(pos + step, total)).tolist()])
        pos += step
        on = not on
    return strips


def plan_points(path_pts, cell=1.0):
    a = np.asarray(path_pts, float)
    if a.ndim != 2 or len(a) == 0:
        return np.zeros((0, 3))
    if a.shape[1] == 2:
        a = np.column_stack([a, np.zeros(len(a))])
    return a[:, :3] * cell


def log_plan_updates(path, plans, cell=1.0, color=PLAN_COLOR, dash=(0.6, 0.4), radius=0.05):
    for p in sorted(plans, key=lambda q: q.get("t", 0.0)):
        set_time(p.get("t", 0.0))
        pts = plan_points(p.get("path", p.get("points", [])), cell)
        rr.log(f"{path}/plan", rr.LineStrips3D(dash_strips(pts, dash[0], dash[1]),
               colors=[list(color)], radii=radius))


def log_ball(path, traj6, color, radius, cell=1.0, draw_plan=True):
    pts = traj6[:, 1:4] * cell
    if draw_plan:
        rr.log(f"{path}/plan", rr.LineStrips3D([pts], colors=[PLAN_COLOR], radii=0.06), static=True)
    for i in range(len(traj6)):
        set_time(traj6[i, 0])
        rr.log(f"{path}/ball", rr.Ellipsoids3D(centers=[pts[i]], half_sizes=[[radius] * 3],
               colors=[list(color)], fill_mode="solid"))
        rr.log(f"{path}/trail", rr.LineStrips3D([pts[: i + 1]], colors=[list(color)], radii=0.09))


def log_plane(path, traj6, color, radius=DEFAULT_RADIUS, cell=1.0, wing_color=(245, 120, 110), draw_plan=True):
    pts = traj6[:, 1:4] * cell
    if draw_plan:
        rr.log(f"{path}/plan", rr.LineStrips3D([pts], colors=[PLAN_COLOR], radii=0.06), static=True)
    (fv, ff), (wv, wf) = plane_meshes(radius)
    rr.log(f"{path}/pose/fuselage", rr.Mesh3D(vertex_positions=fv, triangle_indices=ff,
           albedo_factor=list(color)), static=True)
    rr.log(f"{path}/pose/wings", rr.Mesh3D(vertex_positions=wv, triangle_indices=wf,
           albedo_factor=list(wing_color)), static=True)
    for i in range(len(traj6)):
        set_time(traj6[i, 0])
        rr.log(f"{path}/pose", rr.Transform3D(translation=pts[i],
               mat3x3=rot_matrix(traj6[i, 4], traj6[i, 5], traj6[i, 6])))
        rr.log(f"{path}/trail", rr.LineStrips3D([pts[: i + 1]], colors=[list(color)], radii=0.09))


def log_agent(agent, cell=1.0, angle_units="rad", densify_dt=None):
    name = agent["name"]
    color = agent.get("color", [60, 120, 240])
    radius = float(agent.get("radius", DEFAULT_RADIUS))
    body = agent.get("body", "ball")
    rows = agent.get("trajectory", agent.get("traj"))
    if densify_dt:
        rows = densify_rows(rows, densify_dt)
    traj6, width = normalize_rows(rows, angle_units)
    path = f"world/agents/{name}"
    plans = agent.get("plans")
    draw_plan = not plans
    if body == "plane":
        if width < 7:
            smooth = int(agent.get("orient_smooth", 5))
            bank = float(agent.get("bank", 4.0))
            traj6 = orientation_from_path(traj6[:, :4], bank=bank, smooth=smooth)
        log_plane(path, traj6, color, radius, cell, draw_plan=draw_plan)
    else:
        log_ball(path, traj6, color, radius, cell, draw_plan=draw_plan)
    if plans:
        plan_color = agent.get("plan_color", PLAN_COLOR)
        dash = agent.get("dash", [0.6, 0.4])
        log_plan_updates(path, plans, cell, plan_color, (dash[0], dash[1]))


def render_document(doc, name="scene_traj", save=None, densify_dt=None):
    doc = load_json(doc)
    cell = float(doc.get("cell_size", 1.0))
    units = doc.get("angle_units", "rad")
    rr.init(name, spawn=not save)
    if save:
        rr.save(save)
    rr.log("world", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
    if "scene" in doc and isinstance(doc["scene"], dict):
        objects = doc["scene"].get("objects", [])
    else:
        objects = doc.get("objects", [])
    log_scene(objects, cell)
    for ag in doc.get("agents", []):
        log_agent(ag, cell, units, densify_dt)
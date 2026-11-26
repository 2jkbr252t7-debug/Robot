"""overenie_C/tip_seam_C.py - black tip plane, seam position and cover-magnet room for variant C (vs 0). Own code (geomC)."""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geomC as G

YA, ZA = 3.0, -17.0
out = {}
for vid, shp in (("C", G.SHAPE_C), ("0", G.SHAPE_0)):
    o = {}
    # --- seam surface on the shoulder axis and at r 12 above / below / front / back (world x)
    def seam_world_x(y, z):
        xs = np.linspace(40, 80, 40001)
        Q = np.c_[xs, np.full_like(xs, y), np.full_like(xs, z)]
        P = G.to_local(Q)
        f = P[:, 0] - shp.sec(np.clip(-P[:, 2] / G.L, 0, 1))[0]
        i = np.nonzero(np.diff(np.sign(f)))[0]
        return float(xs[i[0]]) if len(i) else None
    def skins(y, z):
        xs = np.linspace(40, 80, 40001)
        ins = shp.inside(G.to_local(np.c_[xs, np.full_like(xs, y), np.full_like(xs, z)]))
        return (float(xs[ins][0]), float(xs[ins][-1])) if ins.any() else None
    o["axis"] = dict(skins=skins(YA, ZA), seam_x=seam_world_x(YA, ZA))
    for nm, (dy, dz) in dict(up=(0, 12), down=(0, -12), front=(-12, 0), back=(12, 0)).items():
        o[f"r12_{nm}"] = dict(skins=skins(YA + dy, ZA + dz), seam_x=seam_world_x(YA + dy, ZA + dz))
    # --- black tip plane
    ut = shp.p["utip"]; c = float(shp.sec(ut)[0])
    pt = np.array([c, 0.0, -G.L * ut]); n = np.array([-0.50, -0.35, -0.79]); n /= np.linalg.norm(n)
    rng = np.random.default_rng(3)
    P = np.c_[rng.uniform(-14, 10, 3_000_000), rng.uniform(-18, 18, 3_000_000), rng.uniform(-72, -36, 3_000_000)]
    P = P[shp.inside(P)]
    tip = (P - pt) @ n > 0
    cs = shp.sec(np.clip(-P[:, 2] / G.L, 0, 1))[0]
    outer = P[:, 0] >= cs
    vol_cell = 24 * 36 * 36 / 3_000_000
    o["tip_volume_mm3"] = round(float(tip.sum() * vol_cell), 0)
    o["tip_volume_on_cover_side_mm3"] = round(float((tip & outer).sum() * vol_cell), 0)
    o["tip_u_range"] = [round(float((-P[tip, 2] / G.L).min()), 3), 1.0]
    # angle between the tip plane and the arm surface along their intersection (feather edge where small)
    us = np.linspace(0.70, 0.999, 1500); th = np.linspace(0, 2 * np.pi, 1440, endpoint=False)
    S = np.concatenate([shp.ring(u, th) for u in us])
    sd = (S - pt) @ n
    k = np.abs(sd) < 0.03
    Sk = S[k]
    # surface normal by finite differences of the inside test gradient (numerical)
    h = 0.01
    def f(Pp):
        u = np.clip(-Pp[:, 2] / G.L, 1e-6, 1 - 1e-6)
        cc, ti, to, w = shp.sec(u)
        dx = Pp[:, 0] - cc
        return np.where(dx >= 0, (np.abs(dx) / to) ** shp.p["no"] + (np.abs(Pp[:, 1]) / w) ** shp.p["no"],
                        (np.abs(dx) / ti) ** shp.p["ni"] + (np.abs(Pp[:, 1]) / w) ** shp.p["ni"])
    g = np.stack([(f(Sk + h * e) - f(Sk - h * e)) / (2 * h) for e in np.eye(3)], 1)
    g /= np.linalg.norm(g, axis=1)[:, None]
    ang = np.degrees(np.arccos(np.clip(np.abs(g @ n), 0, 1)))      # angle between the normals
    edge = 90.0 - np.abs(90.0 - ang)                               # dihedral between plane and surface (0 = tangent)
    side = Sk[:, 0] >= shp.sec(np.clip(-Sk[:, 2] / G.L, 0, 1))[0]
    o["tip_cut_angle_deg_min"] = round(float(edge.min()), 1)
    o["tip_cut_angle_deg_min_cover_side"] = round(float(edge[side].min()), 1) if side.any() else None
    o["tip_cut_angle_at"] = Sk[int(np.argmin(edge))].round(2).tolist()
    # --- cover magnets (v1 spots: u 0.16 / 0.66 at y = +-(hw - 3.5) of the APPROVED outline) and the C outline
    mags = []
    for u in (0.16, 0.66):
        cc, ti, to, w = (float(v) for v in shp.sec(u))
        hw0 = float(G.base(u)[0])
        for y in (hw0 - 3.5, w - 3.5):
            q = max(0.0, 1 - (abs(y) / w) ** shp.p["no"]) if abs(y) < w else 0.0
            dcov = to * q ** (1 / shp.p["no"])
            qi = max(0.0, 1 - (abs(y) / w) ** shp.p["ni"]) if abs(y) < w else 0.0
            dinn = ti * qi ** (1 / shp.p["ni"])
            mags.append(dict(u=u, y=round(y, 2), cover_depth_from_seam=round(dcov, 2), inner_depth_from_seam=round(dinn, 2),
                             room_cover_for_magnet_wall1p6=round(dcov - 1.6 - 0.25, 2)))
    o["cover_magnet_spots"] = mags
    cj = shp.sec(0.22)
    o["joint_u022"] = dict(seam=round(float(cj[0]), 2), inner_half=round(float(cj[1]), 2), outer_half=round(float(cj[2]), 2),
                           cover_cavity_depth_wall1p6=round(float(cj[2]) - 1.6, 2))
    out[vid] = o
    print(vid, json.dumps(o, indent=1))
json.dump(out, open(os.path.join(HERE, "tip_seam_C.json"), "w"), indent=1)

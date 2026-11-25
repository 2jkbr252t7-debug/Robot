"""LAYOUT (b)/(c) - servo beside / below the column + a transmission to a shoulder shaft.  The only servo that the map lets in
near a shoulder is the KST X06 in the front-left pocket (exact_kst.json, fitted after T5 from the open side).  Here: the
belt / cord / gear corridor from its output to the shoulder axis, tested in every plane x = const (0.5 steps) against the
STATIC voxel map (no clearance added) - which parts block it and how much.  Corridor = convex hull of a servo pulley r_p
about the servo output and a shoulder pulley r_s about the shoulder axis (y 3, z -17) in the y-z plane.
Also the gear-train alternative (centre distance -> gear sizes).  Writes layout_b.json."""
import sys, os, json, math
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"]); N = tuple(D["n"])
static, label, names, moving = D["static"], D["label"], list(D["lab_names"]), D["moving"]
K = json.load(open(os.path.join(HERE, "exact_kst.json")))
c = np.array(K["centre"]); Lh = np.array(K["axes_world"]["L"]); Hh = np.array(K["axes_world"]["H (shaft)"])
if Hh[0] < 0:
    Hh = -Hh
L, W, Hc = K["case"]
# shaft 5 mm from the upper end of the 20 mm side (toward the shoulder), output on the +x face, spline end ~4 mm proud
shaft_pt = c + (L / 2 - 5.0) * Lh * np.sign(Lh[2])
out_pt = shaft_pt + (Hc / 2 + 4.0) * Hh
SH = np.array([3.0, -17.0])
Cd = float(np.hypot(out_pt[1] - SH[0], out_pt[2] - SH[1]))


def hull_mask(y, z, p, rp, q, rq):
    """points (y, z) inside the convex hull of two discs (stadium-like belt envelope)"""
    P = np.stack([y, z], -1)
    a = np.array(p); b = np.array(q)
    d = b - a; Ld = np.linalg.norm(d); u = d / Ld
    t = np.clip(((P - a) @ u) / Ld, 0, 1)
    r = rp + (rq - rp) * t                      # linear radius interpolation (exact for the tangent hull up to small error)
    closest = a + np.outer(t * Ld, u)
    return np.linalg.norm(P - closest, axis=1) <= r


Y = lo[1] + (np.arange(N[1]) + 0.5) * H; Z = lo[2] + (np.arange(N[2]) + 0.5) * H
YY, ZZ = np.meshgrid(Y, Z, indexing="ij")
rows = []
for rp, rs, what in ((3.0, 5.0, "cord / thin belt, pulleys r 3 / r 5"), (5.0, 8.0, "GT2 belt, pulleys 16T (r 5) / 25T (r 8)")):
    m = hull_mask(YY.ravel(), ZZ.ravel(), out_pt[1:], rp, SH, rs).reshape(YY.shape)
    per_x = []
    for xv in np.arange(34.0, 47.01, 0.5):
        i = int((xv - lo[0]) / H)
        blk = static[i] & m
        mv = moving[i] & m
        labs = np.unique(label[i][blk]); nm = [names[k] for k in labs if k > 0]
        per_x.append(dict(x=float(xv), blocked_mm2=round(float(blk.sum()) * H * H, 1), corridor_mm2=round(float(m.sum()) * H * H, 1),
                          sweep_mm2=round(float(mv.sum()) * H * H, 1), parts=nm))
    best = min(per_x, key=lambda r: r["blocked_mm2"] + r["sweep_mm2"])
    rows.append(dict(corridor=what, per_x=per_x, least_blocked_plane=best))
    print(what, "least blocked plane", best)
# gear train alternative
gear = dict(centre_distance_mm=round(Cd, 1),
            one_pair_m05=f"z1 + z2 = 2 C / m = {2 * Cd / 0.5:.0f} teeth -> e.g. 2 x {Cd / 0.5:.0f}T, tip D {Cd + 1:.1f} each (r {Cd / 2 + 0.5:.1f} about the shoulder axis)",
            three_gear_train_m05=f"pinion + idler + shoulder gear spanning {Cd:.1f} mm: e.g. 3 x 26T (D 13) in a line, the idler centre at "
                                 f"({(out_pt[1] + SH[0]) / 2:.1f}, {(out_pt[2] + SH[1]) / 2:.1f}) in y-z")
json.dump(dict(kst_pose=K, shaft_point=[round(float(v), 2) for v in shaft_pt], output_point=[round(float(v), 2) for v in out_pt],
               shoulder_axis_yz=SH.tolist(), centre_distance_mm=round(Cd, 1), corridors=rows, gears=gear),
          open(os.path.join(HERE, "layout_b.json"), "w"), indent=1)
print("output point", out_pt.round(2), "C", round(Cd, 1), gear)

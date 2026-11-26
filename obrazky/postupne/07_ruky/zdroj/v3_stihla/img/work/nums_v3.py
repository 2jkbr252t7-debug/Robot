"""R3 img: numbers for the comparison sheets (CAD venv).  Reads R3/tvar (variants.py, chk_variants.json), R3/mech/out,
R3/overenie_* (read only).  Writes nums_v3.json.  Own computations: front-view silhouettes / cover band, thin-spot
locations (KD-tree distance from the governing point to the analytic skin) - checked against the JSON numbers."""
import sys, json, math
import numpy as np
from scipy.spatial import cKDTree
sys.dont_write_bytecode = True
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA
CH = json.load(open("/tmp/claude-0/gapwf/fin/R3/tvar/chk_variants.json"))
YA, ZA = 3.0, -17.0
out = {}
u = np.linspace(0.001, 0.999, 20000)
for v in VA.VIDS:
    t = VA.thickness(v, u); w, ti, to = VA.profile(v, u)
    i, j = int(t.argmax()), int(w.argmax())
    w22, ti22, to22 = VA.profile(v, 0.22)
    c = CH[v]
    # front view (ortho along y): silhouette of the left arm on the horizontal line through the u 0.22 centre point
    rows, top, bot = VA.pebble_rows(v, 300, 400)
    W = VA.to_world(rows.reshape(-1, 3), v)
    z0 = float(VA.to_world(np.array([0.0, 0.0, -VA.L * 0.22]), v)[2])
    m = np.abs(W[:, 2] - z0) < 0.08
    xin, xout = float(W[m, 0].min()), float(W[m, 0].max())
    # seam line seen from the front = equator on the front side (local y = -w) ; find the u where its world z = z0
    us = np.linspace(0.05, 0.6, 4000)
    cc, tti, tto, ww, _, _ = VA.section(v, us)
    E = VA.to_world(np.stack([cc + 0.0, -ww, -VA.L * us], 1), v)
    k = int(np.argmin(np.abs(E[:, 2] - z0)))
    xs = float(E[k, 0])
    # top view band (seen from above) not needed; outermost / innermost world x of the whole arm
    out[v] = dict(name=VA.params(v)["name"], thickness_max=round(float(t[i]), 4), thickness_max_u=round(float(u[i]), 3),
                  thick_joint=round(float(VA.thickness(v, 0.22)), 4), inner_joint=round(float(ti22), 4), outer_joint=round(float(to22), 4),
                  width_max=round(float(2 * w[j]), 4), width_max_u=round(float(u[j]), 3),
                  robot_width=c["robot_width_over_arms"], gap_rest=c["gap_rest"], gap_min=c["gap_min_-45_135"],
                  gap_140=c["gap_at_140.5"], front_gap_axis=c["front_view_gap_at_axis"],
                  outermost_x=c["outermost_world_x"], innermost_x=c["innermost_world_x"],
                  front_band=dict(z=round(z0, 3), x_in=round(xin, 3), x_seam=round(xs, 3), x_out=round(xout, 3),
                                  cover=round(xout - xs, 3), visible=round(xout - xin, 3)),
                  outermost_z=float(W[np.argmax(W[:, 0]), 2]))
# ---- thin spots of the best joint option per variant (governing values from fit_tvar_*.json / verification)
SPOTS = {"0": ("M1", "ARM_naboj", "out", 67.6, 12.7), "A": ("M2b", "ARM_podlozka_M12", "in", 55.9, 12.0),
         "B": ("M2b", "DRV_unasac", "out", 62.9, 4.7), "C": ("M2b", "DRV_unasac", "out", 62.9, 4.7)}
for v, (opt, part, side, x, r) in SPOTS.items():
    fit = [d for d in json.load(open(f"/tmp/claude-0/gapwf/fin/R3/mech/out/fit_tvar_{v}.json")) if d["option"] == opt][0]
    p = fit["parts"][part]
    jwall = p["wall_out"] if side == "out" else p["wall_in"]
    req = p["req_out"] if side == "out" else p["req_in"]
    P = VA.pebble_cloud(v, 0.1)
    tr = cKDTree(P)
    best = None
    at = p["at_out"] if side == "out" else p["at_in"]
    azs = np.arange(0, 360, 0.25) if "az" not in at else np.arange(at["az"] - 10, at["az"] + 10, 0.05)
    for az in azs:
        a = math.radians(az)
        q = np.array([x, YA + r * math.cos(a), ZA + r * math.sin(a)])
        ql = VA.to_local(q, v)
        d, ii = tr.query(ql)
        ins = bool(VA.inside_local(v, ql[None])[0])
        sk = P[ii]
        hside = "out" if sk[0] > float(VA.seam_x(v, -sk[2] / VA.L)) else "in"
        if hside != side:
            continue
        s = d if ins else -d
        if best is None or s < best[0]:
            best = (s, az, q, VA.to_world(sk, v))
    s, az, q, skw = best
    out[v]["spot"] = dict(opt=opt, part=part, side=side, wall_json=jwall, req=req, wall_own=round(float(s), 3), az=float(az),
                          p=[round(float(a), 3) for a in q], skin=[round(float(a), 3) for a in skw], fits=fit["fits"],
                          governing=fit["governing"])
    print(v, opt, part, "json", jwall, "own", round(float(s), 3), "az", az, "fits", fit["fits"])
json.dump(out, open("nums_v3.json", "w"), indent=1)
for v in VA.VIDS:
    o = out[v]
    print(v, "tmax %.3f tj %.3f in %.3f out %.3f wmax %.3f robot %.2f | band cover %.2f of %.2f (designer: 0 11.6/23.6, A 7.2/19.1, B 6.3/16.0, C 5.3/12.9)"
          % (o["thickness_max"], o["thick_joint"], o["inner_joint"], o["outer_joint"], o["width_max"], o["robot_width"],
             o["front_band"]["cover"], o["front_band"]["visible"]))

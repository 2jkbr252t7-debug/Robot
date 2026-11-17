"""m01 - which parts of the pan stage are outside r 26.5 (the glued collar ring has r 26.75), what the collar ring /
disc / T_stred bore really measure, and how round the corners of the finished neck are (-> well corner radius).
Run: /opt/venv/cad/bin/python m01_stage_radius.py   (about 20 s)"""
import numpy as np, math
from zj_lib import read_stl, sample, rprof, bbox, dump, say

res = {}
# ---- 1. collar parts (finished B) -------------------------------------------------------------------------------
for n in ("golier_prstenec", "golier_kotuc"):
    P = sample(read_stl(n), 0.3)
    r = np.hypot(P[:, 0], P[:, 1])
    res[n] = dict(bbox=bbox(P), r_min=round(float(r.min()), 3), r_max=round(float(r.max()), 3))
    say(n, res[n])
# ring inner radius per z (min r of the ring material)
P = sample(read_stl("golier_prstenec"), 0.2); r = np.hypot(P[:, 0], P[:, 1])
res["prstenec_r_in_by_z"] = [(round(z, 1), round(float(r[(P[:, 2] >= z) & (P[:, 2] < z + 0.5)].min()), 3))
                            for z in np.arange(-2.0, 4.0, 0.5) if ((P[:, 2] >= z) & (P[:, 2] < z + 0.5)).any()]

# ---- 2. stage parts: r_max per z band ---------------------------------------------------------------------------
stage = ["P_sachta", "P_koleso", "P_drziak_serva", "P_kluka", "servo_zdvih", "L_pata", "L_jazyk", "L_ucho",
         "fpc_pan", "spoj_zdvih", "kabel_zdvih", "cap_kluky", "ptfe_pas_capu", "skr_F10_1", "skr_F10_2", "skr_F11",
         "skr_kluky", "skr_F12", "skr_jazyka", "kolik_ucha", "kolik_dorazu", "vl_F10_1", "vl_F10_2"]
over = {}
for n in stage:
    P = sample(read_stl(n), 0.3)
    r = np.hypot(P[:, 0], P[:, 1])
    m = r > 26.5
    over[n] = dict(r_max=round(float(r.max()), 3), z=(round(float(P[:, 2].min()), 2), round(float(P[:, 2].max()), 2)),
                   over_26_5=bool(m.any()),
                   over_zone=(bbox(P[m]) if m.any() else None))
    say(n, over[n])
res["stage_parts"] = over

# P_sachta in detail: radius profile and where the material beyond 26.5 is (corners / journal / fin)
P = sample(read_stl("P_sachta"), 0.25)
res["P_sachta_rprof"] = rprof(P, -42.5, -1.5, 1.0)
r = np.hypot(P[:, 0], P[:, 1]); az = np.degrees(np.arctan2(P[:, 1], P[:, 0])) % 360
m = r > 26.5
hist = {}
for a0 in range(0, 360, 10):
    s = m & (az >= a0) & (az < a0 + 10)
    if s.any():
        hist[a0] = dict(n=int(s.sum()), z=(round(float(P[s, 2].min()), 1), round(float(P[s, 2].max()), 1)),
                        r_max=round(float(r[s].max()), 2))
res["P_sachta_over_26_5_by_az"] = hist

# ---- 3. well inner corner: inner extreme radius (rays toward the corner directions) -------------------------------
# the well interior is the region |x|<23.5, |y|<11 ; measure the material nearest to the axis along the corner diagonals
zs = np.arange(-38, -4, 2.0)
corner = []
for z in zs:
    s = (np.abs(P[:, 2] - z) < 0.3)
    Q = P[s]
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        q = Q[(Q[:, 0] * sx > 18) & (Q[:, 1] * sy > 6)]
        if len(q) == 0:
            continue
        rq = np.hypot(q[:, 0], q[:, 1])
        corner.append((float(z), sx, sy, round(float(rq.min()), 3), round(float(rq.max()), 3)))
res["well_corner_r_in_out"] = corner[:12]

# ---- 4. finished neck: corner radius of the 45 x 20 blade -------------------------------------------------------
for n in ("krk_predna_polovica", "krk_zadna_polovica"):
    P = sample(read_stl(n), 0.2)
    res[n + "_bbox"] = bbox(P)
Pn = np.concatenate([sample(read_stl(n), 0.2) for n in ("krk_predna_polovica", "krk_zadna_polovica")])
rows = []
for z in (-36.0, -34.0, -30.0, -20.0, -10.0, 0.0, 3.0):
    s = np.abs(Pn[:, 2] - z) < 0.15
    Q = Pn[s]
    if len(Q) == 0:
        continue
    xmax, ymax = np.abs(Q[:, 0]).max(), np.abs(Q[:, 1]).max()
    rmax = np.hypot(Q[:, 0], Q[:, 1]).max()
    # corner radius c from r_max = |(X-c, Y-c)| + c
    X, Y = xmax, ymax
    lo, hi = 0.0, min(X, Y)
    for _ in range(60):
        c = 0.5 * (lo + hi)
        if math.hypot(X - c, Y - c) + c > rmax:
            lo = c
        else:
            hi = c
    rows.append(dict(z=z, half_x=round(float(xmax), 3), half_y=round(float(ymax), 3), r_max=round(float(rmax), 3),
                     corner_r=round(c, 2)))
    say("neck", rows[-1])
res["neck_section"] = rows


# ---- 5. well corner wall if the stage is trimmed to r 26.5 (analytic, inner corner radius ci) --------------------
def corner_wall(ci, hx=23.5, hy=11.0, rt=26.5):
    cx, cy = hx - ci, hy - ci
    return rt - (math.hypot(cx, cy) + ci)


def neck_clear(ci, c_neck, nx=22.5, ny=10.0, hx=23.5, hy=11.0):
    """clearance between a neck corner (radius c_neck) and the well inner corner (radius ci) along the diagonal"""
    d = math.hypot((hx - ci) - (nx - c_neck), (hy - ci) - (ny - c_neck))
    return ci - (d + c_neck)


cn = min(r["corner_r"] for r in rows if r["z"] <= 0) if rows else 0.0
res["trim_26_5"] = [dict(inner_corner_r=ci, wall_at_corner=round(corner_wall(ci), 3),
                         neck_corner_clearance=round(neck_clear(ci, cn), 3)) for ci in (1.5, 2.0, 2.5, 3.0, 3.5)]
res["neck_corner_r_used"] = cn
say("trim", res["trim_26_5"])

# ---- 6. T_stred: bore radius and collar-tube outer radius per z (material within r < 33) ------------------------
P = sample(read_stl("T_stred"), 0.3)
r = np.hypot(P[:, 0], P[:, 1])
rows = []
for z in np.arange(-12.0, 4.01, 0.5):
    s = (P[:, 2] >= z) & (P[:, 2] < z + 0.5) & (r < 33.5)
    if s.any():
        rr = r[s]
        rows.append((round(float(z), 1), round(float(rr.min()), 3), round(float(np.percentile(rr, 99)), 3)))
res["T_stred_bore_by_z(z, r_min, r_p99_within_33.5)"] = rows
dump("m01_stage_radius.json", res)

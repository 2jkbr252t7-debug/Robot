"""R4/tvar (copy of R3/tvar/chk_variants.py, same gap method, imports variants_b; "outside" is measured against B0): numeric checks of the slim arm variants (CAD venv: numpy + scipy).  Writes chk_variants.json.
 1. variant 0 == approved pebble (rows, world placement, inside test) - max deviation
 2. thickness / width along the arm, inner / outer half at the joint (u 0.22)
 3. innermost world x of the arm at rest, robot width over both arms (front view)
 4. how far each variant leaves the approved pebble (+ = outside), and where
 5. arm - torso gap at rest and over the swing (torso model = armgap_top.py 'rec1': approved torso exterior, socket cap
    edge r 14 about the shoulder axis, plug face r <= 13.5 recessed 1.0) - same method as armgap_top.py (KD on a dense
    arm surface cloud, sign from the analytic inside test), angles -51 .. 142 deg
usage: chk_variants.py [vids]"""
import sys, os, json, time, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import variants_b as VA
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v1/work")
import v1geo as V1
sys.path.insert(0, "/home/user/Robot/obrazky/postupne/07_ruky/zdroj/geometria")
import armgeo as AG
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import t4_common as C

t0 = time.time()
vids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(VA.VIDS)
OUT = {}

# ---------------------------------------------------------------- approved pebble SDF (for the 'leaves the old pebble' check)
def sdf_factory(vid, h=0.15, dmax=8.0, hc=0.6):
    """signed distance to the arm surface (local frame), as armgeo.sdf_local (fine cloud h 0.15, sign from the analytic
    inside test); two-stage: a coarse cloud (hc) finds the candidates, the fine cloud is queried only for those.
    Exact for the MINIMUM over a point set (sdf_min); sdf() returns per-point values (fine query for all)."""
    rows, top, bot = VA.pebble_rows(vid, int(2.2 * VA.L / h), int(2 * math.pi * 17.5 / h))
    tree = cKDTree(np.concatenate([rows.reshape(-1, 3), [top, bot]]))
    rc, _, _ = VA.pebble_rows(vid, int(2.2 * VA.L / hc), int(2 * math.pi * 17.5 / hc))
    ctree = cKDTree(np.concatenate([rc.reshape(-1, 3), [top, bot]]))
    dc_err = 1.5 * hc            # generous bound of (coarse cloud distance - true distance)

    def sdf(P):
        d, _ = tree.query(np.atleast_2d(P), distance_upper_bound=dmax)
        d = np.minimum(d, dmax)
        return np.where(VA.inside_local(vid, P), -d, d)

    def sdf_min(P):
        P = np.atleast_2d(P)
        ins = VA.inside_local(vid, P)
        if ins.any():
            k = np.nonzero(ins)[0]
            d = -tree.query(P[k], distance_upper_bound=dmax)[0]
            j = int(np.argmin(d)); return float(max(d[j], -dmax)), int(k[j])
        dc, _ = ctree.query(P, distance_upper_bound=dmax + 2 * dc_err)
        m0 = dc.min()
        if not np.isfinite(m0):
            return dmax, 0
        k = np.nonzero(dc <= m0 + dc_err)[0]
        d, _ = tree.query(P[k], distance_upper_bound=dmax)
        j = int(np.argmin(d)); return float(min(d[j], dmax)), int(k[j])
    sdf.min = sdf_min
    return sdf


sdf0 = sdf_factory("B0")          # R4: "outside" = outside arm B (not the T3 pebble)

# ---------------------------------------------------------------- torso model (= armgap_top.py, rec1)
hs = 0.2
ys = np.arange(-34.0, 36.0, hs); zs = np.arange(-80.0, 3.9, hs)
Y, Z = np.meshgrid(ys, zs, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
X = np.array([C.x_surface(y, z) for y, z in zip(Y, Z)])
ok = np.isfinite(X) & (X > 38.0)
S0 = np.c_[X[ok], Y[ok], Z[ok]]
ra = np.hypot(S0[:, 1] - 3.0, S0[:, 2] + 17.0)
th = np.linspace(0, 2 * np.pi, 600, endpoint=False)
rim = np.c_[np.zeros_like(th), 3.0 + 14.0 * np.cos(th), -17.0 + 14.0 * np.sin(th)]
rim[:, 0] = [C.x_surface(y, z) for y, z in rim[:, 1:]]
disc = S0[ra <= 13.5].copy(); disc[:, 0] -= 1.0
TOR = np.r_[S0[ra >= 14.0], rim, disc]
print("torso samples", len(TOR), f"{time.time() - t0:.0f}s", flush=True)
ANG = np.r_[np.arange(-51.0, 130.0, 1.0), np.arange(130.0, 142.01, 0.5)]
ANG = np.unique(np.r_[0.0, ANG])

for vid in vids:
    R = {}
    us = np.linspace(0, 1, 2001)
    c, ti, to, w, _, _ = VA.section(vid, us)
    T = ti + to
    k = int(T.argmax()); kw_ = int(w.argmax())
    c22, ti22, to22, w22, _, _ = VA.section(vid, 0.22)
    hw0, ht0 = VA._base(0.22)
    R["thickness_max"] = round(float(T.max()), 2); R["thickness_max_at_u"] = round(float(us[k]), 3)
    R["width_max"] = round(float(2 * w.max()), 2); R["width_max_at_u"] = round(float(us[kw_]), 3)
    R["thickness_at_joint_u022"] = round(float(ti22 + to22), 2)
    R["inner_half_at_joint"] = round(float(ti22), 2); R["outer_half_at_joint"] = round(float(to22), 2)
    R["seam_x_local_at_joint"] = round(float(c22), 2)
    R["inner_face_x_local_at_joint"] = round(float(c22 - ti22), 3); R["B0_inner_face_x_local"] = round(-float(ht0), 3)
    R["table"] = [dict(u=round(float(u), 2), thick=round(float(VA.thickness(vid, u)), 2), width=round(float(2 * VA.profile(vid, u)[0]), 2),
                       seam_x=round(float(VA.seam_x(vid, u)), 2), inner_face_x=round(float(VA.faces(vid, u)[0]), 2))
                  for u in (0.05, 0.1, 0.22, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95)]
    rows, top, bot = VA.pebble_rows(vid, 500, 720)
    P = np.concatenate([rows.reshape(-1, 3), [top, bot]])
    W = VA.to_world(P, vid)
    i = int(W[:, 0].argmin()); j = int(W[:, 0].argmax())
    R["innermost_world_x"] = round(float(W[i, 0]), 3); R["innermost_at_local"] = P[i].round(2).tolist(); R["innermost_u"] = round(float(-P[i, 2] / VA.L), 3)
    R["outermost_world_x"] = round(float(W[j, 0]), 3)
    R["robot_width_over_arms"] = round(float(2 * W[j, 0]), 2)
    # left the approved pebble?
    d0 = sdf0(P)
    out_m = ~VA.inside_local("B0", P, -0.03)          # analytic: outside the approved pebble by more than ~0.03
    R["max_outside_approved_mm"] = round(float(d0[out_m].max()), 3) if out_m.any() else 0.0
    if out_m.any():
        uu = -P[out_m, 2] / VA.L
        R["outside_u_range"] = [round(float(uu.min()), 3), round(float(uu.max()), 3)]
        R["outside_world_x_min"] = round(float(W[out_m, 0].min()), 2)
        for lo, hi in ((0.0, 0.04), (0.04, 0.5), (0.5, 1.0)):
            m = (uu >= lo) & (uu < hi)
            R[f"max_outside_u{lo}-{hi}"] = round(float(d0[out_m][m].max()), 3) if m.any() else 0.0
    # front-view gap (silhouettes, like nums.py) at the shoulder axis height
    m = np.abs(W[:, 2] + 17.0) < 0.3
    yy = np.linspace(-34, 34, 681)
    xt = max(C.x_surface(y, -17.0) for y in yy)
    R["front_view_gap_at_axis"] = round(float(W[m, 0].min() - xt), 2)
    # axis skins (shoulder axis line) and inner room
    xs = np.linspace(40, 100, 6001)
    for inset, key in ((0.0, "axis_skin_x"), (1.2, "axis_inside_wall1.2_x"), (1.6, "axis_inside_wall1.6_x")):
        L_ = np.c_[xs, np.full_like(xs, 3.0), np.full_like(xs, -17.0)]
        ins = VA.inside_local(vid, VA.to_local(L_), inset)
        R[key] = [round(float(xs[ins].min()), 2), round(float(xs[ins].max()), 2)] if ins.any() else None
    # gap over the swing
    sdf = sdf_factory(vid)
    per = []
    Wc = VA.to_world(VA.pebble_cloud(vid, 1.0), vid)
    for a in ANG:
        Ws = VA.swing(Wc, a)
        lo, hi = Ws.min(0) - 9.0, Ws.max(0) + 9.0
        m = np.all((TOR >= lo) & (TOR <= hi), axis=1)          # torso points that can be within dmax of the swung arm
        if not m.any():
            per.append((float(a), 8.0, None)); continue
        Tm = TOR[m]
        dmin, kk = sdf.min(VA.to_local(VA.swing(Tm, -a)))
        per.append((float(a), dmin, Tm[kk].round(2).tolist()))
    pa = np.array([p[1] for p in per]); aa = np.array([p[0] for p in per])
    rng_m = (aa >= -45) & (aa <= 135)
    k2 = int(np.argmin(np.where(rng_m, pa, 1e9)))
    R["gap_rest"] = round(float(pa[aa == 0][0]), 3); R["gap_rest_at"] = per[int(np.nonzero(aa == 0)[0][0])][2]
    R["gap_min_-45_135"] = round(float(pa[k2]), 3); R["gap_min_angle"] = float(aa[k2]); R["gap_min_at"] = per[k2][2]
    R["gap_at_135"] = round(float(pa[aa == 135][0]), 3)
    R["gap_at_140.5"] = round(float(pa[aa == 140.5][0]), 3)
    R["gap_min_-51_142"] = round(float(pa.min()), 3); R["gap_min_-51_142_angle"] = float(aa[int(pa.argmin())])
    R["gap_per_10deg"] = {str(int(a)): round(float(v), 2) for a, v in zip(aa, pa) if abs(a % 10) < 1e-9}
    OUT[vid] = R
    print(vid, json.dumps({k: v for k, v in R.items() if k not in ("table", "gap_per_10deg")}), f"{time.time() - t0:.0f}s", flush=True)

json.dump(OUT, open(os.path.join(HERE, "out", "chk_%s.json" % "_".join(vids)), "w"), indent=1)
print("done", f"{time.time() - t0:.0f}s")

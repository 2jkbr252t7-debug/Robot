"""R4/klb: clearance checks of the shoulder-joint variants (CAD venv: numpy + scipy).  Writes chk_klb.json.
For every variant (left side, frame B):
 A  rotating joint parts (collar / ring, solids of revolution about the swing axis) vs every static surface near the
    shoulder (T_bok_L mesh, the variant's plug mesh incl. screws): POSE-INDEPENDENT -> exact 2-D (x, r) distance of the
    static surface samples to the part's (x, r) profile
 B  arm B shell vs the static plug / cover: the static cover is a solid of revolution -> pose-independent (x, r) distance
    of the arm surface samples (outside the arm's opening) to the cover profile; plus a full swing sweep -51..142 deg of
    the arm (analytic shape, opening in the inner half modelled as max(d_arm, hole_r - r)) against T_bok_L + plug + screws
 C  rotating parts vs the M2b joint envelope (R3/mech parts.py option M2b), exact (x, r) polygon distances
 D  numbers for the look: visible black length per azimuth (top / front / bottom / back) and visible diameter
usage: chk_klb.py [K0,K1,...]"""
import sys, os, json, math, time
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "work"))
import numpy as np
from scipy.spatial import cKDTree
import klb as K
import stlu
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/mech")
import parts as MP
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C

t0 = time.time()
YA, ZA = K.YA, K.ZA
VID_ARM = "B"
vids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(K.VIDS)
OUT = {}


def az_of(P):
    return np.degrees(np.arctan2(P[:, 2] - ZA, P[:, 1] - YA)) % 360.0


def where(P):
    P = np.asarray(P, float)
    return dict(xyz=P.round(2).tolist(), r=round(float(np.hypot(P[1] - YA, P[2] - ZA)), 2),
                az=round(float(np.degrees(np.arctan2(P[2] - ZA, P[1] - YA)) % 360), 1))


# ------------------------------------------------------------------ static surfaces
TB = stlu.load("/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod/T_bok_L.stl")
def near(P, rmax=30.0):
    r_ = np.hypot(P[:, 1] - YA, P[:, 2] - ZA)
    return P[(r_ < rmax) & (P[:, 0] > 36.0)]


STB_F = near(stlu.sample(TB, 0.12))           # fine (local refinement)
STB = near(stlu.sample(TB, 0.3))              # coarse (sweep)
print("T_bok_L samples", len(STB), f"{time.time() - t0:.0f}s", flush=True)


def static_samples(vid, fine=False, drop_ring=False):
    v = K.variant(vid)
    S = {"T_bok_L": STB_F if fine else STB}
    for p in v["parts"]:
        if p["role"] == "static":
            Q = near(stlu.sample(stlu.load(p["stl"]), 0.1 if fine else 0.3))
            if drop_ring:          # plug ring r <= 6.5 enters the arm opening by design (M2b fit) -> not an arm-torso gap
                Q = Q[np.hypot(Q[:, 1] - YA, Q[:, 2] - ZA) > 6.6]
            S[p["id"]] = Q
    return S


# ------------------------------------------------------------------ arm B (analytic) surface cloud + sdf
def arm_cloud(dx, h=0.15):
    rows, top, bot = VA.pebble_rows(VID_ARM, int(2.2 * VA.L / h), int(2 * math.pi * 17.5 / h))
    Pl = np.concatenate([rows.reshape(-1, 3), [top, bot]])
    return Pl, VA.to_world(Pl, VID_ARM, dx)


ARM_L, ARM_W0 = arm_cloud(K.DX0)
ARM_TREE = cKDTree(ARM_L, balanced_tree=False, compact_nodes=False)
ARM_LC, _ = arm_cloud(K.DX0, 0.5)
ARM_TREE_C = cKDTree(ARM_LC, balanced_tree=False, compact_nodes=False)
print("arm samples", len(ARM_L), f"{time.time() - t0:.0f}s", flush=True)


def arm_sdf_min(Pw, dx, hole_r):
    """min over static world points Pw of the distance to the (holed) arm at its rest pose for shift dx (Pw already
    rotated back by the swing); returns (d, index)"""
    Pl = VA.to_local(Pw, VID_ARM, dx)
    d, _ = ARM_TREE_C.query(Pl, distance_upper_bound=8.0, workers=2)      # coarse (h 0.5): overestimates by <= ~0.35
    d = np.minimum(d, 8.0)
    cand = d <= d.min() + 0.8
    if cand.any():
        df, _ = ARM_TREE.query(Pl[cand], distance_upper_bound=8.0, workers=2)
        d[cand] = np.minimum(df, 8.0)
    ins = VA.inside_local(VID_ARM, Pl)
    if ins.any():                                                          # penetration depth (fine) for inside points
        df, _ = ARM_TREE.query(Pl[ins], distance_upper_bound=8.0, workers=2)
        d[ins] = np.minimum(df, 8.0)
    d = np.where(ins, -d, d)
    # opening in the inner half: points inside the opening cylinder on the inner side are at least hole_r - r away
    r = np.hypot(Pw[:, 1] - YA, Pw[:, 2] - ZA)
    inner = Pl[:, 0] < VA.seam_x(VID_ARM, np.clip(-Pl[:, 2] / VA.L, 0, 1))
    m = inner & (r < hole_r)
    d = np.where(m, np.maximum(d, hole_r - r), d)
    k = int(np.argmin(d))
    return float(d[k]), k


def hole_r_of(vid):
    return K.VARIANTS[vid].get("arm_hole_r", 7.0)


# ------------------------------------------------------------------ M2b envelope (x, r outlines)
M2B = MP.options()["M2b"]["parts"]


def m2b_outlines(shift):
    out = []
    for p in M2B:
        P = np.array(p.outline_xr(), float).copy()
        P[:, 0] += shift
        out.append((p.name, p.role, p.kind, P))
    return out


def poly_poly(A, B, h=0.05):
    """signed min distance between two (x, r) polygons (negative = overlap depth estimate)"""
    def dens(P):
        pts = []
        for i in range(len(P)):
            p, q = P[i], P[(i + 1) % len(P)]
            n = max(2, int(math.ceil(np.hypot(*(q - p)) / h)))
            t = np.linspace(0, 1, n, endpoint=False)
            pts.append(p + t[:, None] * (q - p))
        return np.concatenate(pts)
    da = K.poly_dist(dens(A), B); db = K.poly_dist(dens(B), A)
    return float(min(da.min(), db.min()))


ANG = np.unique(np.r_[np.arange(-51.0, 130.0, 3.0), np.arange(130.0, 142.01, 1.0), 0.0, -45.0, 135.0, 140.5])

for vid in vids:
    v = K.variant(vid)
    dx = K.arm_dx(vid)
    sh = dx - K.DX0
    R = dict(name=v["name_sk"], dx=dx, visible_d=v["visible_d"])
    S = static_samples(vid, drop_ring=True)
    SF = static_samples(vid, True)
    SFR = static_samples(vid, True, drop_ring=True)
    rot = [p for p in K.VARIANTS[vid]["parts"] if p["role"] == "rotating"]
    # ---------------- A: rotating parts vs static (pose-independent)
    for p in rot:
        prof = p["profile"]()
        res = {}
        r_in_p = float(prof[:, 1].min())
        for nm, Ss in SF.items():
            Ss = near(Ss, 20.0)
            Ss = Ss[Ss[:, 0] > float(prof[:, 0].min()) - 3.0]
            d = K.poly_dist(K.to_xr(Ss), prof)
            k = int(np.argmin(d))
            res[nm] = dict(min=round(float(d[k]), 3), at=where(Ss[k]))
            # outside the bore zone (static points at r > r_in + 1): the gaps one can see
            rs = np.hypot(Ss[:, 1] - YA, Ss[:, 2] - ZA)
            mo = rs > r_in_p + 1.0
            if mo.any():
                ko = int(np.argmin(np.where(mo, d, 1e9)))
                res[nm]["min_outside_bore"] = round(float(d[ko]), 3)
                res[nm]["at_outside_bore"] = where(Ss[ko])
        R["A_" + p["id"]] = res
        print(vid, "A", p["id"], {k: (v_["min"], v_.get("min_outside_bore")) for k, v_ in res.items()}, flush=True)
    # ---------------- B1: arm vs static solids of revolution (cover) -> pose-independent
    hr = hole_r_of(vid)
    Wl = ARM_W0 + np.array([sh, 0, 0])
    rA = np.hypot(Wl[:, 1] - YA, Wl[:, 2] - ZA)
    inner = ARM_L[:, 0] < VA.seam_x(VID_ARM, np.clip(-ARM_L[:, 2] / VA.L, 0, 1))
    keep = ~(inner & (rA < hr))
    Wk = Wl[keep]
    cov = [p for p in K.VARIANTS[vid]["parts"] if p["role"] == "static" and "profile" in p]
    for p in cov:
        prof = p["profile"]()
        d = K.poly_dist(K.to_xr(Wk), prof)
        k = int(np.argmin(d))
        R["B_arm_vs_" + p["id"] + "_pose_independent"] = dict(min=round(float(d[k]), 3), at=where(Wk[k]))
        print(vid, "B1 arm vs cover", round(float(d[k]), 3), where(Wk[k]), flush=True)
    # rotating part vs the cover (both solids of revolution)
    for p in rot:
        for q in cov:
            R[f"A_{p['id']}_vs_{q['id']}_profile"] = round(poly_poly(p["profile"](), q["profile"]()), 3)
    # ---------------- B2: swing sweep of the (holed) arm vs T_bok_L + plug + screws
    per = []
    Wc = Wl[::4]
    for a in ANG:
        Ws = VA.swing(Wc, a)
        lo, hi = Ws.min(0) - 4.0, Ws.max(0) + 4.0
        best = (12.0, None, None)
        for nm, Ss in S.items():
            m = np.all((Ss >= lo) & (Ss <= hi), axis=1)
            if not m.any():
                continue
            Sm = Ss[m]
            dmin, kk = arm_sdf_min(VA.swing(Sm, -a), dx, hr)
            if dmin < best[0]:
                best = (dmin, nm, Sm[kk])
        per.append((float(a), best[0], best[1], None if best[2] is None else where(best[2])))
    # refine the key angles with the fine static samples within 4 mm of the coarse minimum point
    def refine(a, coarse):
        d_, nm_, w_ = coarse
        if w_ is None:
            return coarse
        c_ = np.array(w_["xyz"])
        best_ = (d_, nm_, w_)
        for nm2, Ss in SFR.items():
            m = np.all(np.abs(Ss - c_) < 4.0, axis=1)
            if not m.any():
                continue
            dd, kk = arm_sdf_min(VA.swing(Ss[m], -a), dx, hr)
            if dd < best_[0]:
                best_ = (dd, nm2, where(Ss[m][kk]))
        return best_
    for i, (a, d_, nm_, w_) in enumerate(per):
        if a in (0.0, -45.0, 135.0, 140.5) or d_ < 1.6:
            per[i] = (a,) + tuple(refine(a, (d_, nm_, w_)))
    pa = np.array([q[1] for q in per]); aa = np.array([q[0] for q in per])
    rngm = (aa >= -45) & (aa <= 135)
    k2 = int(np.argmin(np.where(rngm, pa, 1e9)))
    k0 = int(np.nonzero(aa == 0)[0][0])
    R["B_sweep"] = dict(rest=round(float(pa[k0]), 3), rest_part=per[k0][2], rest_at=per[k0][3],
                        min_m45_135=round(float(pa[k2]), 3), min_angle=float(aa[k2]), min_part=per[k2][2], min_at=per[k2][3],
                        at_135=round(float(pa[aa == 135][0]), 3), at_140_5=round(float(pa[aa == 140.5][0]), 3),
                        per_10deg={str(int(a)): round(float(d), 2) for a, d in zip(aa, pa) if abs(a % 10) < 1e-9})
    # white-only (arm vs T_bok_L only) for the comparison with R3 (3.70 / 1.125 / 0.97)
    perw = []
    for a in (0.0, 135.0, 140.5):
        Ws = VA.swing(Wc, a)
        lo, hi = Ws.min(0) - 4.0, Ws.max(0) + 4.0
        m = np.all((STB_F >= lo) & (STB_F <= hi), axis=1)
        dmin, kk = arm_sdf_min(VA.swing(STB_F[m], -a), dx, hr)
        perw.append(round(dmin, 3))
    R["B_sweep_white_T_bok_L_only"] = dict(rest=perw[0], at_135=perw[1], at_140_5=perw[2])
    print(vid, "B2 sweep", {k: R["B_sweep"][k] for k in ("rest", "rest_part", "min_m45_135", "min_angle", "min_part", "at_140_5")},
          "white", R["B_sweep_white_T_bok_L_only"], f"{time.time() - t0:.0f}s", flush=True)
    # ---------------- C: rotating parts vs the M2b envelope
    for p in rot:
        prof = p["profile"]()
        rows = []
        for nm, role, kind, P in m2b_outlines(sh):
            d = poly_poly(prof, P)
            need = 0.3 if role in ("static", "drive", "torso") else 0.0
            rows.append(dict(part=nm, role=role, kind=kind, dist=round(d, 3), need=need, ok=bool(d >= need - 1e-6)))
        R["C_" + p["id"] + "_vs_M2b"] = rows
        print(vid, "C", p["id"], [(r_["part"], r_["dist"]) for r_ in rows if r_["dist"] < 1.0], flush=True)
    # inside the arm: the hidden back of the part must stay inside the arm (local inset 0 at the visible cylinder)
    for p in rot:
        prof = p["profile"]()
        xb = float(prof[:, 0].max()); ro = float(prof[:, 1].max())
        th = np.radians(np.arange(0, 360, 2.0))
        Q = np.c_[np.full_like(th, xb), YA + ro * np.cos(th), ZA + ro * np.sin(th)]
        Ql = VA.to_local(Q - np.array([sh, 0, 0]) + 0.0, VID_ARM, K.DX0)
        ins = VA.inside_local(VID_ARM, Ql)
        # depth of the back rim below the arm's inner face (x of the inner face along +x at that (y, z))
        xs = np.arange(44.0, 70.0, 0.02)
        depth = []
        for q in Q:
            L_ = np.c_[xs, np.full_like(xs, q[1]), np.full_like(xs, q[2])]
            insl = VA.inside_local(VID_ARM, VA.to_local(L_, VID_ARM, dx))
            depth.append(q[0] - xs[insl].min() if insl.any() else -99)
        depth = np.array(depth)
        R["C_" + p["id"] + "_back_rim_depth_in_arm"] = dict(min=round(float(depth.min()), 3), at_az=float(np.degrees(th[int(depth.argmin())])),
                                                            all_inside=bool(ins.all()))
    # ---------------- D: look numbers - visible black length at the outer radius of the visible part per azimuth
    xs = np.arange(40.0, 70.0, 0.02)

    def arm_face(y, z):
        L_ = np.c_[xs, np.full_like(xs, y), np.full_like(xs, z)]
        ins = VA.inside_local(VID_ARM, VA.to_local(L_, VID_ARM, dx))
        return float(xs[ins].min()) if ins.any() else float("nan")
    look = {}
    if vid == "K0":
        rv, start = 6.5, "plug"
    elif vid == "K1":
        rv, start = K.K1["r_out"], "collar"
    else:
        rv, start = K.COVER["r"], "cover"
    for nm, a in (("hore", 90), ("vpredu", 180), ("dole", 270), ("vzadu", 0)):
        t = math.radians(a)
        y, z = YA + rv * math.cos(t), ZA + rv * math.sin(t)
        yt, zt = YA + K.SOCKET_R * math.cos(t), ZA + K.SOCKET_R * math.sin(t)
        x_t = C.x_surface(yt, zt)                       # torso surface at the socket rim
        x_arm = arm_face(y, z)
        if start == "plug":
            x0 = C.x_surface(y, z) - 1.0
        elif start == "collar":
            x0 = max(K.K1["x_end"], min(x_t, x_arm))
        else:
            x0 = min(x_t, K.COVER["x_end"] + sh)
        look[nm] = dict(torso_rim_x=round(x_t, 2), black_from_x=round(x0, 2), arm_face_x=round(x_arm, 2),
                        black_visible_mm=round(max(0.0, x_arm - max(x0, x_t if start != "plug" else x0)), 2),
                        black_total_mm=round(x_arm - x0, 2))
    R["D_look_at_r"] = rv
    R["D_look"] = look
    print(vid, "D", {k: (v_["black_visible_mm"], v_["black_total_mm"]) for k, v_ in look.items()}, flush=True)
    OUT[vid] = R

p = os.path.join(HERE, "chk_klb.json")
old = json.load(open(p)) if os.path.exists(p) else {}
old.update(OUT)
json.dump(old, open(p, "w"), indent=1)
print("done", f"{time.time() - t0:.0f}s")

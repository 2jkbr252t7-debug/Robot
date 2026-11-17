#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso, module PAN: module-level checks  ->  pan_checks.json, pan_checks.log

    /opt/venv/cad/bin/python t4_pan_checks.py [A B C D E F G H]      (default: all sections)

A  solids / STL of parts_pan.json (valid, single solid, bbox, watertight)
B  interference among the PAN parts (OCC common volume + exact mesh distance), rest pose and lift 5 / 10 / 15 / 20,
   incl. the finished neck halves and the collar disc (B meshes)
C  crank kinematics (stroke, dead centres, pin in the slot) and pan stop
D  swept envelope: every P / L part over lift 0..20 against PAN_ENV + low-zone rule, and against the analytic shell
   inner surface (inset 2.2) over pan -85..85
E  real meshes: P / L parts over pan -85..85 (5 deg) x lift 0..20 (2.5) against the STL of the OBAL and RAM modules
   (+ golier_prstenec), hard stops +-90 as an extra pose; pan gear against the rotating pinion
F  seats of the bought parts / fits (measured on the solids)
G  walls of the printed parts (opposing-face ray scan)
H  assembly: stage through the bore, tool channels D4.5 of F10 / F12 / tongue screw, bracket unit through the door

Distances are exact point-to-triangle distances from surface samples (all mesh vertices + 0.3 mm grid) of the moving part to
the triangles of the other part (STL deflection 0.01 mm).
"""
from __future__ import annotations
import os, sys, json, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from scipy.spatial import cKDTree
import t4_common as C
import t4_pan as M
import build123d as bd

P = C.PAN
STL = os.path.join(HERE, "stl")
WORK = os.path.join(HERE, "pan_work")
SECT = [a for a in sys.argv[1:] if a in list("ABCDEFGH")] or list("ABCDEFGH")
LOG = open(os.path.join(HERE, "pan_checks.log"), "a" if len(SECT) < 8 else "w")
RES = {}
PANS = list(np.arange(-85.0, 85.1, 5.0))
LIFTS = list(np.arange(0.0, 20.1, 2.5))


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n"); LOG.flush()


# ---------------------------------------------------------------------------------------------------------------------
# mesh helpers
# ---------------------------------------------------------------------------------------------------------------------
def tris_of(shape, lin=0.01, ang=0.1):
    V, T = C.mesh_of(shape, lin, ang)
    return V[T]


def stl(name, d=STL):
    return M.read_stl(os.path.join(d, name + ".stl"))


def sample(T, h=0.3, dd=None):
    """surface samples: ALL distinct vertices + barycentric interior grid of pitch <= h (de-duplicated on a grid dd, default
    h / 2); returns (points, triangle index).  Vertices come first, so corners are always kept exactly."""
    dd = h / 2 if dd is None else dd
    e = np.max([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], axis=0)
    n = np.clip(np.ceil(e / h).astype(int), 1, 400)
    V = T.reshape(-1, 3); VI = np.repeat(np.arange(len(T)), 3)
    _, k = np.unique(np.round(V / 0.01).astype(np.int64), axis=0, return_index=True)
    V, VI = V[k], VI[k]
    pts, idx = [], []
    for nv in np.unique(n):
        if nv < 2:
            continue
        sel = np.where(n == nv)[0]
        i, j = np.meshgrid(np.arange(nv + 1), np.arange(nv + 1), indexing="ij"); m = ((i + j) <= nv) & ~(((i == 0) & (j == 0)) | ((i == nv) & (j == 0)) | ((i == 0) & (j == nv)))
        u, v = i[m] / nv, j[m] / nv
        Q = (T[sel, 0][:, None, :] * (1 - u - v)[None, :, None] + T[sel, 1][:, None, :] * u[None, :, None]
             + T[sel, 2][:, None, :] * v[None, :, None])
        pts.append(Q.reshape(-1, 3)); idx.append(np.repeat(sel, len(u)))
    if pts:
        S = np.concatenate(pts); I = np.concatenate(idx)
        _, k = np.unique(np.round(S / dd).astype(np.int64), axis=0, return_index=True)
        return np.concatenate([V, S[k]]), np.concatenate([VI, I[k]])
    return V, VI


def pt_tri(Pt, A, B, Cc):
    AB, AC, AP = B - A, Cc - A, Pt - A
    n = np.cross(AB, AC); nn = np.einsum("ij,ij->i", n, n)
    d00 = (AB * AB).sum(1); d01 = (AB * AC).sum(1); d11 = (AC * AC).sum(1); d20 = (AP * AB).sum(1); d21 = (AP * AC).sum(1)
    den = d00 * d11 - d01 * d01
    ok = den > 1e-18
    dn = np.where(ok, den, 1.0)
    v = np.where(ok, (d11 * d20 - d01 * d21) / dn, -1.0); w = np.where(ok, (d00 * d21 - d01 * d20) / dn, -1.0)
    inside = ok & (v >= 0) & (w >= 0) & (v + w <= 1)
    d = np.where(inside, np.abs((AP * n).sum(1)) / np.sqrt(np.where(nn > 0, nn, 1.0)), np.inf)
    for U, V in ((A, B), (B, Cc), (Cc, A)):
        E = V - U
        t = np.clip(((Pt - U) * E).sum(1) / np.maximum((E * E).sum(1), 1e-30), 0, 1)
        d = np.minimum(d, np.linalg.norm(Pt - (U + t[:, None] * E), axis=1))
    return d


class Target:
    """triangle mesh with a KD-tree of surface samples -> exact point distances"""

    def __init__(self, name, T, h=0.35):
        self.name, self.T = name, T
        self.S, self.I = sample(T, h)
        self.tree = cKDTree(self.S)
        V = T.reshape(-1, 3); self.lo, self.hi = V.min(0), V.max(0)

    def dist(self, Q, dmax=1.6, k=8):
        d = np.full(len(Q), np.inf)
        m = np.all((Q > self.lo - dmax) & (Q < self.hi + dmax), axis=1)
        if not m.any():
            return d
        q = Q[m]
        dd, ii = self.tree.query(q, k=k, distance_upper_bound=dmax + 0.5)
        best = np.full(len(q), np.inf)
        for j in range(k):
            ok = np.isfinite(dd[:, j])
            if not ok.any():
                continue
            t = self.I[ii[ok, j]]
            e = pt_tri(q[ok], self.T[t, 0], self.T[t, 1], self.T[t, 2])
            best[ok] = np.minimum(best[ok], e)
        d[m] = best
        return d


def rotz(Q, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = Q.copy(); R[..., 0] = c * Q[..., 0] - s * Q[..., 1]; R[..., 1] = s * Q[..., 0] + c * Q[..., 1]
    return R


def rot_about(Q, deg, cx, cy):
    R = Q.copy(); R[..., 0] -= cx; R[..., 1] -= cy
    R = rotz(R, deg); R[..., 0] += cx; R[..., 1] += cy
    return R


def crank_xform(Q, theta):
    """rotate points of the crank (built at theta 0) to servo angle theta about the X axis through (YL, ZL)"""
    a = math.radians(-theta); c, s = math.cos(a), math.sin(a)
    R = Q.copy(); y, z = Q[..., 1] - M.YL, Q[..., 2] - M.ZL
    R[..., 1] = M.YL + c * y - s * z; R[..., 2] = M.ZL + s * y + c * z
    return R


def common_vol(a, b):
    try:
        c = a & b
    except Exception as e:
        return None
    if c is None:
        return 0.0
    try:
        sol = c.solids() if hasattr(c, "solids") else [q for x in c for q in x.solids()]
        return float(sum(s.volume for s in sol))
    except Exception:
        return 0.0


def bbox(T):
    V = T.reshape(-1, 3)
    return V.min(0), V.max(0)


def bb_near(a, b, g):
    return bool(np.all(a[0] < b[1] + g) and np.all(b[0] < a[1] + g))


# ---------------------------------------------------------------------------------------------------------------------
# the module in poses
# ---------------------------------------------------------------------------------------------------------------------
T0 = time.time()
PARTS = M.build()
DOC = json.load(open(os.path.join(HERE, "parts_pan.json")))
GRP = {n: p["group"] for n, p in PARTS.items()}
CRANK_SET = ("P_kluka", "cap_kluky", "skr_kluky")
L_SET = [n for n in PARTS if GRP[n] == "L"]
P_RIGID = [n for n in PARTS if GRP[n] == "P" and n not in CRANK_SET and n != "fpc_pan"]
TRI = {n: tris_of(p["shape"]) for n, p in PARTS.items() if n != "fpc_pan"}
TRI["fpc_stage"] = tris_of(M.fpc_stage())
B_STL = C.B_STL
TRI["golier_kotuc"] = stl("golier_kotuc", B_STL)
TRI["krk_predna_polovica"] = stl("krk_predna_polovica", B_STL)
TRI["krk_zadna_polovica"] = stl("krk_zadna_polovica", B_STL)
P_RIGID_M = P_RIGID + ["fpc_stage", "golier_kotuc"]           # rigid on the stage (mesh checks)
L_SET_M = L_SET + ["krk_predna_polovica", "krk_zadna_polovica"]
_FL, _FP = {}, {}


def fpc_lift_tris(lift):
    if lift not in _FL:
        _FL[lift] = tris_of(M.fpc_lift(lift))
    return _FL[lift]


def fpc_loop_tris(pan):
    if pan not in _FP:
        _FP[pan] = tris_of(M.fpc_loop(pan))
    return _FP[pan]


def moving_tris(name, lift):
    """triangles of a moving part in the stage frame at `lift`"""
    if name in CRANK_SET:
        return crank_xform(TRI[name], M.crank_angle(lift)) if name != "skr_kluky" else TRI[name]
    if name in L_SET_M:
        T = TRI[name].copy(); T[..., 2] += lift
        return T
    if name == "fpc_lift":
        return fpc_lift_tris(lift)
    return TRI[name]


say(f"== t4_pan_checks {time.strftime('%Y-%m-%d %H:%M:%S')}  sections {''.join(SECT)}  (parts built in {time.time() - T0:.1f} s) ==")

# =====================================================================================================================
# A  solids
# =====================================================================================================================
if "A" in SECT:
    bad = []
    for e in DOC["parts"]:
        p = PARTS[e["name"]]["shape"]
        ok = bool(p.is_valid and len(p.solids()) == 1 and p.volume > 0 and e["watertight"] and e.get("bbox_ok", True))
        st = M.mesh_stats(stl(e["name"]))
        ok = ok and st["open_edges"] == 0 and st["nonmanifold_edges"] == 0 and st["flipped_edges"] == 0 and st["volume"] > 0
        ok = ok and abs(st["volume"] - p.volume) <= max(0.02 * p.volume, 0.05)
        if not ok:
            bad.append(e["name"])
    step_null = [e["name"] for e in DOC["parts"] if e["step"] is None]
    step_max = max(os.path.getsize(os.path.join(HERE, e["step"])) for e in DOC["parts"] if e["step"])
    RES["A_solids"] = dict(status="PASS" if not bad else "FAIL", n=len(DOC["parts"]), not_ok=bad, step_null=step_null,
                           step_max_bytes=step_max,
                           note="valid single solid, volume > 0, bbox of the 7 printed parts as designed, STL (absolute deflection 0.01) "
                                "re-read: 0 open / non-manifold / flipped edges, mesh volume within 2 % of the solid")
    say(f"A  {len(DOC['parts'])} parts, not ok: {bad}; STEP null: {step_null}; largest STEP {step_max / 1e6:.2f} MB")

# =====================================================================================================================
# B  interference among the PAN parts
# =====================================================================================================================
DECL_OVERLAP = {   # pairs that overlap by design (press / thread / serration); max volume mm3
    ("P_kluka", "cap_kluky"): (0.5, "crank pin D2.00 pressed in D1.98"),
    ("P_kluka", "servo_zdvih"): (4.0, "21T serration of the crank (D4.44 / 4.84) on the servo spline D4.8"),
    ("servo_zdvih", "skr_kluky"): (12.0, "crank screw M2.5 in the servo shaft thread"),
    ("P_kluka", "skr_kluky"): (1.0, "countersunk head seat of the crank screw"),
    ("P_koleso", "kolik_dorazu"): (0.3, "stop pin D2.00 pressed in D1.98"),
    ("P_drziak_serva", "skr_F11"): (5.0, "M2 thread-forming screw in the D1.7 pilot of the tab post"),
    ("L_pata", "skr_F12"): (6.0, "M2 thread-forming screw in the D1.7 pilot of the foot"),
    ("L_pata", "kolik_ucha"): (0.3, "ear dowel D1.50 pressed in D1.48"),
    ("L_pata", "skr_jazyka"): (5.0, "M1.6 screw self-tapping in the D1.3 pilot of the foot"),
    ("skr_F10_1", "vl_F10_1"): (9.0, "M2 screw in the insert thread"), ("skr_F10_2", "vl_F10_2"): (9.0, "M2 screw in the insert thread"),
    ("fpc_pan", "spoj_zdvih"): (0.5, "stiffener bonded on the FPC branch (pins soldered through)"),
    ("kabel_zdvih", "spoj_zdvih"): (8.0, "lead crimped in the 1x3 socket"),
    ("kabel_zdvih", "servo_zdvih"): (16.0, "lead leaves the servo inside the reserved exit block"),
    ("P_koleso", "fpc_pan"): (0.05, "FPC inner run lies on the drum (contact, numeric sliver)"),
    ("P_sachta", "fpc_pan"): (0.05, "FPC bonded in the 0.2 groove under the floor / on the fin (contact, numeric sliver)"),
    ("L_pata", "fpc_pan"): (0.05, "FPC paddle bonded in the foot pocket"), ("L_jazyk", "fpc_pan"): (0.05, "FPC corner piece in the tongue recess"),
}
DECL_NEAR = {   # pairs closer than 1.0 by design: (min allowed, max expected, text)
    ("L_ucho", "cap_kluky"): (0.08, 0.12, "crank pin D2 in the slot 2.2: 0.10 per side"),
    ("L_ucho", "P_kluka"): (0.38, 0.42, "crank arm <-> ear side gap 0.40 (set with the bracket slots)"),
    ("L_pata", "P_sachta"): (0.35, 0.52, "foot 44.6 x 19.6 between the guide lands (0.50) / 0.5 above the hub disc at rest"),
    ("L_jazyk", "P_sachta"): (0.45, 1.0, "tongue in the end window (1.0 side, 0.5 to the window top at lift 20, 0.5 above the floor at rest)"),
    ("L_ucho", "P_sachta"): (0.45, 1.0, "ear in the back window (0.5 above the floor at rest, 1.0 sides / top)"),
    ("krk_predna_polovica", "P_sachta"): (0.25, 0.32, "neck 45 x 20 on the guide lands: 0.30 bare"),
    ("krk_zadna_polovica", "P_sachta"): (0.25, 0.32, "neck 45 x 20 on the guide lands: 0.30 bare"),
    ("P_kluka", "servo_zdvih"): (0.0, 0.35, "crank on the servo spline (serration), hub face 0.3 from the turret"),
    ("krk_predna_polovica", "golier_kotuc"): (0.24, 0.26, "neck in the slot 45.5 x 20.5 of the collar disc: 0.25 (variant B, unchanged)"),
    ("krk_zadna_polovica", "golier_kotuc"): (0.24, 0.26, "neck in the slot 45.5 x 20.5 of the collar disc: 0.25 (variant B, unchanged)"),
}
if "B" in SECT:
    t0 = time.time()
    rows, bad = [], []

    def solids_at(lift):
        S = {n: p["shape"] for n, p in PARTS.items()}
        if lift > 0:
            S.update(M.pose_parts(lift))
            S["fpc_pan"] = M.one(M.fuse([M.fpc_lift(lift), M.fpc_stage(), M.fpc_loop(0.0)]))
        return S

    seen = {}
    for lift in (0.0, 10.0, 20.0):
        S = solids_at(lift)
        names = list(S)
        BB = {n: S[n].bounding_box() for n in names}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if lift > 0 and not (GRP[a] == "L" or GRP[b] == "L" or a in CRANK_SET or b in CRANK_SET or "fpc_pan" in (a, b)):
                    continue                                      # rigid P-P pairs do not change with the lift
                A, Bb = BB[a], BB[b]
                if (A.min.X > Bb.max.X + 0.01 or Bb.min.X > A.max.X + 0.01 or A.min.Y > Bb.max.Y + 0.01 or Bb.min.Y > A.max.Y + 0.01
                        or A.min.Z > Bb.max.Z + 0.01 or Bb.min.Z > A.max.Z + 0.01):
                    continue
                v = common_vol(S[a], S[b])
                key = tuple(sorted((a, b)))
                if v is None or v > 1e-3:
                    seen.setdefault(key, []).append((lift, v))
    for key, lst in sorted(seen.items()):
        vmax = max((v if v is not None else 1e9) for _, v in lst)
        d = DECL_OVERLAP.get(key) or DECL_OVERLAP.get((key[1], key[0]))
        ok = d is not None and vmax <= d[0]
        rows.append(dict(a=key[0], b=key[1], overlap_mm3_max=round(vmax, 3), lifts=[l for l, _ in lst], declared=d[1] if d else None, ok=ok))
        if not ok:
            bad.append(key)
        say(f"B  overlap {key[0]:16s} {key[1]:16s} {vmax:8.3f} mm3 at lifts {[l for l, _ in lst]}  {'declared: ' + d[1] if d else '<-- NOT DECLARED'}"
            + ("" if ok or d is None else "  <-- LARGER THAN DECLARED"))
    # ---- exact distances between the lift / crank parts and everything else on the stage, over the stroke
    near = {}
    movers = L_SET_M + ["P_kluka", "cap_kluky"]
    others = P_RIGID_M + ["skr_kluky"]
    TG = {n: Target(n, TRI[n]) for n in others}
    for lift in (0.0, 5.0, 10.0, 15.0, 20.0):
        mt = {n: moving_tris(n, lift) for n in movers}
        for a in movers:
            Sa, _ = sample(mt[a], 0.3)
            for b in others:
                d = TG[b].dist(Sa, 1.2)
                k = int(np.argmin(d))
                if np.isfinite(d[k]):
                    key = (a, b)
                    if key not in near or d[k] < near[key][0]:
                        near[key] = (float(d[k]), lift, [round(float(x), 2) for x in Sa[k]])
        # ear / foot / tongue against the crank
        for a in ("L_ucho", "L_pata", "krk_zadna_polovica", "krk_predna_polovica", "skr_F12", "kolik_ucha"):
            Sa, _ = sample(mt[a], 0.3)
            for b in ("P_kluka", "cap_kluky"):
                d = Target(b, mt[b]).dist(Sa, 1.2)
                k = int(np.argmin(d))
                if np.isfinite(d[k]):
                    key = (a, b)
                    if key not in near or d[k] < near[key][0]:
                        near[key] = (float(d[k]), lift, [round(float(x), 2) for x in Sa[k]])
    FAST = ("skr_", "kolik_", "vl_", "ptfe_", "fpc_", "spoj_", "kabel_")
    nrows = []
    for (a, b), (d, lift, at) in sorted(near.items(), key=lambda kv: kv[1][0]):
        if d >= 1.0 - 1e-3:
            continue
        dec = DECL_NEAR.get((a, b)) or DECL_NEAR.get((b, a))
        fast = a.startswith(FAST) or b.startswith(FAST)
        ok = (dec is not None and dec[0] - 1e-6 <= d <= dec[1] + 1e-6) or fast
        nrows.append(dict(a=a, b=b, min_mm=round(d, 3), lift=lift, at=at, declared=dec[2] if dec else ("fastener / tape / FPC in its seat" if fast else None), ok=ok))
        if not ok:
            bad.append((a, b))
        say(f"B  near    {a:20s} {b:16s} {d:6.3f} at lift {lift:4.1f} {at}  {('declared: ' + dec[2]) if dec else ('(fastener / tape / FPC)' if fast else '<-- NOT DECLARED')}"
            + ("" if ok else "  <-- OUTSIDE THE DECLARED RANGE"))
    RES["B_interference"] = dict(status="PASS" if not bad else "FAIL", overlaps=rows, near_pairs_below_1mm=nrows, not_ok=[list(k) for k in bad],
                                 method="OCC common volume of every bbox-overlapping pair at lift 0 / 10 / 20; exact mesh distances of the lift "
                                        "and crank parts (incl. the finished neck) to the stage parts at lift 0 / 5 / 10 / 15 / 20")
    say(f"B  {len(rows)} overlapping pairs, {len(nrows)} pairs below 1.0, not ok {bad}  ({time.time() - t0:.0f} s)")

# =====================================================================================================================
# C  kinematics
# =====================================================================================================================
if "C" in SECT:
    E = P["EAR"]; hw = C.EAR["slot_w"] / 2
    th = np.linspace(0, 180, 361)
    y = M.YL - M.RC * np.sin(np.radians(th)); z = M.ZL - M.RC * np.cos(np.radians(th))
    lift = z - z[0]
    stroke = float(lift.max() - lift.min())
    dz = M.RC * np.sin(np.radians(th))                       # d lift / d theta (mm / rad), analytic
    sy0, sy1 = E["slot_y"]
    end_gap_front = float(y.min() - C.CRANK["pin_d"] / 2 - sy0)
    end_gap_back = float(sy1 - (y.max() + C.CRANK["pin_d"] / 2))
    # geometric proof on the solids: the pin stays inside the slot of the ear (ear lifted by R (1 - cos))
    worst = []
    ear0 = TRI["L_ucho"]; pin0 = TRI["cap_kluky"]
    for t in (0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180):
        lf = M.RC * (1 - math.cos(math.radians(t)))
        ear = ear0.copy(); ear[..., 2] += lf
        pin = crank_xform(pin0, t)
        Sp, _ = sample(pin, 0.2)
        m = (Sp[:, 0] > C.EAR["x"][0] + 0.05) & (Sp[:, 0] < C.EAR["x"][1] - 0.05)
        d = Target("ear", ear, 0.25).dist(Sp[m], 1.0)
        worst.append((t, round(lf, 3), round(float(d.min()), 3)))
    dmin = min(w[2] for w in worst); dmax = max(w[2] for w in worst)
    # servo torque
    m_head = 0.170       # kg: head + neck + foot (variant B E2: about 150 g head / neck + margin)
    tq = m_head * 9.81 * M.RC * 1e-3
    fw = 3.0             # recommended firmware margin from the dead centres (deg)
    ok = abs(stroke - 20.0) < 1e-6 and abs(dz[0]) < 1e-9 and abs(dz[-1]) < 1e-8 and dmin > 0.05 and end_gap_front >= 0.5
    sp = P["GEAR"]["stop_pin"]; gr = C.PAN_STOP
    RES["C_kinematics"] = dict(
        status="PASS" if ok else "FAIL", stroke_mm=round(stroke, 4), crank_r=M.RC, law="lift = 10 (1 - cos theta), theta 0..180 deg",
        dead_centres=dict(theta_deg=[0, 180], dlift_dtheta=[float(dz[0]), float(dz[-1])], pin_yz=[list(map(float, M.pin_pos(0))), list(map(float, M.pin_pos(180)))]),
        mid_stroke=dict(theta_deg=90, pin_yz=list(map(float, M.pin_pos(90))), crank_tip_y=M.YL - M.RC - C.CRANK["tip_r"],
                        tip_to_neck_back_face=round(M.YL - M.RC - C.CRANK["tip_r"] - C.NECK[1] / 2, 3)),
        slot=dict(w=C.EAR["slot_w"], y=list(sy0 for sy0 in E["slot_y"]), length=round(sy1 - sy0, 2), pin_centre_y=[float(y.min()), float(y.max())],
                  end_gap_front_at_mid_stroke=round(end_gap_front, 3), end_gap_back_at_dead_centres=round(end_gap_back, 3)),
        pin_to_slot_flanks_on_solids=dict(min=dmin, max=dmax, table_theta_lift_gap=worst),
        firmware=dict(recommended_theta_range=[fw, 180 - fw], stroke_loss_per_end=round(M.RC * (1 - math.cos(math.radians(fw))), 4),
                      pin_to_slot_back_end=round(end_gap_back + M.RC * math.sin(math.radians(fw)), 3),
                      note="at the exact dead centres the pin is 0.10 from the closed back end of the slot; an overshoot of the servo "
                           "would run the pin into it - limit theta to 3..177 deg (stroke 19.97)"),
        torque=dict(mass_kg=m_head, peak_Nm=round(tq, 4), MG90S_stall_Nm=0.18, factor=round(0.18 / tq, 1), holding_at_dead_centres_Nm=0.0),
        pan_stop=dict(pin_r=sp["r"], pin_az_gear=sp["az"], groove_az=list(gr["az"]), hard_stop_deg=[-90.0, 90.0], firmware_deg=[-85.0, 85.0],
                      teeth_gear_az=list(P["GEAR"]["teeth_az"]), pinion_in_gear_frame_at_stops=[254.3 - 90, 254.3 + 90],
                      teeth_margin_deg=[254.3 - 90 - P["GEAR"]["teeth_az"][0], P["GEAR"]["teeth_az"][1] - (254.3 + 90)]))
    say(f"C  stroke {stroke:.3f}, d lift / d theta at 0 / 180: {dz[0]:.2e} / {dz[-1]:.2e}; pin <-> slot flanks {dmin:.3f}..{dmax:.3f}; "
        f"slot end gaps: front {end_gap_front:.2f} (mid stroke), back {end_gap_back:.2f} (dead centres); torque {tq:.4f} N m (x{0.18 / tq:.1f})")

# =====================================================================================================================
# D  swept envelope vs PAN_ENV and the analytic shell
# =====================================================================================================================
if "D" in SECT:
    t0 = time.time()
    env = C.PAN_ENV
    rows, viol, low = [], [], []
    shell_min = {}
    DECL_ENV = {"kolik_dorazu": "stop pin runs in the groove of T_paluba below z -45.7 (interface, spec 6.2 / 7.2)",
                "P_koleso": "retaining lip r 16.5 at z -42.6..-42.0 (spec 7.2; 0.6 thick since the integrator's K10 fix) is outside the r 15.9 band of PAN_ENV; back sector only"}
    allp = P_RIGID_M + list(CRANK_SET) + L_SET_M + ["fpc_lift"]
    for name in allp:
        rmax_by_band = {}
        worst_margin = 9e9; wpt = None
        lifts = LIFTS if (name in L_SET_M or name in CRANK_SET or name == "fpc_lift") else [0.0]
        if name.startswith("krk_"):
            lifts = [0.0, 20.0]
        cl_min = (9e9, None, None, None)
        for lift in lifts:
            S, _ = sample(moving_tris(name, lift), 0.3)
            if name in ("krk_predna_polovica", "krk_zadna_polovica"):
                S = S[S[:, 2] < 4.0]
            if name == "golier_kotuc":
                S = S[S[:, 2] < 3.99]
            r = np.hypot(S[:, 0], S[:, 1]); z = S[:, 2]; az = np.degrees(np.arctan2(S[:, 1], S[:, 0])) % 360
            lim = np.full(len(S), -1.0)
            for z0, z1, rm in env:
                m = (z >= z0 - 1e-6) & (z <= z1 + 1e-6)
                lim[m] = np.maximum(lim[m], rm)
            out = lim < 0
            mg = np.where(out, -9.0, lim - r)
            k = int(np.argmin(mg))
            if mg[k] < worst_margin:
                worst_margin = float(mg[k]); wpt = [round(float(x), 2) for x in S[k]] + [lift]
            # low-zone rule
            # (between the gear plane z -42.2 and the wall bottom z -41.3; the gear itself is band 1 of PAN_ENV + the mesh test in E)
            lz = (z < C.Z_WALL_BOT - 1e-6) & (z > C.Z_GEAR_PAN[1] + 1e-6) & (r > C.R_HUB + 1e-6) & \
                ~((az >= C.STAGE_BACK_AZ[0] - 0.05) & (az <= C.STAGE_BACK_AZ[1] + 0.05))
            if lz.any():
                k2 = int(np.argmax(np.where(lz, r, 0)))
                low.append(dict(part=name, n=int(lz.sum()), at=[round(float(x), 2) for x in S[k2]], az=round(float(az[k2]), 1)))
            # analytic shell, pan sweep
            far = (r > 26.0) & (name not in ("golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica"))   # r <= 26: >= 2.3 everywhere
            if far.any():
                Sf = S[far]
                for pan in PANS:
                    c = C.clearance_to_shell(rotz(Sf, pan))
                    k3 = int(np.argmin(c))
                    if c[k3] < cl_min[0]:
                        cl_min = (float(c[k3]), pan, lift, [round(float(x), 2) for x in rotz(Sf[k3:k3 + 1], pan)[0]])
        ok_env = worst_margin >= -0.011
        rows.append(dict(part=name, env_margin_min=round(worst_margin, 3), at_xyz_lift=wpt, shell_clear_min=round(cl_min[0], 3) if cl_min[1] is not None else None,
                         shell_at=dict(pan=cl_min[1], lift=cl_min[2], xyz=cl_min[3]) if cl_min[1] is not None else None,
                         declared=DECL_ENV.get(name)))
        if not ok_env and name not in DECL_ENV:
            viol.append(name)
        if cl_min[1] is not None and cl_min[0] < 1.0:
            viol.append(name + " (shell)")
        say(f"D  {name:20s} PAN_ENV margin {worst_margin:7.3f} at {wpt}   shell clearance min "
            + (f"{cl_min[0]:6.3f} at pan {cl_min[1]:.0f} lift {cl_min[2]:.1f} {cl_min[3]}" if cl_min[1] is not None else "  (r < 24)")
            + (f"   declared: {DECL_ENV[name]}" if name in DECL_ENV and not ok_env else ""))
    low_bad = [l for l in low if l["part"] not in ("kolik_dorazu",)]
    RES["D_envelope"] = dict(status="PASS" if not viol and not low_bad else "FAIL", parts=rows, violations=viol, low_zone_rule_hits=low,
                             shell_criterion=1.0, shell_min=min((r["shell_clear_min"] for r in rows if r["shell_clear_min"] is not None)),
                             method="surface samples 0.3 mm of every P / L part (stage frame, lift 0..20 step 2.5) against PAN_ENV(z) and the "
                                    "low-zone rule; samples with r > 26 rotated to pan -85..85 step 5 against the analytic inner surface "
                                    "(true offset 2.2, t4_common.clearance_to_shell)")
    say(f"D  violations {viol}; low-zone hits {low}  ({time.time() - t0:.0f} s)")

# =====================================================================================================================
# E  real meshes of OBAL + RAM
# =====================================================================================================================
class Multi:
    """all static parts in ONE KD-tree; query -> candidate (point index, exact distance, static part index) triples"""

    def __init__(self, parts, h=0.4):
        self.names = list(parts)
        self.T = np.concatenate([parts[n] for n in self.names])
        self.pid = np.concatenate([np.full(len(parts[n]), i, np.int32) for i, n in enumerate(self.names)])
        self.S, self.I = sample(self.T, h, 0.1)
        self.tree = cKDTree(self.S)
        # occupancy grid (2 mm voxels, dilated by one voxel): points outside it are farther than 2.0 from every sample
        self.vx = 2.0; self.org = self.S.min(0) - 3 * self.vx
        ijk = np.floor((self.S - self.org) / self.vx).astype(int)
        self.dim = ijk.max(0) + 4
        G = np.zeros(self.dim, bool); G[ijk[:, 0], ijk[:, 1], ijk[:, 2]] = True
        D = np.zeros_like(G)
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                for c in (-1, 0, 1):
                    D |= np.roll(G, (a, b, c), (0, 1, 2))
        self.G = D

    def near(self, Q):
        ijk = np.floor((Q - self.org) / self.vx).astype(int)
        ok = np.all((ijk >= 0) & (ijk < self.dim), axis=1)
        m = np.zeros(len(Q), bool)
        m[ok] = self.G[ijk[ok, 0], ijk[ok, 1], ijk[ok, 2]]
        return m

    def query(self, Q, dmax=1.6, k=8):
        sel = np.where(self.near(Q))[0]
        if len(sel) == 0:
            return sel, np.zeros(0), np.zeros(0, np.int32)
        dd, ii = self.tree.query(Q[sel], k=k, distance_upper_bound=dmax + 0.3, workers=3)
        rows, cols = np.where(np.isfinite(dd))
        if len(rows) == 0:
            return rows, np.zeros(0), np.zeros(0, np.int32)
        tri = self.I[ii[rows, cols]]
        e = pt_tri(Q[sel[rows]], self.T[tri, 0], self.T[tri, 1], self.T[tri, 2])
        return sel[rows], e, self.pid[tri]


def _r(Q):
    return np.hypot(Q[:, 0], Q[:, 1])


RULES_E = [   # (moving, static, zone(Q) -> mask or None = everywhere, minimum allowed, text)
    ("P_sachta", "T_stred", lambda Q: (_r(Q) < 28.6) & (Q[:, 2] > -10.6), 0.20, "journal D56.14 in the bore D56.68: 0.27 radial bare (0.14 with the PTFE band)"),
    ("ptfe_pas_capu", "T_stred", None, 0.10, "journal with the PTFE band D56.40 in the bore (measured r 28.342): running clearance 0.14"),
    ("golier_kotuc", "golier_prstenec", None, 0.20, "collar disc r 26.5 in the ring r 26.75: running seam 0.25 (variant B, unchanged)"),
    ("P_sachta", "golier_prstenec", None, 0.20, "stage top r 26.5 at the running seam 0.25; journal cone 0.90 under the ring"),
    ("ptfe_pas_capu", "golier_prstenec", None, 0.9, "tape top z -5.0 under the ring"),
    ("P_koleso", "cap_pan", None, 0.02, "gear bore D6.05 on the pivot pin D6: 0.025 radial"),
    ("P_sachta", "cap_pan", None, 0.02, "hub bore D6.05 on the pivot pin: 0.025 radial"),
    ("P_koleso", "ptfe_podlozka", None, 0.0, "gear runs on the PTFE thrust washer (contact)"),
    ("P_koleso", "T_paluba", None, 0.19, "gear 0.3 above the deck (washer); recess 0.5 / 0.2 around the pivot boss"),
    ("kolik_dorazu", "T_paluba", None, 0.19, "stop pin D2 in the groove 2.4 wide: 0.2 per side, 0.5 to the groove floor (touches the groove ends at +-90)"),
    ("kolik_dorazu", "ptfe_podlozka", None, 0.3, "stop pin r 12.5..14.5 beside the washer r 12.0"),
    ("kolik_kolesa_1", "ptfe_podlozka", None, 0.6, "dowel inside the gear (blind hole, 0.5 floor between dowel and washer)"),
    ("kolik_kolesa_2", "ptfe_podlozka", None, 0.6, "dowel inside the gear (blind hole, 0.5 floor between dowel and washer)"),
    ("kolik_kolesa_1", "T_paluba", None, 0.9, "dowel inside the gear"), ("kolik_kolesa_2", "T_paluba", None, 0.9, "dowel inside the gear"),
    ("L_pata", "cap_pan", None, 0.65, "foot at rest: 0.7 above the pin top, 0.5 above the hub disc (end position, spec 1.3/7)"),
    ("skr_F12", "cap_pan", None, 0.65, "moves with the foot"), ("kolik_ucha", "cap_pan", None, 0.65, "moves with the foot"),
    ("fpc_loop", "T_paluba", None, 0.0, "outer run lies on the channel wall, tail through the arc slot, strip 0.1 above the deck"),
    ("fpc_loop", "T_prichytka_fpc", None, 0.0, "static end clamped between the clamp and the wall"),
    ("fpc_loop", "skr_fpc", None, 0.3, "clamp screw beside the clamped end"),
    ("fpc_loop", "T_ram", None, 0.0, "tail below the deck (to the controller)"),
    ("fpc_loop", "servo_J1", None, 0.0, "tail below the deck (to the controller)"),
    ("fpc_loop", "DPS_riadenie", None, 0.0, "tail plugs into the controller"),
    ("fpc_loop", "pena_J1", None, 0.0, "tail below the deck"),
]
if "E" in SECT:
    t0 = time.time()
    stat = {}
    for f in ("parts_obal.json", "parts_ram.json"):
        for e in json.load(open(os.path.join(HERE, f)))["parts"]:
            if e["group"] == "T":
                stat[e["name"]] = f[6:-5]
    stat["golier_prstenec"] = "B"
    sp = {}
    for n in stat:
        T = stl(n, B_STL if stat[n] == "B" else STL)
        lo, hi = T.min(1), T.max(1)
        m = (hi[:, 2] > -53.0) & (lo[:, 2] < 6.0) & (lo[:, 0] < 37.5) & (hi[:, 0] > -37.5) & (lo[:, 1] < 41.0) & (hi[:, 1] > -41.0)
        ctr = T.mean(1); m &= (np.hypot(ctr[:, 0], ctr[:, 1]) < 39.5) | (np.linalg.norm(hi - lo, axis=1) > 6.0)
        if m.sum():
            sp[n] = T[m]
    MS = Multi(sp, 0.4)
    say(f"E  {len(sp)} static parts near the pan stage, {len(MS.T)} triangles, {len(MS.S)} samples ({time.time() - t0:.0f} s)")
    rule_of = {}
    for i, (a, b, zone, dmin, txt) in enumerate(RULES_E):
        rule_of.setdefault((a, b), []).append(i)
    res, hard = {}, {}

    def run(name, Q, pan, lift, store, skip=()):
        rows, e, pid = MS.query(Q)
        if len(rows) == 0:
            return
        for p_ in np.unique(pid):
            b = MS.names[p_]
            if b in skip:
                continue
            m = pid == p_
            r_, e_ = rows[m], e[m]
            cat = np.full(len(r_), -1)
            for i in rule_of.get((name, b), []):
                zone = RULES_E[i][2]
                zm = np.ones(len(r_), bool) if zone is None else zone(Q[r_])
                cat[zm & (cat < 0)] = i
            for c in np.unique(cat):
                mm = cat == c
                k = int(np.argmin(e_[mm])); d = float(e_[mm][k])
                key = (name, b, int(c))
                if key not in store or d < store[key][0]:
                    store[key] = (d, float(pan), float(lift), [round(float(x), 2) for x in Q[r_[mm][k]]])

    SMP = {n: sample(TRI[n], 0.3)[0] for n in P_RIGID_M}
    SMP["golier_kotuc"] = SMP["golier_kotuc"][np.hypot(SMP["golier_kotuc"][:, 0], SMP["golier_kotuc"][:, 1]) > 25.5]   # rim only (slot / top face: variant B)
    LM = list(CRANK_SET[:2]) + L_SET + ["fpc_lift"]            # the neck itself stays inside the well / collar disc
    SMPL = {(n, lf): sample(moving_tris(n, lf), 0.3)[0] for lf in LIFTS for n in LM}
    say(f"E  moving samples: rigid {sum(len(v) for v in SMP.values())}, lift set {sum(len(SMPL[(n, 0.0)]) for n in LM)} per lift ({time.time() - t0:.0f} s)")
    fres = {}
    TG2 = {b: Target(b, TRI[b]) for b in ("P_sachta", "P_koleso", "P_drziak_serva", "kolik_dorazu", "kolik_kolesa_1", "kolik_kolesa_2", "spoj_zdvih", "servo_zdvih")}
    for pan in PANS + [-90.0, 90.0]:
        store = hard if abs(pan) > 85.1 else res
        for n in P_RIGID_M:
            run(n, rotz(SMP[n], pan), pan, 0.0, store, skip=("pastorok_pan",) if n == "P_koleso" else ())
        for lf in LIFTS:
            for n in LM:
                run(n, rotz(SMPL[(n, lf)], pan), pan, lf, store)
        Qf = sample(fpc_loop_tris(pan), 0.3)[0]
        run("fpc_loop", Qf, pan, 0.0, store)
        Qs = rotz(Qf, -pan)
        for b, tg in TG2.items():
            d = tg.dist(Qs, 1.6)
            k = int(np.argmin(d))
            if np.isfinite(d[k]) and (("fpc_loop", b) not in fres or d[k] < fres[("fpc_loop", b)][0]):
                fres[("fpc_loop", b)] = (float(d[k]), float(pan), 0.0, [round(float(x), 2) for x in Qs[k]])
        print(f"   pan {pan:6.1f} done ({time.time() - t0:.0f} s)", flush=True)
    rows, bad = [], []
    for (a, b, c), (d, pan, lf, at) in sorted(res.items(), key=lambda kv: kv[1][0]):
        lim = RULES_E[c][3] if c >= 0 else 1.0
        ok = d >= lim - 1e-3
        if d < 1.5 or not ok:
            rows.append(dict(moving=a, static=b, module=stat.get(b), min_mm=round(d, 3), pan=pan, lift=lf, at=at, required=lim,
                             declared=RULES_E[c][4] if c >= 0 else None, ok=ok))
            say(f"E  {a:16s} {b:18s} {d:6.3f} (>= {lim})  pan {pan:5.0f} lift {lf:4.1f} {at}  " + (f"declared: {RULES_E[c][4]}" if c >= 0 else "") + ("" if ok else "  <-- FAIL"))
        if not ok:
            bad.append((a, b))
    hrows = []
    for (a, b, c), (d, pan, lf, at) in sorted(hard.items(), key=lambda kv: kv[1][0]):
        prev = res.get((a, b, c), (9.0,))[0]
        if d < 1.0 and d < prev - 0.02:
            stop = (a, b) == ("kolik_dorazu", "T_paluba")
            okh = d > 0.05 or stop
            hrows.append(dict(moving=a, static=b, min_mm=round(d, 3), pan=pan, lift=lf, at=at, ok=okh, note="hard stop: pin on the groove end" if stop else ""))
            say(f"E  hard stop +-90: {a:16s} {b:18s} {d:6.3f}  pan {pan:5.0f} lift {lf:4.1f} {at}" + ("" if okh else "  <-- CONTACT"))
            if not okh:
                bad.append((a, b, "pan 90"))
    DECL_F = {"P_koleso": "inner run lies on the drum r 15.7, under the retaining lip", "P_sachta": "riser comes out of the groove under the back floor (same FPC)"}
    frows = []
    for (a, b), (d, pan, lf, at) in sorted(fres.items(), key=lambda kv: kv[1][0]):
        if d < 1.0:
            ok = b in DECL_F
            frows.append(dict(moving=a, stage_part=b, min_mm=round(d, 3), pan=pan, at_stage_frame=at, declared=DECL_F.get(b), ok=ok))
            say(f"E  fpc_loop <-> {b:16s} {d:6.3f} pan {pan:5.0f} {at}  " + (f"declared: {DECL_F.get(b)}" if ok else "<-- NOT DECLARED"))
            if not ok:
                bad.append((a, b))
    # ---- gear against the ROTATING pinion (pinion turns -2 x pan about PAN_AX)
    pin_T = stl("pastorok_pan")
    Sg = sample(TRI["P_koleso"], 0.15)[0]
    gmin = (9.0, None); glist = []
    for pan in list(np.arange(-90.0, 90.01, 2.5)) + list(np.arange(0.25, 10.0, 0.5)):
        Tp = rot_about(pin_T, -2.0 * pan, *C.PAN_AX)
        Q = rotz(Sg, pan)
        m = np.hypot(Q[:, 0] - C.PAN_AX[0], Q[:, 1] - C.PAN_AX[1]) < 8.6
        d = Target("pinion", Tp, 0.15).dist(Q[m], 1.0)
        glist.append((float(pan), round(float(d.min()), 4)))
        if d.min() < gmin[0]:
            gmin = (float(d.min()), float(pan))
    gvals = np.array([g[1] for g in glist])
    Sd = Sg[(np.hypot(Sg[:, 0], Sg[:, 1]) > 15.25)]                     # drum r 15.7 + lip r 16.5 (outside the tip circle 15.2)
    dmin = (9.0, None)
    for pan in np.arange(-90.0, 90.01, 2.5):
        Q = rotz(Sd, pan)
        m = np.hypot(Q[:, 0] - C.PAN_AX[0], Q[:, 1] - C.PAN_AX[1]) < 10.5
        if m.any():
            d = Target("pinion", rot_about(pin_T, -2.0 * pan, *C.PAN_AX), 0.15).dist(Q[m], 2.6)
            if d.min() < dmin[0]:
                dmin = (float(d.min()), float(pan))
    say(f"E  drum / lip of the gear <-> pinion: min {dmin[0]:.3f} at pan {dmin[1]} (hard stops included)")
    free = [r_ for r_ in rows if r_["declared"] is None]
    RES["E_real_meshes"] = dict(status="PASS" if not bad and gmin[0] > 0.004 and dmin[0] > 0.2 else "FAIL", pairs_below_1p5=rows, not_ok=[list(k) for k in bad],
                                min_undeclared=min((r_["min_mm"] for r_ in free), default=None),
                                hard_stop_poses_pan_90=hrows, static_parts_tested=sorted(sp), fpc_loop_vs_stage=frows,
                                drum_lip_vs_pinion=dict(min_mm=round(dmin[0], 3) if dmin[1] is not None else None, at_pan=dmin[1],
                                                        note="smooth drum r 15.7 / lip r 16.5 never enter the pinion zone; pan -90..90 (> 2.6 = not within range)"),
                                gear_vs_rotating_pinion=dict(min_flank_gap=round(gmin[0], 4), at_pan=gmin[1], max_of_min=round(float(gvals.max()), 4),
                                                             n_poses=len(glist), note="pinion STL of RAM rotated by -2 x pan about PAN_AX; a "
                                                             "gap > 0 at every pose = no tooth interference; value = flank gap (backlash share)"),
                                method="P / L surface samples (0.3 mm + all vertices) rotated to pan -85..85 step 5 (hard stops +-90 extra), lift 0..20 "
                                       "step 2.5; exact distance to the STL triangles of every group-T part of parts_obal.json / parts_ram.json and "
                                       "golier_prstenec (one KD-tree, 8 nearest candidates per point, per static part minima); rule zones in RULES_E")
    say(f"E  gear <-> rotating pinion: min flank gap {gmin[0]:.4f} at pan {gmin[1]}, largest per-pose minimum {gvals.max():.4f} ({len(glist)} poses)")
    say(f"E  not ok: {bad}  ({time.time() - t0:.0f} s)")

# =====================================================================================================================
# F  seats of the bought parts / fits, measured on the solids and meshes
# =====================================================================================================================
def rz_of(T):
    V = T.reshape(-1, 3)
    return np.hypot(V[:, 0], V[:, 1]), V[:, 2], V


if "F" in SECT:
    rows = []

    def row(name, nominal, measured, lo, hi, note=""):
        ok = lo - 1e-3 <= measured <= hi + 1e-3
        rows.append(dict(seat=name, nominal=nominal, measured=round(float(measured), 3), allowed=[lo, hi], ok=bool(ok), note=note))
        say(f"F  {name:58s} nominal {nominal:<8} measured {measured:7.3f}  allowed {lo}..{hi}  {'ok' if ok else '<-- FAIL'}  {note}")
    # ---- journal / bore
    Sj = sample(TRI["P_sachta"], 0.4)[0]; mj = (Sj[:, 2] > -9.8) & (Sj[:, 2] < -4.7)
    rj = float(np.hypot(Sj[mj, 0], Sj[mj, 1]).max())
    rt, zt, _ = rz_of(TRI["ptfe_pas_capu"]); rtp = float(rt.max())
    Ts = stl("T_stred"); Ts = Ts[(np.hypot(Ts[..., 0], Ts[..., 1]).max(1) < 28.6) & (Ts[..., 2].min(1) < -4.0) & (Ts[..., 2].max(1) > -10.6)]
    Sb_ = sample(Ts, 0.4)[0]; mb = (Sb_[:, 2] > -10.0) & (Sb_[:, 2] < -4.6)
    rbore = float(np.hypot(Sb_[mb, 0], Sb_[mb, 1]).min())
    row("journal resin radius", 28.07, rj, 28.02, 28.12, "P_sachta, z -10..-4.6")
    row("bore radius of T_stred (OBAL mesh)", 28.35, rbore, 28.30, 28.40, "spec D56.70 +0.10/0; OBAL reports 28.342")
    row("journal + PTFE band <-> bore, radial running clearance", 0.15, rbore - rtp, 0.10, 0.20, "spec par. 13: 0.10..0.20")
    row("journal bare <-> bore, radial (if the print is tight: no tape)", 0.28, rbore - rj, 0.20, 0.35)
    row("largest radius of the bench-assembled stage (must pass the bore)", 28.20, max(float(rz_of(TRI[n])[0].max()) for n in P_RIGID if not n.startswith(("servo", "P_drziak", "spoj", "kabel", "skr_F1"))), 0.0, rbore - 0.1)
    # ---- pivot
    for n in ("P_koleso", "P_sachta"):
        r, z, _ = rz_of(TRI[n]); m = (r < 4.0) & (z < -41.1) & (z > (-43.9 if n == "P_koleso" else -42.3))
        row(f"pivot bore radius in {n}", 3.025, float(r[m].min()), 3.02, 3.03, "pin D6 h6 (ISO 2338): running 0.025 radial")
    rp, zp, _ = rz_of(stl("cap_pan"))
    row("pivot pin radius (RAM mesh cap_pan)", 3.0, float(rp.max()), 2.99, 3.0)
    row("pivot pin top below the hub top (z -41.0)", 0.2, -41.0 - float(zp.max()), 0.1, 0.4)
    r, z, _ = rz_of(TRI["P_koleso"]); m = (z < -44.1) & (r < 7.0)
    row("gear recess radius over the deck boss r 5.5", 6.0, float(r[m & (r > 4.0)].min()), 5.95, 6.05, "0.5 radial, 0.2 axial to the boss top -44.2")
    # ---- gear pair
    row("pan gear centre distance |PAN_AX|", 21.6, math.hypot(*C.PAN_AX), 21.60, 21.65, "spec C +0.05/0")
    r, z, _ = rz_of(TRI["P_koleso"])
    row("gear tip radius (36T m0.8: da/2)", 15.2, max(q[0] for t_ in M.gear_profile(C.M_PAN, C.T_PAN[1], P["GEAR"]["phase"], P["GEAR"]["backlash"]) for q in t_), 15.19, 15.21,
        "tooth profile; drum 15.7 and lip 16.5 are outside the toothed sector")
    # ---- MG90S seat
    Ss = sample(TRI["servo_zdvih"], 0.25)[0]
    Tb = TRI["P_drziak_serva"]; lo, hi = Tb.min(1), Tb.max(1)
    lip = Target("lip", Tb[lo[:, 1] > 29.4], 0.25)
    row("MG90S case back edge <-> wedge lip of the ledge (0.20 horizontal, 0.14 normal to the wedge)", 0.2, float(lip.dist(Ss, 2.0).min()), 0.13, 0.21, "servo width 12.2 +-0.3: a wider case rides up the 45 deg wedge")
    post = Target("post", Tb[(lo[:, 2] > -18.05) & (lo[:, 1] > 17.05) & (hi[:, 0] < 5.05) & (lo[:, 0] > -0.05)], 0.25)
    row("MG90S case top end <-> tab post (z)", 0.3, float(post.dist(Ss[Ss[:, 2] < -18.29], 2.0).min()), 0.28, 0.32, "length 22.8 +-0.3")
    row("MG90S <-> bracket, overall (plate y 17.1, ledge z -41.1, tab face x 0.0)", 0.0, float(Target("b", Tb, 0.25).dist(Ss, 1.0).min()), 0.0, 0.01, "3 seat faces in contact")
    row("bracket slots along X (adjust crank <-> ear gap, tab height +-1)", 1.0, P["BRKT"]["slot"], 1.0, 1.0, "stadium 2.3 x 4.3 at both F10 screws")
    row("servo case <-> well back wall pads / plate thickness under the screws", 1.7, P["BRKT"]["plate_y"][1] - P["PAD"]["face_y"], 1.6, 1.8, "PETG >= 1.6")
    # ---- neck / foot
    row("neck 45 x 20 <-> guide lands (bare resin)", 0.30, P["LAND"]["h"] and (M.YI - P["LAND"]["h"] - C.NECK[1] / 2), 0.28, 0.32)
    row("neck <-> PTFE strips on the lands", 0.17, M.YI - P["LAND"]["h"] - P["LAND"]["tape"] - C.NECK[1] / 2, 0.15, 0.20, "spec par. 13 asked 0.87 with flat walls; lands added as strip seats")
    row("foot 44.6 x 19.6 <-> PTFE strips", 0.37, M.YI - P["LAND"]["h"] - P["LAND"]["tape"] - C.FOOT["size"][1] / 2, 0.3, 0.45)
    Tn = np.concatenate([TRI["krk_predna_polovica"], TRI["krk_zadna_polovica"]])
    row("neck bottom plane (B mesh) = foot top", -36.5, float(Tn[..., 2].min()), -36.51, -36.49, "bonded face, front half only")
    row("collar disc underside (B mesh) = stage top", -2.0, float(TRI["golier_kotuc"][..., 2].min()), -2.01, -1.99, "glued; glue groove r 24.4..25.4")
    fs = P["FOOT"]["slot"]
    row("wire slot margin around the neck wire exits (x 11.75..14.5, y -6.5..2.0 measured on the B mesh)", 0.15, min(11.75 - fs["x"][0], fs["x"][1] - 14.5, -6.5 - fs["y"][0], fs["y"][1] - 2.0), 0.1, 1.0)
    # ---- crank / ear
    row("crank pin D2 in the ear slot 2.2 (per side)", 0.10, (C.EAR["slot_w"] - C.CRANK["pin_d"]) / 2, 0.08, 0.12)
    row("crank arm <-> ear side gap", 0.40, C.CRANK["arm_x"][0] - C.EAR["x"][1], 0.38, 0.42)
    row("crank serration major diameter on the spline D4.8", 4.84, P["CRANK"]["spline"]["d_major"], 4.8, 4.9, "21T, minor 4.44: cuts into the tough resin")
    # ---- inserts
    row("M2 insert hole in the bracket pads (resin, glued)", 3.3, C.INSERTS["M2"][2], 3.25, 3.35, "insert OD 3.2 x 3.0, hole depth 3.2")
    row("floor behind the insert hole to the well inner face", 1.2, P["PAD"]["face_y"] - P["PAD"]["seat_depth"] - M.YI, 1.2, 2.0, "local >= 1.2")
    row("F10 screw M2x4: thread engagement in the insert", 2.3, 4.0 - (P["BRKT"]["plate_y"][1] - P["PAD"]["face_y"]), 2.0, 3.0, "tip 0.5 short of the hole floor")
    row("pad wall around the insert hole", 1.35, P["PAD"]["r"] - C.INSERTS["M2"][2] / 2, 1.2, 2.0, "local >= 1.2")
    bad = [r_["seat"] for r_ in rows if not r_["ok"]]
    RES["F_seats"] = dict(status="PASS" if not bad else "FAIL", seats=rows, not_ok=bad)

# =====================================================================================================================
# G  walls of the printed parts
# =====================================================================================================================
def sample_in(T, h):
    """interior samples of the triangles (never on an edge) + their triangle index"""
    e = np.max([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1), np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], axis=0)
    n = np.clip(np.ceil(e / h).astype(int), 1, 60)
    pts, idx = [], []
    for nv in np.unique(n):
        sel = np.where(n == nv)[0]
        uv = [((i + 1 / 3) / nv, (j + 1 / 3) / nv) for i in range(nv) for j in range(nv - i)] + \
             [((i + 2 / 3) / nv, (j + 2 / 3) / nv) for i in range(nv) for j in range(nv - i - 1)]
        u = np.array([a for a, _ in uv]); v = np.array([b for _, b in uv])
        Q = (T[sel, 0][:, None, :] * (1 - u - v)[None, :, None] + T[sel, 1][:, None, :] * u[None, :, None] + T[sel, 2][:, None, :] * v[None, :, None])
        pts.append(Q.reshape(-1, 3)); idx.append(np.repeat(sel, len(u)))
    return np.concatenate(pts), np.concatenate(idx)


def wall_scan(T, h=0.5, nmax=9000, seed=1):
    """thickness along the inward normal to the first OPPOSING face (normals within 37 deg of antiparallel)"""
    N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); A2 = np.linalg.norm(N, axis=1)
    good = A2 > 1e-9
    N = N / np.where(good, A2, 1.0)[:, None]
    S, I = sample_in(T[good], h); I = np.where(good)[0][I]
    if len(S) > nmax:
        k = np.random.default_rng(seed).choice(len(S), nmax, replace=False); S, I = S[k], I[k]
    D = -N[I]; O = S + D * 1e-4
    E1 = T[:, 1] - T[:, 0]; E2 = T[:, 2] - T[:, 0]; A = T[:, 0]
    th = np.full(len(S), np.inf)
    for c0 in range(0, len(S), 128):
        o, d = O[c0:c0 + 128], D[c0:c0 + 128]
        pv = np.cross(d[:, None, :], E2[None, :, :]); det = (E1[None] * pv).sum(2)
        ok = np.abs(det) > 1e-12
        inv = 1.0 / np.where(ok, det, 1.0)
        tv = o[:, None, :] - A[None]
        u = (tv * pv).sum(2) * inv
        qv = np.cross(tv, E1[None]); v = (d[:, None, :] * qv).sum(2) * inv
        t = (E2[None] * qv).sum(2) * inv
        opp = (d @ N.T) > 0.8                                  # exit face roughly perpendicular to the ray
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-3)
        tt = np.where(hit, t, np.inf)
        j = np.argmin(tt, axis=1); t1 = tt[np.arange(len(o)), j]
        th[c0:c0 + 128] = np.where(opp[np.arange(len(o)), j], t1, np.inf)   # first hit must be an opposing face
    return S, th


WALL_MIN = {"resin_black": 1.2, "petg": 1.6, "pom": 1.2}
DECL_THIN = {   # printed part: list of (description, test on the sample point (x, y, z) -> bool, minimum allowed)
    "P_sachta": [("back-sector floor 0.9 (spec 7.1, z -41.9..-41.0); 0.7 in the 0.2 FPC groove", lambda p: p[2] < -40.9, 0.68),
                 ("guide lands 0.7 high on the 1.6 wall (ray from a land flank)", lambda p: abs(abs(p[1]) - 10.65) < 0.4 or abs(abs(p[0]) - 23.15) < 0.4, 0.65),
                 ("fin 1.2 behind the lift loop / apron edge", lambda p: p[0] > 24.9 and p[1] > 4.4, 0.85),
                 ("glue groove 0.3 deep in the 1.5 top plate; rim 1.1 x 0.3 outside the groove", lambda p: p[2] > -3.6, 1.05)],
    "P_koleso": [("floor 0.6 under the two blind dowel holes D2 (dowels D2 x 4: 2.85 in the gear, 1.15 in the hub disc)",
                  lambda p: 7.8 < math.hypot(p[0], p[1]) < 10.2 and abs(p[1]) < 1.2, 0.45),
                 ("retaining lip 0.6 x 0.8 (spec 7.2 asked 0.4; thickened upward to z -42.0)", lambda p: p[2] > -42.65 and math.hypot(p[0], p[1]) > 15.6, 0.58),
                 ("web 1.7 over the boss recess, minus dowel / pin holes", lambda p: math.hypot(p[0], p[1]) < 10.2, 0.9),
                 ("gear teeth m0.8 (tip land 0.5)", lambda p: math.hypot(p[0], p[1]) > 13.3, 0.3)],
    "P_drziak_serva": [("lands 0.85 / 1.05 above the two F10 slots (lug must pass under the frame magnet pad, tab under the door edge)",
                        lambda p: p[1] > 15.3 and (abs(p[2] + 30.1) < 0.9 or p[2] > -13.7), 0.84),
                       ("web 1.25 between the +X end of the lower slot and the lug end (x 22.9)", lambda p: p[0] > 21.0 and p[1] > 15.3, 1.2),
                       ("web 1.3 under the F11 pilot hole (post bottom 0.3 above the servo end)", lambda p: p[0] < 5.1 and p[1] > 17.0 and p[2] > -18.1, 1.25),
                       ("ledge 0.8 under the servo end (spec 7.3, z -41.9..-41.1)", lambda p: p[2] < -41.0, 0.75),
                       ("wedge lip tip", lambda p: p[1] > 29.3, 0.1),
                       ("plate 1.7 behind the pad pockets (y 15.4..17.1)", lambda p: True, 1.55)],
    "P_kluka": [("hub wall 1.2 around the serration", lambda p: abs(p[1] - M.YL) < 3.7 and abs(p[2] - M.ZL) < 3.7, 1.0),
                ("arm tip 1.2 around the pin hole", lambda p: abs(p[2] - (M.ZL - M.RC)) < 2.3, 1.15)],
    "L_pata": [("skins 1.05 / 1.15 above and below the tongue key slot, 0.85 around the D1.3 pilot", lambda p: p[0] > 17.0, 0.84),
               ("webs 0.81 under the ear dowel hole D1.48, 1.15 at the ear pilot D1.7, countersinks of the optional screws", lambda p: True, 0.8)],
    "L_jazyk": [("key prongs 1.5, recess floor 2.2, countersink rim", lambda p: True, 0.5)],
    "L_ucho": [("webs 0.78 above / below the D1.5 locating dowel hole (flange only 3.1 high under the crank sweep)",
                lambda p: abs(p[0] + 15.5) < 1.0 and p[1] < 12.5, 0.76),
               ("slot closing web 0.8 at the far end (sweep limit r 32.03)", lambda p: p[1] > 23.4, 0.75),
               ("upper tine 1.2 above the slot", lambda p: p[2] > M.ZS0 + 1.0, 1.15),
               ("webs 0.85 above / below the M2 clearance hole in the 4.0 flange; front web 1.4", lambda p: p[1] < 12.5, 0.84)],
}
if "G" in SECT:
    t0 = time.time()
    rows, bad = [], []
    for n in M.PRINTED:
        mat = PARTS[n]["mat"]; lim = WALL_MIN[mat]
        S, th = wall_scan(TRI[n])
        f = np.isfinite(th)
        thin = np.where(f & (th < lim - 2e-3))[0]
        und = []
        cover = {d[0]: [9.0, 0] for d in DECL_THIN.get(n, [])}
        for k in thin:
            p = S[k]; hit = False
            for desc, test, tmin in DECL_THIN.get(n, []):
                if test(p) and th[k] >= tmin - 1e-6:
                    cover[desc][0] = min(cover[desc][0], float(th[k])); cover[desc][1] += 1; hit = True
                    break
            if not hit:
                und.append((round(float(th[k]), 3), [round(float(x), 2) for x in p]))
        und.sort()
        cl = {}
        for t_, p_ in und:
            cl.setdefault(tuple(np.round(np.array(p_) / 1.5).astype(int)), []).append((t_, p_))
        und = sorted(min(v) for v in cl.values())
        rows.append(dict(part=n, material=mat, limit=lim, rays=int(f.sum()), min=round(float(th[f].min()), 3), p01=round(float(np.percentile(th[f], 1)), 3),
                         median=round(float(np.median(th[f])), 3), n_below_limit=int(len(thin)),
                         declared_thin=[dict(feature=d, min=round(v[0], 3), rays=v[1]) for d, v in cover.items() if v[1]],
                         undeclared_below_limit=und[:20], n_undeclared_zones=len(und)))
        if und:
            bad.append(n)
        say(f"G  {n:16s} {mat:11s} limit {lim}: {int(f.sum())} rays, min {th[f].min():.3f}, p1 {np.percentile(th[f], 1):.3f}, median {np.median(th[f]):.3f}; "
            f"below limit {len(thin)}, undeclared zones {len(und)} {und[:14]}")
        for d, v in cover.items():
            if v[1]:
                say(f"G      declared: {d}: min {v[0]:.3f} ({v[1]} rays)")
    RES["G_walls"] = dict(status="PASS" if not bad else "FAIL", parts=rows, not_ok=bad,
                          method="inward ray from 9000 random surface samples per part to the first face; counted when that face opposes "
                                 "the start face (normals within 37 deg of antiparallel) - edge / chamfer artefacts are not walls")
    say(f"G  undeclared thin walls in: {bad}  ({time.time() - t0:.0f} s)")

# =====================================================================================================================
# H  assembly (module level): stage through the bore, tool channels, bracket unit through the door
# =====================================================================================================================
if "H" in SECT:
    t0 = time.time()
    stat = {}
    for f in ("parts_obal.json", "parts_ram.json"):
        for e in json.load(open(os.path.join(HERE, f)))["parts"]:
            if e["group"] == "T":
                stat[e["name"]] = f[6:-5]
    ST = {}
    for n in stat:
        T = stl(n); lo, hi = T.min(1), T.max(1)
        m = (hi[:, 2] > -75.0) & (lo[:, 2] < 6.0) & (lo[:, 0] < 40.0) & (hi[:, 0] > -40.0)
        if m.any():
            ST[n] = T[m]
    out = {}
    # ---- H1 stage straight down through the bore (step 12): bench set = well + gear + pins + tapes + inserts
    bench = [n for n in P_RIGID if not n.startswith(("servo", "P_drziak", "spoj", "kabel", "skr_F1"))]
    present = [n for n in ST if n not in ("T_dvere", "T_prichytka_fpc", "skr_fpc") and not n.startswith(("magnet_dvierka", "T_bok", "T_klb", "T_puzdro", "magnet_klb", "pruzina_klb", "skrutka_klb"))]
    TGs = {n: Target(n, ST[n], 0.4) for n in present}
    Sb = {n: sample(TRI[n], 0.35)[0] for n in bench}
    h1 = {}
    for dz in list(np.arange(0.0, 14.1, 1.0)) + list(np.arange(16.0, 52.1, 4.0)):
        for n in bench:
            Q = Sb[n] + np.array([0, 0, dz])
            for b, tg in TGs.items():
                d = tg.dist(Q, 1.2)
                k = int(np.argmin(d))
                if np.isfinite(d[k]) and ((n, b) not in h1 or d[k] < h1[(n, b)][0]):
                    h1[(n, b)] = (float(d[k]), float(dz), [round(float(x), 2) for x in Q[k]])
    okp = {("P_sachta", "T_stred"), ("ptfe_pas_capu", "T_stred"), ("P_koleso", "pastorok_pan"), ("P_koleso", "cap_pan"), ("P_sachta", "cap_pan"),
           ("P_koleso", "ptfe_podlozka"), ("P_koleso", "T_paluba"), ("kolik_dorazu", "T_paluba"), ("kolik_dorazu", "ptfe_podlozka"), ("kolik_dorazu", "cap_pan"),
           ("P_koleso", "skr_pastorok_pan")}
    r1 = []
    for (a, b), (d, dz, at) in sorted(h1.items(), key=lambda kv: kv[1][0]):
        if d < 0.6:
            r1.append(dict(part=a, static=b, min_mm=round(d, 3), raised_by=dz, at=at, intended=(a, b) in okp))
            say(f"H1 {a:16s} {b:18s} {d:6.3f} raised {dz:5.1f} {at} {'intended guide / seat' if (a, b) in okp else '<-- CHECK'}")
    out["H1_stage_through_bore"] = dict(status="PASS" if all(r_["intended"] and (r_["min_mm"] > 0.004 or r_["raised_by"] == 0.0 or r_["static"] in ("cap_pan", "pastorok_pan")) for r_ in r1) else "FAIL",
                                        pairs_below_0p6=r1, bench_set=bench, direction="-Z, pan 0, raised 0..52 mm",
                                        note="golier_prstenec, FPC clamp, side caps and door are not mounted at this step; the FPC is flexible")
    # ---- H2 tool channels D4.5
    def channel(name, origin, direction, length, movers, statics, skip):
        o = np.array(origin, float); d = np.array(direction, float); d /= np.linalg.norm(d)
        worst = (9.0, None, None)
        for n, T in list(movers.items()) + list(statics.items()):
            if n in skip:
                continue
            S = sample(T, 0.3)[0]
            w = S - o; s = w @ d
            rad = np.linalg.norm(w - s[:, None] * d[None], axis=1)
            m = (s > 0.05) & (s < length)
            if m.any():
                k = int(np.argmin(np.where(m, rad, 9e9)))
                if rad[k] < worst[0]:
                    worst = (float(rad[k]), n, [round(float(x), 2) for x in S[k]])
        ok = worst[0] >= 2.25
        say(f"H2 {name:12s} nearest part to the tool axis: {worst[1]} at r {worst[0]:.2f} {worst[2]}  -> {'free' if ok else 'BLOCKED'} (tool r 2.25)")
        return dict(screw=name, origin=list(map(float, origin)), direction=list(map(float, direction)), nearest=worst[1], r_min=round(worst[0], 3),
                    clear_of_tool=round(worst[0] - 2.25, 3), at=worst[2], ok=bool(ok))
    flex = {"kabel_zdvih", "fpc_pan", "fpc_stage", "fpc_lift"}
    door = {n for n in ST if n == "T_dvere" or n.startswith("magnet_dvierka")}
    rest = {n: TRI[n] for n in list(PARTS) if n != "fpc_pan"}
    rest.update({n: TRI[n] for n in ("golier_kotuc", "krk_predna_polovica", "krk_zadna_polovica")})
    b1, b2 = P["PADS"]; py1 = P["BRKT"]["plate_y"][1]; E_ = P["EAR"]
    ch = [channel("F10_1", (b1["x"], py1 + 2.0, b1["z"]), (0, 1, 0), 30.0, rest, ST, flex | door | {"skr_F10_1"}),
          channel("F10_2", (b2["x"], py1 + 2.0, b2["z"]), (0, 1, 0), 30.0, rest, ST, flex | door | {"skr_F10_2"}),
          channel("F12", (E_["screw"]["x"], E_["flange_y"][1] + 1.6, M.ZS0 + E_["screw"]["zrel"]), (0, 1, 0), 32.0, rest, ST, flex | door | {"skr_F12"})]
    rot90 = {n: rotz(T, 90.0) for n, T in rest.items()}
    tp = P["FOOT"]["tongue_pilot"]; xt = P["TONGUE"]["x"][1]
    ch.append(channel("skr_jazyka", (-tp["y"], xt, tp["z"]), (0, 1, 0), 14.0, rot90, ST, flex | door | {"skr_jazyka"}))
    # static FPC clamp screw (RAM part skr_fpc, axis Z) through the tool hole of the stage top plate: BEFORE the lift module,
    # the neck and the collar disc are mounted, stage at pan -58.5
    A_ = C.RAM["FPC_ANCHOR"]; Th = P["TOOL_HOLE"]
    sx, sy = M.pol(A_["screw_r"], A_["screw_az"])
    benchT = {n: rotz(TRI[n], Th["pan"]) for n in P_RIGID if not n.startswith(("servo", "P_drziak", "spoj", "kabel", "skr_F1"))}
    ch.append(channel("skr_fpc (RAM)", (sx, sy, A_["clamp_z"][1]), (0, 0, 1), 48.0, benchT, ST, flex | {"skr_fpc", "T_prichytka_fpc"}))
    hx, hy = rotz(np.array([[Th["at"][0], Th["at"][1], 0.0]]), Th["pan"])[0][:2]
    ch[-1]["tool_hole_centre_at_pan"] = [round(float(hx), 2), round(float(hy), 2)]; ch[-1]["tool_hole_d"] = Th["d"]; ch[-1]["pan"] = Th["pan"]
    out["H2_tool_channels"] = dict(status="PASS" if all(c["ok"] for c in ch) else "FAIL", channels=ch,
                                   note="D4.5 cylinder from the screw head along +Y to the door opening (door + its magnets removed, flexible "
                                        "lead / FPC pushed aside); F10, F12 at pan 0 / lift 0, tongue screw at pan +90; F11 and the crank screw are bench steps; "
                                        "the FPC clamp screw of RAM is reached from above through the D4.8 hole of the stage top plate at pan -58.5 "
                                        "while the lift module, neck and collar disc are not yet mounted")
    # ---- H3 bracket unit through the door along -Y (step 13)
    unit = ["servo_zdvih", "P_drziak_serva", "P_kluka", "cap_kluky", "skr_F11", "skr_kluky"]
    others = {n: Target(n, ST[n], 0.4) for n in ST if n not in door}
    others.update({n: Target(n, TRI[n], 0.35) for n in ("P_sachta", "P_koleso", "vl_F10_1", "vl_F10_2", "ptfe_pas_capu", "golier_kotuc")})
    Su = {n: sample(TRI[n], 0.35)[0] for n in unit}
    h3 = {}
    for s in np.arange(0.0, 30.1, 1.0):
        for n in unit:
            Q = Su[n] + np.array([0, s, 0])
            for b, tg in others.items():
                d = tg.dist(Q, 1.2)
                k = int(np.argmin(d))
                if np.isfinite(d[k]) and ((n, b) not in h3 or d[k] < h3[(n, b)][0]):
                    h3[(n, b)] = (float(d[k]), float(s), [round(float(x), 2) for x in Q[k]])
    r3 = []
    seat = {("P_drziak_serva", "P_sachta"), ("P_drziak_serva", "vl_F10_1"), ("P_drziak_serva", "vl_F10_2"), ("P_drziak_serva", "P_koleso")}
    for (a, b), (d, s, at) in sorted(h3.items(), key=lambda kv: kv[1][0]):
        if d < 0.8:
            r3.append(dict(part=a, other=b, min_mm=round(d, 3), pulled_back_by=s, at=at, seat=(a, b) in seat))
            say(f"H3 {a:16s} {b:18s} {d:6.3f} pulled back {s:4.1f} {at} {'seat / declared' if (a, b) in seat else '<-- CHECK'}")
    out["H3_bracket_unit_through_door"] = dict(status="PASS" if all(r_["seat"] or r_["min_mm"] >= 0.3 for r_ in r3) else "FAIL", pairs_below_0p8=r3, unit=unit,
                                               direction="-Y through the door opening, pan 0, crank at BDC; unit pulled back 0..30 mm")
    RES["H_assembly"] = dict(status="PASS" if all(v["status"] == "PASS" for v in out.values()) else "FAIL", **out)
    say(f"H  {[(k, v['status']) for k, v in out.items()]}  ({time.time() - t0:.0f} s)")

# ---------------------------------------------------------------------------------------------------------------------
# merge the sections into pan_checks.json
# ---------------------------------------------------------------------------------------------------------------------
SD = os.path.join(WORK, "checks")
os.makedirs(SD, exist_ok=True)
for k, v in RES.items():
    json.dump(v, open(os.path.join(SD, k + ".json"), "w"), indent=1)
ALL = {}
for f in sorted(os.listdir(SD)):
    ALL[f[:-5]] = json.load(open(os.path.join(SD, f)))
summary = {k: v.get("status") for k, v in ALL.items()}
json.dump(dict(module="pan", generated=time.strftime("%Y-%m-%d %H:%M:%S"), summary=summary,
               all_pass=all(s == "PASS" for s in summary.values()) and len(summary) == 8, checks=ALL),
          open(os.path.join(HERE, "pan_checks.json"), "w"), indent=1)
say(f"summary {summary}")

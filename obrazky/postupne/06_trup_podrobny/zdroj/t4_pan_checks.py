#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso, module PAN, REV. 2: module-level checks  ->  pan_checks.json, pan_checks.log

    /opt/venv/cad/bin/python t4_pan_checks.py [A B C D E F G H]      (default: all sections)

A  solids / STL of parts_pan.json; every permanent stage part r <= 26.50 (STL vertices); stage up through the glued collar
   ring (r_in 26.748) and the T_stred journal bore (r 26.65) with the lift-loop tails tucked into the empty well
B  PAN_ENV2 (+ PAN_ENV2_SECTORS) for every stage / lift part over lift 0..20 (stage frame)
C  K3 clearances: (C1) inside the module over lift 0..20 with the declared fits; (C2) moving PAN parts over pan -90.3..90.3 x
   lift 0..20 against the current RAM / OBAL STLs (+ glued collar ring, + the rev. 2 bore as an analytic stand-in while the
   OBAL STL is rev. 1); (C3) 36T gear against the ROTATING RAM pinion (flank gap / backlash)
D  pan hard stop: lug faces against the two RAM stop pins (contact angle, engagement incl. the 0.1 L1 rise)
E  crank kinematics: stroke, dead centres, pin in the ear slot, ear <-> arm gap, arm / pin sweep against the pocket + stage
F  K7: lift module (+ ear on the pin) out through the door at pan 0; neck + DPS_krk up through the collar-disc slot; line of
   sight from the door opening to the DPS_krk ZIF mouths at pan +85; tool paths F10 A/B, F11, F12
G  K13 resin rules: walls (ray scan) of P_sachta / P_drziak_serva, root fillets, closed pockets, print table
H  strength rows of the PAN parts (overenie_pevnost.md rows recomputed on the rev. 2 geometry, Z2 allowables 8.5 / 4.3 / 12.9)

Distances: exact point-to-triangle from surface samples (all vertices + 0.4 mm grid) of the moving part to the triangles of the
other part (STL deflection 0.01).  Cables are checked as solids too (pose solids from t4_pan).
"""
from __future__ import annotations
import os, sys, json, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from scipy.spatial import cKDTree
import t4_common as C
import t4_pan as M

R2 = C.R2; P2 = M.P2
STL = os.path.join(HERE, "stl")
SECT = [a for a in sys.argv[1:] if a in list("ABCDEFGH")] or list("ABCDEFGH")
LOG = open(os.path.join(HERE, "pan_checks.log"), "a" if len(SECT) < 8 else "w")
RESF = os.path.join(HERE, "pan_checks.json")
RES = json.load(open(RESF)) if (len(SECT) < 8 and os.path.exists(RESF)) else {}
RES = {k: v for k, v in RES.items() if isinstance(v, dict) and v.get("rev") == 2}
T0 = time.time()


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n"); LOG.flush()


def put(key, d):
    d["rev"] = 2
    d["run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    RES[key] = d
    json.dump(RES, open(RESF, "w"), indent=1, default=str)


# ---------------------------------------------------------------------------------------------------------------------
# mesh helpers (rev. 1 infrastructure)
# ---------------------------------------------------------------------------------------------------------------------
def tris_of(shape, lin=0.01, ang=0.1):
    V, T = C.mesh_of(shape, lin, ang)
    return V[T]


def stl(name, d=STL):
    return M.read_stl(os.path.join(d, name + ".stl"))


def sample(T, h=0.4, dd=None):
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
        i, j = np.meshgrid(np.arange(nv + 1), np.arange(nv + 1), indexing="ij")
        m = ((i + j) <= nv) & ~(((i == 0) & (j == 0)) | ((i == nv) & (j == 0)) | ((i == 0) & (j == nv)))
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

    def __init__(self, name, T, h=0.4):
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
            best[ok] = np.minimum(best[ok], pt_tri(q[ok], self.T[t, 0], self.T[t, 1], self.T[t, 2]))
        d[m] = best
        return d


def inside_mesh(Q, T):
    """parity test (points strictly inside a closed mesh) - used to tell penetration from contact"""
    A, B, Cc = T[:, 0], T[:, 1], T[:, 2]
    out = np.zeros(len(Q), bool)
    d = np.array([1.0, 0.0137, 0.0071])
    E1, E2 = B - A, Cc - A
    pv = np.cross(d, E2); det = (E1 * pv).sum(1); ok = np.abs(det) > 1e-12; inv = 1 / np.where(ok, det, 1)
    for c0 in range(0, len(Q), 256):
        o = Q[c0:c0 + 256]
        tv = o[:, None, :] - A[None]; u = (tv * pv[None]).sum(2) * inv
        qv = np.cross(tv, E1[None]); v = (qv * d).sum(2) * inv; t = (qv * E2[None]).sum(2) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        out[c0:c0 + 256] = hit.sum(1) % 2 == 1
    return out


def rotz(Q, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = Q.copy(); R[..., 0] = c * Q[..., 0] - s * Q[..., 1]; R[..., 1] = s * Q[..., 0] + c * Q[..., 1]
    return R


def rot_about(Q, deg, cx, cy):
    R = Q.copy(); R[..., 0] -= cx; R[..., 1] -= cy
    R = rotz(R, deg); R[..., 0] += cx; R[..., 1] += cy
    return R


def crank_xform(Q, theta):
    a = math.radians(-theta); c, s = math.cos(a), math.sin(a)
    R = Q.copy(); y, z = Q[..., 1] - M.YL, Q[..., 2] - M.ZL
    R[..., 1] = M.YL + c * y - s * z; R[..., 2] = M.ZL + s * y + c * z
    return R


def ray_hits(O, Dv, T, tmax):
    """True per ray if it hits mesh T within 0 < t < tmax (Moller-Trumbore)"""
    A, E1, E2 = T[:, 0], T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    hit = np.zeros(len(O), bool)
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    for c0 in range(0, len(O), 64):
        o, d = O[c0:c0 + 64], Dv[c0:c0 + 64]
        pv = np.cross(d[:, None, :], E2[None]); det = (E1[None] * pv).sum(2); ok = np.abs(det) > 1e-12
        inv = 1 / np.where(ok, det, 1); tv = o[:, None, :] - A[None]
        u = (tv * pv).sum(2) * inv; qv = np.cross(tv, E1[None]); v = (d[:, None, :] * qv).sum(2) * inv
        t = (E2[None] * qv).sum(2) * inv
        h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6) & (t < tmax[c0:c0 + 64, None])
        hit[c0:c0 + 64] = h.any(1)
    return hit


# ---------------------------------------------------------------------------------------------------------------------
# the module in poses
# ---------------------------------------------------------------------------------------------------------------------
DOC = json.load(open(os.path.join(HERE, "parts_pan.json")))
GRP = {e["name"]: e["group"] for e in DOC["parts"]}
NAMES = [e["name"] for e in DOC["parts"]]
TRI = {n: stl(n) for n in NAMES}
TRI["ffc_riser"] = tris_of(M.ffc_riser())
TRI["ffc_static"] = tris_of(M.ffc_static())
for n in ("golier_kotuc", "golier_prstenec", "krk_predna_polovica", "krk_zadna_polovica"):
    TRI[n] = stl(n, C.B_STL)
CRANK = ("rameno_zdvih", "cap_kluky")
LIFTED = ("L_pata", "L_ucho", "DPS_krk", "skr_F12_1", "kolik_F12", "ffc_A_krk", "ffc_B_krk", "krk_predna_polovica", "krk_zadna_polovica")
POSE_CABLES = ("pigtail_zdvih", "fpc_lift")
STATIC_MINE = ("ffc_static", "ffc_A_nosic", "ffc_B_nosic")
RIGID = [n for n in NAMES if GRP[n] == "P" and n not in CRANK + ("ffc_par", "pigtail_zdvih")] + ["ffc_riser", "golier_kotuc"]
_POSE = {}


def pose_tris(name, lift):
    if name in CRANK:
        return crank_xform(TRI[name], M.crank_angle(lift))
    if name in LIFTED:
        T = TRI[name].copy(); T[..., 2] += lift
        return T
    if name in POSE_CABLES:
        key = (name, lift)
        if key not in _POSE:
            # integrator rev2: pigtail as the exact r 0.7 tube about its spline (the OCC mesher hangs on the sweep at lift 15)
            _POSE[key] = M.pigtail_tris(lift) if name == "pigtail_zdvih" else tris_of(M.fpc_lift(lift), 0.02, 0.2)
        return _POSE[key]
    return TRI[name]


def load_static():
    out, note = {}, {}
    for mod in ("ram", "obal"):
        f = os.path.join(HERE, f"parts_{mod}.json")
        if not os.path.exists(f):
            continue
        d = json.load(open(f))
        note[mod] = dict(generated=d.get("generated"), revision=d.get("revision", 1))
        for e in d["parts"]:
            if e.get("group") == "T" and os.path.exists(os.path.join(STL, e["name"] + ".stl")):
                out[e["name"]] = stl(e["name"])
    out["golier_prstenec"] = TRI["golier_prstenec"]
    return out, note


# =====================================================================================================================
# A  solids + slim stage
# =====================================================================================================================
PERMANENT = ["P_sachta", "koleso_pan", "vl_F10_A", "vl_F10_B", "kolik_F10", "ffc_riser"] + [n for n in NAMES if n.startswith("ptfe_")]
if "A" in SECT:
    bad = []
    for e in DOC["parts"]:
        st = M.mesh_stats(TRI[e["name"]])
        ok = bool(e["valid"] and e["n_solids"] == 1 and e["watertight"] and e.get("bbox_ok", True) and st["open_edges"] == 0
                  and st["nonmanifold_edges"] == 0 and st["flipped_edges"] == 0 and st["volume"] > 0)
        if not ok:
            bad.append(e["name"])
    step_null = [e["name"] for e in DOC["parts"] if e["step"] is None]
    rmax = {}
    for n in PERMANENT:
        V = TRI[n].reshape(-1, 3); rmax[n] = round(float(np.hypot(V[:, 0], V[:, 1]).max()), 3)
    worst = max(rmax.values())
    ring, bore = R2["RING_R_IN"], R2["BORE"]["r"]
    okA = (not bad) and worst <= R2["STAGE_R_MAX"] + 1e-3
    put("A_solids_slim", dict(status="PASS" if okA else "FAIL", n=len(DOC["parts"]), not_ok=bad, step_null=step_null, rmax_permanent=rmax,
                              rmax=worst, limit=R2["STAGE_R_MAX"], ring_clear=round(ring - worst, 3), bore_clear=round(bore - worst, 3),
                              note="permanent stage = P_sachta + 36T gear + inserts / dowel + PTFE tapes + FFC riser with its bonded fixed "
                                   "leg; lift module, crank, neck group removed before; the free lift loop, Z-fold and DPS_krk tails are "
                                   "tucked into the empty well through the end window"))
    say(f"A  {len(DOC['parts'])} parts, not ok {bad}; STEP null {step_null}; permanent stage r max {worst} (limit 26.50) -> ring {ring - worst:.3f}, "
        f"bore {bore - worst:.3f}; per part {rmax}")

# =====================================================================================================================
# B  PAN_ENV2 incl. sectors (stage frame) over lift 0..20
# =====================================================================================================================
ENV_PARTS = [n for n in RIGID if n not in ("golier_kotuc",)] + list(CRANK) + list(LIFTED[:7]) + list(POSE_CABLES)


def env_rmax(z, az):
    r = -1.0
    for z0, z1, rr in C.PAN_ENV2:
        if z0 - 2e-3 <= z <= z1 + 2e-3:
            r = max(r, rr)
    for s in C.PAN_ENV2_SECTORS:
        if s["z"][0] - 2e-3 <= z <= s["z"][1] + 2e-3 and s["az"][0] - 1e-3 <= az <= s["az"][1] + 1e-3:
            r = max(r, s["r"])
    return r


def env_rmax_v(z, az):
    # vectorised env_rmax (integrator rev2: identical bands / tolerances, numpy instead of a per-vertex loop)
    r = np.full(len(z), -1.0)
    for z0, z1, rr in C.PAN_ENV2:
        m = (z >= z0 - 2e-3) & (z <= z1 + 2e-3)
        r[m] = np.maximum(r[m], rr)
    for s in C.PAN_ENV2_SECTORS:
        m = (z >= s["z"][0] - 2e-3) & (z <= s["z"][1] + 2e-3) & (az >= s["az"][0] - 1e-3) & (az <= s["az"][1] + 1e-3)
        r[m] = np.maximum(r[m], s["r"])
    return r


if "B" in SECT:
    viol, margin = {}, {}
    for n in ENV_PARTS:
        for lift in ((0.0, 5.0, 10.0, 15.0, 20.0) if (n in CRANK or n in LIFTED or n in POSE_CABLES) else (0.0,)):
            V = pose_tris(n, lift).reshape(-1, 3)
            V = V[np.unique(np.round(V, 3), axis=0, return_index=True)[1]]
            r = np.hypot(V[:, 0], V[:, 1]); az = np.degrees(np.arctan2(V[:, 1], V[:, 0])) % 360.0
            lim = env_rmax_v(V[:, 2], az)
            exc = r - lim
            k = int(np.argmax(exc))
            margin[n] = min(margin.get(n, 9e9), round(float(-exc[k]), 3))
            if exc[k] > 2e-3:
                viol.setdefault(n, []).append(dict(lift=lift, excess=round(float(exc[k]), 3), at=[round(float(x), 2) for x in V[k]],
                                                   r=round(float(r[k]), 3), az=round(float(az[k]), 1), limit=lim[k]))
    put("B_pan_env2", dict(status="PASS" if not viol else "FAIL", violations=viol, min_margin=margin,
                           note="every vertex of every PAN stage / lift part (lift 0, 5, 10, 15, 20) against PAN_ENV2 + PAN_ENV2_SECTORS; "
                                "the pan rolling loop (duct, shared with RAM) and the static FFC run are checked in C2"))
    say(f"B  PAN_ENV2 violations: {json.dumps(viol)[:1500]}")
    say(f"B  smallest margins: {sorted(margin.items(), key=lambda kv: kv[1])[:12]}")

# =====================================================================================================================
# C  K3 clearances
# =====================================================================================================================
DECL1 = {
    ("L_pata", "P_sachta"): (0.10, "rest gap foot <-> hub disc 0.15 (0.10 .. 0.20), lands 0.5"),
    ("L_ucho", "P_sachta"): (0.10, "ear flange over the back floor 0.15 at rest (lands with the foot)"),
    ("skr_F12_1", "P_sachta"): (0.30, "F12 heads 0.4 over the back floor at rest (the foot lands first)"),
    ("kolik_F12", "L_ucho"): (0.0, "dowel in the flange"), ("kolik_F12", "L_pata"): (0.0, "dowel slip fit D2.05 in the foot (bonded in the ear)"),
    ("skr_F12_1", "L_ucho"): (0.0, "head on the flange"), ("skr_F12_1", "L_pata"): (0.0, "thread"), ("L_ucho", "L_pata"): (0.0, "flange on the foot"),
    ("L_ucho", "DPS_krk"): (0.5, "-"), ("cap_kluky", "P_drziak_serva"): (0.95, "-"),
    ("krk_predna_polovica", "P_sachta"): (0.25, "neck on the lands 0.30 bare, corners 0.59"),
    ("krk_zadna_polovica", "P_sachta"): (0.25, "neck on the lands 0.30 bare, corners 0.59"),
    ("krk_predna_polovica", "golier_kotuc"): (0.0, "B: neck in the collar-disc slot (finished parts)"),
    ("krk_zadna_polovica", "golier_kotuc"): (0.0, "B: neck in the collar-disc slot (finished parts)"),
    ("L_pata", "krk_predna_polovica"): (0.0, "foot bonded to the front neck half"), ("L_pata", "krk_zadna_polovica"): (0.0, "release film"),
    ("DPS_krk", "L_pata"): (0.0, "board bonded in the foot slot"), ("DPS_krk", "krk_predna_polovica"): (0.3, "board 0.5 under the neck"),
    ("DPS_krk", "krk_zadna_polovica"): (0.3, "board 0.5 under the neck"),
    ("ffc_A_krk", "DPS_krk"): (0.0, "FFC in its ZIF"), ("ffc_B_krk", "DPS_krk"): (0.0, "FFC in its ZIF"),
    ("ffc_A_krk", "L_pata"): (0.0, "tail in the foot slot"), ("ffc_B_krk", "L_pata"): (0.0, "tail in the foot slot"),
    ("pigtail_zdvih", "DPS_krk"): (0.0, "soldered"), ("pigtail_zdvih", "L_pata"): (0.0, "in the foot slot"),
    ("pigtail_zdvih", "ffc_A_krk"): (0.0, "cable on cable"), ("pigtail_zdvih", "ffc_B_krk"): (0.0, "cable on cable"),
    ("pigtail_zdvih", "fpc_lift"): (0.0, "cable on cable (move together)"), ("pigtail_zdvih", "konektor_zdvih"): (0.0, "crimped in the plug"),
    ("pigtail_zdvih", "P_drziak_serva"): (0.0, "pigtail end through the wire notch of the plug shelf"),
    ("pigtail_zdvih", "kabel_zdvih"): (0.0, "cable on cable at the plug"),
    ("fpc_lift", "ffc_A_krk"): (0.0, "Z-fold"), ("fpc_lift", "ffc_B_krk"): (0.0, "Z-fold"), ("fpc_lift", "ffc_riser"): (0.0, "same strip"),
    ("fpc_lift", "P_sachta"): (0.0, "fixed leg bonded on the end wall"),
    ("ffc_riser", "P_sachta"): (0.0, "riser / fixed leg bonded"), ("ffc_riser", "koleso_pan"): (0.2, "riser on the shroud, gear tips 0.3 inside"),
    ("koleso_pan", "P_sachta"): (0.0, "gear bonded under the hub disc, tips 0.3 to the shroud"),
    ("ptfe_pas_capu", "P_sachta"): (0.0, "tape on the journal"),
    ("rameno_zdvih", "servo_zdvih"): (0.0, "arm on the spline"), ("rameno_zdvih", "skr_ramena"): (0.0, "arm screw"),
    ("rameno_zdvih", "cap_kluky"): (0.0, "pin pressed in the arm"), ("cap_kluky", "skr_ramena"): (0.3, "-"),
    ("L_ucho", "skr_ramena"): (0.35, "arm screw flush with the arm face: = the 0.4 ear <-> arm gap"),
    ("L_ucho", "P_drziak_serva"): (0.75, "ear 1.0 off the stop bridge, 0.78 off the R1.5 step fillet between the low and the high bridge (rev3 LD3; "
                                         "both are parts of the lift module, relative motion = lift only)"),
    ("DPS_krk", "P_sachta"): (0.45, "board inside the neck footprint: 0.6 to the +X end land, the neck (0.30 / 0.17) guides first"),
    ("cap_kluky", "L_ucho"): (0.09, "pin in the ear slot 0.10 per side"), ("rameno_zdvih", "L_ucho"): (0.35, "ear <-> arm side gap 0.4"),
    # integrator rev2: lift loop as a y-z U (free legs 0.25 off the end wall face, crease block CF on the bonded leg)
    ("pigtail_zdvih", "ffc_riser"): (0.25, "pigtail beside / under the crease block CF and the bonded leg (cable on cable)"),
    ("P_sachta", "ffc_A_krk"): (0.75, "rev3 (v8): R2.0 top corners of the +X end window - the FFC-A tail passes 0.82 under the -Y corner at lift 20 "
                                      "(both on the stage, relative motion = lift only; flexible strip)"),
    ("P_sachta", "ffc_B_krk"): (0.75, "rev3 (v8): same at the +Y top corner (0.89 at lift 20)"),
    ("pigtail_zdvih", "P_sachta"): (0.15, "rev3: the stage floor now lies under the foot slot - the pigtail (flexible, D1.4) runs inside the 4.0 foot "
                                          "thickness 0.35 above the floor (the modelled spline sags 0.3); 1.1 off the end-wall face, under the window edge"),
}
for i in range(1, 9):
    DECL1[("L_pata", f"ptfe_pasik_{i}")] = (0.3, "foot (19.6 x 44.6) 0.37 to the tapes, inside the neck footprint")
    DECL1[("DPS_krk", f"ptfe_pasik_{i}")] = (0.4, "board inside the neck footprint (neck guided at 0.17)")
    DECL1[("krk_predna_polovica", f"ptfe_pasik_{i}")] = (0.15, "neck on the guide tapes 0.17")
    DECL1[("krk_zadna_polovica", f"ptfe_pasik_{i}")] = (0.15, "neck on the guide tapes 0.17")
    DECL1[("ptfe_pasik_%d" % i, "P_sachta")] = (0.0, "tape on its land")
DECL1 = {frozenset(k): v for k, v in DECL1.items()}
DECL2 = {
    ("koleso_pan", "ptfe_podlozka"): (0.0, "gear runs on the PTFE thrust washer (contact)"),
    ("koleso_pan", "ptfe_cap"): (0.0, "gear bore on the taped boss (0.02 radial)"),
    ("koleso_pan", "T_cap"): (0.0, "gear bore around the boss (0.13 tape)"),
    ("koleso_pan", "pd_F15"): (0.05, "retention washer above the gear (rev3: it bears on the hub lip of the well)"),
    # rev3 (R3-1 / R3-2): pivot stack inside the hub lip of the well - declared running fits of the pan bearing
    ("P_sachta", "pd_F15"): (0.10, "DIN 9021 over the hub lip: axial play 0.12 (0.10 .. 0.25), washer in the lip recess r 4.9 (0.4 radial)"),
    ("P_sachta", "pd_F15_d1"): (0.25, "spacer washers r 3.5 in the lip bore r 3.80 (0.30 radial)"), ("P_sachta", "pd_F15_d2"): (0.25, "same"),
    ("P_sachta", "T_cap"): (0.2, "lip bore r 4.15 around the T_cap top (0.30 radial); lip nose 0.2 above the T_cap top"),
    ("P_sachta", "ptfe_cap"): (0.2, "same (taped boss)"),
    ("koleso_pan", "pd_F15_d1"): (0.45, "spacer washer r 3.5 above the gear bore r 4.0"), ("koleso_pan", "pd_F15_d2"): (0.7, "same"),
    ("L_pata", "pd_F15"): (0.99, "foot hole r 5.5 around the DIN 9021 r 4.5: 1.00 by design (STL chords 0.002)"),
    ("koleso_pan", "pastorok_pan"): (0.0, "mesh - checked in C3 with the rotating pinion"),
    ("P_sachta", "pastorok_pan"): (1.0, "-"),
    ("koleso_pan", "T_paluba"): (0.25, "gear teeth 0.3 over the deck (stack 17.1: PTFE washer 0.3 only r 5..12)"),
    ("koleso_pan", "T_most"): (0.25, "gear 0.3 over the Al bridge (stack 17.1)"),
    ("koleso_pan", "skr_F3b_1"): (0.25, "gear 0.3 over the flush F3b head (stack 17.1)"), ("koleso_pan", "skr_F3b_2"): (0.25, "same"),
    ("koleso_pan", "servo_pan"): (0.3, "gear tips 0.2 radial / 0.3 above the pan-servo boss top -46.2 (stack 17.2.2)"),
    ("ffc_riser", "T_paluba"): (0.05, "FFC band 0.1 over the deck (R2 FFC z -46.1)"), ("ffc_riser", "T_most"): (0.05, "same"),
    ("ffc_riser", "skr_F3b_1"): (0.05, "same (flush head)"), ("ffc_riser", "skr_F3b_2"): (0.05, "same"),
    ("fpc_loop", "T_most"): (0.05, "FFC band 0.1 over the bridge"), ("fpc_loop", "skr_F3b_1"): (0.05, "same (flush head)"),
    ("fpc_loop", "skr_F3b_2"): (0.05, "same"), ("fpc_loop", "pastorok_pan"): (1.0, "-"),
    ("P_sachta", "T_most"): (0.55, "drum shroud 0.6 over the bridge"), ("P_sachta", "skr_F3b_1"): (0.55, "shroud 0.6 over the flush head"),
    ("P_sachta", "skr_F3b_2"): (0.55, "same"), ("P_sachta", "golier_prstenec"): (0.2, "stage top 0.248 inside the glued collar ring (A1)"),
    ("P_sachta", "T_paluba"): (0.55, "drum shroud 0.6 over the deck"),
    ("P_drziak_serva", "kolik_dorazu_1"): (0.0, "lug on the stop pin at pan -90 (contact)"),
    ("P_drziak_serva", "kolik_dorazu_2"): (0.0, "lug on the stop pin at pan +90 (contact)"),
    ("ptfe_pas_capu", "T_stred"): (0.0, "taped journal in the bore (0.15 bare)"), ("P_sachta", "T_stred"): (0.1, "journal 0.15 in the bore"),
    ("ptfe_pas_capu", "bore_R2_standin"): (0.0, "taped journal in the rev. 2 bore"), ("P_sachta", "bore_R2_standin"): (0.1, "journal 0.15 / 0.28 bare"),
    ("golier_kotuc", "golier_prstenec"): (0.2, "collar seam 0.248 (B)"), ("golier_kotuc", "bore_R2_standin"): (0.1, "-"),
    ("fpc_loop", "T_paluba"): (0.0, "outer run on the static wall, U-turn over the deck (cable)"),
    ("fpc_loop", "P_sachta"): (0.0, "inner run on the drum shroud (cable)"), ("fpc_loop", "koleso_pan"): (0.25, "inner run 0.3 outside the tips"),
    ("ffc_static", "T_paluba"): (0.0, "through the deck slot / on the static wall"),
    ("ffc_static", "T_spodok"): (0.0, "through the cradle-wall slot (approximate route)"),
    ("ffc_A_nosic", "DPS_riadenie"): (0.0, "FFC in the FH12 ZIF"), ("ffc_B_nosic", "DPS_riadenie"): (0.0, "FFC in the FH12 ZIF"),
    ("fpc_loop", "ffc_static"): (0.0, "same strip"),
    # integrator rev2
    ("golier_kotuc", "T_stred"): (0.1, "collar disc r 26.50 in the journal bore r 26.65 (0.15, B / A2)"),
    ("P_drziak_serva", "T_paluba"): (0.85, "lug 1.0 off the deck C-ear at the nominal stops +-90.0; 0.87 only at the +-90.3 tolerance pose "
                                           "(pin position +-0.15 = +-0.29 deg)"),
}
DECL2[("P_sachta", "servo_pan")] = (0.99, "rev3 (R3-3): floor underside relieved 0.2 over the STS3032 spline tip - designed at exactly 1.00 (the check "
                                           "measures 0.999x on the 0.01 STL)")
DECL2[("P_drziak_serva", "T_spodok")] = (0.99, "module bottom -41.9 vs T_spodok: designed at exactly 1.00 (0.999x on the 0.01 STL; unchanged since round 1)")
DECL2 = {frozenset(k): v for k, v in DECL2.items()}

if "C" in SECT:
    t0 = time.time()
    LIFTS = (0.0, 2.5, 5.0, 10.0, 15.0, 20.0)
    MOV = list(CRANK) + list(LIFTED) + list(POSE_CABLES)
    TGT = {n: Target(n, TRI[n]) for n in RIGID}
    res1 = {}
    for lift in LIFTS:
        Tm = {n: pose_tris(n, lift) for n in MOV}
        Sm = {n: sample(Tm[n])[0] for n in MOV}
        for n in MOV:
            for s in RIGID:
                d = TGT[s].dist(Sm[n], 1.2)
                if np.isfinite(d).any() and d.min() < 1.0:
                    key = frozenset((n, s)); v = float(d.min())
                    if key not in res1 or v < res1[key][0]:
                        res1[key] = (v, lift)
        TgM = {n: Target(n, Tm[n]) for n in MOV}
        for i, a in enumerate(MOV):
            for bn in MOV[i + 1:]:
                if a in LIFTED and bn in LIFTED:
                    continue
                d = TgM[bn].dist(Sm[a], 1.2)
                if np.isfinite(d).any() and d.min() < 1.0:
                    key = frozenset((a, bn)); v = float(d.min())
                    if key not in res1 or v < res1[key][0]:
                        res1[key] = (v, lift)
    und1, dec1 = [], []
    for key, (v, lift) in sorted(res1.items(), key=lambda kv: kv[1][0]):
        row = dict(pair=sorted(key), min=round(v, 3), lift=lift)
        if key in DECL1 and v >= DECL1[key][0] - 1e-3:
            row["declared"] = DECL1[key][1]; dec1.append(row)
        else:
            und1.append(row)
    put("C1_module", dict(status="PASS" if not und1 else "FAIL", undeclared_below_1=und1, declared=dec1, lifts=LIFTS,
                          note="moving parts (crank, foot group, neck halves, pigtail, lift loop) against the stage-rigid PAN parts and "
                               "against each other at lift 0 .. 20; pairs below 1.0 must be declared fits"))
    say(f"C1 undeclared below 1.0: {und1[:30]}")
    say(f"C1 declared: {[(r['pair'], r['min']) for r in dec1][:60]}  ({time.time() - t0:.0f} s)")

if "C" in SECT:
    t0 = time.time()
    ST, NOTE = load_static()
    obal_rev = NOTE.get("obal", {}).get("revision", 1)
    if obal_rev < 2:
        ST["bore_R2_standin"] = tris_of(C.tube_z(R2["BORE"]["r"] + 3.0, R2["BORE"]["r"], *R2["BORE"]["z"]))
        ST.pop("T_stred", None)                           # rev. 1 bore r 28.34 would hide the rev. 2 journal fit
    TGT2 = {n: Target(n, T) for n, T in ST.items()}
    PANS = [-90.3, -90.0, -85.0, -75.0, -60.0, -45.0, -30.0, -15.0, 0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 85.0, 90.0, 90.3]
    LIFTS2 = (0.0, 5.0, 10.0, 15.0, 20.0)
    res2 = {}
    SAMP = {(n, 0.0): sample(TRI[n])[0] for n in RIGID}
    for n in list(CRANK) + list(LIFTED) + list(POSE_CABLES):
        for lift in LIFTS2:
            SAMP[(n, lift)] = sample(pose_tris(n, lift))[0]

    def run(name, S, pan, lift):
        Q = rotz(S, pan)
        lo, hi = Q.min(0), Q.max(0)
        for s, tg in TGT2.items():
            if np.any(lo > tg.hi + 1.2) or np.any(hi < tg.lo - 1.2):
                continue
            d = tg.dist(Q, 1.2)
            if np.isfinite(d).any() and d.min() < 1.0:
                key = frozenset((name, s)); v = float(d.min())
                if key not in res2 or v < res2[key][0]:
                    res2[key] = (v, pan, lift)
    for pan in PANS:
        for (n, lift), S in SAMP.items():
            run(n, S, pan, lift)
        run("fpc_loop", sample(tris_of(M.fpc_loop(pan), 0.02, 0.2))[0], 0.0, 0.0)
        say(f"C2   pan {pan} done ({time.time() - t0:.0f} s)")
    for n in STATIC_MINE:
        run(n, sample(TRI[n])[0], 0.0, 0.0)
    und2, dec2 = [], []
    for key, (v, pan, lift) in sorted(res2.items(), key=lambda kv: kv[1][0]):
        row = dict(pair=sorted(key), min=round(v, 3), pan=pan, lift=lift)
        stop_pose = ("P_drziak_serva" in key and any(k.startswith("kolik_dorazu") for k in key) and abs(abs(pan) - 90.0) < 0.35)
        if (key in DECL2 and v >= DECL2[key][0] - 1e-3) or stop_pose:
            row["declared"] = DECL2.get(key, (0, "stop contact"))[1]; dec2.append(row)
        else:
            if any(x in key for x in STATIC_MINE):
                row["note"] = "static PAN cable in the RAM zone (approximate route)"
            und2.append(row)
    put("C2_static", dict(status="PASS" if not und2 else "FAIL", undeclared_below_1=und2, declared=dec2, static_sources=NOTE,
                          obal_rev2_available=obal_rev >= 2, pans=PANS, lifts=LIFTS2,
                          note="every moving PAN part sampled (vertices + 0.4 grid) and rotated by pan, against the triangles of every "
                               "static RAM / OBAL part (+ glued collar ring); T_stred replaced by the analytic rev. 2 bore while OBAL is rev. 1"))
    say(f"C2 static sources {NOTE}; OBAL rev2 STL: {obal_rev >= 2}")
    say(f"C2 undeclared below 1.0: {und2[:40]}")
    say(f"C2 declared: {[(r['pair'], r['min'], r['pan']) for r in dec2][:40]}  ({time.time() - t0:.0f} s)")

if "C" in SECT:
    if os.path.exists(os.path.join(STL, "pastorok_pan.stl")):
        Tp = stl("pastorok_pan"); Tg = TRI["koleso_pan"]
        Sg = sample(Tg, 0.15)[0]
        z0, z1 = R2["GEAR_PAN"]["plane"]
        Sg = Sg[(Sg[:, 2] > z0 + 0.3) & (Sg[:, 2] < z1 - 0.3) & (np.hypot(Sg[:, 0], Sg[:, 1]) > 13.5)]
        Vp = Tp.reshape(-1, 3)
        pz = (round(float(Vp[:, 2].min()), 3), round(float(Vp[:, 2].max()), 3))
        rows = []
        for pan in np.arange(-90.0, 90.01, 2.5):
            Tq = rot_about(Tp, -2.0 * pan, *M.AX)
            tg = Target("p", Tq, 0.15)
            Q = rotz(Sg, pan)
            d = tg.dist(Q, 1.0)
            near = np.isfinite(d) & (d < 0.05)
            pen = inside_mesh(Q[near], Tq) if near.any() else np.zeros(0, bool)
            rows.append((round(float(pan), 1), round(float(d.min()), 4), int(pen.sum())))
        mn = min(r[1] for r in rows); npen = sum(r[2] for r in rows)
        okc = mn > 0.0 and npen == 0 and mn < 0.1
        put("C3_mesh", dict(status="PASS" if okc else "FAIL", min_flank_gap=mn, penetrating_samples=npen, poses=len(rows), pinion_z=pz,
                            per_pose=rows[::6], note="36T gear samples (teeth, mid face) against the RAM pinion STL turned by -2 x pan "
                                                     "about PAN_AX (ratio 2); min flank gap ~ half the normal backlash"))
        say(f"C3 gear <-> rotating pinion: min flank gap {mn:.4f} over {len(rows)} poses, penetrating samples {npen}; pinion z {pz}")
    else:
        put("C3_mesh", dict(status="NOT RUN", note="pastorok_pan.stl missing"))

# =====================================================================================================================
# D  pan hard stop
# =====================================================================================================================
if "D" in SECT:
    St = R2["STOP"]; Lg = P2["POCKET"]["lug"]
    V = sample(TRI["P_drziak_serva"], 0.1)[0]
    V = V[V[:, 2] < St["pin_top"] + 0.001]
    out = {}
    for i, (px, py) in enumerate(St["pin_xy"], 1):
        def gap(pan, px=px, py=py):
            Q = rotz(V, pan)
            return float(np.min(np.hypot(Q[:, 0] - px, Q[:, 1] - py)) - St["pin_d"] / 2)
        sgn = -1.0 if i == 1 else 1.0
        a = 0.0
        while gap(a + sgn * 0.25) > 0 and abs(a) < 120:
            a += sgn * 0.25
        b = a + sgn * 0.25
        for _ in range(40):
            mid = (a + b) / 2
            if gap(mid) > 0:
                a = mid
            else:
                b = mid
        out[f"pin_{i}"] = dict(contact_pan=round(a, 3), expected=St["stops"][i - 1], err=round(a - St["stops"][i - 1], 3))
    # real pin meshes (RAM) if present
    real = {}
    for i in (1, 2):
        f = os.path.join(STL, f"kolik_dorazu_{i}.stl")
        if os.path.exists(f):
            Vp = stl(f"kolik_dorazu_{i}").reshape(-1, 3)
            real[f"pin_{i}"] = dict(xy=[round(float(c), 2) for c in (Vp[:, :2].max(0) + Vp[:, :2].min(0)) / 2], top=round(float(Vp[:, 2].max()), 3),
                                    r=round(float((Vp[:, 0].max() - Vp[:, 0].min()) / 2), 3))
    eng = round(St["pin_top"] - Lg["z"][0], 3)
    ok = all(abs(v["err"]) <= 0.3 for v in out.values()) and eng - 0.1 >= 2.5 - 1e-6
    put("D_stop", dict(status="PASS" if ok else "FAIL", contact=out, engagement=eng, engagement_L1=round(eng - 0.1, 3),
                       bridge_over_pin=round(P2["POCKET"]["bridge"]["z"][0] - St["pin_top"], 3), ram_pins=real,
                       note="lug vertices below the pin top rotated by pan until they touch the stop-pin cylinder r 1.5 (R2 positions); "
                            "engagement = pin top - lug bottom; L1 rise 0.10 = pivot axial play"))
    say(f"D  stop contact {out}; engagement {eng} ({eng - 0.1:.2f} with the L1 rise); RAM pins {real}")

# =====================================================================================================================
# E  crank kinematics
# =====================================================================================================================
if "E" in SECT:
    E = P2["EAR"]
    th = np.linspace(0.0, 180.0, 181)
    lift = np.array([10.0 * (1 - math.cos(math.radians(t))) for t in th])
    stroke = round(float(lift.max() - lift.min()), 4)
    dl0, dl1 = lift[1] - lift[0], lift[-1] - lift[-2]
    zc0 = (E["slot_z"][0] + E["slot_z"][1]) / 2; hw = E["slot_w"] / 2; pr = 1.0
    flank, end_front, end_back = [], [], []
    for t in np.linspace(3.0, 177.0, 59):
        y, z = M.pin_pos(t); L = 10.0 * (1 - math.cos(math.radians(t)))
        flank.append(hw - pr - abs(z - (zc0 + L)))
        end_front.append((y - pr) - E["slot_y"][0])
        end_back.append(E["slot_y"][1] - (y + pr))
    arm_gap = round(P2["ARM"]["arm_x"][0] - E["plate_x"][1], 3)
    tg = {n: Target(n, TRI[n]) for n in ("P_drziak_serva", "P_sachta", "servo_zdvih")}
    sweep = {}
    for n in ("rameno_zdvih", "cap_kluky"):
        S0 = sample(TRI[n])[0]
        for t in np.linspace(0.0, 180.0, 37):
            S = crank_xform(S0, t); L = 10.0 * (1 - math.cos(math.radians(t)))
            Tq = TRI["L_ucho"].copy(); Tq[..., 2] += L
            for s, T_ in list(tg.items()) + [("L_ucho", Target("L_ucho", Tq))]:
                if s == "servo_zdvih" and n == "rameno_zdvih":
                    continue
                d = T_.dist(S, 1.2)
                v = float(d.min()) if np.isfinite(d).any() else 9.0
                k = f"{n}<->{s}"
                if k not in sweep or v < sweep[k][0]:
                    sweep[k] = (round(v, 3), round(float(t), 1))
    bad = [k for k, (v, t) in sweep.items() if v < 1.0 and not (k == "cap_kluky<->L_ucho" and v >= 0.09)
           and not (k == "rameno_zdvih<->L_ucho" and v >= 0.35)]
    ok = abs(stroke - 20.0) < 1e-3 and min(flank) >= 0.09 and min(end_front) >= 0.09 and min(end_back) >= 0.09 and not bad
    put("E_crank", dict(status="PASS" if ok else "FAIL", stroke=stroke, dlift_dtheta_at_dead_centres=(round(dl0, 4), round(dl1, 4)),
                        pin_slot_flank_min=round(min(flank), 3), slot_front_end_min=round(min(end_front), 3),
                        slot_back_end_min=round(min(end_back), 3), ear_arm_gap=arm_gap, sweep_min=sweep, sweep_undeclared=bad,
                        working_range_deg=(3.0, 177.0), note="lift = 10 (1 - cos theta); pin r 1.0 in the 2.20 slot (0.10 per side); "
                                                             "sweep of the arm and the pin every 5 deg against the pocket, stage and ear"))
    say(f"E  stroke {stroke}; flank {min(flank):.3f}; slot ends front {min(end_front):.3f} back {min(end_back):.3f}; ear-arm {arm_gap}; sweep {sweep}; bad {bad}")

# =====================================================================================================================
# F  K7 assembly / service
# =====================================================================================================================
MODULE = ["P_drziak_serva", "servo_zdvih", "rameno_zdvih", "cap_kluky", "skr_ramena", "skr_F11", "podl_F11", "matica_F11", "L_ucho",
          "kolik_F12"]   # integrator rev2: F12 dowel bonded in the ear
SOFT = ["konektor_zdvih", "kabel_zdvih"]          # unplugged before the module moves; the lead is tucked on the servo


_TGC = {}


def seg_clear(p0, p1, Ts, r, skip=(), tag=""):
    n = max(2, int(np.linalg.norm(np.subtract(p1, p0)) / 0.2))
    Q = np.linspace(p0, p1, n)
    best = (9.0, None)
    for name, T in Ts.items():
        if name in skip:
            continue
        key = (tag, name)
        if key not in _TGC:
            _TGC[key] = Target(name, T, 0.3)
        d = _TGC[key].dist(Q, r + 1.5)
        v = float(d.min()) if np.isfinite(d).any() else 9.0
        if v - r < best[0]:
            best = (round(v - r, 3), name)
    return best


if "F" in SECT:
    t0 = time.time()
    ST, NOTE = load_static()
    ST.pop("T_dvere", None)
    STAGE = {n: TRI[n] for n in RIGID if n not in MODULE + SOFT + ["skr_F10_A", "skr_F10_B", "podl_F10_A", "podl_F10_B"]}
    for n in LIFTED:
        if n not in MODULE:
            STAGE[n] = TRI[n]
    STAGE["fpc_lift"] = pose_tris("fpc_lift", 0.0); STAGE["pigtail_zdvih"] = pose_tris("pigtail_zdvih", 0.0)
    MODT = {n: TRI[n] for n in MODULE}
    # F1
    worst = {}
    allT = {**ST, **{k: v for k, v in STAGE.items() if k not in ("pigtail_zdvih",)}}
    tgs = {k: Target(k, v) for k, v in allT.items()}
    SM = {n: sample(T)[0] for n, T in MODT.items()}
    for dy in np.arange(0.0, 26.01, 1.0):
        for n, S in SM.items():
            Q = S.copy(); Q[:, 1] += dy
            lo, hi = Q.min(0), Q.max(0)
            for s, tg in tgs.items():
                if np.any(lo > tg.hi + 1.0) or np.any(hi < tg.lo - 1.0):
                    continue
                d = tg.dist(Q, 1.0)
                if np.isfinite(d).any():
                    v = float(d.min())
                    if v < 0.8 and ((n, s) not in worst or v < worst[(n, s)][0]):
                        worst[(n, s)] = (round(v, 3), float(dy))
    slide = {("kolik_F12", "L_pata"), ("P_drziak_serva", "kolik_F10")}       # slide fits along Y (the module leaves along them)
    blocked = {f"{a}<->{b}": v for (a, b), v in worst.items() if v[1] > 0.3 and v[0] < 0.1 and not ((a, b) in slide and v[1] <= 3.5)}
    tight = {f"{a}<->{b}": v for (a, b), v in worst.items() if v[1] > 0.3 and v[0] >= 0.1}
    F1 = dict(status="PASS" if not blocked else "FAIL", blocked=blocked, below_0_8=tight,
              note="module group (pocket, MG90S, arm, pin, plug, lead, F11, ear hanging on the pin) translated +Y 0 .. 26 at pan 0, "
                   "door removed, against the static RAM / OBAL meshes and the stage parts (seats at dy 0 are contacts by design)")
    say(f"F1 lift module out +Y: blocked {blocked}; tight {tight}")
    # F2
    grid = np.array([(x, y) for x in np.arange(-26, 26.01, 0.25) for y in np.arange(-12, 12.01, 0.25)])
    O = np.c_[grid, np.full(len(grid), 10.0)]; Dv = np.tile([0, 0, -1.0], (len(O), 1))
    blockedD = ray_hits(O, Dv, TRI["golier_kotuc"], np.full(len(O), 30.0))
    FP = np.concatenate([TRI[n].reshape(-1, 3)[:, :2] for n in ("L_pata", "DPS_krk")])
    dd, _ = cKDTree(grid[~blockedD]).query(FP)
    open_frac = float((dd < 0.2).mean())
    F2 = dict(status="PASS" if open_frac > 0.999 else "FAIL", footprint_inside_slot=round(open_frac, 4),
              note="plan footprint of foot + DPS_krk + unplugged tails against the open area of the collar disc (vertical rays, 0.25 grid)")
    say(f"F2 neck group through the disc slot: footprint inside the opening {open_frac:.4f}")
    # F3
    F3s = {}
    for pan in (85.0, 90.0):
      Z = P2["DPS"]["zif"]
      tgtp = np.array([(Z["x"][1] + 0.05, y, (Z["z"][0] + Z["z"][1]) / 2) for y0, y1 in Z["y"] for y in np.linspace(y0 + 0.4, y1 - 0.4, 5)])
      tgtp = rotz(tgtp, pan)
      door = np.array([(x, 40.0, z) for x in np.linspace(-26.0, 26.0, 11) for z in np.linspace(-70.0, -14.0, 11)])
      obst = dict(ST)
      for n, T in STAGE.items():
          if n not in ("DPS_krk", "ffc_A_krk", "ffc_B_krk", "pigtail_zdvih", "fpc_lift"):   # the cable being plugged is not an obstacle
              obst[n] = rotz(T, pan)
      for n in MODULE:
          obst[n] = rotz(TRI[n], pan)
      Oall, Dall, Tm = [], [], []
      for p in tgtp:
          v = p - door; L = np.linalg.norm(v, axis=1); Oall.append(door); Dall.append(v / L[:, None]); Tm.append(L - 0.3)
      Oall = np.concatenate(Oall); Dall = np.concatenate(Dall); Tm = np.concatenate(Tm)
      hit = np.zeros(len(Oall), bool)
      blockers = {}
      for n, T in obst.items():
          h = ray_hits(Oall, Dall, T, Tm)
          if h.any():
              blockers[n] = int((h & ~hit).sum())
          hit |= h
      free = float((~hit).mean())
      per = [round(float((~hit[i * len(door):(i + 1) * len(door)]).mean()), 3) for i in range(len(tgtp))]
      # rev3 (R3-3 b, recorded in opravy3.md): the stage now has a CLOSED floor (z -41.9 .. -40.65) - a ZIF mouth cannot be seen from below it.
      # The criterion counts the door points ABOVE the floor underside (the rev. 2 number over the whole opening is still reported)
      up = np.tile(door[:, 2] > C.R3["FLOOR"]["z"][0], len(tgtp)); free_up = float((~hit[up]).mean())
      F3s[pan] = dict(line_of_sight=round(free, 3), line_of_sight_above_floor=round(free_up, 3), per_target=per, blockers=blockers)
      F3 = dict(status="PASS" if free_up >= 0.8 else "FAIL", line_of_sight=round(free, 3), per_target=per, pan=pan, blockers=blockers,
                note="121 points on the door opening (x -26..26, z -70..-14, y 40) to 10 points on the two ZIF mouths, stage at pan +85, "
                     "door off; obstacles: every static RAM / OBAL part (T_stred rev. 1 STL), the stage and the lift module")
    best = max(F3s, key=lambda k: F3s[k]["line_of_sight"])
    F3 = dict(status="PASS" if F3s[90.0]["line_of_sight_above_floor"] >= 0.8 else "FAIL", plug_pan=90.0,
              criterion="rev3: >= 0.8 of the lines from the door points ABOVE the stage floor underside (z > -41.9); rev. 2 (open-bottom stage): >= 0.8 "
                        "of all 121 door points - with the closed floor of R3-3 (b) that number is reported only (line_of_sight)",
              by_pan=F3s, note="121 door points (x -26..26, z -70..-14, y 40) to 10 points on the two ZIF mouths; obstacles: every static "
                               "RAM / OBAL part, the stage and the lift module; the FFC being plugged is not an obstacle.  Procedure "
                               "(integrator rev2, 17.15): the FFCs are plugged with the stage turned BY HAND to the +90 stop (the lug "
                               "on pin 2), not at the firmware +85")
    say(f"F3 ZIF line of sight: {json.dumps(F3s)}")
    # F4
    tools = {}
    allT2 = {**ST, **STAGE, **MODT}
    yp = P2["POCKET"]["plate"]["y"][1] + 0.3 + 1.3
    for tag in ("A", "B"):
        x, z = P2["F10"][tag]
        if tag == "B":   # fixer rev2: F10_B (18.0, -33.3) beside the MG90S case -> 1.3 hex precision screwdriver (blade 1.5 across corners)
            ypb = yp - P2["F10_B_CB"]["depth"]
            tools["F10_B"] = (seg_clear((x, ypb + 0.8, z), (x, 40.0, z), allT2, 0.8, tag="p0"),
                              "1.3 hex precision screwdriver (blade r 0.8) along -Y at pan 0; head in the D4.8 x 0.4 counterbore beside the servo case",
                              seg_clear((x, ypb + 2.3, z), (x, 40.0, z), allT2, 2.25, tag="p0"))
            continue
        tools[f"F10_{tag}"] = (seg_clear((x, yp + 2.3, z), (x, 40.0, z), allT2, 2.25, tag="p0"), "D4.5 along -Y at pan 0 (servo seated); axis from the head top + r",
                               seg_clear((x, yp + 1.6, z), (x, 40.0, z), allT2, 1.5, tag="p0"))
    zt = C.LIFT_CASE["z"][1] + C.MG90S["tab"]["hole"]
    all85 = {k: (rotz(v, -85.0) if k in ST else v) for k, v in allT2.items() if k not in SOFT}   # static parts seen from the stage at pan +85
    sk11 = ("skr_F11", "podl_F11", "matica_F11")
    tools["F11"] = (seg_clear((1.6 + 2.3, M.YL, zt), (60.0, M.YL, zt), all85, 2.25, skip=sk11, tag="p85"),
                    "INFORMATION ONLY (F11 is driven on the bench with the lift module out, 17.11 B5 / service): D4.5 along -X from "
                    "the door at pan +85",
                    seg_clear((1.6 + 1.6, M.YL, zt), (60.0, M.YL, zt), all85, 1.5, skip=sk11, tag="p85"))
    for i, hx in enumerate(P2["EAR"]["holes_x"], 1):
        y0 = P2["EAR"]["flange_y"][1] + 1.3 + 0.2
        sk = (f"skr_F12_{i}", "kolik_F12")
        tools[f"F12_{i}"] = (seg_clear((hx, y0, P2["EAR"]["hole_z"]), (hx, 40.0, P2["EAR"]["hole_z"]), allT2, 0.65, skip=sk, tag="p0"),
                             "1.3 hex key (long leg) along -Y at pan 0 through the D2.4 key hole of the stop bridge",
                             seg_clear((hx, y0, P2["EAR"]["hole_z"]), (hx, 40.0, P2["EAR"]["hole_z"]), allT2, 2.25, skip=sk, tag="p0"))
    okT = all(v[0][0] >= 0.0 for k, v in tools.items() if k != "F11")      # F11 is driven on the bench (B5b, module out)
    F4 = dict(status="PASS" if okT else "FAIL", tools={k: dict(clear=v[0][0], nearest=v[0][1], tool=v[1],
                                                                 **({"alt": v[2]} if len(v) > 2 else {})) for k, v in tools.items()},
              note="tool axis sampled every 0.2 from the screw head to y / x 40 (outside the door); distance to every mesh minus the "
                   "tool radius ('alt' = the other tool size)")
    say(f"F4 tool paths: {F4['tools']}")
    put("F_k7", dict(status="PASS" if all(d["status"] == "PASS" for d in (F1, F2, F3, F4)) else "FAIL", F1=F1, F2=F2, F3=F3, F4=F4,
                     static_sources=NOTE))
    say(f"F  done ({time.time() - t0:.0f} s)")

# =====================================================================================================================
# G  resin rules K13
# =====================================================================================================================
def sample_in(T, h):
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
        opp = (d @ N.T) > 0.8
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-3)
        tt = np.where(hit, t, np.inf)
        j = np.argmin(tt, axis=1); t1 = tt[np.arange(len(o)), j]
        th[c0:c0 + 128] = np.where(opp[np.arange(len(o)), j], t1, np.inf)
    return S, th


def _r(p):
    return math.hypot(p[0], p[1])


STRUCT = 2.0
DECL_THIN = {
    "P_sachta": [
        ("well end / front walls 1.6 (declared guide walls, section 17.3); back wall 1.6 at x < -6", lambda p: abs(abs(p[0]) - 24.3) < 0.9 or p[1] < -10.9 or (p[1] > 10.9 and p[0] < -5.9), 1.55),
        ("trimmed outer corners 1.35 (r 26.50 vs inner R2.5), local >= 1.2", lambda p: _r(p) > 24.3 and abs(p[0]) > 20.0 and abs(p[1]) > 7.5, 1.2),
        ("guide lands 0.7 high (ray from a land flank / lead-in)", lambda p: (abs(abs(p[1]) - 10.65) < 0.45 or abs(abs(p[0]) - 23.15) < 0.45) and p[2] > -39.0, 0.6),
        ("drum shroud 1.2 (cable guide, unloaded) and its ends", lambda p: 15.4 < _r(p) < 16.8 and p[2] < -41.85, 1.15),
        ("FFC retaining lip 0.8 x 0.6 (cable only)", lambda p: 16.6 < _r(p) < 17.6 and p[2] < -41.8, 0.55),
        ("0.8 floor behind the F10 insert seats (pilot through; the insert pull acts outward); 1.1 behind the dowel hole", lambda p: 11.4 < p[1] < 12.2 and p[2] > -39.2, 0.75),
        ("R1 root fillets inside the well (ray across the fillet strip)", lambda p: abs(abs(p[1]) - 10.5) < 0.6 and -40.7 < p[2] < -39.5, 1.3),
        ("back floor / hub disc 1.25 (compression on the gear) and 0.95 over the 0.3 FFC groove (fixer rev2: up to z -40.4 = the floor top "
         "edge at the FFC under-run arc r 16.72)", lambda p: p[2] < -40.4, 0.9),
        ("journal ring 2.0 with the 0.5 lead-in chamfer; top plate 1.5 (collar-disc glue land)", lambda p: p[2] > -10.1, 1.45),
        ("rev3: mounting plateau 2.1 on the back wall (0.15 face recess between the contact zones), 0.7 edge chamfer under the down-stop nose", lambda p: p[1] > 12.9 and -6.6 < p[0] < 22.0, 1.45),
        ("insert / dowel / pilot holes in the r 3.25 .. 3.5 pads", lambda p: p[1] > 10.9 and p[2] > -37.4 and p[0] > 3.0, 1.0),
        ("end-wall edge round R0.6 at the FFC wrap; window jambs", lambda p: p[0] > 23.0, 1.2),
        ("rev3 (v9): R1.5 fillet between the raised sill (curb z -39.5) of the +X end window and its jamb y 3.4 - ray across the run-out of the fillet strip",
         lambda p: p[0] > 22.9 and 1.5 < p[1] < 3.6 and -39.6 < p[2] < -37.9, 0.25),
        ("rev3: R1 floor root at the end walls and corners (wall 1.6 / corner 1.5 + fillet run-out)", lambda p: (abs(p[0]) > 22.9 or _r(p) > 23.0) and -40.7 < p[2] < -39.0, 1.5),
        ("rev3 (R3-2): hub lip under the DIN 9021 - lip 0.98 thick, retention nose 0.68 x 0.35 (FE row 'hub ring / lip'; fail-safe rows)", lambda p: _r(p) < 5.2 and p[2] > -42.0, 0.6),
        ("rev3 (R3-3): 0.2 relief of the floor underside over the spline-tip annulus r 18 .. 25.2 (floor 1.05), relief rim", lambda p: p[2] < -41.6 and 17.9 < _r(p) < 25.0, 0.65),
        ("rev3: feather edge where that relief (r 25.2) runs out through the end faces (-X: |y| < 2.5; +X: y -2.3 .. -3.5 at az 357; 0.2 high): deburr",
         lambda p: p[2] < -41.6 and _r(p) >= 25.0, 0.0),        # round 1d: the +X end was missing from the declaration (same feature)
        ("rev3 (R3-7): toe of the R1.0 roof / back-wall fillet strip beyond the roof edge r 16.7 (feather < 0.1, x 9.6 .. 10.3): deburr", lambda p: 9.0 < p[0] < 10.4 and 12.9 < p[1] < 14.1 and -40.7 < p[2] < -39.6, 0.05),
        ("rev3: 0.2 skin closing the D4.1 insert hole of F10_A on the well side inside the guide band (unloaded: pierce it or leave it; the insert stops short of it)",
         lambda p: abs(p[0] - C.R3["F10_A"][0]) < 2.3 and p[1] < 10.6 and abs(p[2] - C.R3["F10_A"][1]) < 2.3, 0.15),
    ],
    "P_drziak_serva": [
        ("rev3: feather edge of the keyhole scallop (r 6.65, y < 17.4) where it meets the keyhole r 6.05 inside the turret wall: deburr",
         lambda p: -10.6 < p[0] < -5.4 and 17.3 < p[1] < 18.2 and -27.6 < p[2] < -20.8, 0.0),
        ("rev3: 0.65 skin between the D2.4 F12 key hole and the pocket bottom relief z -40.35 (unloaded)", lambda p: -11.3 < p[0] < -8.7 and p[1] < 17.3 and p[2] < -39.5, 0.6),
        ("v10 (LD7): plate-root fin under the plate at the sole (taper 1.45 -> 0.75 thick, blunt end at x -5.0 with an R1.5 run-out; attached to the sole "
         "and to the plate above; 0.15 bottom relief over the FFC lip)", lambda p: -8.4 < p[0] < -3.3 and p[1] < 17.3 and p[2] < -40.3, 0.7),
        ("rev3: plate 2.0 (keyhole scallop 0.55 deep beside the turret wall; window of the down stop, bottom chord 4.15)", lambda p: p[1] < 17.2, 1.2),
        ("F11 block walls 1.6 (+X, in compression under the nut) / 3.05 (-X) beside the through nut slot", lambda p: -8.6 < p[0] < -2.4 and p[2] > -18.6, 1.0),
        ("rev3: turret wall 4.0 (inner face 0.2 back except the corner pad) around the keyhole", lambda p: -10.6 < p[0] < -6.4, 1.6),
        ("bridge around the D2.4 key holes (1.1 above)", lambda p: p[2] < -35.0 and p[0] < -6.5, 1.0),
        ("F10 holes D2.3 in the 2.0 plate: 1.35 to the plate top (A) / plate edge (B)", lambda p: 15.0 < p[1] < 17.2 and (abs(p[0] - C.R3["F10_A"][0]) < 3.0 or abs(p[0] - 18.0) < 3.4), 1.3),
        ("lug root fillets", lambda p: p[2] < -42.0, 0.5),
    ],
}
ROOTS = [
    ("P_sachta", "F10 pads r 3.5 / 3.25 on the back wall", "R1.0 (revolved / extruded flare)", True),
    ("P_sachta", "rev3: mounting plateau / pad-B box / ledge rib to the back wall; ledge rib bottom to the plateau face", "R1.0 (fillet strips)", True),
    ("P_sachta", "hub disc to the front wall, back floor to the back wall and the +X pillar (inside the well)", "R1.0 (fillet strips)", True),
    ("P_sachta", "well inner vertical corners", "R2.5", True),
    ("P_sachta", "ribs to the top plate / ring / walls", "R0 - ribs support the journal only (declared)", False),
    ("P_sachta", "rev3 (R3-7): drum shroud roof to the back wall", "R1.0 (fillet strip); the shroud hangs under a full roof r <= 16.7 (no free arch)", True),
    ("P_drziak_serva", "lug inner side to the bridge underside", "R1.5", True),
    ("P_drziak_serva", "rev3: down-stop nose / plate (L2 bearing root)", "R0.6 (fillet strip; the plateau edge is chamfered 0.7)", True),
    ("P_drziak_serva", "lug contact (CW) side to the bridge underside", "R0.8 (pin 1 top is only 1.0 below the bridge)", True),
    ("P_drziak_serva", "turret wall / plate junction behind the case corner", "R0 - the servo case corner occupies it (declared Z3.3 exception)", False),
    ("P_drziak_serva", "block (F11 post) / plate", "R0 - the servo tab sits in the corner (declared)", False),
]
PRINT = {   # fixer rev2 (overenie2 M2 / m6): taken from the module print records; the cup test itself runs in checks.py K10
    k: dict(orientation=v["orientation"], supports=v["supports"], drain=v["drains"], u_away=v["u_away"], on_plate=v["on_plate"],
            fits_printer="tested in checks.py K10 (oriented size + cup test)") for k, v in M.PRINT.items()
}
if "G" in SECT:
    t0 = time.time(); rows, bad = [], []
    for n in M.PRINTED:
        S, th = wall_scan(TRI[n])
        f = np.isfinite(th)
        thin = np.where(f & (th < STRUCT - 2e-3))[0]
        und, cover = [], {d[0]: [9.0, 0] for d in DECL_THIN[n]}
        for k in thin:
            p = S[k]; hit = False
            for desc, test, tmin in DECL_THIN[n]:
                if test(p) and th[k] >= tmin - 1e-6:
                    cover[desc][0] = min(cover[desc][0], float(th[k])); cover[desc][1] += 1; hit = True
                    break
            if not hit:
                und.append((round(float(th[k]), 3), [round(float(x), 2) for x in p]))
        cl = {}
        for t_, p_ in sorted(und):
            cl.setdefault(tuple(np.round(np.array(p_) / 1.5).astype(int)), []).append((t_, p_))
        und = sorted(min(v) for v in cl.values())
        sh = len(M.cached_part(n, M.PRINTED[n][0]).shells())
        rows.append(dict(part=n, rays=int(f.sum()), min=round(float(th[f].min()), 3), median=round(float(np.median(th[f])), 3),
                         n_below_2=int(len(thin)), declared=[dict(feature=d, min=round(v[0], 3), rays=v[1]) for d, v in cover.items() if v[1]],
                         undeclared=und[:20], n_undeclared_zones=len(und), shells=sh, print=PRINT[n]))
        if und or sh != 1:
            bad.append(n)
        say(f"G  {n}: {int(f.sum())} rays, min {th[f].min():.3f}, median {np.median(th[f]):.3f}; below 2.0 {len(thin)}; shells {sh}; "
            f"undeclared zones {len(und)} {und[:12]}")
        for d, v in cover.items():
            if v[1]:
                say(f"G      declared: {d}: min {v[0]:.3f} ({v[1]} rays)")
    k13 = dict(no_petg_pom=all(e["mat"] not in ("petg", "pom") for e in DOC["parts"]), heat_set_inserts=0, countersunk_on_resin=[],
               insert_bosses=dict(F10_A=P2["PAD_A"]["r"], F10_B=P2["PAD_B2"]["r"], rule="r >= 3.65 (M2 x 4 x OD 4.0 bonded insert, D4.1 hole: wall 1.6; fixer rev2)"),
               slide_fits=["kolik_F10 D2 in D2.05 + epoxy", "inserts D4.0 in D4.1 + epoxy (fixer rev2)", "36T gear bonded (no press)",
                           "DPS_krk bonded in the foot slot (0.2 per side)"],
               flexing_features=[], roots=[dict(part=a, root=b, radius=c, ok=d) for a, b, c, d in ROOTS])
    put("G_resin", dict(status="PASS" if not bad else "FAIL", parts=rows, not_ok=bad, k13=k13,
                        note="inward ray from 9000 surface samples to the first opposing face; every reading below 2.0 must be a declared "
                             "feature with its own minimum; shells = 1 means no internal void"))
    say(f"G  undeclared thin zones in: {bad}  ({time.time() - t0:.0f} s)")

# =====================================================================================================================
# H  strength rows (Z2 allowables: normal 8.5, sustained / unfilleted notch 4.3, abuse 12.9 MPa incl. Kt; epoxy 2.7)
# =====================================================================================================================
if "H" in SECT:
    R2_FIX = C.FIX2
    AL = dict(normal=8.5, notch=4.3, sustained=4.3, abuse=12.9, epoxy=2.7)
    rows = []

    def row(n, feature, case, cls, value, limit, basis="", kt=1.0):
        v = value * kt
        rows.append(dict(n=n, feature=feature, load_case=case, cls=cls, stress=round(v, 2), limit=round(limit, 1),
                         margin=round(limit / v, 2) if v else 99.0, verdict="OK" if v <= limit else "FAIL", basis=basis, kt=kt))
    G = R2["GEAR_PAN"]; m = G["m"]; b = G.get("mesh_width", G["face"]); rp36 = m * 36 / 2 / 1000.0     # rev3 (R3-3 b): mesh width 3.0
    Y36 = 0.377; Y18 = 0.309
    R3 = C.R3
    T3, T8 = 0.6, 2 * 0.441
    for case, T_ in (("L3 0.6 N m", T3), ("L8 stall 0.88 N m", T8)):
        Ft = T_ / rp36
        row(1, f"36T brass gear tooth (Lewis, mesh width {b}, Y 0.377)", case, "metal", Ft / (b * m * Y36), 100.0, basis="brass C3604 100 MPa (assumed, UNVERIFIED); rev3: the pinion face is 3.0 (top -42.9)")
        row(1, f"18T pinion tooth (Lewis, face {b}, Y 0.309)", case, "metal", Ft / (b * m * Y18), 100.0,
            basis="rated as BRASS C3604 100 MPa (assumed, UNVERIFIED) - a steel pinion (preferred) has >= 2 x this margin")
    # rev3: bond = gear top face inside the root circle r 13.35 under the floor (whole well outline |y| <= 12.6) and the hub lip (r >= 4.15)
    gx = np.arange(-13.4, 13.41, 0.05); GX, GY = np.meshgrid(gx, gx, indexing="ij"); GR = np.hypot(GX, GY)
    bm = (GR <= 13.35) & (GR >= R3["LIP"]["r_low"]) & (np.abs(GY) <= P2["WELL"]["yb"])
    A_ann = float(bm.sum()) * 0.05 ** 2; Mom = float((GR[bm]).sum()) * 0.05 ** 2
    row(2, f"36T gear epoxy bond under the floor + hub lip (A {A_ann:.0f} mm2 inside the root circle; rev. 2 had 387.8, not 442)", "L8 0.88 N m", "epoxy",
        T8 * 1000.0 / Mom, AL["epoxy"], basis="mean tau = T / sum(r dA); the LOCAL peaks (0.6 mm average) are the K12 FE rows")
    row(3, "same bond under L1 x 2: the well is held by the DIN 9021 on its hub lip (R3-2) - the bond carries only the gear weight (0.2 N)", "L1 x 2",
        "epoxy", 0.2 / A_ann, AL["epoxy"], basis="no axial head load passes the bond; self-equilibrated peel from the floor bending: K12 FE rows")
    St = R2["STOP"]; Lg = P2["POCKET"]["lug"]; Bq = P2["POCKET"]["bridge"]; Sh_ = P2["RAIL"]["shelf"]
    # LD2: the pan servo stalling into a hard stop is a FAULT (firmware range +-85, stops +-90) = abuse 12.9, like the L3 hand twist
    for case, T_, cls, lim in (("L3 0.6 N m (hand, into a stop)", T3, "abuse", AL["abuse"]), ("L8 stall 0.88 N m into a stop (fault)", T8, "abuse", AL["abuse"])):
        # rev3 (R3-5): planar stop faces normal to x: the pin reaction acts along x, F = T / y_contact (the larger of the two stops)
        F = T_ * 1000.0 / min(C.R3["STOP"]["contact_y"])                       # ccw stop (pin 2): plane normal to x, force along +x
        zf = (Lg["z"][0] + St["pin_top"]) / 2
        cwf = C.R3["STOP"].get("cw_face")
        # v10b (LD7): cw face = plane through p, normal n (38 deg from +x): the lug is 5.49 long along x at the contact radius
        lt = (cwf["p"][0] if cwf else Lg["face_x"][1]) - Lg["face_x"][0]; br = Lg["r"][1] - Lg["r"][0]
        LG3 = C.R3["LUG"]
        s_root = 6 * F * (Lg["z"][1] - zf) / (br * lt ** 2)
        row(4, f"LD3 stop lug root at z -43.6, ccw stop (block {lt:.2f} along x x {br:.1f} radial; R{LG3['root_in']} inner root, "
               f"R{LG3['root_face']} at both pin faces = tangent at the pin top)", case, cls,
            s_root, lim, kt=1.6, basis=f"pin force F {F:.1f} N along x at z {zf:.1f}, lever {Lg['z'][1] - zf:.2f}; Z = {br:.1f} x {lt:.2f}^2 / 6 = {br * lt ** 2 / 6:.1f} mm3; "
                                       f"Kt 1.6 (R1.0 on a 5.2 section); FE: K12 row 'stop lug + low bridge'")
        if cwf:
            Fc = T_ * 1000.0 / cwf["lever"]; Fcx, Fcy = Fc * cwf["n"][0], Fc * cwf["n"][1]; lev = Lg["z"][1] - zf
            row(4, f"LD3 stop lug root at z -43.6, cw stop (v10b: face turned {cwf['phi']:.0f} deg; pin force {Fc:.1f} N = {Fcx:.1f} along -x + {Fcy:.1f} along -y)", case, cls,
                6 * Fcx * lev / (br * lt ** 2) + 6 * Fcy * lev / (lt * br ** 2), lim, kt=1.6,
                basis=f"biaxial bending of the {lt:.2f} x {br:.1f} root block, lever {lev:.2f}: Zy {br * lt ** 2 / 6:.1f}, Zx {lt * br ** 2 / 6:.1f} mm3; Kt 1.6 (R1.0 / R1.5 roots)")
        # LD3: the -X part of the lug hangs under the 2.1 low bridge beyond the end face of the high bridge (x -16.9): the tensile part of the
        # root bending block there is carried by the low bridge as a cantilever to the step (R1.5)
        xs_ = Bq["high"][0][0][0]; a_ = xs_ - Lg["face_x"][0]; tb_ = Bq["z_low_top"] - Bq["z"][0]
        xx = np.linspace(0.0, a_, 400); sg = np.clip(s_root * (1 - 2 * xx / lt), 0.0, None)
        N_ = float(np.trapezoid(sg, xx)) * br; e_ = a_ - float(np.trapezoid(sg * xx, xx) / max(np.trapezoid(sg, xx), 1e-9))
        row(4, f"LD3 low bridge {tb_:.1f} x {Bq['r'][1] - Bq['r'][0]:.2f} over the -X part of the lug: cantilever to the R{LG3['step_r']} step at x {xs_}", case, cls,
            6 * N_ * e_ / ((Bq["r"][1] - Bq["r"][0]) * tb_ ** 2), lim, kt=1.4,
            basis=f"tension resultant of the lug root block beyond the step {N_:.1f} N at {e_:.2f} from it (pin 2 pushing +x); Kt 1.4 (R1.5 on 2.1)")
        # stop moment about z in the pocket plate: the pin force acts along x at y_contact, the x reaction (F10 dowel) at the plate plane
        ypm = sum(P2["POCKET"]["plate"]["y"]) / 2; tp_ = P2["POCKET"]["plate"]["y"][1] - P2["POCKET"]["plate"]["y"][0]
        hp_ = P2["POCKET"]["plate"]["z"][1] - Sh_["pocket_bottom"]
        for nm_, yc_ in (("cw stop (pin 1)", C.R3["STOP"]["contact_y"][0]), ("ccw stop (pin 2)", C.R3["STOP"]["contact_y"][1])):
            Fq = T_ * 1000.0 / yc_; Mz = Fq * (yc_ - ypm); how = f"M = {Fq:.1f} N x {yc_ - ypm:.2f} = {Mz:.0f} N mm"
            if cwf and nm_.startswith("cw"):
                # v10b (LD7): the oblique pin force (Fx, Fy) at p; the y component presses the sole onto the curb - the plate has to carry only
                # the moment of the force about the -X end of the seat (curb / sole pad) at the plate mid-plane
                Fq = T_ * 1000.0 / cwf["lever"]; xe = C.R3["CURB"]["pad_x"][0]
                Mz = Fq * cwf["n"][0] * (cwf["p"][1] - ypm) - Fq * cwf["n"][1] * (cwf["p"][0] - xe)
                how = (f"pin force {Fq:.1f} N turned {cwf['phi']:.0f} deg: M about the -X end of the curb seat (x {xe}) = {Fq * cwf['n'][0]:.1f} x {cwf['p'][1] - ypm:.2f} - "
                       f"{Fq * cwf['n'][1]:.1f} x {cwf['p'][0] - xe:.2f} = {Mz:.0f} N mm (v9, plane normal to x, no curb: {T_ * 1000.0 / yc_ * (yc_ - ypm):.0f})")
            row(29, f"pocket plate {tp_:.1f} x {hp_:.1f}: out-of-plane bending by the stop moment about z, {nm_}: {how} "
                    f"(no fastener can be placed at the -X end; a roof beam over the servo is blocked by the door lintel, K7)", case, cls,
                6 * Mz / (hp_ * tp_ ** 2), lim, kt=2.0,
                basis="NOMINAL over the full plate height, Kt 2.0 at the unfilleted corner to the turret wall (servo case corner); the 3-D FE row "
                      "'P_drziak_serva plate' is the reference -> USAGE LIMIT of the pan stops (opravy3.md, LD7)")
        h0, h1 = Bq["z"][0], -36.2; wb = Bq["r"][1] - Bq["r"][0]; dh = Bq["key_holes"]["d"]; zh = Bq["key_holes"]["z"]
        zs = np.linspace(h0, h1, 800); dz = zs[1] - zs[0]
        wz = np.where(np.abs(zs - zh) < dh / 2, 0.0, wb)
        A_ = (wz * dz).sum(); zc = (wz * zs * dz).sum() / A_; I_ = (wz * (zs - zc) ** 2 * dz).sum()
        cmax = max(h1 - zc, zc - h0)
        row(5, "stop bridge section through the F12 key hole D2.4", case, cls, F * (zc - zf) * cmax / I_ + F / A_, lim, kt=1.3,
            basis=f"I {I_:.0f} mm4, A {A_:.1f} mm2, lever {zc - zf:.2f}; Kt 1.3")
        row(6, "stop pin D3 bearing on the lug (2.5 engaged incl. L1 rise)", case, cls, max(F, T_ * 1000.0 / cwf["lever"] if cwf else 0.0) / (3.0 * 2.5), lim)
        if cwf:                                   # v10b (LD7): the sole on the curb (compression only): y component of the cw pin force + the tilt share
            Fc = T_ * 1000.0 / cwf["lever"]; Ac = C.R3["CURB"]; a_c = M.fe_bearing()["curb_y"]
            row(6, f"LD7 sole of the module on the sill curb of the well ({a_c:.1f} mm2, compression only): y component of the cw pin force x 1.5 (tilt about x)", case, cls,
                1.5 * Fc * cwf["n"][1] / a_c, lim, basis="nominal bearing; the FE contact row 'sill curb' is the reference")
        # rev3 (R3-5): planar stop faces normal to x - the pin reaction acts along x: F_x = T / y_contact (larger of the two stops)
        Fx = T_ * 1000.0 / min(C.R3["STOP"]["contact_y"]); Db = P2["RAIL"]["dowel"]; eng_p = Db["boss_y"] - P2["POCKET"]["plate"]["y"][0]
        row(7, f"pocket -> stage: stop reaction along x on the F10 dowel D2 ({eng_p:.1f} in the pocket, {P2['F10']['dowel_depth']} in the well pad)", case, cls,
            max(Fx / (2.0 * eng_p), Fx / (2.0 * P2["F10"]["dowel_depth"])), lim,
            basis=f"F_x {Fx:.1f} N (rev3: stop faces = planes normal to x, no pull-off component); the moments go into the plateau (compression), "
                  f"the ledge / floor stops and F10 tension - K12 FE rows")
    F30 = 30.0
    kh = P2["POCKET"]["keyhole"][0][0] * 2
    Tu = P2["POCKET"]["turret"]; tw_ = Tu["x"][1] - Tu["x"][0]; Bk = P2["POCKET"]["block"]; Ns = P2["POCKET"]["nut_slot"]
    arm_pin = 18.65 + (Tu["x"][0] + Tu["x"][1]) / 2; zh_ = C.LIFT_CASE["z"][1] + C.MG90S["tab"]["hole"]
    T1 = F30 * arm_pin / (zh_ - (C.LIFT_CASE["z"][0] + 1.25)); T2 = F30 * arm_pin / (zh_ - P2["F10"]["dowel"][1])
    row(8, f"turret keyhole bearing (boss D11.8 on the {tw_:.1f} wall): the keyhole carries the pin force, the couple goes along x (LD1)", "L1 x 2 / L2 30 N", "normal",
        F30 / (kh * tw_), AL["normal"], basis=f"servo couple about y = 30 N x {arm_pin:.2f}: L1 -> F11 tension {T1:.1f} N + case corner on the wall; "
                                              f"L2 -> tab on the block + case end on the proud F10 dowel {T2:.1f} N")
    wn_ = Bk["x"][1] - Ns["x"][1]; Ln_ = Ns["y"][1] - Ns["y"][0]; hb_ = Bk["z"][1] - Bk["z"][0]
    row(9, f"F11 block: {wn_:.1f} wall under the nut, held at both ends of the closed slot (span {Ln_:.1f}, height {hb_:.1f})", "L1 x 2 30 N up", "normal",
        6 * (T1 * Ln_ / 8) / (hb_ * wn_ ** 2), AL["normal"], kt=1.5, basis=f"F11 tension {T1:.1f} N at mid span, fixed ends M = T L / 8; Kt 1.5 (slot corners)")
    wpy = C.R3["WALL_PAD"]["y_end"] - P2["POCKET"]["plate"]["y"][1]
    row(10, f"MG90S lower case corner on the wall pad next to the plate (L1 couple; {wpy:.1f} x 2.5 strip, bearing)", "L1 x 2 30 N up", "normal", T1 / (wpy * 2.5), AL["normal"])
    row(11, "F11 DIN 562 nut bearing on the +X wall of its slot (L1 couple)", "L1 x 2", "normal", T1 / (4.0 * 4.0 - 3.14), AL["normal"])
    SS = C.R3["SERVO_SEAT"]; dwl = P2["F10"]["dowel_depth"]; lev = SS["dowel_proud"] / 2 + (ypl_ := (P2["POCKET"]["plate"]["y"][1] - P2["POCKET"]["plate"]["y"][0])) / 2
    row(11, f"L2 couple: MG90S case end on the proud end of the F10 dowel (D2 x {SS['dowel_proud']} proud, gap {SS['end_gap']}); dowel in the 2.0 plate / prying in the "
            f"well pad ({dwl} deep)", "L2 30 N lift 20 (abuse, LD2)", "abuse", max(T2 / (2.0 * ypl_), 6 * T2 * lev / (2.0 * dwl ** 2)), AL["abuse"],
        basis=f"T {T2:.1f} N; plate hole {T2 / (2.0 * ypl_):.1f}; well pad 6 M / (d L^2) = {6 * T2 * lev / (2.0 * dwl ** 2):.1f} with M = T x {lev:.2f}")
    # rev3 (R3-5): no tongue / groove.  Rocking of the module about the F10 dowel: the -X reaction goes UP into the ledge rib (L1) or
    # DOWN onto the plateau top through the pocket nose (L2); hand rows (bearing / web); the 3-D FE values are the K12 rows 'rail / ledge'
    Ra = P2["RAIL"]; Lr, Sh = Ra["ledge"], Ra["shelf"]; xd = P2["F10"]["dowel"][0]; ypl = P2["POCKET"]["plate"]["y"]
    xl = sum(Lr["x"]) / 2; Rend = F30 * (xd + 18.65) / (xd - xl); Rdow = Rend - F30
    Al = (Lr["x"][1] - Lr["x"][0]) * (Lr["y_end"] - Lr["bear_y0"])
    row(12, f"ledge rib (up stop): bearing of the pocket block top on the rib bottom (A {Al:.1f} mm2; -X reaction {Rend:.1f} N = 30 N x "
            f"{xd + 18.65:.2f} / {xd - xl:.2f})", "L1 x 2 30 N", "normal", Rend / Al, AL["normal"], basis="compression; gap 0.10 before contact")
    tw = Lr["x"][1] - Lr["x"][0]; hw = Lr["z"][1] - Lr["z"][0]; arm = (Lr["bear_y0"] + Lr["y_end"]) / 2 - P2["WELL"]["yb2"]
    row(12, f"ledge rib web {tw:.1f} x {hw:.2f} at the back wall (hangs under the top plate; cantilever estimate, lever {arm:.2f}, R{Lr['root_r']} roots)",
        "L1 x 2 30 N", "normal", 6 * Rend * arm / (tw * hw ** 2), AL["normal"], kt=1.5, basis="the top plate carries it too (conservative)")
    dn_y = Sh["y_end"] - (ypl[0] + Sh["root_r"] + 0.2); sxa, sxb = Sh["x"][0] + Sh["edge_chamfer"], Sh["x"][1] - Sh["notch_r"] - 0.15; xs_ = (sxa + sxb) / 2
    Rdn = F30 * (xd + 18.65) / (xd - xs_); Af = (sxb - sxa) * dn_y
    row(13, f"down stop: ceiling of the plate window on the well shelf z {Sh['z_top']} (bearing {sxb - sxa:.2f} x {dn_y:.2f} = {Af:.1f} mm2; -X reaction {Rdn:.1f} N = 30 N x "
            f"{xd + 18.65:.2f} / {xd - xs_:.2f})", "L2 30 N (lift 0-2 normal; lift 20 abuse)",
        "normal", Rdn / Af, AL["normal"], basis="rated against the NORMAL allowable (covers the chain path at lift 0 before the foot lands); gap 0.10 before contact")
    hs = Sh["z_top"] - Sh.get("z_bot", P2["R3"]["FLOOR"]["z"][1]); ws = Sh["x"][1] - Sh["x"][0]; arm_s = (ypl[0] + Sh["root_r"] + 0.2 + Sh["y_end"]) / 2 - ypl[0]
    row(13, f"shelf {ws:.1f} x {hs:.2f} high on the plateau face (ledge inside the plate window): bending at its root (lever {arm_s:.2f}, R{Sh['root_r']} root)", "L2 30 N", "normal",
        6 * Rdn * arm_s / (ws * hs ** 2), AL["normal"], kt=2.0, basis="LD1 (b): hand calc of the supporting section with the stop reaction")
    Db = Ra["dowel"]; eng_p = Db["boss_y"] - ypl[0]; eng_w = P2["F10"]["dowel_depth"]
    row(13, f"F10 dowel D2: vertical reaction {Rdow:.1f} N in the pocket ({eng_p:.1f} engaged) / in the well pad ({eng_w} deep)", "L1 x 2 / L2 30 N", "normal",
        max(Rdow / (2.0 * eng_p), Rdow / (2.0 * eng_w)), AL["normal"], basis="projected bearing")
    oi, li = C.INSERTS["M2"][:2]
    row(14, f"F10 insert bond (M2 x {li} x OD {oi}, fixer rev2), L1 share 15 N", "L1 x 2", "epoxy", 15.0 / (math.pi * oi * li), AL["epoxy"])
    pre = R2_FIX["TQ_DESIGN"] / (0.2 * 0.002)
    row(15, f"F10 insert bond at the fingertip design case {R2_FIX['TQ_DESIGN']} N m (preload {pre:.0f} N, K 0.2; lead decision: "
            f"1.5 x preload <= epoxy 8 MPa)", "L7", "epoxy 8 / 1.5", pre / (math.pi * oi * li), R2_FIX["EPOXY_MPA"] / R2_FIX["PULLOUT_FACTOR"])
    Aw = math.pi / 4 * (4.2 ** 2 - 2.3 ** 2)
    row(27, "F10 DIN 433 washer (OD 4.2 at its lower tolerance) on the P_drziak_serva plate at the design case", "L7", "crush (short-term)",
        pre / Aw, R2_FIX["CRUSH_MPA"], basis="relaxation harmless: the module is located by the F10 dowel + ledge rib / nose")
    An = 16.0 - math.pi
    row(28, "F11 DIN 562 nut on the block slot at the design case", "L7", "crush (short-term)", pre / An, R2_FIX["CRUSH_MPA"],
        basis="the MG90S is held by the closed pocket; the block between nut and tab is in compression")
    rpa = P2["PAD_A"]["r"]
    row(16, f"F10 pad root r {rpa} + R1 (15 N lateral, lever 2.1; D4.1 hole through)", "L2", "normal",
        32 * 15.0 * 2.1 * (2 * rpa) / (math.pi * ((2 * rpa) ** 4 - 4.1 ** 4)), AL["normal"], kt=1.3)
    row(17, "hub disc ring under the Al foot (compression onto the brass gear)", "L2 30 N lift 0", "normal", F30 / (math.pi * (12.6 ** 2 - 6.5 ** 2)), AL["normal"])
    row(18, "back floor 0.95 over the FFC groove (foot contact 0.08 MPa, span 8, simply supported)", "L2 30 N lift 0", "normal",
        6 * (0.08 * 8.0 ** 2 / 8) / 0.95 ** 2, AL["normal"])
    E = P2["EAR"]; t = E["t"]
    row(19, "L_ucho plate 304 1.5 at TDC: plate root beside the relief kerf (overenie2 2-D FE t06: 137.7 MPa von Mises; fixer rev2: "
            "304 only, D1.0 at the kerf end)", "L2 lift 20", "metal", R2_FIX["EAR_FE_MPA"], 215.0 / 1.5,
        basis="FE value before the D1.0 relief (conservative); 5754-H22 2.0 deleted (103 > 87 MPa)")
    row(20, "L_ucho lower ligament under the pin at mid stroke (5.2 x 1.5, pin past the bend tangent)", "L1 x 2", "metal",
        6 * (F30 * 1.0) / (t * 5.2 ** 2), 215.0 / 1.5)
    row(21, "F12 single M2 screw tension (prying 13.4 / 2.0; dowel takes the shear)", "L1 x 2 lift 0", "metal", (F30 * 13.4 / 2.0) / 2.07, 640.0 / 1.5)
    row(22, "F12 thread shear in the Al foot (3.6 engaged, one screw)", "L1 x 2", "metal", (F30 * 13.4 / 2.0) / (math.pi * 1.6 * 3.6 * 0.5), 0.6 * 130.0 / 1.5,
        basis="Al 6060/5754 yield ~130 (lower bound), shear 0.6")
    row(23, "crank pin D2 bending (lever 1.9)", "L2 30 N", "metal", 32 * F30 * 1.9 / (math.pi * 2.0 ** 3), 400.0 / 1.5)
    row(24, "pin in the 304 ear slot (bearing)", "L2 30 N", "metal", F30 / (2.0 * t), 215.0 / 1.5)
    row(25, "Al arm 5 x 2 at the hub (L2 30 N x 10 in its plane)", "L2 mid lift", "metal", 6 * F30 * 10.0 / (2.0 * 5.0 ** 2), 130.0 / 1.5,
        basis="bending in the arm plane: section 2 thick x 5 deep")
    rows.append(dict(n=26, feature="MG90S output side load 30 N, 6 mm outboard", load_case="L1 / L2", cls="bought", stress=None, limit=None,
                     margin=None, verdict="UNVERIFIED", basis="not published (unchanged risk)"))
    nfail = [r for r in rows if r["verdict"] == "FAIL"]
    put("H_strength", dict(status="PASS" if not nfail else "FAIL", rows=rows, allowables=AL,
                           fails=[(r["n"], r["feature"], r["load_case"], r["stress"], r["limit"]) for r in nfail],
                           note="hand calculations on the rev. 3 geometry; Kt per row; the 3-D FE rows of the well (fe_sachta/results.json) are added by K12"))
    for r in rows:
        say(f"H  {r['n']:2d} {r['feature'][:72]:72s} {r['load_case'][:20]:20s} {r['stress'] if r['stress'] is not None else '-':>8} / "
            f"{r['limit'] if r['limit'] is not None else '-':>6} -> {r['verdict']}")

say(f"== done sections {''.join(SECT)} in {time.time() - T0:.0f} s; " + ", ".join(f"{k}: {v.get('status')}" for k, v in RES.items()))

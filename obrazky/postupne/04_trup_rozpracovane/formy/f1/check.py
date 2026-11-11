"""f1 fit + sweep checks -> check.json
A  static fit, rest pose, CAD booleans + BRepExtrema: every internal part of pack/layout.json vs the f1 shells
   (intersection volume, inside the outer body, minimum distance).
B  moving parts with the REAL f1 shapes (dense surface samples of the fine STLs, KD-tree, ~0.1 mm):
   pan stage / lift parts vs torso shells over pan -85..85 x lift 0..20; J1 rotating parts + torso shells vs base
   parts over J1 -155..155; arms (halves + cap) vs torso over arm -45..135, vs base over arm x J1; arm vs arm.
C  t1lib sweep (STD_POSES + own poses) with the f1 shells injected as custom comps (volume clashes).
D  arm limit table vs the REAL head (B rev. E2 STL, >= 2.0 mm) per head state x pan; real head vs the f1 torso top.
E  mass, CoG, tipping with the f1 shells.
Run: /opt/venv/cad/bin/python check.py [A B C D E]"""
import sys, os, json, math, time, struct, itertools
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1")
import t1lib as T
import form as F
from build123d import import_brep, Location, Pos, Rot
from exterior import mesh_volume, one

PACK = "/tmp/claude-0/gapwf/fin/T1/pack/layout.json"
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"
PARTS = json.load(open(os.path.join(HERE, "parts.json")))
OUTF = os.path.join(HERE, "check.json")
RES = json.load(open(OUTF)) if os.path.exists(OUTF) else {}
T0 = time.time()
DENS = {"white": 1.15e-3, "black": 1.15e-3, "glow": 1.19e-3, "glass": 1.19e-3, "grey": 1.27e-3}
FOOT_PETG = {"Z_noha_stred", "Z_kryt_baterie_P", "Z_kryt_baterie_Z"}

SHELL_MOUNTED = {"T_stlpik_L", "T_stlpik_R", "T_horny_kruh", "T_reproduktor", "B_golier_prstenec",
                 "Z_J1_kanal", "Z_J1_kabel"}          # screwed / glued to the shell (contact allowed, no overlap)
THROUGH = {"T_paka_L", "T_paka_R", "T_kabel_ramena_L", "T_kabel_ramena_R",   # in the shoulder pocket (shell cut)
           "T_svetlo", "Z_svetlo", "Z_USB_C", "Z_vypinac", "Z_ToF",           # behind light guides / windows / ports
           "B_krk", "B_golier_kotuc", "B_kabel_krk", "B_uska", "B_hlava", "B_usi", "B_ram_tvar"}


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def shapes():
    return {nm: one(import_brep(os.path.join(HERE, "work", nm + ".brep"))) for nm in PARTS}


def aux(nm):
    return one(import_brep(os.path.join(HERE, "work", nm + ".brep")))


# ---------------------------------------------------------------- point samples of STL meshes
def read_stl(fn, dense=True):
    b = open(fn, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + 50 * n], dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("att", "<u2")]))
    Tr = a["v"].astype(float)
    if not dense:
        return Tr.reshape(-1, 3)
    pts = [Tr.reshape(-1, 3), Tr.mean(axis=1), (Tr[:, 0] + Tr[:, 1]) / 2, (Tr[:, 1] + Tr[:, 2]) / 2,
           (Tr[:, 2] + Tr[:, 0]) / 2]
    # long triangles: extra samples along the longest edge
    L = np.linalg.norm(Tr[:, [1, 2, 0]] - Tr, axis=2).max(axis=1)
    m = L > 1.0
    if m.any():
        for f in (0.25, 0.75):
            pts.append(Tr[m, 0] * f + Tr[m, 1] * (1 - f)); pts.append(Tr[m, 1] * f + Tr[m, 2] * (1 - f))
            pts.append(Tr[m, 2] * f + Tr[m, 0] * (1 - f))
    return np.unique(np.round(np.vstack(pts), 3), axis=0)


def mat4(loc: Location):
    t = loc.wrapped.Transformation()
    return np.array([[t.Value(r, c) for c in range(1, 5)] for r in range(1, 4)])


def xf(P, M):
    return P @ M[:, :3].T + M[:, 3]


def pack_pts(L, nm, tol=0.1):
    v, t = L.raw(nm).tessellate(tol, 0.2)
    V = np.array([[p.X, p.Y, p.Z] for p in v]); Tr = np.array(t)
    return np.vstack([V, (V[Tr[:, 0]] + V[Tr[:, 1]] + V[Tr[:, 2]]) / 3, (V[Tr[:, 0]] + V[Tr[:, 1]]) / 2,
                      (V[Tr[:, 1]] + V[Tr[:, 2]]) / 2, (V[Tr[:, 2]] + V[Tr[:, 0]]) / 2])


def cloud_min(A, treeB):
    d, i = treeB.query(A, distance_upper_bound=30.0)
    k = int(np.argmin(d))
    return float(d[k]), A[k]


# ---------------------------------------------------------------- layout with the f1 shells as custom comps
def f1_layout(S):
    d = json.load(open(PACK))
    drop = {"T_shell", "Z_shell", "A_R_ruka", "A_L_ruka", "A_R_kryt", "A_L_kryt"}   # replaced by f1 parts (same names
    #                                                                                for the arms: f1 shapes injected)
    d["comps"] = [c for c in d["comps"] if c["name"] not in drop]
    for nm, m in PARTS.items():
        dens = 1.27e-3 if nm in FOOT_PETG else DENS[m["color"]]
        cg = centroid(S[nm])
        d["comps"].append({"name": nm, "kind": "box", "size": [1, 1, 1], "group": m["group"],
                           "mass": round(m["volume_mm3"] * dens, 2), "cog": cg, "color": m["color"]})
    d["allow"] = [p for p in d["allow"] if not set(p) & drop]
    d["allow"] += [["T_trup_zadny", "B_golier_prstenec"], ["T_svetlo", "T_predny_panel"], ["T_svetlo", "T_svetlovod"],
                   ["A_R_servo", "A_R_ruka"], ["A_L_servo", "A_L_ruka"], ["Z_USB_C", "Z_skrupina"], ["Z_vypinac", "Z_skrupina"],
                   ["Z_svetlo", "Z_skrupina"], ["Z_ToF", "Z_skrupina"], ["A_R_servo", "A_R_kryt"],
                   ["A_L_servo", "A_L_kryt"]]
    L = T.Layout(d)
    for nm in PARTS:
        L._raw[nm] = S[nm]
    return L


def centroid(s):
    v, t = s.tessellate(0.05, 0.2)
    V = np.array([[p.X, p.Y, p.Z] for p in v]); Tr = np.array(t)
    a, b, c = V[Tr[:, 0]], V[Tr[:, 1]], V[Tr[:, 2]]
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)) / 6
    cg = ((a + b + c) / 4 * vol[:, None]).sum(axis=0) / vol.sum()
    return [round(float(x), 2) for x in cg]


# ================================================================ A: static CAD fit
def check_A(S):
    L0 = T.Layout(PACK)
    tor = ["T_trup_zadny", "T_predny_panel", "T_dno", "T_svetlovod", "T_mriezka"]
    bas = ["Z_skrupina", "Z_plint", "Z_noha_stred", "Z_kryt_baterie_P", "Z_kryt_baterie_Z", "Z_svetlovod",
           "Z_okno_ToF", "Z_led_nabijania", "Z_tlacidlo"]
    T_out, Z_out = aux("T_outer"), aux("Z_outer")
    rows = {}
    for c in L0.comps:
        nm, g = c["name"], c["group"]
        if g in ("H", "AR", "AL") or nm in ("T_shell", "Z_shell") or nm in THROUGH and nm not in ("T_svetlo",):
            continue
        sh = L0.raw(nm)
        bb = sh.bounding_box()
        if g in ("T", "P", "L") and bb.max.Z > F.TZ0 + 0.01:
            shells, outer, need = tor, T_out, (0.0 if nm in SHELL_MOUNTED else 1.0)
        elif g == "B":
            shells, outer, need = bas, Z_out, (0.0 if nm in SHELL_MOUNTED else 1.0)
        else:
            continue
        if nm == "T_svetlo":
            need = 0.0
        best = (1e9, None); vint = 0.0
        for s in shells:
            d = sh.distance_to(S[s])
            if d < best[0]:
                best = (d, s)
            if d < 1e-6:
                vint += mesh_volume(sh & S[s])
        try:
            vout = mesh_volume(sh - outer) if nm not in ("T_STS3215",) else mesh_volume(
                (sh - outer) - Pos(-18, 0, 40) * __import__("build123d").Cylinder(7.0, 8))
        except Exception:
            vout = -1
        ok = vint < 0.05 and (best[0] >= need - 0.02 or nm == "T_svetlo") and vout < 0.05
        rows[nm] = {"min_dist_mm": round(best[0], 2), "to": best[1], "need": need,
                    "intersection_mm3": round(vint, 3), "outside_outer_mm3": round(vout, 3), "ok": bool(ok)}
        log("A", nm, rows[nm])
    for tag in ("R", "L"):                             # arm internals vs the one-piece paddle + cap
        for nm, need in ((f"A_{tag}_servo", 0.0), (f"A_{tag}_kabel", 0.5)):
            sh = L0.raw(nm)
            d = min(sh.distance_to(S[f"A_{tag}_ruka"]), 99)
            vint = mesh_volume(sh & S[f"A_{tag}_ruka"]) if d < 1e-6 else 0.0
            vcap = mesh_volume(sh & S[f"A_{tag}_kryt"])
            ok = vint < 0.05 and vcap < 0.05 and d >= need - 0.02
            rows[nm] = {"min_dist_mm": round(d, 2), "to": f"A_{tag}_ruka", "need": need,
                        "intersection_mm3": round(vint + vcap, 3), "ok": bool(ok),
                        "note": "servo case flush in the inner-face window, bonded to the outer wall" if "servo" in nm else ""}
            log("A", nm, rows[nm])
    RES["A_static_fit_rest"] = {"note": "pack internals vs f1 shells, rest pose, CAD (BRepExtrema distance, boolean "
                                        "volumes by tessellation). need = 1.0 mm for free parts, 0 for parts screwed/"
                                        "glued to the shell. T_svetlo = LED flex strip behind the light guide (bent to"
                                        " the crowned panel, see forma.md); T_STS3215 spline boss passes the J1 hole.",
                                "parts": rows, "all_ok": all(r["ok"] for r in rows.values())}


# ================================================================ B: moving parts with real shapes (point clouds)
def check_B(S):
    L0 = T.Layout(PACK)
    P = {nm: read_stl(PARTS[nm]["stl"]) for nm in PARTS}
    out = {}
    # --- pan stage + lift vs torso shells
    tor = np.vstack([P[n] for n in ("T_trup_zadny", "T_predny_panel", "T_dno", "T_svetlovod", "T_mriezka")])
    tt = cKDTree(tor)
    moving = [c["name"] for c in L0.comps if c["group"] in ("P", "L") and not c["name"].startswith("B_")]
    moving += ["B_krk", "B_kabel_krk"]
    log("B start", len(tor), "torso pts")
    best = (1e9, None, None)
    for nm in moving:
        V = pack_pts(L0, nm)
        g = L0.comp(nm)["group"]
        for pan in range(-85, 86, 5):
            for lift in ((0, 5, 10, 15, 20) if g == "L" else (0,)):
                M = mat4(L0.loc(g, {"pan": pan, "lift": lift}))
                d, p = cloud_min(xf(V, M), tt)
                if d < best[0]:
                    best = (d, nm, {"pan": pan, "lift": lift})
    out["pan_lift_vs_torso_shells"] = {"min_mm": round(best[0], 2), "part": best[1], "pose": best[2], "need": 1.0,
                                       "ok": best[0] >= 1.0}
    log("B pan/lift", out["pan_lift_vs_torso_shells"])
    # --- J1 rotating parts + torso shell vs base parts
    base = np.vstack([P[n] for n in PARTS if PARTS[n]["group"] == "B"])
    bt = cKDTree(base)
    rot = {nm: pack_pts(L0, nm) for nm in ("T_J1_sukna", "T_J1_noha", "T_J1_pastorok", "T_STS3215", "T_J1_lozisko")}
    rot.update({nm: P[nm] for nm in ("T_trup_zadny", "T_dno", "T_predny_panel")})
    best = (1e9, None, None)
    for j1 in range(-155, 156, 5):
        M = mat4(L0.loc("T", {"j1": j1}))
        for nm, V in rot.items():
            W = xf(V, M)
            if nm == "T_J1_lozisko":      # bearing inner ring sits on the hub (intended fit) - only vs the shell parts
                continue
            d, p = cloud_min(W, bt)
            if d < best[0]:
                best = (d, nm, j1)
    out["J1_rotating_vs_base_parts"] = {"min_mm": round(best[0], 2), "part": best[1], "j1": best[2], "need": 1.0,
                                        "ok": best[0] >= 1.0,
                                        "note": "skirt, foot ring, pinion, STS3215 boss, torso shells vs f1 base shell,"
                                                " plinth ring, foot (bearing on the hub = intended fit, excluded)"}
    log("B J1", out["J1_rotating_vs_base_parts"])
    # --- arms vs torso (arm angle sweep) and vs base (arm x J1), arm vs arm
    armR = np.unique(np.round(np.vstack([read_stl(PARTS[n]["stl"], dense=False) for n in ("A_R_ruka", "A_R_kryt")]), 2), axis=0)
    armL = np.unique(np.round(np.vstack([read_stl(PARTS[n]["stl"], dense=False) for n in ("A_L_ruka", "A_L_kryt")]), 2), axis=0)
    torso_all = np.vstack([tor] + [pack_pts(L0, n) for n in ("T_paka_R", "T_paka_L", "T_kabel_ramena_R",
                                                             "T_kabel_ramena_L", "T_stlpik_R", "T_stlpik_L")])
    tta = cKDTree(torso_all)
    best_t = (1e9, None); best_b = (1e9, None); best_aa = (1e9, None)
    tlo = cKDTree(np.vstack([tor]))
    for ang in range(-45, 136, 5):
        for tag, V, key in (("R", armR, "armR"), ("L", armL, "armL")):
            M = mat4(L0.loc("A" + tag, {key: ang}))
            W = xf(V, M)
            d, p = cloud_min(W, tlo)
            if d < best_t[0]:
                best_t = (d, {key: ang})
            for j1 in range(-150, 151, 30):
                Mj = mat4(L0.loc("A" + tag, {key: ang, "j1": j1}))
                d, p = cloud_min(xf(V, Mj), bt)
                if d < best_b[0]:
                    best_b = (d, {key: ang, "j1": j1})
    for a1 in range(-45, 136, 15):
        WR = xf(armR, mat4(L0.loc("AR", {"armR": a1})))
        tr = cKDTree(WR)
        for a2 in range(-45, 136, 15):
            d, p = cloud_min(xf(armL, mat4(L0.loc("AL", {"armL": a2}))), tr)
            if d < best_aa[0]:
                best_aa = (d, {"armR": a1, "armL": a2})
    out["arm_vs_torso_shells"] = {"min_mm": round(best_t[0], 2), "pose": best_t[1], "need": 1.0,
                                  "ok": best_t[0] >= 1.0, "range": "-45..135 step 5"}
    out["arm_vs_base"] = {"min_mm": round(best_b[0], 2), "pose": best_b[1], "need": 2.0, "ok": best_b[0] >= 2.0,
                          "range": "arm -45..135 step 5 x J1 -150..150 step 30"}
    out["arm_vs_arm"] = {"min_mm": round(best_aa[0], 2), "pose": best_aa[1], "ok": best_aa[0] >= 2.0}
    # cap in the shoulder pocket (static socket, cable spiral, cup collar)
    capR = P["A_R_kryt"]
    d, p = cloud_min(capR, tta)
    out["cap_in_pocket_rest"] = {"min_mm": round(d, 2), "ok": d >= 1.0 - 0.05}
    # servo + cable inside the arm halves (servo bonded flush -> >= 0; cable >= 0.5)
    for tag in ("R", "L"):
        sh = P[f"A_{tag}_ruka"]
        st = cKDTree(sh)
        for nm, need in ((f"A_{tag}_servo", 0.0), (f"A_{tag}_kabel", 0.5)):
            V = pack_pts(L0, nm)
            V = V[np.abs(V[:, 0]) > 46.55] if nm.endswith("servo") else V   # spline boss sticks out by design
            d, p = cloud_min(V, st)
            out[f"{nm}_in_paddle"] = {"min_mm": round(d, 2), "need": need, "ok": d >= need - 0.05}
    log("B arms", {k: v for k, v in out.items() if k.startswith("arm") or k.startswith("cap") or "_in_" in k})
    RES["B_moving_real_shapes"] = out


# ================================================================ C: t1lib sweep with custom comps
OWN_POSES = [
    {"pan": 85, "lift": 0}, {"pan": -85, "lift": 20}, {"pan": 85, "lift": 20, "tilt": -40},
    {"armR": -45, "armL": -45, "j1": 150}, {"armR": 135, "armL": 135, "pan": 85}, {"armR": 135, "armL": 135, "pan": -85},
    {"j1": 155, "armR": 90, "armL": 90}, {"j1": -155, "armR": 135, "armL": -45}, {"armR": 60, "armL": 60, "j1": 90},
    {"lift": 12.5, "tilt": 8, "armR": 12, "armL": 12},
    {"j1": 20, "pan": 30, "lift": 12.5, "tilt": -8, "armL": 130, "armR": -15},
]


def check_C(S):
    L = f1_layout(S)
    st = L.clashes({})
    log("C static", st)
    sw_std = L.sweep(T.STD_POSES)
    log("C std", sw_std)
    sw_own = L.sweep(OWN_POSES)
    log("C own", sw_own)
    def summarize(sw, poses):
        return {k: [{"pose": poses[i], "mm3": v} for i, v in lst] for k, lst in sw.items()}
    RES["C_t1lib_sweep"] = {"static_clashes": st, "STD_POSES": summarize(sw_std, T.STD_POSES),
                            "own_poses": summarize(sw_own, OWN_POSES),
                            "note": "t1lib volume clashes between groups with the f1 shells as custom comps; B_* are "
                                    "the t1lib head ENVELOPES (rf-14 box, ear cylinder) - arm x head instances are "
                                    "handled by the firmware arm table (section D, real head)."}


# ================================================================ D: real head
HEAD_PARTS = ["hlava_skrupina", "ram_displeja", "usi", "displej", "led_kruzky", "usko_kryt", "usko_lozisko"]
TABLE = [(0, 5, 10), (2.5, 10, 15), (5, 15, 20), (7.5, 20, 30), (10, 25, 35), (12.5, 30, 40), (16, 35, 40), (18, 40, 40)]


def head_states():
    out = []
    for i, (lf, dn, up) in enumerate(TABLE):
        lmax = TABLE[i + 1][0] if i + 1 < len(TABLE) else 20.0
        for lift in sorted({lf, (lf + lmax) / 2, lmax if i + 1 == len(TABLE) else lmax - 0.01}):
            for t in sorted(set(list(np.arange(-up, dn + 0.1, 5.0)) + [-up, dn])):
                out.append((lift, float(t)))
    return out


def check_D(S):
    L0 = T.Layout(PACK)
    dzB = T.b_frame_dz(L0.Z_TT)
    H = np.unique(np.round(np.vstack([read_stl(os.path.join(B_STL, p + ".stl"), dense=False) for p in HEAD_PARTS]),
                           2), axis=0)
    H[:, 2] += dzB
    armR = np.unique(np.round(np.vstack([read_stl(PARTS[n]["stl"], dense=False) for n in ("A_R_ruka", "A_R_kryt")]), 3), axis=0)
    # --- arm limit table (right arm; left = same table with pan sign inverted)
    states = [(0, 0), (12.5, 8), (12.5, -8), (12.5, 30), (12.5, -40), (20, 0), (20, 40), (20, -40)]
    table = {}
    for lift, tilt in states:
        row = {}
        for pan in (-85, -60, -30, 0, 30, 60, 85):
            Hw = xf(H, mat4(L0.loc("H", {"pan": pan, "lift": lift, "tilt": tilt})))
            Hw = Hw[(Hw[:, 0] < -41.0)]                   # the right arm + cap live at x <= -44.2 (2 mm criterion)
            ht = cKDTree(Hw)
            def gap(a):
                d, _ = ht.query(xf(armR, mat4(L0.loc("AR", {"armR": a}))), distance_upper_bound=2.5)
                return float(d.min())
            lim = None
            for a in range(0, 181, 5):
                if gap(a) < 2.0:
                    lim = a - 5
                    for b in range(a - 4, a + 1):
                        if gap(b) < 2.0:
                            break
                        lim = b
                    break
            row[str(pan)] = 180 if lim is None else lim
        table[f"lift{lift}_tilt{tilt}"] = row
        log("D arm", lift, tilt, row)
    # --- arms hanging / awake vs head (rest of the table, any pan): min gap
    # --- real head vs the f1 torso top (analytic surface) over the B table x pan
    Hlow = H[H[:, 2] < L0.Z_TT + 30]
    best = (1e9, None)
    zz = np.linspace(F.TZ1 - F.THT, F.TZ1, 4001)
    ab = np.array([F.torso_ab(z) for z in zz])
    def z_top(x, y):
        # highest torso point under (x, y): flat top inside the top outline, else the round (search over z)
        out = np.full(len(x), -1e9)
        for k in range(len(zz) - 1, -1, -40):
            a, b = ab[k]
            ins = (np.abs(x) / a) ** F.TN + (np.abs(y) / b) ** F.TN <= 1
            out = np.where(ins & (out < -1e8), zz[k], out)
        r = np.hypot(x, y)
        out = np.where(r <= 28.35, np.where(r <= 28.25, 133.0, out), out)   # B collar ring (static) to z 133
        return out
    for lift, tilt in head_states():
        for pan in range(-85, 86, 5):
            Hw = xf(Hlow, mat4(L0.loc("H", {"pan": pan, "lift": lift, "tilt": tilt})))
            m = Hw[:, 2] < L0.Z_TT + 6
            if not m.any():
                continue
            Q = Hw[m]
            r = np.hypot(Q[:, 0], Q[:, 1])
            Q = Q[r > 28.25]                              # over the collar: B-verified (>= 0.25), unchanged here
            if not len(Q):
                continue
            cl = Q[:, 2] - z_top(Q[:, 0], Q[:, 1])
            k = int(np.argmin(cl))
            if cl[k] < best[0]:
                best = (float(cl[k]), {"lift": lift, "tilt": tilt, "pan": pan,
                                       "point": [round(float(v), 1) for v in Q[k]]})
    log("D head vs torso top", best)
    RES["D_real_head"] = {"arm_limit_table_deg": dict(note="max RIGHT-arm angle (0 down, 90 forward, 180 up) with >= "
                                                          "2.0 mm to the REAL head (B rev. E2 STL: shell, bezel, display,"
                                                          " ears, LED rings, hinge lugs); LEFT arm = same table with pan"
                                                          " sign inverted. Mechanical travel -45..+135; back limit -45 "
                                                          "free in all states.", **table),
                          "head_vs_f1_torso_top_outside_collar_mm": {"min": round(best[0], 2), "worst": best[1],
                                                                     "need": 1.0, "ok": best[0] >= 1.0}}


# ================================================================ E: mass / CoG / tipping
def check_E(S):
    L = f1_layout(S)
    out = {}
    for nm, p in (("rest", {}), ("awake", {"lift": 12.5, "tilt": 8, "armR": 12, "armL": 12}),
                  ("worst_arms100_lift20_tilt40", {"armR": 100, "armL": 100, "lift": 20, "tilt": 40}),
                  ("persona", {"j1": 20, "pan": 30, "lift": 12.5, "tilt": -8, "armL": 130, "armR": -15})):
        out[nm] = L.tipping(p, accel_g=0.15)
    M, c, rows = L.cog({})
    f1m = {r[0]: r[1] for r in rows if r[0] in PARTS}
    out["f1_part_masses_g"] = f1m
    out["f1_shells_total_g"] = round(sum(f1m.values()), 1)
    RES["E_mass_cog_tipping"] = out
    log("E", json.dumps(out)[:600])


if __name__ == "__main__":
    want = sys.argv[1:] or ["A", "B", "C", "D", "E"]
    S = shapes() if set(want) & set("ABCE") else {}
    for k in want:
        globals()["check_" + k](S)
        json.dump(RES, open(OUTF, "w"), indent=1, default=str)
    log("CHECK DONE")

"""dense surface cloud of every moving T4/B part in the STAGE frame (pan 0), lift-group parts replicated over lift 0..20
(0.5 steps), crank / FFC loop / pigtail posed; only points with r >= RMIN kept.  Cached to movcloud.npz."""
import sys, os, json, math
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as V
T4 = V.T4
RMIN = 24.0


def build(h=0.25):
    sys.path.insert(0, T4); cwd = os.getcwd(); os.chdir(T4)
    import t4_common as C
    import t4_pan as MP
    PJ = json.load(open(os.path.join(T4, "parts.json"))); REC = {p["name"]: p for p in PJ["parts"]}
    CRANK = ("rameno_zdvih", "cap_kluky", "skr_ramena")
    P_rigid = [n for n in REC if REC[n]["group"] == "P" and n not in CRANK + ("pigtail_zdvih",)]
    L_rigid = [n for n in REC if REC[n]["group"] == "L" and n not in ("pigtail_zdvih",)]
    B_L = ["krk_predna_polovica", "krk_zadna_polovica", "kabel", "capy", "klzny_kruzok", "loziska_MR85", "paka", "pena_serva",
           "servo_MG90S", "usko_kryt", "usko_lozisko", "skrutky"]
    keep = lambda P: P[np.hypot(P[:, 0], P[:, 1]) >= RMIN]
    S = lambda tr: V.vlib.sample_surface(tr, h)
    rigid, lifted, tag_r, tag_l = [], [], [], []
    for n in P_rigid:
        p = keep(S(V.load(n))); rigid.append(p); tag_r += [n] * len(p)
    p = keep(S(V.load("golier_kotuc", V.BST))); rigid.append(p); tag_r += ["golier_kotuc"] * len(p)
    for n in L_rigid:
        p = keep(S(V.load(n))); lifted.append(p); tag_l += [n] * len(p)
    for n in B_L:
        p = S(V.load(n, V.BST)); p = keep(p[p[:, 2] < 6.0]); lifted.append(p); tag_l += ["B:" + n] * len(p)
    for n in CRANK:
        P0 = S(V.load(n))
        for lf in np.arange(0.0, 20.01, 0.5):
            th = MP.crank_angle(lf); a = math.radians(-th); c, s = math.cos(a), math.sin(a)
            q = P0.copy(); y, z = P0[:, 1] - C.Y_LIFT, P0[:, 2] - C.Z_LIFT
            q[:, 1] = C.Y_LIFT + c * y - s * z; q[:, 2] = C.Z_LIFT + s * y + c * z
            q = keep(q); rigid.append(q); tag_r += [n] * len(q)
    for lf in np.arange(0.0, 20.01, 1.25):
        V_, T_ = C.mesh_of(MP.fpc_lift(lf), 0.01, 0.1); q = keep(S(V_[T_])); rigid.append(q); tag_r += ["fpc_lift"] * len(q)
        q = keep(S(MP.pigtail_tris(lf))); rigid.append(q); tag_r += ["pigtail"] * len(q)
    os.chdir(cwd)
    R = np.concatenate(rigid); L = np.concatenate(lifted)
    LL = np.concatenate([L + np.array([0, 0, lf]) for lf in np.arange(0.0, 20.01, 0.5)])
    tags = np.array(tag_r + tag_l * len(np.arange(0.0, 20.01, 0.5)))
    P = np.concatenate([R, LL])
    np.savez_compressed(os.path.join(HERE, "movcloud.npz"), P=P.astype(np.float32), tags=tags)
    return P, tags


def get():
    f = os.path.join(HERE, "movcloud.npz")
    if os.path.exists(f):
        D = np.load(f); return D["P"].astype(float), D["tags"]
    return build()


if __name__ == "__main__":
    P, t = build(); print(len(P), "points")

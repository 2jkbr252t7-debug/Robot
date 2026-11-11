"""Fast numeric fit check (tuning tool): internal parts of pack/layout.json vs the ANALYTIC outer surfaces of form.py.
Distance = nearest point of a dense surface point cloud (0.25 x 0.4 mm) -> needs >= wall (+1.0 for free parts).
The final verification is done on the CAD solids in check.py."""
import sys, math, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T1/forma/f1")
import t1lib as T
import form as F

PACK = "/tmp/claude-0/gapwf/fin/T1/pack/layout.json"
SHELL_MOUNTED = {"T_stlpik_L", "T_stlpik_R", "T_horny_kruh", "T_reproduktor", "B_golier_prstenec", "T_paka_L",
                 "T_paka_R", "T_kabel_ramena_L", "T_kabel_ramena_R"}
THROUGH = {"T_svetlo", "Z_svetlo", "Z_USB_C", "Z_vypinac", "Z_ToF", "T_shell", "Z_shell"}


def surf_cloud(abfun, n, z0, z1, ds=0.25, dphi=0.4, flats=()):
    pts = []
    for z in F.stations(lambda z: abfun(z)[0], z0, z1, ds):
        a, b = abfun(z)
        if a < 0.05:
            continue
        per = 4 * (a + b)
        m = max(64, int(per / dphi))
        P = np.array(F.se_pts(a, b, n, m, dense=max(2000, 4 * m)))
        pts.append(np.column_stack([P, np.full(len(P), z)]))
    for z, a, b in flats:
        g = np.arange(-a, a + 0.4, 0.4)
        X, Y = np.meshgrid(g, np.arange(-b, b + 0.4, 0.4))
        m = (np.abs(X / a) ** n + np.abs(Y / b) ** n) <= 1
        pts.append(np.column_stack([X[m], Y[m], np.full(m.sum(), z)]))
    return np.vstack(pts)


_TAB = {}


def inside(abfun, n, z0, z1, P):
    key = (abfun.__name__, z0, z1)
    if key not in _TAB:
        zz = np.linspace(z0, z1, 20001)
        ab = np.array([abfun(z) for z in zz])
        _TAB[key] = (zz, ab)
    zz, ab = _TAB[key]
    ok = (P[:, 2] > z0) & (P[:, 2] < z1)
    a = np.interp(P[:, 2], zz, ab[:, 0]); b = np.interp(P[:, 2], zz, ab[:, 1])
    a = np.maximum(a, 1e-6); b = np.maximum(b, 1e-6)
    return ok & ((np.abs(P[:, 0]) / a) ** n + (np.abs(P[:, 1]) / b) ** n < 1)


def tess(L, name, tol=0.2):
    v, t = L.raw(name).tessellate(tol, 0.3)
    V = np.array([[p.X, p.Y, p.Z] for p in v])
    Tr = np.array(t)
    mids = (V[Tr[:, 0]] + V[Tr[:, 1]] + V[Tr[:, 2]]) / 3
    E = np.vstack([(V[Tr[:, 0]] + V[Tr[:, 1]]) / 2, (V[Tr[:, 1]] + V[Tr[:, 2]]) / 2, (V[Tr[:, 2]] + V[Tr[:, 0]]) / 2])
    return np.vstack([V, mids, E])


def rotz(V, deg, dz=0.0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    W = V @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T
    W[:, 2] += dz
    return W


def run(wall_t=2.2, wall_b=2.2, verbose=True):
    L = T.Layout(PACK)
    tc = surf_cloud(F.torso_ab, F.TN, F.TZ0, F.TZ1,
                    flats=[(F.TZ1, *F.torso_ab(F.TZ1)), (F.TZ0, *F.torso_ab(F.TZ0))])
    bc = surf_cloud(F.base_ab, F.BN, F.BZ0, F.BZ1, flats=[(F.BZ1, *F.base_ab(F.BZ1))])
    tk, bk = cKDTree(tc), cKDTree(bc)
    res = {"torso": {}, "base": {}}
    for c in L.comps:
        nm, g = c["name"], c["group"]
        if nm in THROUGH or g in ("H", "AR", "AL") or nm.startswith("B_") and nm != "B_golier_prstenec" and g not in ("P", "L"):
            continue
        V = tess(L, nm)
        if g in ("T", "P", "L") and V[:, 2].max() > F.TZ0 + 0.01:
            if g == "T":
                sets = [V]
            elif g == "P":
                sets = [rotz(V, a) for a in range(-85, 86, 5)]
            else:
                sets = [rotz(V, a, dz) for a in range(-85, 86, 10) for dz in (0, 5, 10, 15, 20)]
            P = np.vstack(sets)
            P = P[P[:, 2] > F.TZ0 - 0.01]
            d, _ = tk.query(P)
            ins = inside(F.torso_ab, F.TN, F.TZ0 - 1e-6, F.TZ1 + 1e-6, P) | (np.abs(P[:, 2] - F.TZ1) < 1e-6)
            need = wall_t + (0.0 if nm in SHELL_MOUNTED else 1.0)
            k = int(np.argmin(np.where(ins, d, -d)))
            dm = float(d[k]) if ins[k] else -float(d[k])
            res["torso"][nm] = (round(dm - need, 2), [round(float(v), 1) for v in P[k]])
        if g == "B" or (g == "T" and V[:, 2].min() < F.TZ0 - 0.01):
            P = V if g == "B" else np.vstack([rotz(V, a) for a in range(-155, 156, 10)])
            if g == "T":
                P = P[P[:, 2] < F.TZ0]
            P = P[P[:, 2] > F.BZ0 + 0.01]
            if not len(P):
                continue
            d, _ = bk.query(P)
            ins = inside(F.base_ab, F.BN, F.BZ0, F.BZ1, P)
            need = wall_b + 1.0
            dd = np.where(ins, d, -d)
            k = int(np.argmin(dd))
            res["base"][nm] = (round(float(dd[k]) - need, 2), [round(float(v), 1) for v in P[k]])
    if verbose:
        for part in ("torso", "base"):
            for nm, (m, p) in sorted(res[part].items(), key=lambda kv: kv[1][0]):
                print(f"{part:5s} {nm:22s} margin {m:6.2f} at {p}")
    return res


if __name__ == "__main__":
    run()

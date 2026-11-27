"""C4: wall thickness of the new / changed printed parts by inward ray casting (Moller-Trumbore) from random surface samples
(mesh vertices excluded).  Reports min thickness and every spot < 1.2 mm clustered, with (x, r, az).  Region filters keep the
check on the changed zones (plug: x > 44, A_vnut: around the opening)."""
import sys, os, json, math
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/klb")
import numpy as np
from scipy.spatial import cKDTree
import mio, klb as K


def samples(T, h, seed=1):
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    cr = np.cross(B - A, C - A); ar = 0.5 * np.linalg.norm(cr, axis=1)
    n = np.maximum(1, np.ceil(ar / (h * h * 0.5)).astype(int))
    rng = np.random.default_rng(seed)
    idx = np.repeat(np.arange(len(T)), n)
    u = rng.uniform(0.05, 0.95, len(idx)); v = rng.uniform(0.05, 0.95, len(idx))
    m = u + v > 0.95; u[m] = 0.95 - u[m] * 0.5; v[m] = 0.95 - v[m] * 0.5
    u = np.clip(u, 0.02, 0.96); v = np.clip(v, 0.02, 0.96 - u)
    P = A[idx] + u[:, None] * (B[idx] - A[idx]) + v[:, None] * (C[idx] - A[idx])
    N = cr[idx] / np.maximum(np.linalg.norm(cr[idx], axis=1), 1e-12)[:, None]
    return P, N, idx


def thickness(T, P, N, src, tmax=3.0, chunk=4000):
    """distance along -N to the next triangle (excluding the source triangle); tmax if none"""
    C = T.mean(1)
    rad = np.linalg.norm(T - C[:, None, :], axis=2).max(1)
    tr = cKDTree(C)
    out = np.full(len(P), tmax)
    R = tmax / 2 + rad.max()
    for s in range(0, len(P), chunk):
        p = P[s:s + chunk]; d = -N[s:s + chunk]; sr = src[s:s + chunk]
        mid = p + d * (tmax / 2)
        lists = tr.query_ball_point(mid, R)
        ln = np.array([len(l) for l in lists])
        if ln.sum() == 0:
            continue
        ri = np.repeat(np.arange(len(p)), ln); ti = np.concatenate([np.asarray(l, int) for l in lists])
        keep = ti != sr[ri]
        ri, ti = ri[keep], ti[keep]
        O = p[ri]; D = d[ri]
        v0, v1, v2 = T[ti, 0], T[ti, 1], T[ti, 2]
        e1 = v1 - v0; e2 = v2 - v0
        h = np.cross(D, e2); a = np.einsum("ij,ij->i", e1, h)
        ok = np.abs(a) > 1e-12
        f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
        sv = O - v0
        u = f * np.einsum("ij,ij->i", sv, h)
        q = np.cross(sv, e1)
        v = f * np.einsum("ij,ij->i", D, q)
        t = f * np.einsum("ij,ij->i", e2, q)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < tmax)
        if hit.any():
            np.minimum.at(out, s + ri[hit], t[hit])
    return out


def subdivide(T, emax=1.0):
    while True:
        L = np.stack([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                      np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], 1)
        big = L.max(1) > emax
        if not big.any():
            return T
        B = T[big]; k = np.argmax(L[big], 1)
        i0 = k; i1 = (k + 1) % 3; i2 = (k + 2) % 3
        r = np.arange(len(B))
        a, b, c = B[r, i0], B[r, i1], B[r, i2]
        m = 0.5 * (a + b)
        T = np.concatenate([T[~big], np.stack([a, m, c], 1), np.stack([m, b, c], 1)])


def run(name, path, region, h=0.12, tmax=3.0):
    T = subdivide(mio.load(path))
    n, bad, vol = mio.manifold(T)
    if vol < 0:
        T = T[:, ::-1]
    P, N, src = samples(T, h)
    m = region(P)
    P, N, src = P[m], N[m], src[m]
    t = thickness(T, P, N, src, tmax)
    thin = t < 1.2
    res = dict(n=int(len(P)), min=round(float(t.min()), 3), n_below_1_2=int(thin.sum()), spots=[])
    if thin.any():
        Q = P[thin]; tt = t[thin]
        # cluster by 1.5 mm
        lab = -np.ones(len(Q), int); c = 0
        trq = cKDTree(Q)
        for i in np.argsort(tt):
            if lab[i] >= 0:
                continue
            stack = [i]; lab[i] = c
            while stack:
                j = stack.pop()
                for k in trq.query_ball_point(Q[j], 1.5):
                    if lab[k] < 0:
                        lab[k] = c; stack.append(k)
            c += 1
        for ci in range(c):
            mm = lab == ci
            k = np.argmin(np.where(mm, tt, 9))
            q = Q[k]
            res["spots"].append(dict(min=round(float(tt[k]), 3), n=int(mm.sum()), xyz=q.round(2).tolist(),
                                     xr=mio.xr(q[None])[0].round(2).tolist(), az=round(float(mio.az(q[None])[0]), 1)))
        res["spots"].sort(key=lambda s: s["min"])
    print(f"{name:34s} n {res['n']:7d} min {res['min']:.3f} below1.2 {res['n_below_1_2']:6d}")
    for s_ in res["spots"][:12]:
        print("      ", s_)
    return res


OUT = {}
plug_reg = lambda P: P[:, 0] > 43.0
all_reg = lambda P: np.ones(len(P), bool)
hole_reg = lambda P: (mio.xr(P)[:, 1] < 17.0) & (P[:, 0] < 62.0)
jobs = [("K0/PLG_zatka_K0", K.stl("K0", "PLG_zatka_K0"), plug_reg),
        ("K1/PLG_zatka_K1", K.stl("K1", "PLG_zatka_K1"), plug_reg),
        ("K2/PLG_zatka_K2", K.stl("K2", "PLG_zatka_K2"), plug_reg),
        ("K3v/PLG_zatka_K3v", K.stl("K3v", "PLG_zatka_K3v"), plug_reg),
        ("K1/ARM_naboj_golier_K1", K.stl("K1", "ARM_naboj_golier_K1"), all_reg),
        ("K3/ARM_naboj_prstenec_K3", K.stl("K3", "ARM_naboj_prstenec_K3"), all_reg),
        ("K0/A_vnut_otvor_K0", K.stl("K0", "A_vnut_otvor_K0"), hole_reg),
        ("K1/A_vnut_otvor_K1", K.stl("K1", "A_vnut_otvor_K1"), hole_reg),
        ("K3/A_vnut_otvor_K3", K.stl("K3", "A_vnut_otvor_K3"), hole_reg)]
sel = sys.argv[1].split(",") if len(sys.argv) > 1 else None
for nm, p, reg in jobs:
    if sel and not any(s in nm for s in sel):
        continue
    OUT[nm] = run(nm, p, reg)
old = {}
fp = os.path.join(HERE, "c4_walls.json")
if os.path.exists(fp):
    old = json.load(open(fp))
old.update(OUT)
json.dump(old, open(fp, "w"), indent=1)

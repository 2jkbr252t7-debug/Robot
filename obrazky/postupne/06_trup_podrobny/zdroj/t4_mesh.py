"""NOVA mini - T4 torso: numpy mesh helpers shared by checks.py (CAD python) and checks_bl.py (Blender python).
Pure numpy (scipy is optional: only Multi / Target need cKDTree).  Triangle soups are arrays (n, 3, 3)."""
from __future__ import annotations
import os, math, struct, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STL_DIR = os.path.join(HERE, "stl")
B_STL = "/tmp/claude-0/gapwf/fin/B/stl"


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def read_stl(path):
    """binary STL -> triangles (n, 3, 3) float64"""
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(np.float64)


def stl(name, d=None):
    if d is None:
        d = STL_DIR if os.path.exists(os.path.join(STL_DIR, name + ".stl")) else B_STL
    return read_stl(os.path.join(d, name + ".stl"))


def weld(T, dec=5):
    """(V (n, 3), F (m, 3)) welded, degenerate triangles removed"""
    V, inv = np.unique(np.round(T.reshape(-1, 3), dec), axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    return V, F


def mesh_stats(T):
    """volume, centre of gravity, watertightness and connected surface components of a triangle soup"""
    V, F = weld(T)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    v6 = np.einsum("ij,ij->i", a, np.cross(b, c))
    vol = v6.sum() / 6.0
    cog = ((a + b + c) * v6[:, None]).sum(0) / (24.0 * vol) if abs(vol) > 1e-9 else np.zeros(3)
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    key = np.sort(E, axis=1); key = key[:, 0].astype(np.int64) * (len(V) + 1) + key[:, 1]
    _, cnt = np.unique(key, return_counts=True)
    dkey = E[:, 0].astype(np.int64) * (len(V) + 1) + E[:, 1]
    _, dcnt = np.unique(dkey, return_counts=True)
    # connected components over shared vertices (union-find)
    par = np.arange(len(V))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i, j in ((F[:, 0], F[:, 1]), (F[:, 1], F[:, 2])):
        for p, q in zip(i.tolist(), j.tolist()):
            rp, rq = find(p), find(q)
            if rp != rq:
                par[rp] = rq
    roots = np.array([find(i) for i in F[:, 0].tolist()])
    comp_ids, comp_idx = np.unique(roots, return_inverse=True)
    comp_vol = np.zeros(len(comp_ids)); np.add.at(comp_vol, comp_idx, v6 / 6.0)
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum()
    return dict(tris=int(len(F)), verts=int(len(V)), volume=float(vol), area=float(area), cog=[round(float(x), 3) for x in cog],
                open_edges=int((cnt == 1).sum()), nonmanifold_edges=int((cnt > 2).sum()), flipped_edges=int((dcnt > 1).sum()),
                components=int(len(comp_ids)), component_volumes=[round(float(v), 3) for v in sorted(comp_vol, reverse=True)[:6]],
                bbox=[round(float(v), 3) for v in (V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max())])


def tri_normals(T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    l = np.linalg.norm(n, axis=1)
    return n / np.maximum(l, 1e-30)[:, None], 0.5 * l


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
    """exact distance of points Pt (n, 3) to triangles (A, B, Cc) (n, 3) each"""
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


class Multi:
    """several parts in ONE KD-tree of surface samples; query -> (point index, exact distance, part index) candidates.
    Exactness: the 8 nearest samples (pitch h) name the candidate triangles, the distance to those triangles is exact."""

    def __init__(self, parts, h=0.4):
        from scipy.spatial import cKDTree
        self.names = list(parts)
        self.T = np.concatenate([parts[n] for n in self.names])
        self.pid = np.concatenate([np.full(len(parts[n]), i, np.int32) for i, n in enumerate(self.names)])
        self.S, self.I = sample(self.T, h, 0.1)
        self.tree = cKDTree(self.S)
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
        dd, ii = self.tree.query(Q[sel], k=k, distance_upper_bound=dmax + 0.3, workers=2)
        rows, cols = np.where(np.isfinite(dd))
        if len(rows) == 0:
            return rows, np.zeros(0), np.zeros(0, np.int32)
        tri = self.I[ii[rows, cols]]
        e = pt_tri(Q[sel[rows]], self.T[tri, 0], self.T[tri, 1], self.T[tri, 2])
        return sel[rows], e, self.pid[tri]

    def min_by_part(self, Q, dmax=1.6):
        """dict part name -> (min distance, query point) for every part within dmax of Q"""
        rows, e, pid = self.query(Q, dmax)
        out = {}
        for p in np.unique(pid):
            m = pid == p
            k = int(np.argmin(e[m]))
            out[self.names[p]] = (float(e[m][k]), Q[rows[m][k]])
        return out


def rotz(Q, deg, cx=0.0, cy=0.0):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array(Q, dtype=np.float64, copy=True)
    x, y = R[..., 0] - cx, R[..., 1] - cy
    R[..., 0] = c * x - s * y + cx; R[..., 1] = s * x + c * y + cy
    return R


def rotx(Q, deg, cy=0.0, cz=0.0):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array(Q, dtype=np.float64, copy=True)
    y, z = R[..., 1] - cy, R[..., 2] - cz
    R[..., 1] = c * y - s * z + cy; R[..., 2] = s * y + c * z + cz
    return R


def bbox(T):
    V = T.reshape(-1, 3)
    return np.concatenate([V.min(0), V.max(0)])


def bb_near(a, b, g=0.0):
    return bool(np.all(a[:3] < b[3:] + g) and np.all(b[:3] < a[3:] + g))


def inset_samples(V, F, h=0.6, shr=0.05):
    """sample points of a closed mesh moved slightly INSIDE the solid (for sweep / ray tests that must ignore coincident
    sliding faces): every welded vertex moved 1.4 x shr along the inward vertex normal, plus a barycentric grid of pitch <= h
    on every triangle, pulled <= 0.06 toward the triangle centroid and moved shr along the inward face normal."""
    T = V[F]
    nrm, area = tri_normals(T)
    VN = np.zeros_like(V)
    for k in range(3):
        np.add.at(VN, F[:, k], nrm * area[:, None])
    VN /= np.maximum(np.linalg.norm(VN, axis=1), 1e-30)[:, None]
    used = np.unique(F)
    Pv = V[used] - 1.4 * shr * VN[used]
    e = np.max([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], axis=0)
    n = np.clip(np.ceil(e / h).astype(int), 1, 400)
    pts = []
    cen = T.mean(1)
    for nv in np.unique(n):
        sel = np.where(n == nv)[0]
        if nv < 2:
            pts.append(cen[sel] - shr * nrm[sel])                 # small triangle: its centroid
            continue
        i, j = np.meshgrid(np.arange(nv + 1), np.arange(nv + 1), indexing="ij")
        m = ((i + j) <= nv) & ~(((i == 0) & (j == 0)) | ((i == nv) & (j == 0)) | ((i == 0) & (j == nv)))
        u, v = i[m] / nv, j[m] / nv
        Q = (T[sel, 0][:, None, :] * (1 - u - v)[None, :, None] + T[sel, 1][:, None, :] * u[None, :, None]
             + T[sel, 2][:, None, :] * v[None, :, None])
        dv = cen[sel][:, None, :] - Q
        dl = np.linalg.norm(dv, axis=2, keepdims=True)
        Q = Q + dv / np.maximum(dl, 1e-12) * np.minimum(0.06, 0.3 * dl) - shr * nrm[sel][:, None, :]
        pts.append(Q.reshape(-1, 3))
    S = np.concatenate(pts) if pts else np.zeros((0, 3))
    if len(S):
        _, k = np.unique(np.round(S / (h / 2)).astype(np.int64), axis=0, return_index=True)
        S = S[k]
    return np.concatenate([Pv, S])


def pulled_samples(T, h=0.5, pull=0.05):
    """(points, triangle index): barycentric grid of pitch <= h on every triangle, every point pulled <= `pull` mm toward the
    triangle centroid (so that no sample sits exactly on an edge), triangle centroids for the small triangles; no vertices."""
    e = np.max([np.linalg.norm(T[:, 1] - T[:, 0], axis=1), np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], axis=0)
    n = np.clip(np.ceil(e / h).astype(int), 1, 400)
    cen = T.mean(1)
    pts, idx = [], []
    for nv in np.unique(n):
        sel = np.where(n == nv)[0]
        if nv < 2:
            pts.append(cen[sel]); idx.append(sel)
            continue
        i, j = np.meshgrid(np.arange(nv + 1), np.arange(nv + 1), indexing="ij")
        m = (i + j) <= nv
        u, v = i[m] / nv, j[m] / nv
        Q = (T[sel, 0][:, None, :] * (1 - u - v)[None, :, None] + T[sel, 1][:, None, :] * u[None, :, None]
             + T[sel, 2][:, None, :] * v[None, :, None])
        dv = cen[sel][:, None, :] - Q
        dl = np.linalg.norm(dv, axis=2, keepdims=True)
        Q = Q + dv / np.maximum(dl, 1e-12) * np.minimum(pull, 0.3 * dl)
        pts.append(Q.reshape(-1, 3)); idx.append(np.repeat(sel, len(u)))
    S, I = np.concatenate(pts), np.concatenate(idx)
    _, k = np.unique(np.round(S / (h / 2)).astype(np.int64), axis=0, return_index=True)       # thin out to about one point per h / 2 cell
    return S[k], I[k]


def ray_tris(T, o, d, tmax=1e9):
    """smallest ray parameter t in (1e-6, tmax) at which the ray o + t d meets one of the triangles T, or None (Moeller-Trumbore)"""
    o = np.asarray(o, float); d = np.asarray(d, float)
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    p = np.cross(d, e2); det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = o - T[:, 0]
    u = (s * p).sum(1) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = (e2 * q).sum(1) * inv
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6) & (t < tmax)
    return float(t[m].min()) if m.any() else None

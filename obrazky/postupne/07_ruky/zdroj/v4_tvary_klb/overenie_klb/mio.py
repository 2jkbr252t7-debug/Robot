"""verifier helpers: STL io, sampling, manifold check, (x, r) conversion (pure numpy + scipy)"""
import struct, math
import numpy as np
YA, ZA = 3.0, -17.0


def load(path):
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0]
    if len(data) == 84 + 50 * n:
        rec = np.frombuffer(data[84:84 + 50 * n], dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        return rec["v"].astype(float)
    V = []
    for line in data.decode(errors="ignore").splitlines():
        s = line.strip().split()
        if s and s[0] == "vertex":
            V.append([float(t) for t in s[1:4]])
    return np.array(V).reshape(-1, 3, 3)


def manifold(T, tol=1e-4):
    """(n_tris, open/nonmanifold edge count, signed volume)"""
    P = T.reshape(-1, 3)
    q = np.round(P / tol).astype(np.int64)
    _, idx = np.unique(q, axis=0, return_inverse=True)
    F = idx.reshape(-1, 3)
    E = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(E, axis=0, return_counts=True)
    bad = int((cnt != 2).sum())
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    vol = float(np.einsum("ij,ij->i", A, np.cross(B, C)).sum() / 6.0)
    return len(T), bad, vol


def sample(T, h=0.2, seed=0, normals=False):
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    cr = np.cross(B - A, C - A)
    ar = 0.5 * np.linalg.norm(cr, axis=1)
    n = np.maximum(1, np.ceil(ar / (h * h * 0.5)).astype(int))
    rng = np.random.default_rng(seed)
    idx = np.repeat(np.arange(len(T)), n)
    u = rng.random(len(idx)); v = rng.random(len(idx))
    m = u + v > 1; u[m] = 1 - u[m]; v[m] = 1 - v[m]
    P = A[idx] + u[:, None] * (B[idx] - A[idx]) + v[:, None] * (C[idx] - A[idx])
    P = np.concatenate([T.reshape(-1, 3), P])
    if not normals:
        return P
    N = cr / np.maximum(np.linalg.norm(cr, axis=1), 1e-12)[:, None]
    N = np.concatenate([np.repeat(N, 3, axis=0), N[idx]])
    return P, N


def xr(P):
    P = np.asarray(P, float)
    return np.c_[P[..., 0], np.hypot(P[..., 1] - YA, P[..., 2] - ZA)]


def az(P):
    return np.degrees(np.arctan2(P[:, 2] - ZA, P[:, 1] - YA)) % 360.0


def swing(Q, deg):
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    Q = np.array(Q, float, copy=True)
    y, z = Q[..., 1] - YA, Q[..., 2] - ZA
    Q[..., 1] = c * y - s * z + YA; Q[..., 2] = s * y + c * z + ZA
    return Q


def seg_dist(Q, P):
    """unsigned distance of 2-D points Q to the closed polygon boundary P"""
    A = P; B = np.roll(P, -1, axis=0); AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-18)
    d = np.full(len(Q), np.inf)
    for i in range(len(P)):
        t = np.clip(((Q - A[i]) @ AB[i]) / L2[i], 0, 1)
        C = A[i] + t[:, None] * AB[i]
        d = np.minimum(d, np.hypot(*(Q - C).T))
    return d


def inpoly(Q, P):
    x, y = Q[:, 0], Q[:, 1]
    ins = np.zeros(len(Q), bool)
    for i in range(len(P)):
        x1, y1 = P[i]; x2, y2 = P[(i + 1) % len(P)]
        c = (y1 > y) != (y2 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
        ins ^= c & (x < xi)
    return ins


def crop(T, center=None, radius=None, rmax=None, xmin=None, xmax=None):
    """keep triangles whose centroid is within radius of center, and/or within rmax of the shoulder axis and x range"""
    C = T.mean(1)
    m = np.ones(len(T), bool)
    if center is not None:
        m &= np.linalg.norm(C - np.asarray(center), axis=1) < radius
    if rmax is not None:
        m &= np.hypot(C[:, 1] - YA, C[:, 2] - ZA) < rmax
    if xmin is not None:
        m &= C[:, 0] > xmin
    if xmax is not None:
        m &= C[:, 0] < xmax
    return T[m]

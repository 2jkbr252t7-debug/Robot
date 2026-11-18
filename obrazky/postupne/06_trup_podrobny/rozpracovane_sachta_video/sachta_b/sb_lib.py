"""sachta_b helper library (lens B review of P_sachta) - numpy only, reads the design STLs read-only.
Frame: B frame, mm, Z up, FRONT = -Y, rest pose (pan 0, lift 0)."""
import struct, os
import numpy as np

T4 = "/tmp/claude-0/gapwf/fin/T4"
STL = os.path.join(T4, "stl")
OUT = os.path.join(T4, "sachta_b")


def read_stl(name):
    path = name if name.endswith(".stl") and os.path.isabs(name) else os.path.join(STL, name if name.endswith(".stl") else name + ".stl")
    with open(path, "rb") as f:
        data = f.read()
    n = struct.unpack("<I", data[80:84])[0]
    if 84 + n * 50 == len(data):
        a = np.frombuffer(data[84:], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n)
        return a["v"].astype(np.float64)
    # ascii fallback
    vs = [list(map(float, l.split()[1:4])) for l in data.decode().splitlines() if l.strip().startswith("vertex")]
    return np.array(vs, dtype=np.float64).reshape(-1, 3, 3)


def ray_hits(T, o, d, eps=1e-9):
    """all ray parameters t (sorted, may be negative) where the line o + t d crosses the mesh T (n,3,3)"""
    o = np.asarray(o, float); d = np.asarray(d, float); d = d / np.linalg.norm(d)
    v0, v1, v2 = T[:, 0], T[:, 1], T[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > eps
    inv = np.zeros_like(det); inv[ok] = 1.0 / det[ok]
    s = o - v0
    u = np.einsum("ij,ij->i", s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    ts = np.sort(t[m])
    # merge duplicates on shared edges
    if len(ts):
        keep = np.concatenate([[True], np.diff(ts) > 1e-6])
        ts = ts[keep]
    return ts


def thickness_along(T, o, d):
    """material intervals along the line o + t d: list of (t_in, t_out)"""
    ts = ray_hits(T, o, d)
    return [(ts[i], ts[i + 1]) for i in range(0, len(ts) - 1, 2)]


def interval_at(T, o, d, t0):
    """the material interval containing t0 (or the nearest one)"""
    iv = thickness_along(T, o, d)
    for a, b in iv:
        if a - 1e-6 <= t0 <= b + 1e-6:
            return a, b
    if not iv:
        return None
    return min(iv, key=lambda ab: min(abs(ab[0] - t0), abs(ab[1] - t0)))


def column_intervals(T, x0, x1, y0, y1, h):
    """Z-column voxeliser: for each (x, y) pixel centre on an h grid, the sorted z crossings of the vertical line.
    returns xs, ys, list-of-arrays (ny, nx) of z crossings"""
    xs = np.arange(x0 + h / 2, x1, h); ys = np.arange(y0 + h / 2, y1, h)
    nx, ny = len(xs), len(ys)
    hits = [[] for _ in range(nx * ny)]
    for tri in T:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-14:
            continue
        i0 = max(int(np.floor((min(ax, bx, cx) - x0) / h - 0.5)), 0); i1 = min(int(np.ceil((max(ax, bx, cx) - x0) / h - 0.5)), nx - 1)
        j0 = max(int(np.floor((min(ay, by, cy) - y0) / h - 0.5)), 0); j1 = min(int(np.ceil((max(ay, by, cy) - y0) / h - 0.5)), ny - 1)
        if i1 < i0 or j1 < j0:
            continue
        X, Y = np.meshgrid(xs[i0:i1 + 1], ys[j0:j1 + 1])
        l1 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
        l2 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
        l3 = 1 - l1 - l2
        m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if not m.any():
            continue
        Z = l1 * az + l2 * bz + l3 * cz
        jj, ii = np.nonzero(m)
        for j, i, z in zip(jj + j0, ii + i0, Z[m]):
            hits[j * nx + i].append(z)
    out = []
    for hl in hits:
        a = np.sort(np.array(hl))
        if len(a):
            a = a[np.concatenate([[True], np.diff(a) > 1e-5])]
        if len(a) % 2:
            a = a[:-1] if len(a) > 1 else np.array([])
        out.append(a)
    return xs, ys, out


def occupancy(out, nx, ny, z):
    m = np.zeros(ny * nx, bool)
    for k, a in enumerate(out):
        if len(a):
            lo, hi = a[0::2], a[1::2]
            m[k] = np.any((lo <= z) & (z <= hi))
    return m.reshape(ny, nx)

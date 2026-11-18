"""helpers for the P_sachta strength review: STL reading, column ray casting (exact parity on the triangle soup),
voxelisation, plane slices.  numpy / scipy only."""
import struct, numpy as np

T4 = "/tmp/claude-0/gapwf/fin/T4"
STL = T4 + "/stl"
BSTL = "/tmp/claude-0/gapwf/fin/B/stl"


def read_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        d = np.frombuffer(f.read(n * 50), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return d["v"].astype(np.float64)


def part(name):
    import os
    p = f"{STL}/{name}.stl"
    return read_stl(p if os.path.exists(p) else f"{BSTL}/{name}.stl")


def column_crossings(T, us, vs, axis=2, eps=1e-7):
    """for every grid column (u in us, v in vs) along `axis`, the sorted crossing coordinates of the closed mesh T.
    The two other axes (in cyclic order axis+1, axis+2) are u, v.  Returns dict {(i, j): array}.  Grid jitter of eps avoids
    hitting edges exactly."""
    a1, a2 = (axis + 1) % 3, (axis + 2) % 3
    P = T[:, :, [a1, a2]]; W = T[:, :, axis]
    us = np.asarray(us) + eps * 1.234567; vs = np.asarray(vs) + eps * 2.345678
    du = us[1] - us[0] if len(us) > 1 else 1.0; dv = vs[1] - vs[0] if len(vs) > 1 else 1.0
    out = {}
    lo = P.min(1); hi = P.max(1)
    i0 = np.clip(np.ceil((lo[:, 0] - us[0]) / du).astype(int), 0, len(us)); i1 = np.clip(np.floor((hi[:, 0] - us[0]) / du).astype(int), -1, len(us) - 1)
    j0 = np.clip(np.ceil((lo[:, 1] - vs[0]) / dv).astype(int), 0, len(vs)); j1 = np.clip(np.floor((hi[:, 1] - vs[0]) / dv).astype(int), -1, len(vs) - 1)
    hits_i, hits_j, hits_w = [], [], []
    for t in range(len(T)):
        if i1[t] < i0[t] or j1[t] < j0[t]:
            continue
        uu, vv = np.meshgrid(us[i0[t]:i1[t] + 1], vs[j0[t]:j1[t] + 1], indexing="ij")
        (x0, y0), (x1, y1), (x2, y2) = P[t]
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(det) < 1e-14:
            continue
        l0 = ((y1 - y2) * (uu - x2) + (x2 - x1) * (vv - y2)) / det
        l1 = ((y2 - y0) * (uu - x2) + (x0 - x2) * (vv - y2)) / det
        l2 = 1 - l0 - l1
        m = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not m.any():
            continue
        w = l0 * W[t, 0] + l1 * W[t, 1] + l2 * W[t, 2]
        ii, jj = np.nonzero(m)
        hits_i.append(ii + i0[t]); hits_j.append(jj + j0[t]); hits_w.append(w[m])
    if not hits_i:
        return out
    hi_ = np.concatenate(hits_i); hj_ = np.concatenate(hits_j); hw_ = np.concatenate(hits_w)
    key = hi_ * len(vs) + hj_
    order = np.lexsort((hw_, key))
    key, hw_ = key[order], hw_[order]
    bounds = np.flatnonzero(np.diff(key)) + 1
    for k, w in zip(np.split(key, bounds), np.split(hw_, bounds)):
        # merge duplicates (shared edges counted twice despite jitter) - keep unique within 1e-6
        w = np.asarray(w)
        if len(w) > 1:
            keep = np.concatenate([[True], np.diff(w) > 1e-6]); w = w[keep]
        out[(int(k[0]) // len(vs), int(k[0]) % len(vs))] = w
    return out


def voxelize(T, origin, h, shape, axis=2):
    """bool array shape (nx, ny, nz): voxel centres origin + (i + 0.5) h inside T (parity along z)"""
    nx, ny, nz = shape
    xs = origin[0] + (np.arange(nx) + 0.5) * h; ys = origin[1] + (np.arange(ny) + 0.5) * h
    zs = origin[2] + (np.arange(nz) + 0.5) * h
    cr = column_crossings(T, xs, ys, axis=2)
    V = np.zeros(shape, bool)
    for (i, j), w in cr.items():
        if len(w) % 2:
            w = w[:-1] if len(w) > 1 else w[:0]
        for a, b in zip(w[0::2], w[1::2]):
            k0 = int(np.ceil((a - origin[2]) / h - 0.5)); k1 = int(np.floor((b - origin[2]) / h - 0.5))
            k0 = max(k0, 0); k1 = min(k1, nz - 1)
            if k1 >= k0:
                V[i, j, k0:k1 + 1] = True
    return V


def intervals(w):
    w = np.asarray(w)
    if len(w) % 2:
        w = w[:-1]
    return list(zip(w[0::2], w[1::2]))


def slice_segments(T, axis, value):
    """intersection segments of the triangle soup with the plane coord[axis] = value -> (n, 2, 3)"""
    d = T[:, :, axis] - value
    s = np.sign(d); s[s == 0] = 1e-9
    m = ~((s > 0).all(1) | (s < 0).all(1))
    segs = []
    for tri, dd in zip(T[m], d[m]):
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if (dd[a] > 0) != (dd[b] > 0):
                t = dd[a] / (dd[a] - dd[b]); pts.append(tri[a] + t * (tri[b] - tri[a]))
        if len(pts) == 2:
            segs.append(pts)
    return np.array(segs)


def raster_slice(T, axis, value, u_rng, v_rng, h):
    """2-D occupancy of the slice plane (u, v = the two other axes in cyclic order) by ray parity along u"""
    a1, a2 = (axis + 1) % 3, (axis + 2) % 3
    segs = slice_segments(T, axis, value)
    us = np.arange(u_rng[0] + h / 2, u_rng[1], h); vs = np.arange(v_rng[0] + h / 2, v_rng[1], h)
    M = np.zeros((len(us), len(vs)), bool)
    if len(segs) == 0:
        return us, vs, M
    A = segs[:, 0, [a1, a2]]; B = segs[:, 1, [a1, a2]]
    for j, v in enumerate(vs):
        v = v + 1.3e-7
        m = (A[:, 1] > v) != (B[:, 1] > v)
        if not m.any():
            continue
        t = (v - A[m, 1]) / (B[m, 1] - A[m, 1]); uc = np.sort(A[m, 0] + t * (B[m, 0] - A[m, 0]))
        cnt = np.searchsorted(uc, us)
        M[:, j] = (cnt % 2) == 1
    return us, vs, M

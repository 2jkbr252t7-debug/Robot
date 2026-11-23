# verifier's own small mesh library (numpy / scipy only)
import numpy as np, struct, os
from scipy.spatial import cKDTree
T4 = "/tmp/claude-0/gapwf/fin/T4"

def load_stl(path):
    with open(path, 'rb') as f:
        data = f.read()
    n = struct.unpack('<I', data[80:84])[0]
    if len(data) == 84 + 50 * n:
        dt = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
        arr = np.frombuffer(data, dtype=dt, count=n, offset=84)
        return arr['v'].astype(np.float64)
    # ascii
    tris = []; cur = []
    for line in data.decode(errors='ignore').splitlines():
        s = line.split()
        if s and s[0] == 'vertex':
            cur.append([float(x) for x in s[1:4]])
            if len(cur) == 3: tris.append(cur); cur = []
    return np.array(tris, dtype=np.float64)

def volume(tr):
    return float(np.einsum('ij,ij->i', tr[:, 0], np.cross(tr[:, 1], tr[:, 2])).sum() / 6.0)

def bbox(tr):
    v = tr.reshape(-1, 3)
    return np.concatenate([v.min(0), v.max(0)])

def area(tr):
    return float(0.5 * np.linalg.norm(np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]), axis=1).sum())

def sample_surface(tr, h=0.2, with_tri=False, thin=0.6):
    """deterministic barycentric subdivision sampling, spacing about h; returns points (and triangle ids)"""
    e = np.maximum.reduce([np.linalg.norm(tr[:, 1] - tr[:, 0], axis=1), np.linalg.norm(tr[:, 2] - tr[:, 1], axis=1), np.linalg.norm(tr[:, 0] - tr[:, 2], axis=1)])
    nsub = np.clip(np.ceil(e / h).astype(int), 1, 400)
    pts = []; ids = []
    for k in np.unique(nsub):
        idx = np.nonzero(nsub == k)[0]
        t = tr[idx]
        ij = [(i, j) for i in range(k + 1) for j in range(k + 1 - i)]
        ij = np.array(ij, dtype=float) / k
        w0 = 1 - ij[:, 0] - ij[:, 1]
        p = (w0[None, :, None] * t[:, None, 0, :] + ij[None, :, 0, None] * t[:, None, 1, :] + ij[None, :, 1, None] * t[:, None, 2, :])
        pts.append(p.reshape(-1, 3)); ids.append(np.repeat(idx, len(ij)))
    P = np.concatenate(pts); I = np.concatenate(ids)
    if thin:                      # one sample per voxel of size thin*h (tiny STL triangles would give millions of duplicates)
        s = thin * h
        q = np.floor(P / s).astype(np.int64); q -= q.min(0)
        m = q.max(0) + 1
        key = (q[:, 0] * m[1] + q[:, 1]) * m[2] + q[:, 2]
        _, first = np.unique(key, return_index=True)
        P = P[first]; I = I[first]
    return (P, I) if with_tri else P

def pt_tri_dist(P, A, B, C):
    """exact distance point(s) P[i] to triangle(s) (A[i],B[i],C[i]); returns dist, closest point (Ericson)"""
    ab = B - A; ac = C - A; ap = P - A
    d1 = np.einsum('ij,ij->i', ab, ap); d2 = np.einsum('ij,ij->i', ac, ap)
    bp = P - B; d3 = np.einsum('ij,ij->i', ab, bp); d4 = np.einsum('ij,ij->i', ac, bp)
    cp = P - C; d5 = np.einsum('ij,ij->i', ab, cp); d6 = np.einsum('ij,ij->i', ac, cp)
    vc = d1 * d4 - d3 * d2; vb = d5 * d2 - d1 * d6; va = d3 * d6 - d5 * d4
    Q = np.empty_like(P)
    done = np.zeros(len(P), bool)
    def setq(m, val):
        mm = m & ~done
        Q[mm] = val[mm]; done[mm] = True
    setq((d1 <= 0) & (d2 <= 0), A)
    setq((d3 >= 0) & (d4 <= d3), B)
    with np.errstate(divide='ignore', invalid='ignore'):
        v = d1 / (d1 - d3)
        setq((vc <= 0) & (d1 >= 0) & (d3 <= 0), A + v[:, None] * ab)
        setq((d6 >= 0) & (d5 <= d6), C)
        w = d2 / (d2 - d6)
        setq((vb <= 0) & (d2 >= 0) & (d6 <= 0), A + w[:, None] * ac)
        w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        setq((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), B + w2[:, None] * (C - B))
        den = 1.0 / (va + vb + vc)
        v = vb * den; w = vc * den
        setq(np.ones(len(P), bool), A + ab * v[:, None] + ac * w[:, None])
    return np.linalg.norm(P - Q, axis=1), Q

def voxel_index(tr, s):
    """samples at spacing <= s; returns unique-voxel sample points + CSR (voxel -> every triangle that has a sample in it)"""
    P, I = sample_surface(tr, s, True, thin=None)
    q = np.floor(P / s).astype(np.int64); q -= q.min(0)
    m = q.max(0) + 1
    key = (q[:, 0] * m[1] + q[:, 1]) * m[2] + q[:, 2]
    nt = len(tr)
    pk = np.unique(key * nt + I)                                    # unique (voxel, triangle)
    pv = pk // nt; ptri = pk % nt
    ukey, start = np.unique(pv, return_index=True)
    end = np.append(start[1:], len(pk))
    _, first = np.unique(key, return_index=True)                    # one representative point per voxel (same order as ukey)
    return P[first], start, end, ptri

class Mesh:
    def __init__(self, tr, h=0.25):
        self.tr = tr; self.h = h
        self.bb = bbox(tr)
        self._samp = None; self._tree = None; self._grid = None
    @property
    def samp(self):
        if self._samp is None:
            self._samp, self._vs, self._ve, self._vt = voxel_index(self.tr, 0.6 * self.h)
        return self._samp
    @property
    def tree(self):
        if self._tree is None:
            self._tree = cKDTree(self.samp)
        return self._tree
    def dist(self, P, k=8, dmax=np.inf):
        """exact unsigned distance of points to the surface: candidates = EVERY triangle registered in the k nearest voxels"""
        P = np.atleast_2d(P)
        d0, i0 = self.tree.query(P, k=k, distance_upper_bound=dmax)
        out = np.full(len(P), np.inf); Qo = np.full((len(P), 3), np.nan)
        ok = np.isfinite(d0)
        pi, kj = np.nonzero(ok)
        if len(pi) == 0: return out, Qo
        v = i0[pi, kj]; n = self._ve[v] - self._vs[v]
        pid = np.repeat(pi, n)
        off = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
        tid = self._vt[np.repeat(self._vs[v], n) + off]
        nt = len(self.tr); pk = np.unique(pid.astype(np.int64) * nt + tid); pid, tid = pk // nt, pk % nt
        for s0 in range(0, len(pid), 2_000_000):
            sl = slice(s0, s0 + 2_000_000)
            d, Q = pt_tri_dist(P[pid[sl]], self.tr[tid[sl], 0], self.tr[tid[sl], 1], self.tr[tid[sl], 2])
            o = np.lexsort((d, pid[sl])); pp = pid[sl][o]
            f = np.concatenate([[True], pp[1:] != pp[:-1]])
            idx = pp[f]; dd = d[o][f]; qq = Q[o][f]
            better = dd < out[idx]
            out[idx[better]] = dd[better]; Qo[idx[better]] = qq[better]
        return out, Qo
    def _build_grid(self, cell=0.5):
        tr = self.tr
        lo = tr[:, :, :2].min(1); hi = tr[:, :, :2].max(1)
        self.g0 = self.bb[:2] - 1e-3; self.gc = cell
        nx, ny = (np.ceil((self.bb[3:5] - self.g0) / cell) + 2).astype(int)
        self.gn = (nx, ny)
        i0 = np.floor((lo - self.g0) / cell).astype(int); i1 = np.floor((hi - self.g0) / cell).astype(int)
        sx = i1[:, 0] - i0[:, 0] + 1; sy = i1[:, 1] - i0[:, 1] + 1
        keys = []; tids = []
        code = sx * 100000 + sy
        for c in np.unique(code):
            m = np.nonzero(code == c)[0]; a, b = int(c // 100000), int(c % 100000)
            X, Y = np.meshgrid(np.arange(a), np.arange(b), indexing='ij'); X = X.ravel(); Y = Y.ravel()
            kx = i0[m, 0][:, None] + X[None, :]; ky = i0[m, 1][:, None] + Y[None, :]
            keys.append((kx * ny + ky).ravel()); tids.append(np.repeat(m, len(X)))
        key = np.concatenate(keys); tid = np.concatenate(tids)
        order = np.argsort(key, kind='stable'); key = key[order]; tid = tid[order]
        self.gkey_start = np.searchsorted(key, np.arange(nx * ny), 'left')
        self.gkey_end = np.searchsorted(key, np.arange(nx * ny), 'right')
        self.gtid = tid
        self._grid = True
    def inside(self, P, chunk=3_000_000):
        """point-in-solid: parity of crossings of the +z AND the -z ray must both be odd (grid accelerated, jittered)"""
        if self._grid is None: self._build_grid()
        P = np.atleast_2d(P).astype(float)
        res = np.zeros(len(P), bool)
        inb = np.all((P >= self.bb[:3]) & (P <= self.bb[3:]), axis=1)
        idx = np.nonzero(inb)[0]
        if len(idx) == 0: return res
        Pj = P[idx] + np.array([1.2345e-5, 2.3456e-5, 3.1e-6])
        c = np.floor((Pj[:, :2] - self.g0) / self.gc).astype(int)
        key = c[:, 0] * self.gn[1] + c[:, 1]
        s = self.gkey_start[key]; e = self.gkey_end[key]
        n = e - s
        up = np.zeros(len(idx), int); dn = np.zeros(len(idx), int)
        cs = np.cumsum(n); start = 0
        while start < len(idx):
            base = cs[start - 1] if start else 0
            end = int(np.searchsorted(cs, base + chunk, 'right')); end = max(end, start + 1)
            nn = n[start:end]
            pid = np.repeat(np.arange(start, end), nn)
            off = np.arange(nn.sum()) - np.repeat(np.cumsum(nn) - nn, nn)
            tid = self.gtid[np.repeat(s[start:end], nn) + off]
            A = self.tr[tid, 0]; B = self.tr[tid, 1]; C = self.tr[tid, 2]
            p = Pj[pid]
            w0 = (C[:, 0] - B[:, 0]) * (p[:, 1] - B[:, 1]) - (C[:, 1] - B[:, 1]) * (p[:, 0] - B[:, 0])
            w1 = (A[:, 0] - C[:, 0]) * (p[:, 1] - C[:, 1]) - (A[:, 1] - C[:, 1]) * (p[:, 0] - C[:, 0])
            w2 = (B[:, 0] - A[:, 0]) * (p[:, 1] - A[:, 1]) - (B[:, 1] - A[:, 1]) * (p[:, 0] - A[:, 0])
            hit = ((w0 > 0) & (w1 > 0) & (w2 > 0)) | ((w0 < 0) & (w1 < 0) & (w2 < 0))
            den = w0 + w1 + w2
            with np.errstate(divide='ignore', invalid='ignore'):
                z = (w0 * A[:, 2] + w1 * B[:, 2] + w2 * C[:, 2]) / den
            up += np.bincount(pid[hit & (z > p[:, 2])], minlength=len(idx))
            dn += np.bincount(pid[hit & (z < p[:, 2])], minlength=len(idx))
            start = end
        res[idx] = ((up % 2) == 1) & ((dn % 2) == 1)
        return res

def rotz(P, deg, c=(0.0, 0.0)):
    a = np.radians(deg); ca, sa = np.cos(a), np.sin(a)
    Q = P.copy()
    x = P[..., 0] - c[0]; y = P[..., 1] - c[1]
    Q[..., 0] = c[0] + ca * x - sa * y; Q[..., 1] = c[1] + sa * x + ca * y
    return Q

_cache = {}
def part(name, d="stl", h=0.25):
    key = (name, d, h)
    if key not in _cache:
        _cache[key] = Mesh(load_stl(os.path.join(T4, d, name + ".stl")), h)
    return _cache[key]

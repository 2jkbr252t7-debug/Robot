"""Small voxel helpers for the torso free-space map (numpy / scipy only).  Nothing in T4 / T3 / B is written.
Grid convention: voxel (i, j, k) has its centre at lo + (i + 0.5, j + 0.5, k + 0.5) * h.
"""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib  # noqa: E402

T4 = "/tmp/claude-0/gapwf/fin/T4"
BST = "/tmp/claude-0/gapwf/fin/B/stl"


class Grid:
    def __init__(self, lo, hi, h):
        self.lo = np.asarray(lo, float)
        self.h = float(h)
        self.n = tuple(int(v) for v in np.ceil((np.asarray(hi, float) - self.lo) / h - 1e-9))

    def axis(self, a):
        return self.lo[a] + (np.arange(self.n[a]) + 0.5) * self.h

    def centres(self, mask=None):
        if mask is None:
            I = np.indices(self.n).reshape(3, -1).T
        else:
            I = np.argwhere(mask)
        return self.lo + (I + 0.5) * self.h

    def index(self, P):
        return np.floor((np.asarray(P, float) - self.lo) / self.h).astype(np.int64)


def _expand_pairs(i0, i1, j0, j1):
    """(triangle, column) pairs for column index boxes [i0..i1] x [j0..j1] (inclusive)"""
    ni = i1 - i0 + 1; nj = j1 - j0 + 1
    ok = (ni > 0) & (nj > 0)
    tids, I, J = [], [], []
    code = np.where(ok, ni * 100000 + nj, -1)
    for c in np.unique(code[ok]):
        m = np.nonzero(code == c)[0]
        a, b = int(c // 100000), int(c % 100000)
        X, Y = np.meshgrid(np.arange(a), np.arange(b), indexing="ij")
        X = X.ravel(); Y = Y.ravel()
        tids.append(np.repeat(m, len(X)))
        I.append((i0[m][:, None] + X[None, :]).ravel())
        J.append((j0[m][:, None] + Y[None, :]).ravel())
    if not tids:
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0, int)
    return np.concatenate(tids), np.concatenate(I), np.concatenate(J)


def vox_solid(tr, g, surface=True, h_surf=None):
    """bool grid (g.n): voxel centres inside the closed mesh `tr` (z-ray parity) OR voxels touched by surface samples.
    Only the sub-box of the mesh bbox is processed."""
    out = np.zeros(g.n, bool)
    if len(tr) == 0:
        return out
    h = g.h; x0, y0, z0 = g.lo
    jx, jy = 1.37e-4, 2.71e-4
    lo = tr.reshape(-1, 3).min(0); hi = tr.reshape(-1, 3).max(0)
    # sub grid limits (index space)
    a0 = np.clip(np.floor((lo - g.lo) / h).astype(int) - 1, 0, np.array(g.n) - 1)
    a1 = np.clip(np.ceil((hi - g.lo) / h).astype(int) + 1, 0, np.array(g.n) - 1)
    if np.any(hi < g.lo) or np.any(lo > g.lo + np.array(g.n) * h):
        return out
    sub = tuple(a1 - a0 + 1)
    xy = tr[:, :, :2]
    tlo = xy.min(1); thi = xy.max(1)
    i0 = np.ceil((tlo[:, 0] - x0 - jx) / h - 0.5).astype(int); i1 = np.floor((thi[:, 0] - x0 - jx) / h - 0.5).astype(int)
    j0 = np.ceil((tlo[:, 1] - y0 - jy) / h - 0.5).astype(int); j1 = np.floor((thi[:, 1] - y0 - jy) / h - 0.5).astype(int)
    i0 = np.maximum(i0, a0[0]); i1 = np.minimum(i1, a1[0]); j0 = np.maximum(j0, a0[1]); j1 = np.minimum(j1, a1[1])
    tid, I, J = _expand_pairs(i0, i1, j0, j1)
    cnt = np.zeros((sub[0], sub[1], sub[2] + 1), np.int16)
    CH = 4_000_000
    for s in range(0, len(tid), CH):
        t = tid[s:s + CH]; ii = I[s:s + CH]; jj = J[s:s + CH]
        px = x0 + (ii + 0.5) * h + jx; py = y0 + (jj + 0.5) * h + jy
        A = tr[t, 0]; B = tr[t, 1]; Cc = tr[t, 2]
        w0 = (Cc[:, 0] - B[:, 0]) * (py - B[:, 1]) - (Cc[:, 1] - B[:, 1]) * (px - B[:, 0])
        w1 = (A[:, 0] - Cc[:, 0]) * (py - Cc[:, 1]) - (A[:, 1] - Cc[:, 1]) * (px - Cc[:, 0])
        w2 = (B[:, 0] - A[:, 0]) * (py - A[:, 1]) - (B[:, 1] - A[:, 1]) * (px - A[:, 0])
        hit = ((w0 > 0) & (w1 > 0) & (w2 > 0)) | ((w0 < 0) & (w1 < 0) & (w2 < 0))
        den = w0 + w1 + w2
        with np.errstate(divide="ignore", invalid="ignore"):
            z = (w0 * A[:, 2] + w1 * B[:, 2] + w2 * Cc[:, 2]) / den
        hit &= np.isfinite(z)
        m = np.ceil((z[hit] - z0) / h - 0.5).astype(int) - a0[2]
        m = np.clip(m, 0, sub[2])
        np.add.at(cnt, (ii[hit] - a0[0], jj[hit] - a0[1], m), 1)
    par = (np.cumsum(cnt[:, :, :-1], axis=2) % 2).astype(bool)
    out[a0[0]:a1[0] + 1, a0[1]:a1[1] + 1, a0[2]:a1[2] + 1] = par
    if surface:
        P = vlib.sample_surface(tr, h_surf or 0.4 * h, thin=0.5)
        k = g.index(P)
        ok = np.all((k >= 0) & (k < np.array(g.n)), axis=1)
        k = k[ok]
        out[k[:, 0], k[:, 1], k[:, 2]] = True
    return out


def solid_points(tr, h=0.5, h_surf=0.25):
    """points filling a closed mesh: centres of inside voxels of a local h-grid + surface samples (for sweeps)"""
    lo = tr.reshape(-1, 3).min(0) - h; hi = tr.reshape(-1, 3).max(0) + h
    g = Grid(lo, hi, h)
    m = vox_solid(tr, g, surface=False)
    P = g.centres(m)
    S = vlib.sample_surface(tr, h_surf, thin=0.5)
    return np.concatenate([P, S]) if len(P) else S


def load(name, d=None):
    return vlib.load_stl(os.path.join(d or (T4 + "/stl"), name + ".stl"))


def sweep_cum(occ, axis, sign):
    """cumulative OR along an axis: a part withdrawn along +axis (sign +1) sweeps every voxel on the + side of its material"""
    if sign > 0:
        return np.maximum.accumulate(occ, axis=axis)
    sl = [slice(None)] * 3; sl[axis] = slice(None, None, -1)
    return np.maximum.accumulate(occ[tuple(sl)], axis=axis)[tuple(sl)]


def max_box(F, h, step=2, min_dim=0):
    """largest-volume axis-aligned box of True voxels in F (3-D bool).  Box x/y sizes scanned in `step`-voxel steps,
    z extent exact (longest run).  Returns (volume, (i0, j0, k0), (ni, nj, nk)).  min_dim (voxels) filters thin boxes."""
    nx, ny, nz = F.shape
    B = (~F).astype(np.int32)
    S = np.zeros((nx + 1, ny + 1, nz), np.int32)
    S[1:, 1:, :] = B.cumsum(0).cumsum(1)
    best = (0, None, None)
    for a in range(max(1, min_dim), nx + 1, step):
        for b in range(max(1, min_dim), ny + 1, step):
            if a * b * nz <= best[0]:
                continue
            W = S[a:, b:, :] - S[:-a, b:, :] - S[a:, :-b, :] + S[:-a, :-b, :]
            E = (W == 0)
            if not E.any():
                break
            # longest run of True along z for every (i, j)
            Z = np.zeros(E.shape[:2] + (1,), bool)
            D = np.diff(np.concatenate([Z, E, Z], axis=2).astype(np.int8), axis=2)
            si = np.argwhere(D == 1); ei = np.argwhere(D == -1)
            L = ei[:, 2] - si[:, 2]
            k = int(np.argmax(L)); c = int(L[k])
            if c < min_dim:
                continue
            v = a * b * c
            if v > best[0]:
                best = (v, (int(si[k, 0]), int(si[k, 1]), int(si[k, 2])), (a, b, c))
    return best


def box_fits(F, dims_vox):
    """all positions (i0, j0, k0) where a box of dims_vox (ni, nj, nk) lies entirely in True voxels of F"""
    a, b, c = dims_vox
    if a > F.shape[0] or b > F.shape[1] or c > F.shape[2]:
        return np.zeros((0, 3), int)
    B = (~F).astype(np.int32)
    S = np.zeros((F.shape[0] + 1, F.shape[1] + 1, F.shape[2] + 1), np.int32)
    S[1:, 1:, 1:] = B.cumsum(0).cumsum(1).cumsum(2)
    W = (S[a:, b:, c:] - S[:-a, b:, c:] - S[a:, :-b, c:] - S[a:, b:, :-c]
         + S[:-a, :-b, c:] + S[:-a, b:, :-c] + S[a:, :-b, :-c] - S[:-a, :-b, :-c])
    return np.argwhere(W == 0)

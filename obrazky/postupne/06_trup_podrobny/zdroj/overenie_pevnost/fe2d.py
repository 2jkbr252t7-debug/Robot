"""fe2d - minimal plane-stress FE on a raster of a REAL section of an STL part (pv_lib.section).
Square Q4 elements of side h, thickness t, isotropic E, nu.  Used for the small printed parts where a beam formula is
too crude (ear plate, crank arm, gear tooth).  Own code; checked on a cantilever against beam theory (selftest)."""
import numpy as np, math
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import pv_lib as L


def raster(seg, u0, u1, w0, w1, h):
    """mask[j, i] of cells (centre u0+(i+.5)h, w0+(j+.5)h) inside the even-odd region of the 2-D segments"""
    nu_, nw = int(round((u1 - u0) / h)), int(round((w1 - w0) / h))
    M = np.zeros((nw, nu_), bool)
    a, b = seg[:, 0], seg[:, 1]
    for j in range(nw):
        w = w0 + (j + 0.5) * h + 1.3e-7
        c = (a[:, 1] > w) != (b[:, 1] > w)
        x = np.sort(a[c, 0] + (w - a[c, 1]) * (b[c, 0] - a[c, 0]) / (b[c, 1] - a[c, 1]))
        uc = u0 + (np.arange(nu_) + 0.5) * h
        cnt = np.searchsorted(x, uc)          # number of crossings left of the centre
        M[j] = (cnt % 2) == 1
    return M


def ke_q4(h, t, E, nu):
    D = E / (1 - nu * nu) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])
    K = np.zeros((8, 8))
    g = 1 / math.sqrt(3)
    xi_n = np.array([-1, 1, 1, -1]); et_n = np.array([-1, -1, 1, 1])
    for xi in (-g, g):
        for et in (-g, g):
            dN_dxi = xi_n * (1 + et * et_n) / 4; dN_det = et_n * (1 + xi * xi_n) / 4
            dN_dx = dN_dxi * 2 / h; dN_dy = dN_det * 2 / h
            B = np.zeros((3, 8))
            B[0, 0::2] = dN_dx; B[1, 1::2] = dN_dy; B[2, 0::2] = dN_dy; B[2, 1::2] = dN_dx
            K += B.T @ D @ B * (h / 2) ** 2 * t
    # centre B for stresses
    dN_dx = xi_n / 4 * 2 / h; dN_dy = et_n / 4 * 2 / h
    Bc = np.zeros((3, 8)); Bc[0, 0::2] = dN_dx; Bc[1, 1::2] = dN_dy; Bc[2, 0::2] = dN_dy; Bc[2, 1::2] = dN_dx
    return K, D, Bc


class Model:
    def __init__(self, mask, u0, w0, h, t, E=L.E_MOD, nu=0.38):
        self.M, self.u0, self.w0, self.h, self.t = mask, u0, w0, h, t
        nw, nu_ = mask.shape
        self.nn_u = nu_ + 1
        J, I = np.nonzero(mask)
        n0 = J * self.nn_u + I
        self.conn = np.stack([n0, n0 + 1, n0 + 1 + self.nn_u, n0 + self.nn_u], 1)      # ccw: (i,j) (i+1,j) (i+1,j+1) (i,j+1)
        used = np.unique(self.conn)
        self.map = -np.ones((nw + 1) * self.nn_u, int); self.map[used] = np.arange(len(used))
        self.nodes = used
        self.K, self.D, self.Bc = ke_q4(h, t, E, nu)
        self.ndof = 2 * len(used)
        self.F = np.zeros(self.ndof); self.fixed = np.zeros(self.ndof, bool)
        self.cent = np.c_[u0 + (I + 0.5) * h, w0 + (J + 0.5) * h]

    def xy(self, nodes=None):
        n = self.nodes if nodes is None else nodes
        return np.c_[self.u0 + (n % self.nn_u) * self.h, self.w0 + (n // self.nn_u) * self.h]

    def fix_where(self, fn, dofs=(0, 1)):
        p = self.xy(); sel = fn(p[:, 0], p[:, 1])
        for d in dofs:
            self.fixed[2 * np.nonzero(sel)[0] + d] = True
        return int(sel.sum())

    def boundary_nodes(self):
        """nodes on the free boundary (belonging to fewer than 4 active elements)"""
        cnt = np.bincount(self.map[self.conn].ravel(), minlength=len(self.nodes))
        return np.nonzero(cnt < 4)[0]

    def load_on(self, idx, f):
        """distribute force vector f (N) equally on local node indices idx"""
        idx = np.asarray(idx)
        if len(idx) == 0:
            raise ValueError("no nodes for the load")
        self.F[2 * idx] += f[0] / len(idx); self.F[2 * idx + 1] += f[1] / len(idx)

    def solve(self):
        dof = np.stack([2 * self.map[self.conn], 2 * self.map[self.conn] + 1], 2).reshape(-1, 8)
        r = np.repeat(dof, 8, 1).ravel(); c = np.tile(dof, (1, 8)).ravel()
        v = np.tile(self.K.ravel(), len(dof))
        K = coo_matrix((v, (r, c)), shape=(self.ndof, self.ndof)).tocsr()
        free = ~self.fixed
        U = np.zeros(self.ndof)
        U[free] = spsolve(K[free][:, free], self.F[free])
        self.U = U
        ue = U[dof]
        S = (self.D @ self.Bc @ ue.T).T                    # sx, sy, txy at element centres
        sx, sy, txy = S[:, 0], S[:, 1], S[:, 2]
        c = (sx + sy) / 2; rr = np.sqrt(((sx - sy) / 2) ** 2 + txy ** 2)
        self.s1, self.s2 = c + rr, c - rr
        self.vm = np.sqrt(sx ** 2 - sx * sy + sy ** 2 + 3 * txy ** 2)
        return self

    def top(self, k=5, what="s1", skip_near=None):
        a = getattr(self, what)
        o = np.argsort(-np.abs(a) if what == "s2" else -a)
        out = []
        for i in o:
            if skip_near is not None and skip_near(*self.cent[i]):
                continue
            out.append((round(float(a[i]), 2), round(float(self.cent[i][0]), 2), round(float(self.cent[i][1]), 2)))
            if len(out) >= k:
                break
        return out

    def p99(self, what="s1", q=99.5, skip_near=None):
        a = getattr(self, what)
        if skip_near is not None:
            keep = np.array([not skip_near(*c) for c in self.cent]); a = a[keep]
        return float(np.percentile(a, q))

    def picture(self, path, what="s1", vmax=None, scale=20):
        from PIL import Image
        a = getattr(self, what)
        nw, nu_ = self.M.shape
        img = np.full((nw, nu_, 3), 255, np.uint8)
        vmax = vmax or max(1e-9, np.percentile(np.abs(a), 99.5))
        J, I = np.nonzero(self.M)
        x = np.clip(a / vmax, -1, 1)
        img[J, I, 0] = np.where(x > 0, 255, (255 * (1 + x)).astype(int))
        img[J, I, 1] = (255 * (1 - np.abs(x))).astype(int)
        img[J, I, 2] = np.where(x < 0, 255, (255 * (1 - x)).astype(int))
        im = Image.fromarray(img[::-1]).resize((nu_ * max(1, scale // 10), nw * max(1, scale // 10)), Image.NEAREST)
        im.save(path)


def selftest():
    """cantilever 20 x 2 x t 1, tip load 10 N: beam sigma = 6 F L / (t h^2) = 300 MPa at the root"""
    h = 0.05
    M = np.ones((int(2 / h), int(20 / h)), bool)
    m = Model(M, 0.0, 0.0, h, 1.0)
    m.fix_where(lambda u, w: u < 1e-6)
    p = m.xy(); tip = np.nonzero(p[:, 0] > 20 - 1e-6)[0]
    m.load_on(tip, (0.0, -10.0)); m.solve()
    # stress at x = 1 mm from the root (beam: 6*10*19/(1*4) = 285)
    sel = np.abs(m.cent[:, 0] - 1.0) < h
    tipd = m.U[2 * tip + 1].mean()
    beam_d = 10 * 20 ** 3 / (3 * L.E_MOD * (1 * 2 ** 3 / 12))
    return float(m.s1[sel].max()), 285.0, float(tipd), -beam_d


if __name__ == "__main__":
    print("selftest: FE sigma1 at x=1 %.1f (beam %.1f);  tip deflection %.3f (beam %.3f)" % selftest())

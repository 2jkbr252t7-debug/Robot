"""Own 3-D voxel finite elements: 8-node hexahedra with Wilson incompatible modes (bending-exact on a regular grid),
partial-volume voxels (E scaled by the solid fraction, stresses reported with the full E), several bodies on one lattice
(each body has its own nodes; nodes of different bodies are merged only where a tie is declared), penalty springs for
supports / contact (active-set iteration for compression-only springs), smoothed-aggregation AMG (pyamg) + CG.
Units: mm, N, MPa."""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
import sys, time, math, numpy as np
import scipy.sparse as sp
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pylib"))
import pyamg

# local node order (i, j, k) offsets
LOC = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]])
XI = 2 * LOC - 1
G = 1 / math.sqrt(3)
GP = XI * G                     # gauss points in the same sign order as the nodes


def Dmat(E, nu):
    lam = E * nu / ((1 + nu) * (1 - 2 * nu)); mu = E / (2 * (1 + nu))
    D = np.zeros((6, 6)); D[:3, :3] = lam; D[np.arange(3), np.arange(3)] += 2 * mu; D[3:, 3:] = np.eye(3) * mu
    return D


def _BG(xi, h):
    """B (6x24) and incompatible G (6x9) at natural point xi for a cube of side h (strain order xx yy zz xy yz zx)"""
    dN = np.zeros((8, 3))
    for a in range(8):
        s = XI[a]
        f = [(1 + s[0] * xi[0]), (1 + s[1] * xi[1]), (1 + s[2] * xi[2])]
        dN[a, 0] = s[0] * f[1] * f[2] / 8; dN[a, 1] = f[0] * s[1] * f[2] / 8; dN[a, 2] = f[0] * f[1] * s[2] / 8
    dN *= 2.0 / h
    B = np.zeros((6, 24))
    for a in range(8):
        dx, dy, dz = dN[a]
        B[0, 3 * a] = dx; B[1, 3 * a + 1] = dy; B[2, 3 * a + 2] = dz
        B[3, 3 * a] = dy; B[3, 3 * a + 1] = dx
        B[4, 3 * a + 1] = dz; B[4, 3 * a + 2] = dy
        B[5, 3 * a] = dz; B[5, 3 * a + 2] = dx
    dP = np.diag([-2 * xi[0], -2 * xi[1], -2 * xi[2]]) * 2.0 / h      # dP_m / dx_n (P1 = 1 - xi^2 ...)
    Gm = np.zeros((6, 9))
    for m in range(3):
        dx, dy, dz = dP[m]
        Gm[0, 3 * m] = dx; Gm[1, 3 * m + 1] = dy; Gm[2, 3 * m + 2] = dz
        Gm[3, 3 * m] = dy; Gm[3, 3 * m + 1] = dx
        Gm[4, 3 * m + 1] = dz; Gm[4, 3 * m + 2] = dy
        Gm[5, 3 * m] = dz; Gm[5, 3 * m + 2] = dx
    return B, Gm


def element(h, nu):
    """condensed 24x24 stiffness for E = 1, and the stress recovery operator S (8 nodes x 6 comps x 24 dofs) for E = 1
    (gauss-point stresses extrapolated to the nodes)"""
    D = Dmat(1.0, nu); w = (h / 2) ** 3
    Kuu = np.zeros((24, 24)); Kua = np.zeros((24, 9)); Kaa = np.zeros((9, 9)); BGs = []
    for g in GP:
        B, Gm = _BG(g, h); BGs.append((B, Gm))
        Kuu += B.T @ D @ B * w; Kua += B.T @ D @ Gm * w; Kaa += Gm.T @ D @ Gm * w
    Kaa_i = np.linalg.inv(Kaa)
    K = Kuu - Kua @ Kaa_i @ Kua.T
    A = -Kaa_i @ Kua.T                               # alpha = A u
    Sg = np.array([D @ (B + Gm @ A) for B, Gm in BGs])  # (8 gauss, 6, 24)
    # extrapolation gauss -> node: node n at natural XI[n] = gauss coords sqrt(3) * XI[n]
    Ex = np.zeros((8, 8))
    for n in range(8):
        p = XI[n] * math.sqrt(3)
        for gi in range(8):
            s = XI[gi]
            Ex[n, gi] = (1 + s[0] * p[0]) * (1 + s[1] * p[1]) * (1 + s[2] * p[2]) / 8
    Sn = np.einsum("ng,gcd->ncd", Ex, Sg)            # (8 nodes, 6, 24)
    return K, Sn, Sg


class Model:
    """bodies on one lattice: origin o, spacing h, shape (nx, ny, nz) of cells"""
    def __init__(self, origin, h, shape, nu_default=0.38):
        self.o = np.asarray(origin, float); self.h = h; self.shape = shape
        self.bodies = []          # dict(name, cells (n,3) int, frac (n,), E, nu)
        self.nu = nu_default

    def add_body(self, name, frac, E, nu, fmin=0.3):
        idx = np.argwhere(frac >= fmin)
        f = frac[frac >= fmin]
        self.bodies.append(dict(name=name, cells=idx.astype(np.int32), frac=f.astype(np.float64), E=E, nu=nu))

    def build_nodes(self, merges=()):
        """node numbering: per body, the corner lattice points of its cells.  merges: list of (bodyA, bodyB, mask_fn) where
        mask_fn(points (n,3) mm) -> bool: lattice points shared by A and B (corners of both) inside the mask are merged
        into A's node."""
        nx, ny, nz = self.shape
        NX, NY, NZ = nx + 1, ny + 1, nz + 1
        self.lat_key = lambda ijk: (ijk[..., 0].astype(np.int64) * NY + ijk[..., 1]) * NZ + ijk[..., 2]
        self.node_ijk = []; self.node_body = []; offs = 0
        self.body_nodemap = []
        for bi, b in enumerate(self.bodies):
            corners = (b["cells"][:, None, :] + LOC[None]).reshape(-1, 3)
            keys = self.lat_key(corners)
            uk, inv = np.unique(keys, return_inverse=True)
            b["enodes"] = (inv.reshape(-1, 8) + offs).astype(np.int64)
            ijk = np.stack([uk // (NY * NZ), (uk // NZ) % NY, uk % NZ], 1)
            self.node_ijk.append(ijk); self.node_body.append(np.full(len(uk), bi))
            self.body_nodemap.append((uk, offs))
            offs += len(uk)
        self.node_ijk = np.concatenate(self.node_ijk); self.node_body = np.concatenate(self.node_body)
        self.X = self.o + self.node_ijk * self.h
        n = offs
        remap = np.arange(n)
        names = [b["name"] for b in self.bodies]
        self.merged = {}
        for A, B, fn in merges:
            ia, ib = names.index(A), names.index(B)
            ka, oa = self.body_nodemap[ia]; kb, ob = self.body_nodemap[ib]
            common, pa, pb = np.intersect1d(ka, kb, return_indices=True)
            pts = self.o + np.stack([common // ((self.shape[1] + 1) * (self.shape[2] + 1)), (common // (self.shape[2] + 1)) % (self.shape[1] + 1), common % (self.shape[2] + 1)], 1) * self.h
            m = fn(pts)
            remap[pb[m] + ob] = pa[m] + oa
            self.merged[(A, B)] = int(m.sum())
        # compact numbering
        keep = remap == np.arange(n)
        newid = np.cumsum(keep) - 1
        final = newid[remap]
        for b in self.bodies:
            b["enodes"] = final[b["enodes"]]
        self.X = self.X[keep]; self.node_body = self.node_body[keep]; self.node_ijk = self.node_ijk[keep]
        self.nn = int(keep.sum())
        self.final_of_old = final
        return self.nn

    def assemble(self):
        """BSR (3x3 blocks) stiffness; element contributions summed with sparse COO in chunks"""
        t0 = time.time(); h = self.h
        rows_all, cols_all, vals_all = [], [], []
        mats = []
        for b in self.bodies:
            Ke, Sn, Sg = element(h, b["nu"]); b["Sn"] = Sn
            Eel = b["E"] * b["frac"]
            en = b["enodes"]
            # block form: for local pair (a, c): block Ke[3a:3a+3, 3c:3c+3]
            for a in range(8):
                ra = en[:, a]
                for c in range(8):
                    rc = en[:, c]
                    blk = Ke[3 * a:3 * a + 3, 3 * c:3 * c + 3]
                    for p in range(3):
                        for q in range(3):
                            if blk[p, q] == 0.0:
                                continue
                            rows_all.append((3 * ra + p).astype(np.int64)); cols_all.append((3 * rc + q).astype(np.int64)); vals_all.append(Eel * blk[p, q])
                if sum(len(r) for r in rows_all) > 4e7:
                    mats.append(sp.csr_matrix((np.concatenate(vals_all), (np.concatenate(rows_all), np.concatenate(cols_all))), shape=(3 * self.nn, 3 * self.nn)))
                    rows_all, cols_all, vals_all = [], [], []
        if rows_all:
            mats.append(sp.csr_matrix((np.concatenate(vals_all), (np.concatenate(rows_all), np.concatenate(cols_all))), shape=(3 * self.nn, 3 * self.nn)))
        K = mats[0]
        for m in mats[1:]:
            K = K + m
        self.K = K.tocsr(); self.K.sum_duplicates()
        print(f"assembled: nodes {self.nn}, dofs {3 * self.nn}, nnz {self.K.nnz}, {time.time() - t0:.1f} s", flush=True)

    def spring_matrix(self, springs):
        """springs: list of (nodes (n,), dirs (n,3) unit, k (n,) or scalar) -> sparse 3n x 3n matrix sum k d d^T"""
        r, c, v = [], [], []
        for nodes, dirs, k in springs:
            k = np.broadcast_to(np.asarray(k, float), (len(nodes),))
            for p in range(3):
                for q in range(3):
                    r.append(3 * nodes + p); c.append(3 * nodes + q); v.append(k * dirs[:, p] * dirs[:, q])
        if not r:
            return sp.csr_matrix((3 * self.nn, 3 * self.nn))
        return sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(c))), shape=(3 * self.nn, 3 * self.nn))

    def solve(self, F, springs, fixed=None, tol=1e-8, maxiter=600, x0=None, verbose=True):
        t0 = time.time()
        A = (self.K + self.spring_matrix(springs)).tocsr()
        n = A.shape[0]
        free = np.ones(n, bool)
        if fixed is not None:
            free[fixed] = False
        Af = A if fixed is None else A[free][:, free].tocsr()
        # rigid body modes as near-nullspace (built on free dofs)
        Xc = self.X - self.X.mean(0)
        Bm = np.zeros((n, 6))
        Bm[0::3, 0] = 1; Bm[1::3, 1] = 1; Bm[2::3, 2] = 1
        Bm[0::3, 3] = -Xc[:, 1]; Bm[1::3, 3] = Xc[:, 0]
        Bm[1::3, 4] = -Xc[:, 2]; Bm[2::3, 4] = Xc[:, 1]
        Bm[2::3, 5] = -Xc[:, 0]; Bm[0::3, 5] = Xc[:, 2]
        Bm = Bm[free]
        ml = pyamg.smoothed_aggregation_solver(Af, B=Bm, max_coarse=500, keep=False)
        self.ml_info = str(ml)
        res = []
        u = ml.solve(F[free], x0=None if x0 is None else x0[free], tol=tol, accel="cg", maxiter=maxiter, residuals=res)
        U = np.zeros(n); U[free] = u
        if verbose:
            print(f"  solve: {len(res)} its, rel res {res[-1] / res[0]:.2e}, {time.time() - t0:.1f} s", flush=True)
        self.last_res = res
        return U

    def stresses(self, U, body):
        """nodal-averaged stress (6 comps, full E, not scaled by the fraction) for the nodes of one body
        -> (node ids, sig (n,6)), plus per-element nodal values"""
        b = self.bodies[[q["name"] for q in self.bodies].index(body)]
        en = b["enodes"]
        ue = np.stack([U[3 * en], U[3 * en + 1], U[3 * en + 2]], 2).reshape(len(en), 24)
        sn = np.einsum("ncd,ed->enc", b["Sn"], ue) * b["E"]        # (el, 8, 6)
        acc = np.zeros((self.nn, 6)); cnt = np.zeros(self.nn)
        w = b["frac"][:, None]                                     # weight by fraction (partial voxels count less)
        for a in range(8):
            np.add.at(acc, en[:, a], sn[:, a] * w); np.add.at(cnt, en[:, a], w[:, 0])
        ids = np.unique(en)
        sig = acc[ids] / cnt[ids][:, None]
        return ids, sig, sn


def principal(sig):
    """sig (n, 6) xx yy zz xy yz zx -> (s1, s2, s3), von Mises"""
    n = len(sig)
    T = np.zeros((n, 3, 3))
    T[:, 0, 0] = sig[:, 0]; T[:, 1, 1] = sig[:, 1]; T[:, 2, 2] = sig[:, 2]
    T[:, 0, 1] = T[:, 1, 0] = sig[:, 3]; T[:, 1, 2] = T[:, 2, 1] = sig[:, 4]; T[:, 0, 2] = T[:, 2, 0] = sig[:, 5]
    ev = np.linalg.eigvalsh(T)
    vm = np.sqrt(0.5 * ((sig[:, 0] - sig[:, 1]) ** 2 + (sig[:, 1] - sig[:, 2]) ** 2 + (sig[:, 2] - sig[:, 0]) ** 2) + 3 * (sig[:, 3] ** 2 + sig[:, 4] ** 2 + sig[:, 5] ** 2))
    return ev[:, 2], ev[:, 1], ev[:, 0], vm


def _BG_vec(xi, h):
    """vectorised B (n,6,24), G (n,6,9) at natural points xi (n,3)"""
    n = len(xi)
    f = 1 + XI[None, :, :] * xi[:, None, :]                   # (n, 8, 3)
    dN = np.empty((n, 8, 3))
    dN[:, :, 0] = XI[None, :, 0] * f[:, :, 1] * f[:, :, 2] / 8
    dN[:, :, 1] = f[:, :, 0] * XI[None, :, 1] * f[:, :, 2] / 8
    dN[:, :, 2] = f[:, :, 0] * f[:, :, 1] * XI[None, :, 2] / 8
    dN *= 2.0 / h
    B = np.zeros((n, 6, 24))
    a = np.arange(8)
    B[:, 0, 3 * a] = dN[:, :, 0]; B[:, 1, 3 * a + 1] = dN[:, :, 1]; B[:, 2, 3 * a + 2] = dN[:, :, 2]
    B[:, 3, 3 * a] = dN[:, :, 1]; B[:, 3, 3 * a + 1] = dN[:, :, 0]
    B[:, 4, 3 * a + 1] = dN[:, :, 2]; B[:, 4, 3 * a + 2] = dN[:, :, 1]
    B[:, 5, 3 * a] = dN[:, :, 2]; B[:, 5, 3 * a + 2] = dN[:, :, 0]
    Gm = np.zeros((n, 6, 9))
    dP = -2 * xi * 2.0 / h                                     # dP_m/dx_m
    m = np.arange(3)
    Gm[:, 0, 0] = dP[:, 0]; Gm[:, 1, 4] = dP[:, 1]; Gm[:, 2, 8] = dP[:, 2]   # P_m multiplies dof (m, comp): index 3m+comp
    Gm[:, 3, 1] = dP[:, 0]; Gm[:, 3, 3] = dP[:, 1]           # gamma_xy: d(v-part of mode0)/dx + d(u-part of mode1)/dy
    Gm[:, 4, 5] = dP[:, 1]; Gm[:, 4, 7] = dP[:, 2]           # gamma_yz
    Gm[:, 5, 2] = dP[:, 0]; Gm[:, 5, 6] = dP[:, 2]           # gamma_zx
    return B, Gm


def point_stress(model, U, body, pts, normals=None, max_nudge=3):
    """stress (n,6) at arbitrary points inside the elements of `body` (true-surface sampling).  Points whose cell is not an
    element are nudged inward along -normal in steps of 0.25 h (up to max_nudge h).  Returns sig, ok mask."""
    b = model.bodies[[q["name"] for q in model.bodies].index(body)]
    h = model.h; o = model.o; nx, ny, nz = model.shape
    if "cellmap" not in b:
        key = (b["cells"][:, 0].astype(np.int64) * ny + b["cells"][:, 1]) * nz + b["cells"][:, 2]
        order = np.argsort(key); b["cellmap"] = (key[order], order)
        D = Dmat(1.0, b["nu"]); w = (h / 2) ** 3
        Kua = np.zeros((24, 9)); Kaa = np.zeros((9, 9))
        for g in GP:
            B1, G1 = _BG(g, h); Kua += B1.T @ D @ G1 * w; Kaa += G1.T @ D @ G1 * w
        b["Aalpha"] = -np.linalg.inv(Kaa) @ Kua.T; b["D"] = D
    keys, order = b["cellmap"]
    n = len(pts); el = np.full(n, -1); P = pts.copy()
    for step in range(int(max_nudge * 4) + 1):
        todo = el < 0
        if not todo.any():
            break
        q = pts[todo] - (0 if normals is None or step == 0 else normals[todo] * step * 0.25 * h)
        ijk = np.floor((q - o) / h).astype(np.int64)
        okb = (ijk >= 0).all(1) & (ijk[:, 0] < nx) & (ijk[:, 1] < ny) & (ijk[:, 2] < nz)
        k = (ijk[:, 0] * ny + ijk[:, 1]) * nz + ijk[:, 2]
        pos = np.clip(np.searchsorted(keys, k), 0, len(keys) - 1)
        hit = okb & (keys[pos] == k)
        idx = np.flatnonzero(todo)
        el[idx[hit]] = order[pos[hit]]; P[idx[hit]] = q[hit]
        if normals is None:
            break
    ok = el >= 0
    sig = np.full((n, 6), np.nan)
    if ok.any():
        e = el[ok]; c = b["cells"][e]
        xi = 2 * ((P[ok] - o) / h - c) - 1
        Bv, Gv = _BG_vec(xi, h)
        en = b["enodes"][e]
        ue = np.stack([U[3 * en], U[3 * en + 1], U[3 * en + 2]], 2).reshape(len(e), 24)
        eps = np.einsum("nij,nj->ni", Bv, ue) + np.einsum("nij,jk,nk->ni", Gv, b["Aalpha"], ue)
        sig[ok] = (eps @ b["D"].T) * b["E"]
    return sig, ok


# ---------------------------------------------------------------------------------------------------------------------
# finite-cell (sub-cell integrated) partial elements
# ---------------------------------------------------------------------------------------------------------------------
NS = 4                                                       # sub-points per cell edge


def subcell_ops(h, nu):
    """per sub-point (64) element matrices for E = 1: Muu (64,24,24), Mua (64,24,9), Maa (64,9,9)"""
    D = Dmat(1.0, nu)
    s = (np.arange(NS) + 0.5) / NS * 2 - 1
    pts = np.array([[a, b, c] for a in s for b in s for c in s])        # order: x-major, then y, then z
    w = (h / NS) ** 3
    Bv, Gv = _BG_vec(pts, h)
    Muu = np.einsum("nki,kl,nlj->nij", Bv, D, Bv) * w
    Mua = np.einsum("nki,kl,nlj->nij", Bv, D, Gv) * w
    Maa = np.einsum("nki,kl,nlj->nij", Gv, D, Gv) * w
    return Muu, Mua, Maa, pts


def occupancy(T, origin, h, shape, ns=NS):
    """sub-cell occupancy (nx, ny, nz, ns^3) bool, sub-point order x-major / y / z within each cell"""
    import sa_lib as L
    nx, ny, nz = shape
    xs = origin[0] + (np.arange(nx * ns) + 0.5) * h / ns; ys = origin[1] + (np.arange(ny * ns) + 0.5) * h / ns
    zs = origin[2] + (np.arange(nz * ns) + 0.5) * h / ns
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    i0 = max(0, int((lo[0] - origin[0]) / (h / ns)) - 1); i1 = min(nx * ns, int((hi[0] - origin[0]) / (h / ns)) + 2)
    j0 = max(0, int((lo[1] - origin[1]) / (h / ns)) - 1); j1 = min(ny * ns, int((hi[1] - origin[1]) / (h / ns)) + 2)
    cr = L.column_crossings(T, xs[i0:i1], ys[j0:j1])
    occ = np.zeros((nx * ns, ny * ns, nz * ns), bool)
    for (i, j), w in cr.items():
        for a, b in L.intervals(w):
            k0 = int(np.ceil((a - origin[2]) / (h / ns) - 0.5)); k1 = int(np.floor((b - origin[2]) / (h / ns) - 0.5))
            k0 = max(k0, 0); k1 = min(k1, nz * ns - 1)
            if k1 >= k0:
                occ[i + i0, j + j0, k0:k1 + 1] = True
    occ = occ.reshape(nx, ns, ny, ns, nz, ns).transpose(0, 2, 4, 1, 3, 5).reshape(nx, ny, nz, ns ** 3)
    return occ


def add_body_fc(model, name, occ, E, nu, nmin=3, eps=1e-3):
    """body from sub-cell occupancy: full cells use the shared condensed K0; partial cells (nmin..63 sub-points) get their
    own sub-cell integrated, condensed matrices (+ eps x full cell for stability)"""
    cnt = occ.sum(-1)
    sel = cnt >= nmin
    cells = np.argwhere(sel).astype(np.int32)
    occs = occ[sel]
    frac = cnt[sel] / occ.shape[-1]
    b = dict(name=name, cells=cells, frac=frac.astype(float), E=E, nu=nu)
    part = np.flatnonzero(frac < 1.0)
    Muu, Mua, Maa, _ = subcell_ops(model.h, nu)
    o = occs[part].astype(float) + eps                       # (np, 64)
    Kuu = (o @ Muu.reshape(64, -1)).reshape(-1, 24, 24)
    Kua = (o @ Mua.reshape(64, -1)).reshape(-1, 24, 9)
    Kaa = (o @ Maa.reshape(64, -1)).reshape(-1, 9, 9)
    Kaa_i = np.linalg.inv(Kaa)
    Aal = -np.einsum("nij,nkj->nik", Kaa_i, Kua)             # (np, 9, 24)
    Kc = Kuu + np.einsum("nij,njk->nik", Kua, Aal)
    b["part"] = part; b["Kpart"] = Kc; b["Apart"] = Aal
    model.bodies.append(b)
    return b


def assemble_fc(model, chunk=3.0e7):
    """assembly for bodies created with add_body_fc (full cells: K0 * E; partial: own matrices * E)"""
    t0 = time.time(); n3 = 3 * model.nn
    mats = []; R, C, V = [], [], []; size = 0
    def flush():
        nonlocal R, C, V, size
        if R:
            mats.append(sp.csr_matrix((np.concatenate(V), (np.concatenate(R), np.concatenate(C))), shape=(n3, n3)))
        R, C, V, size = [], [], [], 0
    for b in model.bodies:
        K0, Sn, Sg = element(model.h, b["nu"]); b["Sn"] = Sn
        en = b["enodes"]; full = np.ones(len(en), bool)
        if "part" in b:
            full[b["part"]] = False
        idxs = [(np.flatnonzero(full), None)]
        if "part" in b:
            idxs.append((b["part"], b["Kpart"]))
        for ids, Kp in idxs:
            if len(ids) == 0:
                continue
            ee = en[ids]
            for a in range(8):
                for c in range(8):
                    for p in range(3):
                        for q in range(3):
                            ia, ic = 3 * a + p, 3 * c + q
                            if Kp is None:
                                if K0[ia, ic] == 0.0:
                                    continue
                                v = np.full(len(ids), K0[ia, ic] * b["E"])
                            else:
                                v = Kp[:, ia, ic] * b["E"]
                            R.append((3 * ee[:, a] + p).astype(np.int32)); C.append((3 * ee[:, c] + q).astype(np.int32)); V.append(v)
                            size += len(ids)
                    if size > chunk:
                        flush()
        flush()
    K = mats[0]
    for m in mats[1:]:
        K = K + m
    model.K = K.tocsr(); model.K.sum_duplicates()
    print(f"assembled (FC): nodes {model.nn}, dofs {n3}, nnz {model.K.nnz}, {time.time() - t0:.1f} s", flush=True)


def point_stress_fc(model, U, body, pts, normals=None, max_nudge=3):
    """as point_stress, using the per-element alpha operator of partial cells"""
    b = model.bodies[[q["name"] for q in model.bodies].index(body)]
    h = model.h; o = model.o; nx, ny, nz = model.shape
    if "cellmap" not in b:
        key = (b["cells"][:, 0].astype(np.int64) * ny + b["cells"][:, 1]) * nz + b["cells"][:, 2]
        order = np.argsort(key); b["cellmap"] = (key[order], order)
        D = Dmat(1.0, b["nu"]); w = (h / 2) ** 3
        Kua = np.zeros((24, 9)); Kaa = np.zeros((9, 9))
        for g in GP:
            B1, G1 = _BG(g, h); Kua += B1.T @ D @ G1 * w; Kaa += G1.T @ D @ G1 * w
        b["Aalpha"] = -np.linalg.inv(Kaa) @ Kua.T; b["D"] = D
        b["partpos"] = np.full(len(b["cells"]), -1)
        if "part" in b:
            b["partpos"][b["part"]] = np.arange(len(b["part"]))
    keys, order = b["cellmap"]
    n = len(pts); el = np.full(n, -1); P = pts.copy()
    for step in range(int(max_nudge * 4) + 1):
        todo = el < 0
        if not todo.any():
            break
        q = pts[todo] - (0 if normals is None or step == 0 else normals[todo] * step * 0.25 * h)
        ijk = np.floor((q - o) / h).astype(np.int64)
        okb = (ijk >= 0).all(1) & (ijk[:, 0] < nx) & (ijk[:, 1] < ny) & (ijk[:, 2] < nz)
        k = (ijk[:, 0] * ny + ijk[:, 1]) * nz + ijk[:, 2]
        pos = np.clip(np.searchsorted(keys, k), 0, len(keys) - 1)
        hit = okb & (keys[pos] == k)
        idx = np.flatnonzero(todo)
        el[idx[hit]] = order[pos[hit]]; P[idx[hit]] = q[hit]
        if normals is None:
            break
    ok = el >= 0
    sig = np.full((n, 6), np.nan)
    if ok.any():
        e = el[ok]; c = b["cells"][e]
        xi = np.clip(2 * ((P[ok] - o) / h - c) - 1, -1, 1)
        Bv, Gv = _BG_vec(xi, h)
        en = b["enodes"][e]
        ue = np.stack([U[3 * en], U[3 * en + 1], U[3 * en + 2]], 2).reshape(len(e), 24)
        pp = b["partpos"][e]
        A = np.broadcast_to(b["Aalpha"], (len(e), 9, 24)).copy()
        if (pp >= 0).any():
            A[pp >= 0] = b["Apart"][pp[pp >= 0]]
        alpha = np.einsum("nij,nj->ni", A, ue)
        eps = np.einsum("nij,nj->ni", Bv, ue) + np.einsum("nij,nj->ni", Gv, alpha)
        sig[ok] = (eps @ b["D"].T) * b["E"]
    return sig, ok, el


def occupancy_w(T, origin, h, shape, ns=NS):
    """weighted sub-cell occupancy (nx, ny, nz, ns^3) as uint8 (255 = full): xy sampled at the sub-column centres, z exact
    (overlap of the column's solid intervals with each sub-layer)"""
    import sa_lib as L
    nx, ny, nz = shape
    hs = h / ns
    xs = origin[0] + (np.arange(nx * ns) + 0.5) * hs; ys = origin[1] + (np.arange(ny * ns) + 0.5) * hs
    lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
    i0 = max(0, int((lo[0] - origin[0]) / hs) - 1); i1 = min(nx * ns, int((hi[0] - origin[0]) / hs) + 2)
    j0 = max(0, int((lo[1] - origin[1]) / hs) - 1); j1 = min(ny * ns, int((hi[1] - origin[1]) / hs) + 2)
    cr = L.column_crossings(T, xs[i0:i1], ys[j0:j1])
    occ = np.zeros((nx * ns, ny * ns, nz * ns), np.uint8)
    zb = origin[2] + np.arange(nz * ns + 1) * hs
    for (i, j), w in cr.items():
        acc = np.zeros(nz * ns)
        for a, b in L.intervals(w):
            k0 = max(int(np.floor((a - origin[2]) / hs)), 0); k1 = min(int(np.floor((b - origin[2]) / hs)), nz * ns - 1)
            if k1 < k0:
                continue
            ks = np.arange(k0, k1 + 1)
            acc[ks] += np.clip(np.minimum(b, zb[ks + 1]) - np.maximum(a, zb[ks]), 0, hs) / hs
        occ[i + i0, j + j0] = np.round(np.clip(acc, 0, 1) * 255).astype(np.uint8)
    occ = occ.reshape(nx, ns, ny, ns, nz, ns).transpose(0, 2, 4, 1, 3, 5).reshape(nx, ny, nz, ns ** 3)
    return occ


def add_body_fcw(model, name, occw, E, nu, wmin=3.0, eps=1e-3):
    """as add_body_fc with weighted occupancy (uint8, 255 = full sub-cell)"""
    cnt = occw.sum(-1, dtype=np.float64) / 255.0
    sel = cnt >= wmin
    cells = np.argwhere(sel).astype(np.int32)
    o_all = occw[sel]
    frac = cnt[sel] / occw.shape[-1]
    b = dict(name=name, cells=cells, frac=frac.astype(float), E=E, nu=nu)
    part = np.flatnonzero(frac < 1.0 - 1e-9)
    Muu, Mua, Maa, _ = subcell_ops(model.h, nu)
    Kc = np.empty((len(part), 24, 24)); Aal = np.empty((len(part), 9, 24))
    for s in range(0, len(part), 20000):
        pp = part[s:s + 20000]
        o = o_all[pp].astype(float) / 255.0 + eps
        Kuu = (o @ Muu.reshape(64, -1)).reshape(-1, 24, 24)
        Kua = (o @ Mua.reshape(64, -1)).reshape(-1, 24, 9)
        Kaa = (o @ Maa.reshape(64, -1)).reshape(-1, 9, 9)
        A = -np.einsum("nij,nkj->nik", np.linalg.inv(Kaa), Kua)
        Aal[s:s + 20000] = A; Kc[s:s + 20000] = Kuu + np.einsum("nij,njk->nik", Kua, A)
    b["part"] = part; b["Kpart"] = Kc; b["Apart"] = Aal
    model.bodies.append(b)
    return b


def build_precond(model, springs):
    """AMG hierarchy on K + springs (springs: list of (nodes, dirs, k)), reused as a preconditioner for nearby systems"""
    t0 = time.time()
    A = (model.K + model.spring_matrix(springs)).tocsr()
    X = model.X; n = A.shape[0]
    Xc = X - X.mean(0)
    Bm = np.zeros((n, 6))
    Bm[0::3, 0] = 1; Bm[1::3, 1] = 1; Bm[2::3, 2] = 1
    Bm[0::3, 3] = -Xc[:, 1]; Bm[1::3, 3] = Xc[:, 0]
    Bm[1::3, 4] = -Xc[:, 2]; Bm[2::3, 4] = Xc[:, 1]
    Bm[2::3, 5] = -Xc[:, 0]; Bm[0::3, 5] = Xc[:, 2]
    ml = pyamg.smoothed_aggregation_solver(A, B=Bm, max_coarse=500, keep=False)
    print(f"AMG setup {time.time() - t0:.0f} s", flush=True)
    print(ml, flush=True)
    model.ml = ml
    return ml


def solve_pcg(model, F, springs, x0=None, tol=1e-8, maxiter=600):
    """CG on K + springs preconditioned with the stored AMG (one V-cycle)"""
    import scipy.sparse.linalg as spl
    t0 = time.time()
    A = (model.K + model.spring_matrix(springs)).tocsr()
    M = model.ml.aspreconditioner(cycle="V")
    res = []
    bn = np.linalg.norm(F)
    def cb(xk):
        pass
    it = [0]
    def cb2(xk):
        it[0] += 1
    u, info = spl.cg(A, F, x0=x0, rtol=tol, maxiter=maxiter, M=M, callback=cb2)
    r = np.linalg.norm(F - A @ u) / bn
    print(f"  pcg: {it[0]} its, rel res {r:.1e}, info {info}, {time.time() - t0:.0f} s", flush=True)
    model.last_res = [1.0, r]
    return u

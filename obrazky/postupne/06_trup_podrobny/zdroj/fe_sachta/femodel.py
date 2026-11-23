"""fe_sachta - reproducible FE model of the NOVA pan stage (P_sachta + koleso_pan + P_drziak_serva) built from the CURRENT
STL files.  Derived from the review harness sachta_a (fe3d.py = own voxel / finite-cell hexahedra with incompatible modes;
fe_build.py / fe_cases_v4.py = positive-location module joint, compression-only contacts, gap journal 0.145, collar-disc
upper guide).  Differences to sachta_a (all stated in results.json["method"]):
  * the lattice origin is derived from the spacing h so that the bond plane z -41.9 and the pad plane y 15.1 are lattice planes;
  * the bond map (well bottom face on the gear top face) is ray-cast from the two STLs (no cached map);
  * the module joint is described by a DESIGN dict (fe_design.py): face / tongue / dowel selectors, direction, kind;
  * the stop pin acts on the lug as a compression-only LINE contact at r 30 (sachta_a: bilateral springs over the whole face =
    the lug face was clamped against rotation, 27 N of non-physical tension);
  * contact iteration = inexact Newton: short PCG sweeps with an active-set update in between (matrix-free spring terms on a
    BSR stiffness matrix), softer contact penalty (2 E h per node pair) -> every case converges incl. L8.
Units mm, N, MPa."""
import os, sys, time, json, hashlib, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "pylib"))
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
import pyamg
import fe3d, sa_lib as L

E_RESIN, NU_RESIN = 1600.0, 0.38           # T4_zivica Z2: E 1.5-1.8 GPa assumed -> 1.6
E_BRASS, NU_BRASS = 100000.0, 0.34
Z_BOND, Y_PAD = -41.9, 15.1
R_BOND = 13.35                             # bond only inside the gear root circle (tooth tops are not counted)
XLO, XHI, YLO, YHI, ZLO, ZHI = -26.8, 26.8, -26.9, 31.5, -47.5, 0.5
PARTS = ("P_sachta", "koleso_pan", "P_drziak_serva")
# the finished collar disc of variant B (read only): glued on the stage top (assembly T12), r 26.5, z -2 .. +4, neck opening 45.5 x 20.5.
# It is part of the stage structure: modelled up to z +0.5 (truncated = less stiff than the real 6 mm disc), tied to the well on the
# glue land r >= 24 (356.6 mm2, sachta_a g13).  sachta_a had only its guide forces (pattern on the land), not its stiffness.
COLLAR_STL = "/tmp/claude-0/gapwf/fin/B/stl/golier_kotuc.stl"
Z_TOP, R_LAND = -2.0, 24.0


def lattice(h):
    oz = Z_BOND - math.ceil((Z_BOND - ZLO) / h - 1e-9) * h
    oy = Y_PAD - math.ceil((Y_PAD - YLO) / h - 1e-9) * h
    ox = XLO
    shape = (int(math.ceil((XHI - ox) / h - 1e-9)), int(math.ceil((YHI - oy) / h - 1e-9)), int(math.ceil((ZHI - oz) / h - 1e-9)))
    return np.array([ox, oy, oz]), shape


def read_part(stl_dir, name):
    return L.read_stl(os.path.join(stl_dir, name + ".stl"))


def stl_stamp(stl_dir, names=PARTS):
    m = hashlib.md5()
    for n in names:
        m.update(open(os.path.join(stl_dir, n + ".stl"), "rb").read())
    return m.hexdigest()[:12]


def occupancies(stl_dir, h, cache_dir, log=print):
    O, shape = lattice(h)
    st = stl_stamp(stl_dir)
    f = os.path.join(cache_dir, f"occ3_{st}_h{h:.2f}.npz")
    if os.path.exists(f):
        d = np.load(f)
        return {k: d[k] for k in d.files}, st
    os.makedirs(cache_dir, exist_ok=True)
    t0 = time.time(); occ = {}
    for n in PARTS:
        occ[n] = fe3d.occupancy_w(read_part(stl_dir, n), O, h, shape)
        log(f"  occupancy {n}: {time.time() - t0:.0f} s")
    occ["golier_kotuc"] = fe3d.occupancy_w(L.read_stl(COLLAR_STL), O, h, shape)
    np.savez_compressed(f, **occ)
    return occ, st


def bond_mask(stl_dir, h, r_max=R_BOND):
    """fn(points) -> bool: lattice points on z -41.9 where the well's bottom face lies on the gear's top face (ray cast along z
    through both STLs at the lattice x, y) and r <= r_max"""
    O, shape = lattice(h)
    xs = O[0] + np.arange(shape[0] + 1) * h; ys = O[1] + np.arange(shape[1] + 1) * h
    Tw, Tg = read_part(stl_dir, "P_sachta"), read_part(stl_dir, "koleso_pan")
    cw = L.column_crossings(Tw, xs, ys); cg = L.column_crossings(Tg, xs, ys)
    M = np.zeros((len(xs), len(ys)), bool)
    for key, w in cw.items():
        g = cg.get(key)
        if g is None:
            continue
        wb = any(abs(a - Z_BOND) < 0.03 for a, b in L.intervals(w))           # a well interval starts on the plane
        gt = any(abs(b - Z_BOND) < 0.03 for a, b in L.intervals(g))           # a gear interval ends on the plane
        M[key] = wb and gt
    area = float(M.sum()) * h * h

    def fn(p):
        i = np.clip(np.round((p[:, 0] - xs[0]) / h).astype(int), 0, len(xs) - 1)
        j = np.clip(np.round((p[:, 1] - ys[0]) / h).astype(int), 0, len(ys) - 1)
        return (np.abs(p[:, 2] - Z_BOND) < 1e-6) & M[i, j] & (np.hypot(p[:, 0], p[:, 1]) <= r_max)
    fn.map = M; fn.xs = xs; fn.ys = ys; fn.area_all = area
    rr = np.hypot(xs[:, None], ys[None, :])
    fn.area = float((M & (rr <= r_max)).sum()) * h * h
    return fn


def build(stl_dir, h, cache_dir, bonded=True, with_gear=True, with_collar=True, log=print):
    O, shape = lattice(h)
    occ, st = occupancies(stl_dir, h, cache_dir, log)
    m = fe3d.Model(O, h, shape)
    fe3d.add_body_fcw(m, "well", occ["P_sachta"], E_RESIN, NU_RESIN)
    if with_gear:
        fe3d.add_body_fcw(m, "gear", occ["koleso_pan"], E_BRASS, NU_BRASS)
    fe3d.add_body_fcw(m, "pocket", occ["P_drziak_serva"], E_RESIN, NU_RESIN)
    if with_collar:
        fe3d.add_body_fcw(m, "collar", occ["golier_kotuc"], E_RESIN, NU_RESIN)
    del occ
    bm = bond_mask(stl_dir, h)
    merges = [("well", "gear", bm)] if (bonded and with_gear) else []
    if with_collar:                       # glue land: the nodes of the cell layer that contains the interface z -2.0, r >= 24
        merges.append(("well", "collar", lambda p: (np.abs(p[:, 2] - Z_TOP) <= 0.6 * h) & (np.hypot(p[:, 0], p[:, 1]) >= R_LAND)))
    m.build_nodes(merges=merges)
    m.names = [b["name"] for b in m.bodies]
    m.bond_area = bm.area; m.bond_fn = bm; m.stamp = st
    log(f"  model h {h}: nodes {m.nn}, merged {m.merged}, bond area (r <= {R_BOND}) {bm.area:.1f} mm2, cells " +
        ", ".join(f"{b['name']} {len(b['cells'])}" for b in m.bodies))
    fe3d.assemble_fc(m)
    return m


def coincident(m, a, b):
    """node ids (A in body a, B in body b) at the same lattice point"""
    X = m.X; nb = m.node_body; ia, ib = m.names.index(a), m.names.index(b)
    key = lambda P: np.round((P - m.o) / m.h).astype(np.int64) @ np.array([1 << 40, 1 << 20, 1])
    wa = np.flatnonzero(nb == ia); wb = np.flatnonzero(nb == ib)
    _, i1, i2 = np.intersect1d(key(X[wa]), key(X[wb]), return_indices=True)
    return wa[i1], wb[i2]


def rigid_modes(X):
    n = 3 * len(X); Xc = X - X.mean(0)
    Bm = np.zeros((n, 6)); Bm[0::3, 0] = 1; Bm[1::3, 1] = 1; Bm[2::3, 2] = 1
    Bm[0::3, 3] = -Xc[:, 1]; Bm[1::3, 3] = Xc[:, 0]; Bm[1::3, 4] = -Xc[:, 2]; Bm[2::3, 4] = Xc[:, 1]
    Bm[2::3, 5] = -Xc[:, 0]; Bm[0::3, 5] = Xc[:, 2]
    return Bm


class Contact:
    """one-sided or two-sided penalty springs.
    node springs : ids, dirs (n,3), k (scalar / (n,)), kind 'both' | 'pos' (active while u.d > gap), gap
    pair springs : (a, b) ids, dir (3,) or (n, 3), k, kind 'both' | 'pos' (active while (u_b - u_a).d > gap) | 'neg' ((u_b - u_a).d < gap;
                   give a negative gap for a clearance)"""
    def __init__(self, name, kind, k, ids=None, dirs=None, a=None, b=None, d=None, gap=0.0, init_closed=None):
        self.name, self.kind, self.gap = name, kind, gap
        self.init_closed = (gap == 0.0) if init_closed is None else init_closed      # first guess of a one-sided contact
        self.pair = a is not None
        if self.pair:
            self.a, self.b = np.asarray(a), np.asarray(b); n = len(self.a)
            d = np.asarray(d, float)
            self.d = d.reshape(n, 3) if d.ndim == 2 else np.tile(d, (n, 1))
        else:
            self.ids = np.asarray(ids); n = len(self.ids); self.d = np.asarray(dirs, float).reshape(n, 3)
        self.k = np.broadcast_to(np.asarray(k, float), (n,)).copy()
        self.n = n
        self.act = np.ones(n, bool) if kind == "both" else np.zeros(n, bool)

    def rel(self, Uv):
        if self.pair:
            return ((Uv[self.b] - Uv[self.a]) * self.d).sum(1)
        return (Uv[self.ids] * self.d).sum(1)

    def force_on(self, Uv):
        """force (n,3) of the spring on the node (node springs) / on node b (pair springs), active set only"""
        r = self.rel(Uv) - self.gap
        return np.where(self.act, -self.k * r, 0.0)[:, None] * self.d

    def update(self, Uv):
        if self.kind == "both":
            return 0
        r = self.rel(Uv) - self.gap
        new = (r > 0) if self.kind == "pos" else (r < 0)
        # anti-chatter (rev3 round 1c): a node that has flipped 6 times sits at zero force either way - it is frozen OPEN
        if not hasattr(self, "flips"):
            self.flips = np.zeros(len(self.act), int)
        self.flips += (new != self.act)
        new = new & (self.flips < 6)
        ch = int((new != self.act).sum()); self.act = new
        return ch

    def apply(self, Uv, out):
        if not self.act.any():
            return
        r = self.rel(Uv)[self.act]; f = (self.k[self.act] * r)[:, None] * self.d[self.act]
        if self.pair:
            np.add.at(out, self.b[self.act], f); np.add.at(out, self.a[self.act], -f)
        else:
            np.add.at(out, self.ids[self.act], f)

    def rhs(self, out):
        """gap offset force k g d on the active nodes (pairs: + on b, - on a)"""
        if self.gap == 0.0 or not self.act.any():
            return
        f = (self.k[self.act] * self.gap)[:, None] * self.d[self.act]
        if self.pair:
            np.add.at(out, self.b[self.act], f); np.add.at(out, self.a[self.act], -f)
        else:
            np.add.at(out, self.ids[self.act], f)

    def matrix(self, n3):
        r, c, v = [], [], []
        on = self.act
        if not on.any():
            return sp.csr_matrix((n3, n3))
        d = self.d[on]; k = self.k[on]
        if self.pair:
            a, b = self.a[on], self.b[on]
            for p in range(3):
                for q in range(3):
                    kk = k * d[:, p] * d[:, q]
                    for (i, j, s) in ((a, a, 1), (b, b, 1), (a, b, -1), (b, a, -1)):
                        r.append(3 * i + p); c.append(3 * j + q); v.append(s * kk)
        else:
            i = self.ids[on]
            for p in range(3):
                for q in range(3):
                    r.append(3 * i + p); c.append(3 * i + q); v.append(k * d[:, p] * d[:, q])
        return sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(c))), shape=(n3, n3))


def solve_contact(m, F, contacts, log=print, tol=2e-6, inner=150, max_outer=60, U0=None, tag=""):
    """inexact Newton / active set: short PCG sweeps on (K + active springs) with an active-set update after every sweep (longer
    sweeps once the set has settled).  Converged when the relative residual (to |F|) of U with the CONSISTENT active set is <= tol:
    by construction no one-sided spring then carries tension and none is open while penetrating."""
    n3 = 3 * m.nn; t0 = time.time()
    K = m.K

    def precond():
        A = K
        for c in contacts:
            A = A + c.matrix(n3)
        ml = pyamg.smoothed_aggregation_solver(A.tocsr(), B=rigid_modes(m.X), max_coarse=600, keep=False)
        del A

        def vc(b):
            x = np.zeros_like(b)
            ml._MultilevelSolver__solve(0, x, b, "V")
            return x
        return spl.LinearOperator((n3, n3), matvec=vc, dtype=float), sum(int(c.act.sum()) for c in contacts)

    # first guess of the one-sided sets: closed, except the gap contacts (journal) and the faces flagged init_closed = False
    # (plate-on-pad faces: their true contact patches are small, an all-closed start has to be peeled open row by row)
    for c in contacts:
        if c.kind != "both":
            c.act[:] = c.init_closed
    M, n_built = precond()
    log(f"  [{tag}] AMG setup {time.time() - t0:.0f} s")
    U = np.zeros(n3) if U0 is None else U0.copy()
    fn = np.linalg.norm(F); hist = []; its_total = 0; res = 1.0; changed = -1

    def mv(x):
        y = K @ x; out = np.zeros((m.nn, 3)); Xv = x.reshape(-1, 3)
        for c in contacts:
            c.apply(Xv, out)
        return y + out.ravel()

    def rhs_now():
        r = np.zeros((m.nn, 3))
        for c in contacts:
            c.rhs(r)
        return F + r.ravel()
    Aop = spl.LinearOperator((n3, n3), matvec=mv, dtype=float)
    res_prev = float(np.linalg.norm(rhs_now() - mv(U)) / max(fn, 1e-30))
    for outer in range(max_outer):
        b = rhs_now(); it = [0]
        # sweep: reduce the residual of the current active set to 3 % of its starting value (or to the final tolerance) before the
        # contact states are judged again - an unconverged iterate carries rigid-body noise that makes the gap contacts chatter
        settled = changed == 0                       # nothing changed in the last update: run this sweep down to the final tolerance
        U, info = spl.cg(Aop, b, x0=U, rtol=1e-30, atol=(0.5 * tol if settled else max(0.5 * tol, 0.03 * res_prev)) * fn,
                         maxiter=(4 * inner if settled else inner), M=M, callback=lambda xk: it.__setitem__(0, it[0] + 1))
        its_total += it[0]
        chg = {c.name: c.update(U.reshape(-1, 3)) for c in contacts}
        changed = sum(chg.values())
        n_act = sum(int(c.act.sum()) for c in contacts)
        res = float(np.linalg.norm(rhs_now() - mv(U)) / max(fn, 1e-30))      # equilibrium of U with the CONSISTENT active set
        res_prev = res
        hist.append(dict(outer=outer, cg=it[0], res=res, changed=changed, active=n_act))
        log(f"  [{tag}] outer {outer}: cg {it[0]:3d} res {res:.1e} changed {changed} {json.dumps({k: v for k, v in chg.items() if v})} active {n_act}  ({time.time() - t0:.0f} s)")
        if res <= tol:
            break
        if abs(n_act - n_built) > max(400, 0.25 * n_built) and outer < max_outer - 5:
            M, n_built = precond()
    return U, dict(outer=len(hist), cg_total=its_total, rel_res=res, last_changed=changed, converged=bool(res <= tol),
                   seconds=round(time.time() - t0, 1), history=hist)

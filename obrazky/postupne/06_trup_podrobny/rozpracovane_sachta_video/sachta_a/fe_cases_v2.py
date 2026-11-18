"""variant V2 (positive location only, Z3.7): pocket <-> well joined by penalty springs instead of merged nodes:
pad A / pad B / rail faces (y 15.1) -> normal (y) only; F10 dowel D2 at (18.4, z -38) -> x and z; tongue <-> groove lips -> z only;
no friction.  Gear bond only inside the root circle (r <= 13.35).  Results in res_v2/."""
import sys, os, numpy as np
import scipy.sparse as sp
import fe3d, fe_build as FB
_orig_bond = FB.bond_mask_fn
FB.bond_mask_fn = lambda: (lambda p, f=_orig_bond(): f(p) & (np.hypot(p[:, 0], p[:, 1]) <= 13.35))
_orig_build = FB.build


def build(assemble=True):
    occ = FB.occupancies()
    m = fe3d.Model(FB.O, FB.H, FB.SHAPE)
    fe3d.add_body_fcw(m, "well", occ["P_sachta"], FB.E_RESIN, FB.NU_RESIN)
    fe3d.add_body_fcw(m, "gear", occ["koleso_pan"], FB.E_BRASS, FB.NU_BRASS)
    fe3d.add_body_fcw(m, "pocket", occ["P_drziak_serva"], FB.E_RESIN, FB.NU_RESIN)
    del occ
    m.build_nodes(merges=[("well", "gear", FB.bond_mask_fn())])
    print("merged", m.merged, "nodes", m.nn, flush=True)
    if not assemble:
        return m
    fe3d.assemble_fc(m)
    # pair springs well <-> pocket at coincident lattice points
    X = m.X; nb = m.node_body
    key = lambda P: np.round(P / FB.H).astype(np.int64) @ np.array([1 << 40, 1 << 20, 1])
    w_ids = np.flatnonzero(nb == 0); p_ids = np.flatnonzero(nb == 2)
    kw = key(X[w_ids] - FB.O); kp = key(X[p_ids] - FB.O)
    common, iw, ip = np.intersect1d(kw, kp, return_indices=True)
    A, B = w_ids[iw], p_ids[ip]
    P = X[A]
    face = FB.pocket_face_fn(P)                                                     # pads + rail lips on y 15.1
    dow = (np.hypot(P[:, 0] - 18.4, P[:, 2] + 38.0) <= 1.45) & (P[:, 1] >= 11.9) & (P[:, 1] <= 17.3)
    tong = (P[:, 0] >= -4.3) & (P[:, 0] <= 14.3) & (P[:, 1] >= 13.4) & (P[:, 1] <= 15.2) & ((np.abs(P[:, 2] + 36.4) <= 0.25) | (np.abs(P[:, 2] + 39.4) <= 0.25))
    k = 20.0 * FB.E_RESIN * FB.H                                                   # 12800 N/mm per pair
    pairs = [(A[face], B[face], (0, 1, 0)), (A[dow], B[dow], (1, 0, 0)), (A[dow], B[dow], (0, 0, 1)), (A[tong], B[tong], (0, 0, 1))]
    r, c, v = [], [], []
    for a, b, d in pairs:
        d = np.asarray(d, float)
        for p in range(3):
            for q in range(3):
                kk = k * d[p] * d[q]
                if kk == 0:
                    continue
                for (i, j, s) in ((a, a, 1), (b, b, 1), (a, b, -1), (b, a, -1)):
                    r.append(3 * i + p); c.append(3 * j + q); v.append(np.full(len(i), s * kk))
    Kp = sp.csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(c))), shape=m.K.shape)
    m.K = (m.K + Kp).tocsr()
    m.pair_info = dict(face=int(face.sum()), dowel=int(dow.sum()), tongue=int(tong.sum()))
    print("pair springs", m.pair_info, flush=True)
    return m


FB.build = build
src = open("fe_cases.py").read().replace('os.makedirs("res", exist_ok=True)', 'os.makedirs("res_v2", exist_ok=True)').replace('f"res/{name}', 'f"res_v2/{name}')
exec(compile(src, "fe_cases_v2", "exec"))

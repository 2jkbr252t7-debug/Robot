"""FC validation: a 20 x 4 x t cantilever as an STL-like box (occupancy from a box), surface stresses"""
import numpy as np, fe3d
def box_tris(x0, x1, y0, y1, z0, z1):
    v = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return np.array([[v[a], v[b], v[c]] for a, b, c in f])
for t, h, zlo in ((1.34, 0.4, 0.13), (1.34, 0.4, 0.3), (1.25, 0.4, 0.05), (1.6, 0.4, 0.0), (1.34, 0.4, 0.21)):
    L, W = 20.0, 4.0
    T = box_tris(0, L, 0, W, zlo, zlo + t)
    shape = (int(L / h), int(W / h), int(np.ceil((t + zlo) / h)) + 1)
    occ = fe3d.occupancy_w(T, (0, 0, 0), h, shape)
    m = fe3d.Model((0, 0, 0), h, shape); fe3d.add_body_fcw(m, "beam", occ, 1600.0, 0.38); m.build_nodes(); fe3d.assemble_fc(m)
    X = m.X; fixed = np.flatnonzero(np.repeat(X[:, 0] < 1e-9, 3))
    F = np.zeros(3 * m.nn); end = np.flatnonzero(np.abs(X[:, 0] - L) < 1e-9); F[3 * end + 2] = 1.0 / len(end)
    U = m.solve(F, [], fixed=fixed, tol=1e-10, verbose=True)
    pts = np.array([[L / 2, y, zz] for y in np.linspace(0.3, W - 0.3, 9) for zz in (zlo + 1e-4, zlo + t - 1e-4)])
    nrm = np.array([[0, 0, -1] if p[2] < zlo + t / 2 else [0, 0, 1] for p in pts], float)
    sig, ok, _ = fe3d.point_stress_fc(m, U, "beam", pts, nrm)
    print(f"t {t} zlo {zlo}: surface sxx {np.nanmax(sig[:, 0]):.3f} / {np.nanmin(sig[:, 0]):.3f} vs beam {10 / (W * t * t / 6):.3f}; tip {U[3 * end + 2].mean():.3f} (beam {1/(3*1600*W*t**3/12)*L**3:.3f}, plate {1/(3*1600*W*t**3/12)*L**3*(1-0.38**2):.3f})")

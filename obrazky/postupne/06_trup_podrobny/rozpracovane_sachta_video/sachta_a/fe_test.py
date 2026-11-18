"""validation of fe3d: cantilever 20 x 1.6 (thick) x 4 (wide), end load, h 0.4 -> beam theory; partial-volume wall 1.34"""
import numpy as np, fe3d
for t, h in ((1.6, 0.4), (1.34, 0.4), (1.34, 0.2), (1.25, 0.4), (1.25, 0.25)):
    L, W = 20.0, 4.0
    nx, ny, nz = int(L / h), int(W / h), int(np.ceil(t / h)) + 1
    frac = np.zeros((nx, ny, nz))
    zlo = 0.13     # wall not aligned to the lattice
    for k in range(nz):
        a, b = k * h, (k + 1) * h
        frac[:, :, k] = max(0.0, min(b, zlo + t) - max(a, zlo)) / h
    m = fe3d.Model((0, 0, 0), h, (nx, ny, nz))
    m.add_body("beam", frac, 1600.0, 0.38, fmin=0.3)
    m.build_nodes(); m.assemble()
    X = m.X
    fixed = np.flatnonzero(np.repeat(X[:, 0] < 1e-9, 3))
    F = np.zeros(3 * m.nn); end = np.flatnonzero(np.abs(X[:, 0] - L) < 1e-9)
    P = 1.0; F[3 * end + 2] = P / len(end)
    U = m.solve(F, [], fixed=fixed, tol=1e-10)
    ids, sig, _ = m.stresses(U, "beam")
    x = m.X[ids, 0]
    sel = np.abs(x - L / 2) < h / 2 + 1e-9
    sxx = sig[sel, 0]
    M = P * (L - L / 2); Z = W * t ** 2 / 6
    print(f"t {t} h {h}: kept thickness {m.bodies[0]['frac'].sum() * h**3 / (L * W):.3f}; mid-span sxx max {sxx.max():.3f} min {sxx.min():.3f} vs beam {M / Z:.3f}; tip w {U[3 * end + 2].mean():.4f} vs {P * L**3 / (3 * 1600 * W * t**3 / 12):.4f}")

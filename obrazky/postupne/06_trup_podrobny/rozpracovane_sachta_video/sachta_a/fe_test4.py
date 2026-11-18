import numpy as np, fe3d
for t, h, zlo in ((1.34, 0.4, 0.13), (1.34, 0.4, 0.3), (1.25, 0.4, 0.05), (1.34, 0.25, 0.13), (1.6, 0.4, 0.0)):
    L, W = 20.0, 4.0
    nx, ny, nz = int(L / h), int(W / h), int(np.ceil((t + zlo) / h)) + 1
    frac = np.zeros((nx, ny, nz))
    for k in range(nz):
        a, b = k * h, (k + 1) * h
        frac[:, :, k] = max(0.0, min(b, zlo + t) - max(a, zlo)) / h
    m = fe3d.Model((0, 0, 0), h, (nx, ny, nz)); m.add_body("beam", frac, 1600.0, 0.38, fmin=0.3); m.build_nodes(); m.assemble()
    X = m.X; fixed = np.flatnonzero(np.repeat(X[:, 0] < 1e-9, 3))
    F = np.zeros(3 * m.nn); end = np.flatnonzero(np.abs(X[:, 0] - L) < 1e-9); F[3 * end + 2] = 1.0 / len(end)
    U = m.solve(F, [], fixed=fixed, tol=1e-10, verbose=False)
    pts = np.array([[L / 2, y, zz] for y in np.linspace(0.3, W - 0.3, 9) for zz in (zlo + 1e-6, zlo + t - 1e-6)])
    nrm = np.array([[0, 0, -1] if p[2] < zlo + t / 2 else [0, 0, 1] for p in pts], float)
    sig, ok = fe3d.point_stress(m, U, "beam", pts, nrm)
    sx = sig[:, 0]
    print(f"t {t} h {h} zlo {zlo}: surface sxx {np.nanmax(sx):.3f} / {np.nanmin(sx):.3f} vs beam {10 / (W * t * t / 6):.3f}; ok {ok.sum()}/{len(ok)}")

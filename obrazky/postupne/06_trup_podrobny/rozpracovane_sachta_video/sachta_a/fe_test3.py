import numpy as np, fe3d, time, sys
sys.path.insert(0, "pylib"); import pyamg
t, h = 1.25, 0.25
L, W = 20.0, 4.0
nx, ny, nz = int(L / h), int(W / h), int(np.ceil(t / h)) + 1
frac = np.zeros((nx, ny, nz)); zlo = 0.13
for k in range(nz):
    a, b = k * h, (k + 1) * h
    frac[:, :, k] = max(0.0, min(b, zlo + t) - max(a, zlo)) / h
print(frac[0, 0, :])
m = fe3d.Model((0, 0, 0), h, (nx, ny, nz)); m.add_body("beam", frac, 1600.0, 0.38, fmin=0.3); m.build_nodes(); m.assemble()
X = m.X; fixed = np.flatnonzero(np.repeat(X[:, 0] < 1e-9, 3))
F = np.zeros(3 * m.nn); end = np.flatnonzero(np.abs(X[:, 0] - L) < 1e-9); F[3 * end + 2] = 1.0 / len(end)
A = m.K.tocsr(); free = np.ones(A.shape[0], bool); free[fixed] = False; Af = A[free][:, free].tocsr()
print("diag min", Af.diagonal().min(), "sym err", abs(Af - Af.T).max())
Xc = X - X.mean(0); n = A.shape[0]; Bm = np.zeros((n, 6))
Bm[0::3, 0] = 1; Bm[1::3, 1] = 1; Bm[2::3, 2] = 1
Bm[0::3, 3] = -Xc[:, 1]; Bm[1::3, 3] = Xc[:, 0]; Bm[1::3, 4] = -Xc[:, 2]; Bm[2::3, 4] = Xc[:, 1]; Bm[2::3, 5] = -Xc[:, 0]; Bm[0::3, 5] = Xc[:, 2]
Bm = Bm[free]
for opts in [dict(), dict(smooth="energy"), dict(presmoother=("gauss_seidel", {"sweep": "symmetric"}), postsmoother=("gauss_seidel", {"sweep": "symmetric"}))]:
    ml = pyamg.smoothed_aggregation_solver(Af, B=Bm, max_coarse=500, **opts); res = []
    u = ml.solve(F[free], tol=1e-8, accel="cg", maxiter=300, residuals=res)
    print(opts, "its", len(res), res[-1] / res[0], "tip", u.max())
import scipy.sparse.linalg as spl
u = spl.spsolve(Af.tocsc(), F[free]); print("direct tip", u.max())

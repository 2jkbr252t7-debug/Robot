"""uniform sample points on the P_sachta STL surface (spacing ~0.13 mm) with outward normals -> surf_pts.npz"""
import numpy as np, sa_lib as L
T = L.part("P_sachta")
a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); A = 0.5 * np.linalg.norm(n, axis=1); nu = n / (2 * A[:, None] + 1e-30)
rng = np.random.default_rng(1)
k = np.maximum(1, np.ceil(A / 0.017).astype(int))
idx = np.repeat(np.arange(len(T)), k)
r1 = rng.random(len(idx)); r2 = rng.random(len(idx)); s = np.sqrt(r1)
P = (1 - s)[:, None] * a[idx] + (s * (1 - r2))[:, None] * b[idx] + (s * r2)[:, None] * c[idx]
N = nu[idx]
# check orientation: points pushed along +normal must be outside (sample)
np.savez_compressed("surf_pts.npz", P=P, N=N, tri=idx)
print("points", len(P), "area", round(A.sum(), 1))

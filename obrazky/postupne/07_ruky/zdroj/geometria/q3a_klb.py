"""T_klb_L from the STL: planar faces normal to X (x, r range) and the radial profile r_max(x) about the shoulder axis"""
from armgeo import *
T = load("T_klb_L")
n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = 0.5 * np.linalg.norm(n, axis=1); n = n / np.maximum(2 * a, 1e-12)[:, None]
r = np.hypot(T[..., 1] - SH_Y, T[..., 2] - ZS)
m = np.abs(n[:, 0]) > 0.999
xs = np.round(T[m, :, 0].mean(1), 3)
for x in np.unique(xs):
    k = m.copy(); k[m] = xs == x
    print("plane x %8.3f normal %+d area %8.2f r %.2f..%.2f" % (x, np.sign(n[k, 0].mean()), a[k].sum(), r[k].min(), r[k].max()))
# radial profile: max r of the surface for x bins
V = T.reshape(-1, 3); rv = np.hypot(V[:, 1] - SH_Y, V[:, 2] - ZS)
for x0 in np.arange(37.0, 59.0, 0.25):
    s = (V[:, 0] >= x0) & (V[:, 0] < x0 + 0.25)
    if s.any():
        print("x %.2f..%.2f  r_max %.3f" % (x0, x0 + 0.25, rv[s].max()))

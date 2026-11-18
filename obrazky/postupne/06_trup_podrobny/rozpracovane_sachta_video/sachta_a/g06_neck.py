"""neck (B) outline at several z, the PTFE guide strips and land faces - where the neck touches the well"""
import numpy as np, sa_lib as L, glob, os
NF = L.part("krk_predna_polovica"); NB = L.part("krk_zadna_polovica")
N = np.concatenate([NF, NB])
for z in (-36.0, -30.0, -20.0, -10.0, -4.5, -1.0, 2.0, 5.0):
    s = L.slice_segments(N, 2, z).reshape(-1, 3)
    if len(s) == 0:
        print(z, "none"); continue
    x, y = s[:, 0], s[:, 1]
    # extents along y at x = 15 and x = -15 and along x at y = +-6
    def ext_y(x0):
        m = np.abs(x - x0) < 0.3
        return (round(y[m].min(), 2), round(y[m].max(), 2)) if m.any() else None
    def ext_x(y0):
        m = np.abs(y - y0) < 0.3
        return (round(x[m].min(), 2), round(x[m].max(), 2)) if m.any() else None
    print(z, "x", round(x.min(), 2), round(x.max(), 2), "y", round(y.min(), 2), round(y.max(), 2), "| y@x15", ext_y(15), "y@x-15", ext_y(-15), "y@x12", ext_y(12), "| x@y6", ext_x(6.5), "x@y-6", ext_x(-6.5))
for f in sorted(glob.glob(L.STL + "/ptfe_pasik_*.stl")):
    T = L.read_stl(f); lo = T.reshape(-1, 3).min(0); hi = T.reshape(-1, 3).max(0)
    print(os.path.basename(f), np.round(lo, 2), np.round(hi, 2))
G = L.part("golier_kotuc")
for z in (-1.9, 0.0, 2.0, 3.9):
    s = L.slice_segments(G, 2, z).reshape(-1, 3)
    r = np.hypot(s[:, 0], s[:, 1])
    m = r < 24
    print("collar z", z, "inner opening x", round(s[m, 0].min(), 2), round(s[m, 0].max(), 2), "y", round(s[m, 1].min(), 2), round(s[m, 1].max(), 2), "r max", round(r.max(), 2))

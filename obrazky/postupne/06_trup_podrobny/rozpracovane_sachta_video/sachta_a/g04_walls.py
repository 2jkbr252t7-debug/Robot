"""wall thickness of P_sachta per z level: raster slice (0.02 px) + Euclidean distance transform -> local thickness
= 2 x inscribed radius on the medial axis.  Reports min thickness per sector (front wall, back wall, end walls, corners)"""
import json, math, numpy as np
from scipy import ndimage as ndi
import sa_lib as L
S = L.part("P_sachta")
h = 0.02
out = {}
for z in (-41.5, -41.0, -40.8, -40.5, -40.0, -39.0, -38.0, -36.0, -34.0, -30.0, -25.0, -20.0, -15.0, -12.0, -10.5, -9.0, -6.0, -4.0, -3.0, -2.5):
    us, vs, M = L.raster_slice(S, 2, z, (-26.6, 26.6), (-26.6, 26.6), h)
    if not M.any():
        out[z] = None; continue
    D = ndi.distance_transform_edt(M) * h
    # medial axis approx: local maxima of D along the gradient -> use maximum filter 3x3 equality
    mx = ndi.maximum_filter(D, size=3)
    med = M & (D >= mx - 1e-9) & (D > 0.1)
    X, Y = np.meshgrid(us, vs, indexing="ij"); R = np.hypot(X, Y); AZ = np.degrees(np.arctan2(Y, X)) % 360
    t = 2 * D
    def sect(mask):
        m = med & mask
        if not m.any():
            return None
        k = np.argmin(np.where(m, t, 1e9)); i, j = np.unravel_index(k, t.shape)
        return [round(float(t[i, j]), 3), round(float(X[i, j]), 2), round(float(Y[i, j]), 2)]
    rows = {}
    rows["front wall |x|<19"] = sect((Y < -10.9) & (Y > -13.5) & (np.abs(X) < 19))
    rows["back wall |x|<19"] = sect((Y > 10.9) & (Y < 13.3) & (np.abs(X) < 19))
    rows["-X end wall |y|<6"] = sect((X < -23.4) & (np.abs(Y) < 6))
    rows["+X end wall |y|<6"] = sect((X > 23.4) & (np.abs(Y) < 6))
    for cx, cy in ((21, 8.5), (-21, 8.5), (-21, -8.5), (21, -8.5)):
        rows[f"corner ({cx},{cy})"] = sect((np.hypot(X - cx, Y - cy) > 2.4) & (np.hypot(X - cx, Y - cy) < 5.5) & (np.sign(X) == np.sign(cx)) & (np.sign(Y) == np.sign(cy)) & (np.abs(X) > 21) & (np.abs(Y) > 8.5))
    rows["ring/journal r>24"] = sect(R > 24.0)
    rows["anything"] = sect(M)
    out[z] = rows
    print(z, json.dumps(rows))
json.dump({str(k): v for k, v in out.items()}, open("g04_walls.json", "w"), indent=1)

"""Real-head (B rev. E2 STL) clearance checks for the K2 placeholder torso top and the K2 well, over the B tilt-vs-lift
table x pan -85..85.  The t1lib head envelopes (rf-14 box, lug box) are much lower/larger than the real parts at the
corners, so poses at the table limits are verified here with the real meshes.  -> head_real_check.json"""
import json, math
import numpy as np
from head_keepout import read_stl, TABLE, poses, AX_REST, DZ, Z_TT

STL = "/tmp/claude-0/gapwf/fin/B/stl"
A, B, N, RF, ZB, RPLAT = 44.5, 40.0, 2.35, 16.0, Z_TT - 1.0, 29.8     # placeholder torso: body top 132, plateau r29.8 @133 (as B)

GS = 0.1
GX = np.arange(-A - 1, A + 1 + GS, GS)
GY = np.arange(-B - 1, B + 1 + GS, GS)
_X, _Y = np.meshgrid(GX, GY, indexing="ij")
_IN = (np.abs(_X) / A) ** N + (np.abs(_Y) / B) ** N < 1
from scipy.ndimage import distance_transform_edt
_D = distance_transform_edt(_IN) * GS                     # inward distance to the outline (0 outside)
_Z = np.where(_D >= RF, ZB, ZB - (RF - np.sqrt(np.clip(RF ** 2 - (RF - np.clip(_D, 0, RF)) ** 2, 0, None))))
_Z = np.where(_IN, _Z, -1e9)
_Z = np.where(np.hypot(_X, _Y) <= RPLAT, Z_TT, _Z)


def z_top(x, y):
    i = np.clip(np.round((x - GX[0]) / GS).astype(int), 0, len(GX) - 1)
    j = np.clip(np.round((y - GY[0]) / GS).astype(int), 0, len(GY) - 1)
    out = (np.abs(x) > A + 0.5) | (np.abs(y) > B + 0.5)
    return np.where(out, -1e9, _Z[i, j])


def pose_pts(P, lift, tilt, pan=0.0):
    ax = AX_REST + lift
    t = math.radians(tilt)
    y, z = P[:, 1], P[:, 2] + lift - ax
    y2 = y * math.cos(t) - z * math.sin(t)
    z2 = y * math.sin(t) + z * math.cos(t) + ax + DZ
    a = math.radians(pan)
    x3 = P[:, 0] * math.cos(a) - y2 * math.sin(a)
    y3 = P[:, 0] * math.sin(a) + y2 * math.cos(a)
    return x3, y3, z2


if __name__ == "__main__":
    H = np.vstack([read_stl(f"{STL}/{p}.stl") for p in ("hlava_skrupina", "ram_displeja", "usi", "displej")])
    H = H[H[:, 2] < 25.0]
    # pre-filter: only points that can come within 6 mm of the top plane in some pose
    best = (1e9, None)
    rows = []
    for lift, tilt in poses():
        for pan in range(-85, 86, 5):
            x, y, z = pose_pts(H, lift, tilt, pan)
            m = z < Z_TT + 4.0
            if not m.any():
                continue
            cl = z[m] - z_top(x[m], y[m])
            k = int(np.argmin(cl))
            v = float(cl[k])
            if v < best[0]:
                best = (v, {"lift": lift, "tilt": tilt, "pan": pan, "point": [round(float(x[m][k]), 1),
                                                                            round(float(y[m][k]), 1),
                                                                            round(float(z[m][k]), 2)]})
        rows.append((lift, tilt, round(best[0], 2)))
    # lugs vs the K2 well (inner 47 x 22 below z 127) and the collar disc slot 45.5 x 20.5 (z 127..133)
    U = np.vstack([read_stl(f"{STL}/{p}.stl") for p in ("usko_kryt", "usko_lozisko")])
    lugd = {}
    for lift, tilt in poses():
        x, y, z = pose_pts(U, lift, tilt, 0)
        for zlo, zhi, hx, hy, nm in ((80, 127, 23.5, 11.0, "K2 well 47x22 (z<127)"), (127, 133, 22.75, 10.25, "B collar slot 45.5x20.5")):
            m = (z >= zlo) & (z < zhi)
            if m.any():
                mg = np.minimum(hx - np.abs(x[m]), hy - np.abs(y[m]))
                v = float(mg.min())
                if v < lugd.get(nm, (1e9,))[0]:
                    lugd[nm] = (round(v, 2), {"lift": lift, "tilt": tilt})
    lug = (min(v[0] for v in lugd.values()), lugd)
    out = {"head_vs_placeholder_torso_top": {"min_clearance_mm": round(best[0], 2), "worst": best[1],
                                             "poses": "B tilt-vs-lift table (all rows, limits + 5 deg steps) x pan -85..85 step 5"},
           "lugs_vs_well_and_collar_slot": {"min_margin_mm": round(lug[0], 2), "worst": lug[1]}}
    json.dump(out, open("/tmp/claude-0/gapwf/fin/T1/k2/head_real_check.json", "w"), indent=1)
    print(json.dumps(out, indent=1))

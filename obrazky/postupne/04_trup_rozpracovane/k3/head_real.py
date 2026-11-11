"""Real B-head mesh (rev. E2 STLs) vs the K3 placeholder torso top, over the B tilt-vs-lift table x pan.
Torso top = sshell outer top (flat inside the superellipse offset by rf, circular fillet rf) [+ raised plateau].
Usage: python head_real.py [rf] [top_drop] [plateau_r]  -> prints min clearance; writes check_parts/head_real.json"""
import sys, json, math, struct
import numpy as np

HERE = "/tmp/claude-0/gapwf/fin/T1/k3"
LAY = json.load(open(f"{HERE}/layout.json"))
Z_TT = LAY["Z_TT"]
DZ = Z_TT - 4.0
AX0 = -3.5 + DZ
sh = [c for c in LAY["comps"] if c["name"] == "T_shell"][0]
A, B, N = sh["a"], sh["b"], sh["n"]
RF = float(sys.argv[1]) if len(sys.argv) > 1 else sh["rf"]
TOP_DROP = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5      # shell top below Z_TT (plateau makes up the rest)
PLAT_R = float(sys.argv[3]) if len(sys.argv) > 3 else 29.8


def read_stl(fn):
    d = open(fn, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    arr = np.frombuffer(d[84:84 + 50 * n], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    return np.unique(arr["v"].reshape(-1, 3).astype(np.float64), axis=0)


V = np.vstack([read_stl(f"/tmp/claude-0/gapwf/fin/B/stl/{n}.stl") for n in ("hlava_skrupina", "ram_displeja", "usi")])
V[:, 2] += DZ
# superellipse boundary (offset by rf inward) sampled
t = np.linspace(0, 2 * np.pi, 1440, endpoint=False)
c, s = np.cos(t), np.sin(t)
ex = (A) * np.sign(c) * np.abs(c) ** (2 / N)
ey = (B) * np.sign(s) * np.abs(s) ** (2 / N)
CURVE = np.stack([ex, ey], 1)


def inside_depth(xy):
    """approx. inward distance from the outer superellipse (positive inside)"""
    d = np.sqrt(((xy[:, None, :] - CURVE[None, :, :]) ** 2).sum(-1)).min(1)
    inside = (np.abs(xy[:, 0] / A) ** N + np.abs(xy[:, 1] / B) ** N) <= 1.0
    return np.where(inside, d, -d)


def surf(xy):
    top = Z_TT - TOP_DROP
    di = inside_depth(xy)
    z = np.full(len(xy), -1e9)
    flat = di >= RF
    z[flat] = top
    fil = (di >= 0) & (di < RF)
    z[fil] = top - RF + np.sqrt(np.maximum(0, RF ** 2 - (RF - di[fil]) ** 2))
    if PLAT_R > 0:
        r = np.hypot(xy[:, 0], xy[:, 1])
        z[r <= PLAT_R] = Z_TT
    return z


# --- height map on a grid (computed once), nearest-cell lookup (conservative: max of the 4 neighbours)
GS = 0.25
gx = np.arange(-A - 1, A + 1 + GS, GS); gy = np.arange(-B - 1, B + 1 + GS, GS)
GX, GY = np.meshgrid(gx, gy, indexing="ij")
pts = np.stack([GX.ravel(), GY.ravel()], 1)
H = np.concatenate([surf(pts[i:i + 4000]) for i in range(0, len(pts), 4000)]).reshape(GX.shape)
Hmax = np.maximum.reduce([H, np.roll(H, 1, 0), np.roll(H, -1, 0), np.roll(H, 1, 1), np.roll(H, -1, 1)])


def surf_lookup(xy):
    i = np.clip(np.round((xy[:, 0] - gx[0]) / GS).astype(int), 0, len(gx) - 1)
    j = np.clip(np.round((xy[:, 1] - gy[0]) / GS).astype(int), 0, len(gy) - 1)
    return Hmax[i, j]


TABLE = [(20, 40, -40), (16, 35, -40), (12.5, 30, -40), (10, 25, -35), (7.5, 20, -30), (5, 15, -20), (2.5, 10, -15),
         (0, 5, -10)]
best = (1e9, None)
rows = []
for lift, tdn, tup in TABLE:
    for tilt in (tdn, tup, 0):
        a = math.radians(tilt)
        R = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        P = (V - [0, 0, AX0]) @ R.T + [0, 0, AX0 + lift]
        low = P[P[:, 2] < Z_TT + 15]
        low = low[::1]                      # only the lower part of the head matters
        for pan in range(-85, 90, 5):
            p = math.radians(pan)
            Rz = np.array([[math.cos(p), -math.sin(p)], [math.sin(p), math.cos(p)]])
            xy = low[:, :2] @ Rz.T
            m = (np.abs(xy[:, 0]) < A + 1) & (np.abs(xy[:, 1]) < B + 1)
            if not m.any():
                continue
            z = surf_lookup(xy[m])
            clr = low[m, 2] - z
            k = int(np.argmin(clr))
            if clr[k] < best[0]:
                best = (float(clr[k]), {"lift": lift, "tilt": tilt, "pan": pan,
                                        "point": [round(float(xy[m][k, 0]), 1), round(float(xy[m][k, 1]), 1),
                                                  round(float(low[m][k, 2]), 1)]})
        rows.append((lift, tilt, round(best[0], 2)))
# --- real lugs + neck (H/L meshes) vs the K3 well (inner 47 x 22, R1.5 corners, z WELL_Z0..Z_TT-6) + tongue relief
WELL_Z0 = Z_TT - 40.6
LUG = np.vstack([read_stl(f"/tmp/claude-0/gapwf/fin/B/stl/{n}.stl") for n in ("usko_kryt", "usko_lozisko", "paka",
                                                                              "klzny_kruzok", "hlava_skrupina")])
NECK = np.vstack([read_stl(f"/tmp/claude-0/gapwf/fin/B/stl/{n}.stl") for n in ("krk_predna_polovica", "krk_zadna_polovica")])
LUG[:, 2] += DZ; NECK[:, 2] += DZ


def well_clear(P):
    m = (P[:, 2] > WELL_Z0) & (P[:, 2] < Z_TT - 6.0)
    if not m.any():
        return 1e9
    x, y = np.abs(P[m, 0]), np.abs(P[m, 1])
    c = np.minimum(23.5 - x, 11.0 - y)
    corner = (x > 22.0) & (y > 9.5)
    c = np.where(corner, 1.5 - np.hypot(x - 22.0, y - 9.5), c)
    return float(c.min())


wbest = (1e9, None)
for lift, tdn, tup in TABLE + [(l, 0, 0) for l in (0, 5, 10, 15, 20)]:
    for tilt in (tdn, tup):
        a_ = math.radians(tilt)
        R = np.array([[1, 0, 0], [0, math.cos(a_), -math.sin(a_)], [0, math.sin(a_), math.cos(a_)]])
        PL = (LUG - [0, 0, AX0]) @ R.T + [0, 0, AX0 + lift]
        PN = NECK + [0, 0, lift]
        for nm, PP in (("lugs/head", PL), ("neck", PN)):
            c_ = well_clear(PP)
            if c_ < wbest[0]:
                wbest = (c_, {"parts": nm, "lift": lift, "tilt": tilt})
print("real lugs/neck vs K3 well: min clearance", round(wbest[0], 2), wbest[1])

print("rf", RF, "top_drop", TOP_DROP, "plateau_r", PLAT_R, "-> min clearance real head vs torso top:",
      round(best[0], 2), best[1])
json.dump({"well_vs_real_lugs_neck_min_clearance_mm": round(wbest[0], 2), "well_worst": wbest[1],
           "rf": RF, "top_drop": TOP_DROP, "plateau_r": PLAT_R, "min_clearance_mm": round(best[0], 2),
           "worst": best[1], "poses": "B tilt-vs-lift table rows (limits + 0) x pan -85..85 step 5",
           "head_parts": ["hlava_skrupina", "ram_displeja", "usi"]},
          open(f"{HERE}/check_parts/head_real.json", "w"), indent=1)

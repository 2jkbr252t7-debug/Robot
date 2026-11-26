"""FIXER: reproduce the colroom free mask (judge merge) WITHOUT the band restriction, print ASCII plan slices.
legend: '#' fill voxel (judge colfill), 'o' free but not filled, '.' not free, 'D' deck-blocking voxel region x<31.3"""
import numpy as np, sys
from scipy import ndimage as ndi
K = np.load("/tmp/claude-0/gapwf/fin/R1/K3_preusporiadanie/k3map.npz")
M1 = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
SIDE = sys.argv[1] if len(sys.argv) > 1 else "L"
lo, h, n = K["lo"], float(K["h"]), K["n"]
ln = [str(s) for s in M1["lab_names"]]
print(ln)
bok = M1["label"] == ln.index("T_bok_L" if SIDE == "L" else "T_bok_P")
hard = K["hard"] | bok
ds = ndi.distance_transform_edt(~hard, sampling=h)
dm = K["dm"].astype(float)
dl = ndi.distance_transform_edt(~M1["lower"], sampling=h)
xs = lo[0] + (np.arange(n[0]) + 0.5) * h
if SIDE == "R":
    ds, dm, dl, bok = ds[::-1], dm[::-1], dl[::-1], bok[::-1]; xs = -xs[::-1]
ys = lo[1] + (np.arange(n[1]) + 0.5) * h
zs = lo[2] + (np.arange(n[2]) + 0.5) * h
X, Y = np.meshgrid(xs, ys, indexing="ij")
bx = np.where(bok, xs[:, None, None], np.inf); capmin = ndi.minimum_filter(bx.min(axis=0), size=3)
F = np.load(f"/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_{SIDE}.npz")["P"].astype(float)
if SIDE == "R": F[:, 0] *= -1
np.savez("/tmp/claude-0/gapwf/fin/R2c/oprava/free_%s.npz" % SIDE, ds=ds, dm=dm, dl=dl, capmin=capmin, xs=xs, ys=ys, zs=zs)
for zq in [float(a) for a in (sys.argv[2:] or [-28.25, -31.25, -34.75, -38.25, -41.25, -43.75, -46.25, -48.25])]:
    kz = int(np.argmin(abs(zs - zq))); z = zs[kz]
    free = (ds[:, :, kz] >= 0.30 + h / 2) & (dm[:, :, kz] >= 1.0 + h / 2) & (dl[:, :, kz] >= 0.5 + h / 2) & (X >= 24.0)
    rsh = np.hypot(Y - 3.0, z + 17.0)
    free &= np.where(rsh <= 16.3, X <= 38.8, X <= 41.5)
    rv = np.hypot(X - 39.0, Y - 3.0)
    if z <= -35.0:
        free &= rv > 5.0
        free &= ~((Y > -1.8) & (Y < 7.8) & (X >= 34.2) & (z >= -44.0))
    else:
        free &= rv > 3.0
    free &= X <= (capmin[:, kz][None, :] - 0.3 - h / 2)
    if z < -44.5:
        free &= ~((Y >= -14.6) & (Y <= 9.2) & (X >= 32.65))
    fz = F[abs(F[:, 2] - z) < 1e-3]
    fill = np.zeros_like(free)
    for p in fz:
        i = int(round((p[0] - xs[0]) / h)); j = int(round((p[1] - ys[0]) / h)); fill[i, j] = True
    print(f"\nz = {z:.2f}   rows y from 18 down to -23, cols x from 24 to 46 (0.5 mm)  hard(ds<0.3)='.' sweep(dm<1)='s' lower(dl<.5)='l'")
    ix = [i for i in range(n[0]) if 24.0 <= xs[i] <= 46.0]
    print("      " + "".join(("|" if abs(xs[i] - round(xs[i])) < 0.3 and int(round(xs[i])) % 2 == 0 else " ") for i in ix))
    for j in range(n[1] - 1, -1, -1):
        y = ys[j]
        if y > 18 or y < -23: continue
        row = ""
        for i in ix:
            if fill[i, j]: c = "#"
            elif free[i, j]: c = "o"
            elif ds[i, j, kz] < 0.3 + h/2: c = "."
            elif dm[i, j, kz] < 1.0 + h/2: c = "s"
            elif dl[i, j, kz] < 0.5 + h/2: c = "l"
            else: c = " "
            row += c
        print(f"{y:6.2f}" + row)

"""FIXER: final column fill voxels = judge colfill_B1merge clipped to the deck path / servo corridor (exact on voxel extents)
+ torsion web between the legs z -35..-27 (free map, r 3.4 keep-out about the vertical axis for the lifted 5 AF hex, x >= 31.3).
Writes colfill_fix_<S>.npz (P = voxel centres, R in real coordinates x < 0), same format as the judge's file."""
import sys, math, json
import numpy as np
SIDE = sys.argv[1]; h = 0.5
F = np.load(f"/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_{SIDE}.npz")["P"].astype(float)
if SIDE == "R": F[:, 0] *= -1
x0, x1, y0, y1, z0, z1 = F[:, 0] - h/2, F[:, 0] + h/2, F[:, 1] - h/2, F[:, 1] + h/2, F[:, 2] - h/2, F[:, 2] + h/2
bad = ((z1 > -48.5) & (x0 < 31.3)) | ((z0 < -44.5) & (x1 > 32.65) & (y1 > -14.6) & (y0 < 9.2))
Fc = F[~bad]
M = np.load(f"free_{SIDE}.npz"); ds, dm, dl, capmin, mx, my, mz = (M[k] for k in ("ds", "dm", "dl", "capmin", "xs", "ys", "zs"))
W = []
for kz, z in enumerate(mz):
    if z < -34.75 or z > -27.0: continue
    for ix, x in enumerate(mx):
        if x - h/2 < 31.3 or x > 41.5: continue
        for jy, y in enumerate(my):
            if not (-9.5 <= y <= 8.0): continue
            ok = ds[ix, jy, kz] >= 0.3 + h/2 and dm[ix, jy, kz] >= 1.0 + h/2 and dl[ix, jy, kz] >= 0.5 + h/2
            rsh = math.hypot(y - 3.0, z + 17.0)
            ok = ok and x <= (38.8 if rsh <= 16.3 else 41.5) - h/2 and x <= capmin[jy, kz] - 0.3 - h/2
            dx = max(abs(x - 39.0) - h/2, 0); dy = max(abs(y - 3.0) - h/2, 0)
            ok = ok and math.hypot(dx, dy) >= 3.4
            if ok: W.append((x, y, z))
W = np.array(W)
# drop web voxels already in the fill
key = lambda A: set(map(tuple, np.round(A, 3)))
KF = key(Fc)
W = np.array([w for w in W if tuple(np.round(w, 3)) not in KF]) if len(W) else W
P = np.r_[Fc, W]
info = dict(side=SIDE, judge=len(F), clipped=int(bad.sum()), clipped_mm3=round(float(bad.sum() * h ** 3), 1), web=len(W), web_mm3=round(len(W) * h ** 3, 1),
            web_x=[round(float(W[:, 0].min() - h/2), 2), round(float(W[:, 0].max() + h/2), 2)], web_y=[round(float(W[:, 1].min() - h/2), 2), round(float(W[:, 1].max() + h/2), 2)],
            web_z=[round(float(W[:, 2].min() - h/2), 2), round(float(W[:, 2].max() + h/2), 2)], total=len(P))
Ps = P.copy()
if SIDE == "R": Ps[:, 0] *= -1
np.savez_compressed(f"colfill_fix_{SIDE}.npz", P=Ps.astype(np.float32), web=(W * ([-1, 1, 1] if SIDE == "R" else [1, 1, 1])).astype(np.float32))
print(json.dumps(info)); json.dump(info, open(f"colfill_fix_{SIDE}.json", "w"), indent=1)

"""B2: how much resin can the UPPER shoulder column (z -44.5 .. -26, above the servo top) get, and is the L5 hand check then
OK with standard screws instead of the cut steel rods?
Free voxel (0.5 mm, left side, from the judge's maps):
  * >= 0.30 (+ half voxel) from kept static parts: k3map 'hard' PLUS the whole T_bok_L (the side cap is kept; k3map had its
    inner features as removable)
  * >= 1.00 (+ half voxel) from the pan / lift sweep (map1 'dm')
  * >= 0.50 from the T_stred lowering path (map1 'lower' mask, EDT)
  * x <= 38.8 where r about the shoulder axis <= 16.3 (cap socket tube, removed along +X), x <= 41.5 elsewhere (judge's leg
    face; cap removal path verified there)
  * outside the B2 drive keep-out: coupler + lift r <= 4.5 about (39, 3) for z -44.5..-35; shaft r <= 3.0 for z -35..-26.85;
    tongue/insert/pinion zone |y-3| <= 5.1 for z >= -27 (handled: the column rows stop at z -27)
  * outside the servo slide zone z < -44.5 (not used here)
Bands: back = y 7.5 .. 16.5, front = y -21 .. -9 (connected to the existing legs / strut).
Section modulus about Y of the free voxels per z (bending from L5, M = 10 (33.9 - z) N.mm), Kt 1.3, plus one M3 screw per
leg where it reaches (back: z <= -40 effective, front: z <= -40 effective when the front screw is an M3x40 at x 37.0).
writes colroom.json"""
import json, math, os
import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
K = np.load("/tmp/claude-0/gapwf/fin/R1/K3_preusporiadanie/k3map.npz")
M1 = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
import sys as _s
SIDE = "R" if "R" in _s.argv[1:] else "L"
lo, h, n = K["lo"], float(K["h"]), K["n"]
ln = [str(s) for s in M1["lab_names"]]
bok = M1["label"] == ln.index("T_bok_L" if SIDE == "L" else "T_bok_P")
hard = K["hard"] | bok
ds = ndi.distance_transform_edt(~hard, sampling=h)
dm = K["dm"].astype(float)
dl = ndi.distance_transform_edt(~M1["lower"], sampling=h)
xs = lo[0] + (np.arange(n[0]) + 0.5) * h
if SIDE == "R":          # mirror x -> -x (grid is symmetric enough: centres -52.75..52.75)
    ds, dm, dl, bok = ds[::-1], dm[::-1], dl[::-1], bok[::-1]
    xs = -xs[::-1]
ys = lo[1] + (np.arange(n[1]) + 0.5) * h
zs = lo[2] + (np.arange(n[2]) + 0.5) * h
X, Y = np.meshgrid(xs, ys, indexing="ij")
# cap removal sweep: per (y, z) column the smallest x of any T_bok_L voxel; static column voxels must stay >= 0.3 inboard of it
# (checked within +-0.5 mm in y and z by a min-filter)
bx = np.where(bok, X[:, :, None] if False else xs[:, None, None], np.inf)
capmin = bx.min(axis=0)                                        # (ny, nz)
capmin = ndi.minimum_filter(capmin, size=3)
E_R, E_S, D3 = 2500.0, 200000.0, 2.387
import sys
WITH_SCREWS = "screws" in sys.argv[1:]
FILL = []
out = {"rows": [], "with_screws": WITH_SCREWS}
for kz, z in enumerate(zs):
    if z < -49.0 or z > -27.0:
        continue
    free = (ds[:, :, kz] >= 0.30 + h / 2) & (dm[:, :, kz] >= 1.0 + h / 2) & (dl[:, :, kz] >= 0.5 + h / 2) & (X >= 26.0)
    rsh = np.hypot(Y - 3.0, z + 17.0)
    free &= np.where(rsh <= 16.3, X <= 38.8, X <= 41.5)
    rv = np.hypot(X - 39.0, Y - 3.0)
    if z <= -35.0:
        free &= rv > 5.0                     # JUDGE merge: B1 coupler r 4.5 rotating, >= 0.5 own clearance
        free &= ~((Y > -1.8) & (Y < 7.8) & (X >= 34.2) & (z >= -44.0))   # JUDGE merge: B1 coupler slides in along -X on the servo (y <= 7.5) -> 0.3
    else:
        free &= rv > 3.0
    free &= X <= (capmin[:, kz][None, :] - 0.3 - h / 2)
    if z < -44.5:      # servo (earless, + 0.3) and its slide-out path along +X
        free &= ~((Y >= -14.6) & (Y <= 9.2) & (X >= 32.65))
    band = ((Y >= 7.5) & (Y <= 16.5)) | ((Y >= -21.0) & (Y <= -9.0))
    sel = free & band
    # keep only voxels 4-connected to the existing legs/strut footprint (x 34.4..38.4 at the band centres)
    lab, nl = ndi.label(sel)
    seeds = set()
    for (xx, yy) in ((36.0, 12.35), (36.0, -15.0)):
        i, j = int((xx - lo[0]) / h), int((yy - lo[1]) / h)
        if lab[i, j] > 0: seeds.add(lab[i, j])
    sel = np.isin(lab, list(seeds)) if seeds else np.zeros_like(sel)
    A = sel.sum() * h * h
    if A == 0:
        continue
    xv = X[sel]
    xc = xv.mean()
    I = ((xv - xc) ** 2).sum() * h * h + sel.sum() * h ** 4 / 12
    c = max(xc - (xv.min() - h / 2), (xv.max() + h / 2) - xc)
    rods = []
    if WITH_SCREWS and z <= -40.0:
        rods = [38.0, 37.0]
    EI_r = E_R * I
    a = math.pi * D3 ** 2 / 4; i0 = math.pi * D3 ** 4 / 64
    EI_s = sum(E_S * (i0 + a * (xr - xc) ** 2) for xr in rods)
    share = EI_r / (EI_r + EI_s)
    Mz = 10.0 * (33.9 - z)
    sig = Mz * 1.3 * share / (I / c)
    xb = X[sel & (Y >= 7.5)]; xf = X[sel & (Y <= -9.0)]
    row = dict(z=round(float(z), 2), A=round(float(A), 1), I=round(float(I), 1), Z=round(float(I / c), 1), xc=round(float(xc), 2),
               x_back=[round(float(xb.min() - h / 2), 2), round(float(xb.max() + h / 2), 2)] if len(xb) else None,
               x_front=[round(float(xf.min() - h / 2), 2), round(float(xf.max() + h / 2), 2)] if len(xf) else None,
               n_screws=len(rods), sigma_MPa=round(float(sig), 2), ok=bool(sig <= 8.5))
    out["rows"].append(row)
    FILL.append(np.c_[X[sel], Y[sel], np.full(sel.sum(), z)])
    print(row, flush=True)
tag = "B1merge_" + SIDE + ("_screws" if WITH_SCREWS else "")
json.dump(out, open(os.path.join(HERE, "colroom_%s.json" % tag), "w"), indent=1)
F = np.concatenate(FILL)
if SIDE == "R":
    F[:, 0] *= -1.0
np.savez_compressed(os.path.join(HERE, "colfill_B1merge_%s.npz" % SIDE), P=F.astype(np.float32))
print("fill voxels", len(F), "sigma max %.2f" % max(r["sigma_MPa"] for r in out["rows"]))

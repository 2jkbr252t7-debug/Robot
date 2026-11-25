"""occupancy AFTER the K3 change (both sides): k3map hard + new parts voxelised (servos, drives, inner boss + tongue, plug
envelope = old socket region, column legs as boxes).  Then box-fit search for the relocated amplifier and buck converter.
usage: k3after.py  -> k3after.npz + electronics_fit.json"""
import sys, os, json, math, itertools
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import k3_parts as KP
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as V
D = np.load(os.path.join(HERE, "k3map.npz"))
M1 = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")
lo, h, n = D["lo"], float(D["h"]), tuple(D["n"])
hard = D["hard"].copy(); dm = D["dm"]; lower = M1["lower"]
X, Y, Z = np.meshgrid(lo[0] + (np.arange(n[0]) + .5) * h, lo[1] + (np.arange(n[1]) + .5) * h, lo[2] + (np.arange(n[2]) + .5) * h, indexing="ij")
def mark(P):
    k = np.floor((P - lo) / h).astype(int); ok = np.all((k >= 0) & (k < np.array(n)), 1); k = k[ok]
    m = np.zeros(n, bool); m[k[:, 0], k[:, 1], k[:, 2]] = True; return m
new = np.zeros(n, bool)
P = KP.parts()
for sg in (1.0, -1.0):
    for k, v in P.items():
        new |= mark(v * np.array([sg, 1, 1]))
    # filled servo envelope (box) + ears
    s = KP.SV
    new |= (np.abs(sg * X - KP.XV) <= s["W"] / 2 + 0.3) & (Y >= KP.YA - (s["L"] - s["sh"]) - 0.3) & (Y <= KP.YA + s["sh"] + 0.3) & \
           (Z >= s["z_top"] - s["H"] - 0.3) & (Z <= s["z_top"] + 0.3)
    # plug / socket envelope: r <= 13.5 about the arm axis, x 38.6 .. 47.5
    ra = np.hypot(Y - KP.YA, Z - KP.ZA)
    new |= (ra <= 13.5) & (sg * X >= 38.4) & (sg * X <= 47.5)
    new |= (ra <= 12.8) & (sg * X >= 34.4) & (sg * X <= 38.4)
    # column legs (boxes): back leg y 9.5..15.5, front strut y -21..-14.6 below the servo top, x 34.4..42, z floor..-28
    new |= (sg * X >= 34.4) & (sg * X <= 42.0) & (Y >= 9.5) & (Y <= 15.5) & (Z >= -82.3) & (Z <= -26.0)
    new |= (sg * X >= 34.4) & (sg * X <= 42.0) & (Y >= -21.0) & (Y <= -14.6) & (Z >= -82.3) & (Z <= -44.0)
    new |= (sg * X >= 34.4) & (sg * X <= 42.0) & (Y >= -14.6) & (Y <= -8.0) & (Z >= -44.0) & (Z <= -26.0)
    # coupler / vertical shaft keep-out (moving): r 4.5 about the vertical axis z -45 .. -20
    new |= (np.hypot(sg * X - KP.XV, Y - KP.YA) <= 4.5) & (Z >= -45.0) & (Z <= -20.0)
occ = hard | new
ds = ndi.distance_transform_edt(~occ, sampling=h).astype(np.float32)
free = D["interior"] & ~occ & (ds >= 0.55) & (dm >= 1.25)
np.savez_compressed(os.path.join(HERE, "k3after.npz"), occ=occ, new=new, free=free)
print("free after K3 (cm3)", round(free.sum() * h ** 3 / 1000, 1), " free before (K3 map, removables gone)",
      round((D["interior"] & ~D["hard"] & (D["ds"] >= 0.55) & (dm >= 1.25)).sum() * h ** 3 / 1000, 1))
res = {}
for nm, dims in (("amp", (19.3, 17.8, 4.5)), ("buck", (17.8, 17.8, 10.3))):
    found = []
    for perm in set(itertools.permutations(dims)):
        dv = tuple(int(math.ceil(d / h)) for d in perm)
        for tag, F in (("any", free), ("not_on_T_stred_path", free & ~lower)):
            pos = V.box_fits(F, dv)
            for p in pos[:: max(1, len(pos) // 400)]:
                c = lo + (p + np.array(dv) / 2) * h
                found.append(dict(dims=perm, where=tag, centre=c.round(1).tolist()))
    res[nm] = found
    xs = sorted({(f["where"], tuple(f["dims"]), round(f["centre"][0] / 5) * 5, round(f["centre"][1] / 5) * 5, round(f["centre"][2] / 5) * 5) for f in found})
    print(nm, len(found), "fits; clusters (where, dims, ~x, ~y, ~z):")
    for c in xs[:60]: print("   ", c)
json.dump(res, open(os.path.join(HERE, "electronics_fit.json"), "w"))

"""STEP 1c - optimistic bound + rotation-free test.
free_opt = interior & not static voxel & not swept voxel (no extra clearance; the swept set is ~0.6 oversize and the static
set ~0.25..0.43 oversize, so this is close to the required 1.0 / 0.3 clearances but on the generous side).
Rotated placements: a box a<=b<=c can only fit if its central (b-a) x (c-a) rectangle lies in the 'core' = points whose distance
to non-free space is >= a/2.  So a core component whose largest internal distance is < hypot(b-a, c-a) proves that the box does
not fit in ANY orientation there.  Writes map3.json."""
import sys, os, json, math, time, itertools
sys.dont_write_bytecode = True
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial.distance import pdist
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voxlib as V  # noqa: E402

D = np.load(os.path.join(HERE, "map1.npz"))
lo, H = D["lo"], float(D["h"]); n = tuple(D["n"])
g = V.Grid(lo, lo + np.array(n) * H, H)
interior, static, moving, free = D["interior"], D["static"], D["moving"], D["free"]
lower, s1, amp = D["lower"], D["s1"], D["amp"]
X, Y, Z = np.meshgrid(g.axis(0), g.axis(1), g.axis(2), indexing="ij")
free_opt = interior & ~static & ~moving
out = dict(free_cons_cm3=round(float(free.sum()) * H ** 3 / 1000, 1), free_opt_cm3=round(float(free_opt.sum()) * H ** 3 / 1000, 1))
SERVOS = {"SCS0009 (23.2x12.1x21.5)": (12.1, 21.5, 23.2), "SCS0009 25.25 case": (12.1, 23.2, 25.25),
          "MG90S (22.8x12.2x22.7)": (12.2, 22.7, 22.8), "STS3032 (23.5x12.5x23)": (12.5, 23.0, 23.5), "KST X06 (20x7x16.6)": (7.0, 16.6, 20.0)}
REG = {"L_shoulder x>=20 z>=-48": (X >= 20) & (Z >= -48), "P_shoulder x<=-20 z>=-48": (X <= -20) & (Z >= -48),
       "lower torso z<-48": Z < -48, "whole torso": np.ones_like(X, bool)}
for vname, F in (("free_conservative", free), ("free_optimistic", free_opt), ("free_opt_minus_assembly", free_opt & ~lower & ~s1 & ~amp)):
    edt = ndi.distance_transform_edt(F, sampling=H)
    res = {}
    for sname, (a, b, c) in SERVOS.items():
        need = math.hypot(b - a, c - a)
        rr = {}
        for rname, RM in REG.items():
            core = (edt >= a / 2.0) & RM
            lab, nl = ndi.label(core, structure=np.ones((3, 3, 3), bool))
            best = 0.0; where = None
            for k in range(1, nl + 1):
                P = g.centres(lab == k)
                if len(P) > 4000:
                    P = P[np.random.default_rng(0).choice(len(P), 4000, replace=False)]
                dmax = float(pdist(P).max()) if len(P) > 1 else 0.0
                if dmax > best:
                    best = dmax; where = [[round(float(P[:, i].min()), 1), round(float(P[:, i].max()), 1)] for i in range(3)]
            rr[rname] = dict(core_components=int(nl), largest_core_extent_mm=round(best + H, 1), needed_mm=round(need, 1),
                             can_fit_rotated=bool(best + H >= need), core_bounds=where)
        # axis-aligned
        aa = {}
        for perm in set(itertools.permutations((a, b, c))):
            dv = [int(math.ceil(d / H)) for d in perm]
            P = V.box_fits(F, dv)
            aa["x%.1f y%.1f z%.1f" % perm] = None if not len(P) else [round(float(v), 1) for v in (g.lo + (P[len(P) // 2] + np.array(dv) / 2) * H)]
        res[sname] = dict(rotated=rr, axis_aligned=aa)
        print(vname, sname, {k: (v["largest_core_extent_mm"], v["needed_mm"]) for k, v in rr.items()}, {k: v for k, v in aa.items() if v})
    out[vname] = res
    out[vname + "_thickest_mm"] = {rname: round(2 * float(edt[RM].max()), 1) for rname, RM in REG.items()}
    print(vname, out[vname + "_thickest_mm"])
json.dump(out, open(os.path.join(HERE, "map3.json"), "w"), indent=1)
print("done")

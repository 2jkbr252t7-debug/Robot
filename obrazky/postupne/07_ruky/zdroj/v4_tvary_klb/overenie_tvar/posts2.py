"""post axis inset sweep (3.5 / 3.7 / 3.9 inside the outline): first u with >= 0.3 clearance to the moving joint parts and
the magnet-pocket back walls there (cover / inner) - same models as posts.py"""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
exec(open("/tmp/claude-0/gapwf/fin/R4/overenie_tvar/posts.py").read().split("OUT = {}")[0])
OUT = {}
for vid in ["B0", "B1", "B2", "B3"]:
    S, lab, U = AS.cloud(vid, 0.06, 0.3, 0.55)
    trees = {1: cKDTree(S[lab >= 1]), -1: cKDTree(S[lab != 1])}
    for ins_ in (3.5, 3.7, 3.9):
        best = None
        for u in np.round(np.arange(0.36, 0.50, 0.005), 3):
            c, ti, to, wi, wo, ni, no = [float(np.ravel(v)[0]) for v in AS.secf(vid, np.array([u]))]
            z = -72 * u; clear = 1e9; back = {}
            for side in (1, -1):
                wh = min(wi, wo)                    # common (coaxial) magnet axis at the narrower half
                yax = wh - ins_
                post = cyl(c, side, yax, z, 2.2, 0.25, 2.65)
                W = VB.to_world(post, vid); X = np.c_[W[:, 0], np.hypot(W[:, 1] - YA, W[:, 2] - ZA)]
                for p in mov:
                    clear = min(clear, float(sd2(X, p.outline_xr()).min()))
                pocket = cyl(c, side, yax, z, 1.6, 0.25, 2.35)
                d, _ = trees[side].query(pocket)
                back[side] = float(np.where(VB.inside_local(vid, pocket), d, -d).min())
            if clear >= 0.3:
                best = dict(u=float(u), clear=round(clear, 3), back_cover=round(back[1], 3), back_inner=round(back[-1], 3)); break
        OUT[f"{vid} inset {ins_}"] = best
        print(vid, ins_, best, flush=True)
json.dump(OUT, open("out/posts2.json", "w"), indent=1)

import sys, os, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.ndimage import map_coordinates
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
SIDE = os.environ.get("SIDE", "L"); sys.argv = [sys.argv[0], SIDE, sys.argv[1], "1", "3.0"] + sys.argv[2:]
xs, th, zt = float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])
exec(open(os.path.join(HERE, "fit_vert.py")).read().split("res = []")[0])
D2 = np.load(os.path.join(HERE, "k3map.npz")); hard = D2["hard"]; lab = D2["lab"]; ln = [str(s) for s in D2["lab_names"]]; cat = D2["cat"]
c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
Q = np.c_[xs + c * P0[:, 0] - s * P0[:, 1], ys + s * P0[:, 0] + c * P0[:, 1], zt + P0[:, 2]]
I = ((Q - lo) / h - 0.5).T
a = map_coordinates(ds, I, order=1, mode="nearest") - 0.55; b = map_coordinates(dm, I, order=1, mode="nearest") - 1.25
for nm, v in (("hard", a), ("move", b)):
    k = np.argsort(v)[:6]
    for kk in k:
        q = Q[kk]
        # nearest hard voxel label
        ii = np.floor((q - lo) / h).astype(int); R = 6
        sub = hard[ii[0]-R:ii[0]+R+1, ii[1]-R:ii[1]+R+1, ii[2]-R:ii[2]+R+1]
        idx = np.argwhere(sub)
        if len(idx):
            d = np.linalg.norm((idx - R) * h, axis=1); j = idx[np.argmin(d)] + ii - R
            L = ln[lab[tuple(j)]] if lab[tuple(j)] else ("wall/feature cat %d" % cat[tuple(j)] if cat[tuple(j)] in (3, 9) else "outside")
        else: L = "-"
        print(nm, "%.2f" % v[kk], np.round(q, 1), L)

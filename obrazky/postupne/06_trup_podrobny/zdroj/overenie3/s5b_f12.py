import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
scr = load_stl(f"{T4}/stl/skr_F12_1.stl"); v = scr.reshape(-1, 3)
print("skr_F12_1: y", v[:, 1].min(), v[:, 1].max(), " axis x", (v[:, 0].min() + v[:, 0].max()) / 2, "z", (v[:, 2].min() + v[:, 2].max()) / 2)
for y0, y1 in ((5.4, 11.3), (11.45, 12.7)):
    m = (v[:, 1] >= y0) & (v[:, 1] <= y1); r = np.hypot(v[m, 0] + 10.0, v[m, 2] + 38.5); print(f"   y {y0}..{y1}: r max {r.max():.3f}")
S = sample_surface(scr, 0.2, thin=0.8)
for d in ('stl', 'rev3_backup/stl'):
    M = part('P_drziak_serva', d, 0.2); U = part('L_ucho', d, 0.2)
    free = []
    for t in np.arange(0, 30.01, 0.25):
        Q = S + np.array([0, t, 0]); ins = M.inside(Q) | U.inside(Q)
        free.append((t, int(ins.sum())))
    blocked = [t for t, n in free if n > 0]
    print(d, ": screw translated +y: blocked (inside P_drziak_serva / L_ucho) for t in", (min(blocked), max(blocked)) if blocked else None)
    # free space directly behind the seated head: along the axis x -10, z -38.5, y from 12.7
    ys = np.arange(12.75, 45, 0.05); ax = np.stack([np.full(len(ys), -10.0), ys, np.full(len(ys), -38.5)], 1)
    dd, _ = M.dist(ax, dmax=6.0); ins = M.inside(ax)
    for rr in (0.7, 1.25, 1.85):
        ok = (dd > rr) & ~ins
        segs = []; on = False
        for i, f in enumerate(ok):
            if f and not on: s = ys[i]; on = True
            if on and (not f or i == len(ok) - 1): segs.append((round(float(s), 2), round(float(ys[i]), 2))); on = False
        print(f"   {d}: y ranges on the F12 axis where a cylinder of r {rr} is free of P_drziak_serva: {segs}")

import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
names = sys.argv[1:]
for n in names:
    a = part(n, 'stl', 0.3); b = part(n, 'rev3_backup/stl', 0.3)
    for lab, s, o in (("new surface not on old", a, b), ("old surface not on new", b, a)):
        d, _ = o.dist(s.samp, k=4)
        m = d > 0.03
        print(f"{n}: {lab}: {m.sum()} / {len(d)} samples, max move {d.max():.3f}")
        if m.sum() == 0: continue
        P = s.samp[m]; dd = d[m]
        # cluster coarse: 6 mm voxel boxes merged by z-bands
        from scipy.cluster.hierarchy import fcluster, linkage
        if len(P) > 4000:
            sel = np.random.default_rng(0).choice(len(P), 4000, replace=False); Pc = P[sel]; dc = dd[sel]
        else: Pc = P; dc = dd
        if len(Pc) > 1:
            Z = linkage(Pc, 'single'); cl = fcluster(Z, 1.5, 'distance')
        else: cl = np.array([1])
        out = []
        for c in np.unique(cl):
            q = Pc[cl == c]
            out.append((len(q), q.min(0), q.max(0), dc[cl == c].max()))
        out.sort(key=lambda t: -t[0])
        for k, lo, hi, mx in out[:14]:
            print(f"   n {k:5d}  x {lo[0]:7.2f}..{hi[0]:7.2f}  y {lo[1]:7.2f}..{hi[1]:7.2f}  z {lo[2]:7.2f}..{hi[2]:7.2f}  max move {mx:.2f}")

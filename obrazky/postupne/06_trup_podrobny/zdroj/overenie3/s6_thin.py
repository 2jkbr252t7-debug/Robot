# thin walls / knife edges: surface sample p with outward normal n; if p - t*n is OUTSIDE the solid the material is thinner than t along the normal
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
from scipy.cluster.hierarchy import fcluster, linkage
def flagged(d, name, t):
    M = part(name, d, 0.2)
    P, I = sample_surface(M.tr, 0.15, True, thin=0.8)
    tr = M.tr[I]; n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]); ln = np.linalg.norm(n, axis=1); ok = ln > 1e-9
    P = P[ok]; n = n[ok] / ln[ok, None]
    out = ~M.inside(P - n * t) & M.inside(P - n * 0.02)        # the second term drops samples sitting on degenerate edges
    return P[out], n[out]
for name in sys.argv[1:]:
    for t in (0.4, 0.8):
        Pn, Nn = flagged('stl', name, t); Po, _ = flagged('rev3_backup/stl', name, t)
        print(f"\n{name}: thinner than {t} along the normal: {len(Pn)} samples (rev. 2: {len(Po)})")
        if len(Pn) == 0: continue
        if len(Po):
            do, _ = cKDTree(Po).query(Pn); new = do > 0.6
        else: new = np.ones(len(Pn), bool)
        Q = Pn[new]
        print(f"   not present in rev. 2 (no rev. 2 thin sample within 0.6): {len(Q)}")
        if len(Q) < 2: continue
        if len(Q) > 6000: Q = Q[np.random.default_rng(0).choice(len(Q), 6000, replace=False)]
        cl = fcluster(linkage(Q, 'single'), 0.8, 'distance')
        rows = []
        for c in np.unique(cl):
            q = Q[cl == c]
            if len(q) < 4: continue
            rows.append((len(q), q.min(0), q.max(0)))
        rows.sort(key=lambda r: -r[0])
        for k, lo, hi in rows[:22]:
            print(f"     n {k:5d}  x {lo[0]:7.2f}..{hi[0]:7.2f}  y {lo[1]:7.2f}..{hi[1]:7.2f}  z {lo[2]:7.2f}..{hi[2]:7.2f}")

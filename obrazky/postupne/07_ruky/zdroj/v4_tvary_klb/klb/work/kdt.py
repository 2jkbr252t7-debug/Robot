import sys, time, math, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA
from scipy.spatial import cKDTree
for h in (0.15, 0.3):
    rows, top, bot = VA.pebble_rows("B", int(2.2 * VA.L / h), int(2 * math.pi * 17.5 / h))
    P = np.concatenate([rows.reshape(-1, 3), [top, bot]])
    t = time.time(); T = cKDTree(P); t1 = time.time() - t
    Q = P[np.random.default_rng(0).integers(0, len(P), 100000)] + np.random.default_rng(1).normal(0, 3, (100000, 3))
    for ub in (12.0, 5.0):
        t = time.time(); T.query(Q, distance_upper_bound=ub); print(h, len(P), "build", round(t1, 2), "ub", ub, "query 100k", round(time.time() - t, 2))
    t = time.time(); T.query(Q, distance_upper_bound=5.0, workers=2); print("workers2", round(time.time() - t, 2))
    t = time.time(); T2 = cKDTree(P, balanced_tree=False, compact_nodes=False); T2.query(Q, distance_upper_bound=5.0); print("unbalanced", round(time.time() - t, 2))

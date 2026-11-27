"""C5: right side = mirror?  Compare T_bok_P / T_klb_P / T_stred near the right shoulder with the left side mirrored."""
import sys, os, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
from scipy.spatial import cKDTree
import mio
MOD = "/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod"; T4 = "/tmp/claude-0/gapwf/fin/T4/stl"
OUT = {}
def near(P, side):
    Pm = P.copy(); Pm[:, 0] *= side
    r = np.hypot(Pm[:, 1] - 3, Pm[:, 2] + 17)
    return (r < 30) & (Pm[:, 0] > 38)
for L, Rr, d in (("T_bok_L", "T_bok_P", MOD), ("T_klb_L", "T_klb_P", T4)):
    A = mio.sample(mio.load(os.path.join(d, L + ".stl")), 0.15)
    B = mio.sample(mio.load(os.path.join(d, Rr + ".stl")), 0.15)
    A = A[near(A, 1)]; B = B[near(B, -1)]
    Bm = B.copy(); Bm[:, 0] *= -1
    if len(A) == 0 or len(B) == 0:
        print(L, Rr, "no points near the shoulder", len(A), len(B)); continue
    d1, _ = cKDTree(A).query(Bm); d2, _ = cKDTree(Bm).query(A)
    OUT[Rr] = dict(n=(len(A), len(B)), max_dev_R_to_L=round(float(d1.max()), 3), p99=round(float(np.percentile(d1, 99)), 3),
                   max_dev_L_to_R=round(float(d2.max()), 3))
    k = int(np.argmax(d1)); OUT[Rr]["worst_R_pt"] = B[k].round(2).tolist()
    print(Rr, OUT[Rr])
# other torso parts within 30 mm of either shoulder axis outboard of |x| 38
for nm in ("T_stred", "T_dvere", "T_spodok", "T_paluba", "T_most", "T_mriezka", "T_svetlovod", "T_cap"):
    p = os.path.join(MOD, nm + ".stl")
    if not os.path.exists(p):
        p = os.path.join(T4, nm + ".stl")
    P = mio.load(p).reshape(-1, 3)
    nl = int(near(P, 1).sum()); nr = int(near(P, -1).sum())
    print(f"{nm:12s} vertices near left shoulder {nl:6d} right {nr:6d}  x range {P[:,0].min():.1f}..{P[:,0].max():.1f}")
    OUT[nm + "_near"] = (nl, nr)
json.dump(OUT, open(os.path.join(HERE, "c5_mirror.json"), "w"), indent=1)

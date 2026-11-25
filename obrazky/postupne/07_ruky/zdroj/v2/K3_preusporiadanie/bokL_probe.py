import sys, os
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as V
sys.path.insert(0, V.T4); os.chdir(V.T4)
import t4_common as C
P = V.vlib.sample_surface(V.load("T_bok_L"), 0.3)
ins = C.dist_outer(P)
ra = np.hypot(P[:, 1] - 3, P[:, 2] + 17)
feat = ins > 2.45
print("T_bok_L x range", P[:, 0].min(), P[:, 0].max())
F = P[feat]; rf = ra[feat]
for r0 in range(0, 30, 2):
    m = (rf >= r0) & (rf < r0 + 2)
    if m.any(): print("feature r %2d..%2d  x %.2f..%.2f  n %d" % (r0, r0 + 2, F[m, 0].min(), F[m, 0].max(), m.sum()))
W = P[~feat]; rw = ra[~feat]
for r0 in range(10, 20, 1):
    m = (rw >= r0) & (rw < r0 + 1)
    if m.any(): print("wall r %2d  x %.2f..%.2f" % (r0, W[m, 0].min(), W[m, 0].max()))

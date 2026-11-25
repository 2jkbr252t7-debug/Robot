import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3"); import vlib
tr = vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_stred.stl")
P = tr.reshape(-1, 3)
# inward-most extent of T_stred in the front-left quadrant: for x bins, max y (least negative) of points with y<0, z < -40
for xb in range(14, 34, 2):
    m = (P[:, 0] >= xb) & (P[:, 0] < xb + 2) & (P[:, 1] < -5) & (P[:, 2] < -40)
    if m.any():
        Q = P[m]; i = np.argmax(Q[:, 1])
        print(f"x {xb}-{xb+2}: max y {Q[i,1]:.2f} at z {Q[i,2]:.2f}; z range {Q[:,2].min():.1f}..{Q[:,2].max():.1f}")
lo = np.load("/tmp/claude-0/gapwf/fin/R1/trup_servo/map1.npz")

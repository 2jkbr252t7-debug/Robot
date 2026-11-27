import numpy as np, sys
sys.path.insert(0, ".")
import stlu
T = stlu.load("/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod/T_bok_L.stl")
print("T_bok_L tris", len(T), T.reshape(-1,3).min(0), T.reshape(-1,3).max(0))
P = stlu.sample(T, 0.15)
r = np.hypot(P[:,1]-3, P[:,2]+17)
m = (r < 18) & (P[:,0] > 36)
Q = P[m]; rq = r[m]
print("near-axis points", len(Q))
# (x,r) profile: for r bins, x range
for r0 in np.arange(10, 18, 0.5):
    k = (rq >= r0) & (rq < r0 + 0.5)
    if k.any():
        az = np.degrees(np.arctan2(Q[k,2]+17, Q[k,1]-3)) % 360
        # max x per az quadrant
        s = []
        for a0 in (0, 90, 180, 270):
            kk = np.abs(((az - a0 + 180) % 360) - 180) < 20
            s.append(f"{Q[k][kk,0].max():.2f}" if kk.any() else "  -  ")
        print(f"r {r0:4.1f}-{r0+0.5:4.1f}: n {k.sum():6d} x {Q[k,0].min():.2f}..{Q[k,0].max():.2f}  max x @az0/90/180/270: {s}")
Z = stlu.load("/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl/zatka.stl")
PZ = stlu.sample(Z, 0.15); rz = np.hypot(PZ[:,1]-3, PZ[:,2]+17)
print("zatka bbox", PZ.min(0).round(2), PZ.max(0).round(2))
for r0 in np.arange(0, 14, 1.0):
    k = (rz >= r0) & (rz < r0 + 1)
    print(f"zatka r {r0:4.1f}: x {PZ[k,0].min():.2f}..{PZ[k,0].max():.2f}")

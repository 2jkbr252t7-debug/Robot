"""VERIFIER: arm gap of the arm pebble (armgeo placement, dx -1.0) against the REAL side-cap mesh (T4 T_bok_L / mirrored T_bok_P)
plus the recessed plug face disc (analytic x_surface - 1.0, r <= 13.5) - judge used the analytic torso surface for both.
Angles -45..+142.  Also sensitivity to an axial shift of the arm (stack tolerance) and to an arm tilt (seat-fit play)."""
import sys, json, math, time
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
from armgeo import sdf_world, swing
import t4_common as C
import vlib
t0 = time.time()
out = {}
ys = np.arange(3 - 13.6, 3 + 13.6, 0.15); zs = np.arange(-17 - 13.6, -17 + 13.6, 0.15)
Y, Z = np.meshgrid(ys, zs, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
m = np.hypot(Y - 3, Z + 17) <= 13.5
disc = np.c_[[C.x_surface(y, z) - 1.0 for y, z in zip(Y[m], Z[m])], Y[m], Z[m]]
for side in ("L", "R"):
    tr = vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/%s.stl" % ("T_bok_L" if side == "L" else "T_bok_P"))
    S = vlib.sample_surface(tr, 0.15)
    if side == "R": S[:, 0] *= -1
    r_ax = np.hypot(S[:, 1] - 3, S[:, 2] + 17)
    S = S[(S[:, 0] > 44.0) & (r_ax < 45) & (r_ax >= 13.9)]
    P = np.r_[S, disc]
    lab = np.r_[np.zeros(len(S), int), np.ones(len(disc), int)]
    res = {}
    for a in [-45, -30, 0, 60, 90, 110, 120, 125, 130, 132, 134, 135, 137, 139, 140.5, 142]:
        d = sdf_world(swing(P, -a), dx=-1.0)
        k = int(np.argmin(d))
        res[str(a)] = dict(gap=round(float(d[k]), 3), at=P[k].round(2).tolist(), what="disc" if lab[k] else "cap")
    out[side] = res
    print(side, {a: v["gap"] for a, v in res.items()}, f"{time.time()-t0:.0f}s", flush=True)
json.dump(out, open("v_gap.json", "w"), indent=1)

"""targeted re-check after the two fixes from hub_b1.py (lip moved to x 66.4..67.6, seat bore D5.0)"""
import sys, json, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import sdf_world
import geo_b1 as B
P = B.arm_side(h=0.15)
out = {}
for a, b in (("DRV_disc", "ARM_lip"), ("DRV_screw_shank", "PLG_seat"), ("DRV_boss", "PLG_seat"), ("DRV_disc", "ARM_wall")):
    d, _ = cKDTree(P[b]).query(P[a], distance_upper_bound=3); out[f"{a} vs {b}"] = round(float(d.min()), 2)
for k in ("ARM_lip", "ARM_wall"):
    v = P[k]; v = v[np.hypot(v[:, 1] - 3, v[:, 2] + 17) > 9.0]          # outer region decides the wall
    out[f"room {k} wall left"] = round(float(-sdf_world(v, dx=-1.0).max()), 2)
print(out); json.dump(out, open("hub_fix.json", "w"), indent=1)

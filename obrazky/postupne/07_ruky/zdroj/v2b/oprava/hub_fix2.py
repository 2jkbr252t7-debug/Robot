"""FIXER: room check of the squeezed 6800ZZ arm hub (outer stack kept within x <= 67.55): 6800 x 55.3..60.3 (bore r 9.5, wall to 10.7),
flange 0.8 (60.4..61.2), washer 61.2..63.2, drive-hub disc 3.05 (63.2..66.25), lip ring 0.8 (66.75..67.55), wall r 11.5..12.7 to 67.55,
rib root ring A r 7.5..8.9 x 53..55, bearing-back ring B r 7.5..10.7 x 54.5..55.3.  Criterion wall_left >= 1.2 (as hub_b1.py)."""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/vyber")
from armgeo import sdf_world
import geo as G
def T(ri, ro, x0, x1, h=0.25): return G.tube("x", 3.0, -17.0, ri, ro, x0, x1, h=h)
parts = dict(ringA=T(7.5, 8.9, 53.0, 55.0), ringB=T(7.5, 10.7, 54.5, 55.3), bore_wall=T(9.5, 10.7, 55.3, 61.2), flange=T(5.0, 12.7, 60.4, 61.2),
             washer=T(5.25, 10.0, 61.2, 63.2), disc=T(0.0, 11.0, 63.2, 66.25), lip=T(4.0, 12.7, 66.75, 67.55), wall=T(11.5, 12.7, 61.2, 67.55),
             rib_tip=T(5.5, 7.5, 53.0, 55.0))
out = {}
for k, P in parts.items():
    d = sdf_world(P, dx=-1.0); i = int(np.argmax(d))
    out[k] = dict(wall_left=round(float(-d.max()), 2), at=[round(float(q), 2) for q in P[i]], ok=bool(-d.max() >= 1.2))
    print(k, out[k], flush=True)
json.dump(out, open("hub_fix2.json", "w"), indent=1)

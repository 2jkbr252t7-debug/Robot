"""FIXER: room inside the arm pebble (armgeo.sdf_world, dx -1.0) for arm-hub variants replacing the 6700ZZ.
wall_left = distance from the part to the pebble OUTER surface (criterion >= 1.2 as hub_b1.py).  Static parts are not checked here
(they do not change); only the arm-side parts whose size or x position changes."""
import sys, json, math
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/vyber")
from armgeo import sdf_world
import geo as G
YA, ZA, DX = 3.0, -17.0, -1.0
def T(ri, ro, x0, x1, h=0.2): return G.tube("x", YA, ZA, ri, ro, x0, x1, h=h)
def room(name, P):
    d = sdf_world(P, dx=DX); i = int(np.argmax(d))
    return dict(wall_left=round(float(-d.max()), 2), at=[round(float(q), 2) for q in P[i]], ok=bool(-d.max() >= 1.2))
V = {}
# B1+ reference (6700, as judged)
V["B1plus_6700"] = dict(bore_wall=T(7.5, 8.7, 55.5, 60.6), flange=T(6.5, 12.7, 59.6, 60.6), washer=T(5.25, 10.0, 60.6, 62.6),
                        wall=T(11.5, 12.7, 60.6, 67.6), lip=T(4.0, 12.0, 66.4, 67.6), disc=T(0.0, 11.0, 62.6, 65.9))
# 6800ZZ 10x19x5 at x 55.3..60.3, outer stack +0.8 (flange 60.4..61.4)
for wall_t in (1.2, 0.8):
    s = 0.8
    V[f"6800_wall{wall_t}"] = dict(bore_wall=T(9.5, 9.5 + wall_t, 55.3, 61.4), inboard_web=T(7.1, 9.5 + wall_t, 53.0, 55.3),
                                   flange=T(5.0, 12.7, 59.6 + s, 60.6 + s), washer=T(5.25, 10.0, 60.6 + s, 62.6 + s),
                                   wall=T(11.5, 12.7, 60.6 + s, 67.6 + s), lip=T(4.0, 12.0, 66.4 + s, 67.6 + s), disc=T(0.0, 11.0, 62.6 + s, 65.9 + s))
# 688ZZ 8x16x5 would need a D8 seat over A2 (OD 7): wall 0.5 -> rejected without a room check
# printed journal (no bearing): hub bore D10.1 on the seat, hub wall r 5.05..7.5, x 55.5..60.6 (same outer stack as B1+)
V["journal"] = dict(bore_wall=T(5.05, 7.5, 55.5, 60.6))
out = {}
for k, parts in V.items():
    out[k] = {p: room(p, P) for p, P in parts.items()}
    print(k, json.dumps(out[k]), flush=True)
json.dump(out, open("hub_fix.json", "w"), indent=1)

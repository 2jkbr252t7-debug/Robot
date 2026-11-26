"""JUDGE fix: two-sided homing stop for B1 (rib in the arm hub vs a widened lug sector on the plug seat).
Rib as in B1 (x 53..55, r 5.5..8.5, width 4.0/7.0 rad); lug x 52.5..55.0, r 5.0..6.6, near edge unchanged (contact at -51),
far edge extended so that the rib meets it at +140.5.  Point models (geo_b1.sector), swing from armgeo."""
import sys, math, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R2c/vyber/B1c")
from armgeo import swing
import geo_b1 as B
W_RIB = 4.0 / 7.0
W_LUG0 = 4.5 / 5.8
LUG_AZ0 = 270.0
RIB_AZ0 = LUG_AZ0 - math.degrees(W_LUG0 / 2 + W_RIB / 2) - 51.0
near = LUG_AZ0 - math.degrees(W_LUG0 / 2)                     # 247.8
TOP = float(sys.argv[1]) if len(sys.argv) > 1 else 140.5
far = (RIB_AZ0 - TOP) - math.degrees(W_RIB / 2) + 360.0       # rib lower edge at TOP
W = math.radians(far - near)
lug = B.sector(5.0, 6.6, 52.5, 55.0, (near + far) / 2, W, 0.1)
rib = B.sector(5.5, 8.5, 53.0, 55.0, RIB_AZ0, W_RIB, 0.1)
tr = cKDTree(lug)
res = dict(top=TOP, lug_edges_deg=[round(near, 1), round(far, 1)], lug_width_deg=round(far - near, 1), rib_rest_az=round(RIB_AZ0, 1))
for a in (-52.0, -51.0, -45.0, 0.0, 60.0, 120.0, 130.0, 135.0, 139.0, 140.5, 141.5):
    d, _ = tr.query(swing(rib, a))
    res[f"gap_at_{a:+.1f}"] = round(float(d.min()), 3)
# sampled minimum over the working range -45..+135
m = min(float(tr.query(swing(rib, a))[0].min()) for a in np.arange(-45.0, 135.01, 1.0))
res["min_gap_working_range"] = round(m, 3)
print(json.dumps(res, indent=1))
json.dump(res, open("/tmp/claude-0/gapwf/fin/R2c/vyber/lug2_%s.json" % TOP, "w"), indent=1)

"""FIXER: wide two-sided hidden stop.  Rib (arm hub) x 53.0..55.0, r 5.5..7.0, 90 deg wide; lug (plug seat) x 52.5..55.0, r 5.0..7.0,
width 360 - 90 - (TOP - BOT); contacts at BOT (-51) and TOP (argv[1], default 135.5).  Working range -45..WR (argv[2], default 130).
Point models (geo_b1.sector, 0.1 mm), swing from armgeo (same conventions as the judge's lug2.py)."""
import sys, math, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R2c/vyber/B1c")
from armgeo import swing
import geo_b1 as B
TOP = float(sys.argv[1]) if len(sys.argv) > 1 else 135.5
WR = float(sys.argv[2]) if len(sys.argv) > 2 else 130.0
BOT = -51.0
W_RIB = 90.0
W_LUG = 360.0 - W_RIB - (TOP - BOT)
RIB_AZ0 = 180.0
near = RIB_AZ0 - BOT + W_RIB / 2                   # lug edge met by the rib's upper edge at BOT
far = near + W_LUG
lug = B.sector(5.0, 7.0, 52.5, 54.8, (near + far) / 2, math.radians(W_LUG), 0.1)
rib = B.sector(5.5, 7.0, 53.0, 55.0, RIB_AZ0, math.radians(W_RIB), 0.1)
tr = cKDTree(lug)
res = dict(top=TOP, bot=BOT, working_range=[-45.0, WR], rib_rest_az=[RIB_AZ0 - W_RIB / 2, RIB_AZ0 + W_RIB / 2], rib_width_deg=W_RIB,
           lug_edges_deg=[round(near, 2), round(far, 2)], lug_width_deg=round(W_LUG, 2),
           contact_face=dict(r=[5.5, 7.0], x=[53.0, 54.8], area_mm2=2.7, r_centroid=6.25))
for a in (BOT - 1, BOT, -45.0, 0.0, 60.0, 120.0, WR, 132.0, 134.0, TOP, TOP + 1):
    d, _ = tr.query(swing(rib, a))
    res[f"gap_at_{a:+.1f}"] = round(float(d.min()), 3)
res["min_gap_working_range"] = round(min(float(tr.query(swing(rib, a))[0].min()) for a in np.arange(-45.0, WR + 0.01, 1.0)), 3)
# stop loads: tip push F at 53.75 mm -> contact force at r 6.25 over 3.0 mm2
res["stop_bearing_MPa"] = {f"tip {F} N": round(F * 53.75 / 6.25 / 2.7, 1) for F in (1, 3, 5, 7, 10)}
res["stop_bearing_MPa"]["homing at clutch 0.0115 N.m"] = round(11.3 / 6.25 / 2.7, 2)
# rib bending as a cantilever from its root (r 7.0..7.5 web): load at the face centroid, lever ~ (7.0-6.25)+0.5 = 1.25 mm, section = arc length
for F in (3, 7, 10):
    Fc = F * 53.75 / 6.25
    arc = math.radians(W_RIB) * 7.0
    res.setdefault("rib_root_bending_MPa", {})[f"tip {F} N"] = round(6 * Fc * 1.25 / (2.0 * arc ** 2) * 0 + Fc / (2.0 * arc), 2)  # shear-dominated: report shear
print(json.dumps(res, indent=1))
json.dump(res, open("lug3_%s.json" % TOP, "w"), indent=1)

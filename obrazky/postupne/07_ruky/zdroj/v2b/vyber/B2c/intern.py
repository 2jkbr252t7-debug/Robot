"""B2: clearances BETWEEN the new parts themselves (chk.py only checks new parts against the kept T4 parts and the sweep).
Rule: >= 0.5 between an own moving part and its neighbours (bearing / journal contacts excepted and listed as fits).
Boss modelled as the real B2 boss: solid r <= 12.8 (x 34.4..38.4) + stop ring r 11.6..12.8 (x 38.4..39.1), minus
  pinion slot |y-3| <= 5.1 for z >= -24.55 (x >= 34.4, open to +X) and shaft slot |y-3| <= 2.5 for x >= 36.5, z -30.0..-24.55.
Also the LIFTED pinion-shaft (service / insertion, +4.2 mm) against the static B2 parts.
writes intern.json"""
import json, os, sys
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geo_b2 as GB

P, bv = GB.parts()
YA, ZA = 3.0, -17.0


def boss_b2(h=0.25):
    B = GB.box(34.4, 39.1, YA - 12.8, YA + 12.8, ZA - 12.8, ZA + 12.8, h)
    r = np.hypot(B[:, 1] - YA, B[:, 2] - ZA)
    keep = ((B[:, 0] <= 38.4) & (r <= 12.8)) | ((B[:, 0] > 38.4) & (r >= 11.6) & (r <= 12.8))
    B = B[keep]
    slot1 = (np.abs(B[:, 1] - YA) <= 5.1) & (B[:, 2] >= -24.55)
    slot2 = (np.abs(B[:, 1] - YA) <= 2.5) & (B[:, 0] >= 36.5) & (B[:, 2] >= -30.0) & (B[:, 2] <= -24.55)
    return B[~(slot1 | slot2)]


S = {k: v for k, v in P.items() if k.startswith("STAT") or k.startswith("SERVO")}
S["STAT_boss"] = boss_b2()
# plug cavity wall (r 6.8 about the shoulder axis, x 38.0..44.31) and ring bore (r 4.05, x 44.31..61) as static surfaces
th = np.linspace(0, 2 * np.pi, 360, endpoint=False)
xs = np.arange(38.0, 44.31, 0.1)
cav = np.array([(x, YA + 6.8 * np.cos(t), ZA + 6.8 * np.sin(t)) for x in xs for t in th])
cav = cav[~((np.abs(cav[:, 1] - YA) <= 5.1) & (cav[:, 2] < ZA) & (cav[:, 0] < 44.0))]     # 6 o'clock slot of the plug
wall = np.array([(44.31, YA + r * np.cos(t), ZA + r * np.sin(t)) for r in np.arange(4.05, 6.8, 0.1) for t in th])
S["PLUG_cavity"] = np.r_[cav, wall]
R = {k: v for k, v in P.items() if k.startswith("ROT")}
FITS = {("ROT_V_shaft", "STAT_insert"): "journal D4.0 in D4.1 (fit)", ("ROT_V_collar", "STAT_insert"): "thrust face (fit)",
        ("ROT_V_coupler", "SERVO"): "printed spline on the servo spline (fit)", ("ROT_A_spindle", "PLUG_cavity"): "journal / thrust (fit)",
        ("ROT_A_gear", "PLUG_cavity"): "gear back on the cavity end wall (thrust, fit)"}
out = {"final": {}, "lifted": {}}
trees = {k: cKDTree(v) for k, v in S.items()}
for rn, rp in R.items():
    for sn, tr in trees.items():
        d, j = tr.query(rp, distance_upper_bound=3.0)
        k = int(np.argmin(d))
        if d[k] > 3.0:
            continue
        key = f"{rn} | {sn}"
        out["final"][key] = dict(min=round(float(d[k]), 2), at=rp[k].round(2).tolist(), fit=FITS.get((rn, sn)))
        print("final ", key, out["final"][key])
# rotating parts among themselves (pinion vs gear = mesh; others)
for a in ("ROT_V_coupler", "ROT_V_shaft", "ROT_V_collar"):
    d, _ = cKDTree(R["ROT_A_gear"]).query(R[a])
    out["final"][f"{a} | ROT_A_gear"] = dict(min=round(float(d.min()), 2))
    print("final ", a, "| ROT_A_gear", round(float(d.min()), 2))
lift = GB.B2["lift"]
for rn in ("ROT_V_coupler", "ROT_V_shaft", "ROT_V_collar", "ROT_V_pinion"):
    rp = GB.lifted(R[rn], lift)
    for sn in ("STAT_boss", "STAT_tongue", "STAT_leg_back_ext", "STAT_strut", "SERVO"):
        d, _ = trees[sn].query(rp, distance_upper_bound=3.0)
        k = int(np.argmin(d))
        if d[k] > 3.0:
            continue
        out["lifted"][f"{rn} | {sn}"] = dict(min=round(float(d[k]), 2), at=rp[k].round(2).tolist())
        print("lifted", rn, sn, out["lifted"][f"{rn} | {sn}"])
json.dump(out, open(os.path.join(HERE, "intern.json"), "w"), indent=1)

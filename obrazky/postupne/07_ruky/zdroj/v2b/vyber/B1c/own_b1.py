"""B1: clearances between the drive's OWN moving parts and the new static parts around them (chk.py only checks new parts
against the kept T4 parts and the pan/lift sweep).  Rule: >= 0.5 mm between own moving parts and their neighbours, except
designed contacts (pinion/shim/MR63 inner race, gear/shim/A1 inner race, bearings in their seats, servo spline/horn).
Static: boss (r 12.8, x 34.4..38.4, 6 o'clock slot |y-3| <= 5.3 from z -24.55 to -15.5, D4 shaft hole), tongue ring
r 3.0..4.4 (z -26.85..-24.05) + MR63 outer race, plug cavity (r 6.9, x 38.6..44.54, slot |y-3| <= 5.3 below the axis for
x < 44.0), cavity end face x 44.54 (r 3.5..6.9), pocket column (legs, strut, web, pad), servo case.
Moving: pinion 12T, vertical shaft, coupler, gear 18T, M4x20 shank + tip.
Left side (right = mirror, same numbers).  Writes own_b1.json"""
import json, math
import numpy as np
from scipy.spatial import cKDTree
import geo as G, geo_b1 as B, variants

YA, ZA = 3.0, -17.0
h = 0.15
p, ex = variants.get("B1")
P, _ = G.parts(p); P.update(ex(p))


def keep(Q, f):
    return Q[f(Q)]


# --- static surfaces (surface samples are enough for distances from outside)
th = np.linspace(0, 2 * np.pi, 720, endpoint=False)
S = {}
# boss: end face x 38.4 (r <= 11.6 inside the stop ring) minus slot and shaft hole
R_, T_ = np.meshgrid(np.arange(0.0, 11.6, h), th, indexing="ij")
face = np.c_[np.full(R_.size, 38.4), YA + (R_ * np.cos(T_)).ravel(), ZA + (R_ * np.sin(T_)).ravel()]
inslot = (np.abs(face[:, 1] - YA) <= 5.3) & (face[:, 2] >= -24.55) & (face[:, 2] <= -15.5)
inhole = (np.hypot(face[:, 0] - 39.0, face[:, 1] - YA) < 2.0) & (face[:, 2] < -24.55)
S["boss_face"] = face[~inslot & ~inhole]
# boss slot walls (inside the boss, x 34.4..38.4) : planes y = 3 +- 5.3 and the slot roof z -15.5
xs = np.arange(34.4, 38.41, h); zs = np.arange(-24.55, -15.49, h); ys = np.arange(YA - 5.3, YA + 5.31, h)
X, Z = np.meshgrid(xs, zs, indexing="ij")
S["boss_slot_walls"] = np.concatenate([np.c_[X.ravel(), np.full(X.size, YA - 5.3), Z.ravel()],
                                       np.c_[X.ravel(), np.full(X.size, YA + 5.3), Z.ravel()],
                                       np.array([(x, y, -15.5) for x in xs for y in ys])])
# plug cavity cylinder r 6.9 (x 38.6..44.54) without the slot, and its end face
Xc, Tc = np.meshgrid(np.arange(38.6, 44.54, h), th, indexing="ij")
cyl = np.c_[Xc.ravel(), YA + 6.9 * np.cos(Tc.ravel()), ZA + 6.9 * np.sin(Tc.ravel())]
cyl = cyl[~((np.abs(cyl[:, 1] - YA) <= 5.3) & (cyl[:, 2] < ZA) & (cyl[:, 0] < 44.0))]
S["plug_cavity"] = cyl
R2, T2 = np.meshgrid(np.arange(3.5, 6.9, h), th, indexing="ij")
S["plug_cavity_end"] = np.c_[np.full(R2.size, 44.54), YA + (R2 * np.cos(T2)).ravel(), ZA + (R2 * np.sin(T2)).ravel()]
# plug slot walls (x 38.6..44.0, y = 3 +- 5.3, from the cavity r 6.9 down to r 13.5 below the axis)
xs2 = np.arange(38.6, 44.01, h); zs2 = np.arange(ZA - 13.5, ZA - math.sqrt(6.9 ** 2 - 5.3 ** 2), h)   # wall starts at the cavity
X2, Z2 = np.meshgrid(xs2, zs2, indexing="ij")
S["plug_slot_walls"] = np.concatenate([np.c_[X2.ravel(), np.full(X2.size, YA - 5.3), Z2.ravel()],
                                       np.c_[X2.ravel(), np.full(X2.size, YA + 5.3), Z2.ravel()]])
S["tongue"] = P["STAT_tongue"]
S["MR63_outer_race"] = G.tube("z", 39.0, YA, 2.4, 3.0, -26.35, -23.85, h=h)
for k in ("STAT_leg_back", "STAT_leg_front", "STAT_strut", "STAT_web", "STAT_pad"):
    S[k] = P[k]
S["servo_case"] = keep(P["SERVO"], lambda Q: Q[:, 2] <= -45.0)
S["servo_boss"] = G.tube("z", 39.0, YA, 0, 3.5, -45.0, -44.0, h=h)

M = {"pinion": P["ROT_V_pinion"], "vertical_shaft": P["ROT_V_shaft"], "coupler": P["ROT_V_coupler"],
     "gear": P["ROT_A_gear"], "M4_shank": P["ROT_A_shaft"]}
SKIP = {("vertical_shaft", "tongue"): "shaft in the D4 tongue hole: radial 0.5 by design (checked below)",
        ("vertical_shaft", "MR63_outer_race"): "", ("vertical_shaft", "servo_boss"): "", ("coupler", "servo_boss"): None}
res = {"pairs": {}, "own_pairs": {}}
for mk, mv in M.items():
    for sk, sv in S.items():
        d, _ = cKDTree(sv).query(mv, distance_upper_bound=4.0)
        m = float(d.min())
        if m < 4.0:
            res["pairs"][f"{mk} vs {sk}"] = round(m, 2)
            print("%-34s %.2f" % (f"{mk} vs {sk}", m))
# moving vs moving (pinion-gear mesh is checked by the tooth model; here only non-meshing pairs)
for a, b in (("pinion", "M4_shank"), ("gear", "vertical_shaft"), ("coupler", "pinion")):
    d, _ = cKDTree(M[b]).query(M[a], distance_upper_bound=6.0)
    res["own_pairs"][f"{a} vs {b}"] = round(float(d.min()), 2)
    print("%-34s %.2f" % (f"{a} vs {b}", d.min()))
# shaft in the tongue's bottom hole D4 (z -26.85..-26.35) : radial clearance
res["shaft_in_tongue_hole_radial"] = round(2.0 - B.SHV["r"], 2)
json.dump(res, open("own_b1.json", "w"), indent=1)

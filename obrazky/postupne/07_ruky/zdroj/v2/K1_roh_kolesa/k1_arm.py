"""K1 - how close can the passive arm come to the torso?  Approved pebble (armgeo, dx = shift along X, < 0 = toward the torso)
swept about the shoulder axis over -45..+135 deg (1 deg steps near the minimum) against the exterior of the side cap T_bok_L and
T_stred (surface samples, x > 40).  The joint itself (T_klb) is NOT counted here (it will be replaced by the new thin ring).
Prints per dx: gap at rest (arm 0 deg), minimum over the range and its angle, and the largest +angle reachable with >= 1.0 / 0.5.
Writes k1_arm.json."""
import sys, os, json, time
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import load, sdf_world, swing, vlib  # noqa: E402
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
t0 = time.time()
P = []
for nm in ("T_bok_L", "T_stred"):
    T = load(nm); Q = vlib.sample_surface(T, 0.25); P.append(Q[Q[:, 0] > 40.0])
P = np.concatenate(P)
# keep only exterior samples (outer skin): points whose distance to the outer surface is < 0.05
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C  # noqa: E402
d_out = C.dist_outer(P)
P = P[d_out < 0.08]
print("exterior samples", len(P), f"{time.time()-t0:.0f}s", flush=True)
ANG = np.arange(-45, 136, 1.0)
res = {}
for dx in (0.0, -0.5, -1.0, -1.5, -2.0, -2.5, -3.0, -3.5):
    per = []
    for a in ANG:
        sd = sdf_world(swing(P, -a), dx=dx)
        per.append(float(sd.min()))
    per = np.array(per)
    rest = per[ANG == 0][0]
    k = per.argmin()
    ok10 = ANG[(per >= 1.0)]; ok05 = ANG[(per >= 0.5)]

    def maxreach(okset):
        # largest a such that every angle 0..a is ok
        a = 0.0
        for v in ANG[ANG >= 0]:
            if v in okset: a = v
            else: break
        return float(a)
    res[str(dx)] = dict(gap_rest=round(float(rest), 2), min=round(float(per[k]), 2), at=float(ANG[k]),
                        reach_with_1p0=maxreach(set(ok10.tolist())), reach_with_0p5=maxreach(set(ok05.tolist())),
                        per_10deg={int(a): round(float(v), 2) for a, v in zip(ANG, per) if a % 15 == 0})
    print(dx, res[str(dx)]["gap_rest"], res[str(dx)]["min"], res[str(dx)]["at"], res[str(dx)]["reach_with_1p0"],
          res[str(dx)]["reach_with_0p5"], f"{time.time()-t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(HERE, "k1_arm.json"), "w"), indent=1)

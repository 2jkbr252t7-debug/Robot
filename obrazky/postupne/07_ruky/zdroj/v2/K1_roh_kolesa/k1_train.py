"""K1 - spur train (pinion on the servo -> one idler -> shoulder gear) in a y-z gear plane.
Input: pinion centre (y, z), gear slab x range, minimum ratio pinion/shoulder (arm deg / servo deg).
Free-distance field of the slab from k1_plane.py (plane_<xa>_<xb><VAR>.npy: distance to the nearest blocked cell, 0.5 to static
already included).  Each gear needs fd(centre) >= tip radius; meshes are exact (C = m (z1 + z2) / 2).
Searches m 0.5 and 0.6, all tooth counts, both idler positions (left / right of the pinion-shoulder line).
usage: k1_train.py <VAR> <xa> <xb> <y_p> <z_p> <min_ratio> [max_idler_tip]"""
import sys, os, math, json
sys.dont_write_bytecode = True
import numpy as np
from scipy.ndimage import map_coordinates
HERE = "/tmp/claude-0/gapwf/fin/R1/K1_roh_kolesa"
VAR, xa, xb, yp, zp, rmin = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
RI_MAX = float(sys.argv[7]) if len(sys.argv) > 7 else 99.0
D = np.load(os.path.join(HERE, f"k1_hard{VAR}.npz")); lo, h = D["lo"], float(D["h"])
fd = np.load(os.path.join(HERE, f"plane_{xa:g}_{xb:g}{VAR}.npy"))


def F(y, z):
    return float(map_coordinates(fd, [[(y - lo[1]) / h - 0.5], [(z - lo[2]) / h - 0.5]], order=1)[0])


S = np.array([3.0, -17.0]); P = np.array([yp, zp]); dPS = np.linalg.norm(S - P)
out = []
for m in (0.5, 0.6):
    for zs in range(16, 61):
        rs_tip = m * (zs + 2) / 2
        if F(*S) < rs_tip: continue
        for zpin in range(12, 61):
            if zpin / zs < rmin: continue
            rp_tip = m * (zpin + 2) / 2
            if F(*P) < rp_tip: continue
            for zi in range(12, 81):
                ri_tip = m * (zi + 2) / 2
                if ri_tip > RI_MAX: continue
                a = m * (zpin + zi) / 2; b = m * (zi + zs) / 2
                if a + b < dPS or abs(a - b) > dPS: continue
                # idler centre: circle intersection
                x = (a * a - b * b + dPS * dPS) / (2 * dPS); hh = math.sqrt(max(a * a - x * x, 0))
                u = (S - P) / dPS; v = np.array([-u[1], u[0]])
                for sgn in (1, -1):
                    I = P + x * u + sgn * hh * v
                    fI = F(*I)
                    if fI < ri_tip: continue
                    # pinion and shoulder gear must not touch (tip circles + 0.5)
                    if dPS < rp_tip + rs_tip + 0.5: continue
                    out.append(dict(m=m, z_pinion=zpin, z_idler=zi, z_shoulder=zs, ratio=round(zpin / zs, 3),
                                    idler=[round(float(I[0]), 2), round(float(I[1]), 2)], idler_tip=ri_tip,
                                    margin_idler=round(fI - ri_tip, 2), margin_pinion=round(F(*P) - rp_tip, 2),
                                    margin_shoulder=round(F(*S) - rs_tip, 2)))
print("pinion-shoulder distance %.2f, free r at pinion %.2f, at shoulder %.2f, solutions %d" % (dPS, F(*P), F(*S), len(out)))
out.sort(key=lambda o: (o["idler_tip"], -min(o["margin_idler"], o["margin_pinion"], o["margin_shoulder"])))
for o in out[:15]:
    print(o)
json.dump(dict(dPS=dPS, free_pinion=F(*P), free_shoulder=F(*S), solutions=out[:200]),
          open(os.path.join(HERE, f"k1_train_{VAR or 'base'}_{yp:g}_{zp:g}.json"), "w"), indent=1)

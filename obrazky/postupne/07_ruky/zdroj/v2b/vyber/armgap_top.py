"""JUDGE (vyber): arm gap of the approved pebble (armgeo.to_world(dx)) swung -45..+135 (1 deg) against the approved torso
exterior (analytic x_surface, left side) with the socket (r < 14 about the shoulder axis) modelled as:
  hole  : nothing inside r 14 (cap edge only)
  flush : plug face r <= 13.5 on the approved surface, seam 13.5..14 void
  rec1  : plug face r <= 13.5 recessed 1.0 (x - 1.0), seam void
  rec2  : recessed 2.0
writes armgap.json (rest gap, min gap + angle + location, last angle with >= 1.0 / >= 0.8)"""
import sys, os, json, time
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import sdf_world, swing  # noqa
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import t4_common as C  # noqa
HERE = "/tmp/claude-0/gapwf/fin/R2c/vyber"
t0 = time.time()
hs = 0.2
ys = np.arange(-34.0, 36.0, hs); zs = np.arange(-80.0, 3.9, hs)
Y, Z = np.meshgrid(ys, zs, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
X = np.array([C.x_surface(y, z) for y, z in zip(Y, Z)])
ok = np.isfinite(X) & (X > 38.0)
S0 = np.c_[X[ok], Y[ok], Z[ok]]
ra = np.hypot(S0[:, 1] - 3.0, S0[:, 2] + 17.0)
# dense rim points of the cap edge r = 14 (on the surface)
th = np.linspace(0, 2 * np.pi, 600, endpoint=False)
rim = np.c_[np.zeros_like(th), 3.0 + 14.0 * np.cos(th), -17.0 + 14.0 * np.sin(th)]
rim[:, 0] = [C.x_surface(y, z) for y, z in rim[:, 1:]]
print("surface samples", len(S0), f"{time.time()-t0:.0f}s", flush=True)
ANG = np.r_[0.0, 130.0, 135.0, 137.0, 139.0, 140.5, 142.0]
res = {}
for opt in sys.argv[1].split(","):
    cap = S0[ra >= 14.0]
    if opt == "hole":
        S = np.r_[cap, rim]
    else:
        dl = dict(flush=0.0, rec1=1.0, rec2=2.0)[opt]
        disc = S0[ra <= 13.5].copy(); disc[:, 0] -= dl
        S = np.r_[cap, rim, disc]
    lab = np.r_[np.zeros(len(cap) + len(rim), int), np.ones(len(S) - len(cap) - len(rim), int)]
    for dx in [float(v) for v in sys.argv[2].split(",")]:
        per, where = [], []
        for a in ANG:
            d = sdf_world(swing(S, -a), dx=dx)
            k = int(d.argmin()); per.append(float(d[k])); where.append((S[k].round(2).tolist(), "disc" if lab[k] else "cap"))
        per = np.array(per)
        print('per-angle', dict(zip([float(a) for a in ANG], [round(float(v), 3) for v in per])), flush=True)
        rest = per[ANG == 0][0]
        k = int(per.argmin())

        def reach(th_):
            r = None
            for a, v in zip(ANG, per):
                if a < 0: continue
                if v >= th_: r = float(a)
                else: break
            return r
        key = f"{opt} dx {dx}"
        res[key] = dict(rest=round(float(rest), 2), rest_at=where[int(np.nonzero(ANG == 0)[0][0])], min=round(float(per[k]), 2),
                        min_angle=float(ANG[k]), min_at=where[k], reach_1p0=reach(1.0), reach_0p8=reach(0.8),
                        back_m45=round(float(per[0]), 2),
                        at_130=round(float(per[ANG == 130][0]), 2))
        print(key, res[key], f"{time.time()-t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(HERE, "armgap_top_%s.json" % sys.argv[1].replace(",", "_")), "w"), indent=1)

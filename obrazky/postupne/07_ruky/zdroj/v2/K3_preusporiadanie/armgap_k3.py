"""K3 arm gap: approved pebble (armgeo, dx) swung -45..+135 against the approved torso exterior (analytic outer surface
x_surface(y, z), left side), with the socket disc (r <= 13.5 about the shoulder axis) replaced by the black plug face
recessed by delta along -X.  The ring (r 6.5) is coaxial with the arm hole (r 7.0) -> constant 0.5 seam, not part of this test.
writes armgap_k3.json"""
import sys, os, json, time
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from armgeo import sdf_world, swing  # noqa
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import t4_common as C  # noqa
HERE = os.path.dirname(os.path.abspath(__file__))
t0 = time.time()
ys = np.arange(-34.0, 36.0, 0.25); zs = np.arange(-80.0, 3.9, 0.25)
Y, Z = np.meshgrid(ys, zs, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
X = np.array([C.x_surface(y, z) for y, z in zip(Y, Z)])
ok = np.isfinite(X) & (X > 30.0)
S0 = np.c_[X[ok], Y[ok], Z[ok]]
ra = np.hypot(S0[:, 1] - 3.0, S0[:, 2] + 17.0)
print("surface samples", len(S0), f"{time.time()-t0:.0f}s", flush=True)
ANG = np.r_[np.arange(-45, 120, 5.0), np.arange(120, 135.1, 1.0)]
res = {}
for delta in (0.0, 1.0):
    S = S0.copy(); S[ra <= 13.5, 0] -= delta
    near = S[S[:, 0] > 38.0]
    for dx in (0.0, -0.5, -1.0, -1.5):
        per = np.array([float(sdf_world(swing(near, -a), dx=dx).min()) for a in ANG])
        rest = float(sdf_world(near, dx=dx).min())
        k = int(per.argmin())
        reach = 0.0
        for a, v in zip(ANG, per):
            if a < 0: continue
            if v >= 1.0: reach = float(a)
            else: break
        key = f"delta {delta} dx {dx}"
        res[key] = dict(gap_rest=round(rest, 2), min=round(float(per[k]), 2), at=float(ANG[k]), reach_plus_with_1p0=reach,
                        back_m45=round(float(per[0]), 2))
        print(key, res[key], f"{time.time()-t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(HERE, "armgap_k3.json"), "w"), indent=1)

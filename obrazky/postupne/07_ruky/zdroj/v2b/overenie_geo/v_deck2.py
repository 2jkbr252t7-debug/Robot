"""VERIFIER: are merged-fill voxels INSIDE the T_paluba solid (left lobe)?  Ray-parity point-in-mesh (+Z rays)."""
import sys, json
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib
FV = np.load("/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_L.npz")["P"].astype(float)
T = vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_paluba.stl")
sel = (FV[:, 2] > -48.6) & (FV[:, 2] < -42.6) & (FV[:, 0] < 34.5)
Q = FV[sel]
def inside(P, T):
    # +Z ray parity with a tiny xy jitter to avoid edge hits
    P = P + np.array([1.3e-4, 0.7e-4, 0])
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    res = np.zeros(len(P), bool)
    for i, p in enumerate(P):
        # 2-D barycentric in xy
        v0 = c[:, :2] - a[:, :2]; v1 = b[:, :2] - a[:, :2]; v2 = p[:2] - a[:, :2]
        den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
        ok = np.abs(den) > 1e-14
        u = np.where(ok, (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / np.where(ok, den, 1), -1)
        v = np.where(ok, (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / np.where(ok, den, 1), -1)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
        z = a[hit, 2] + u[hit] * (c[hit, 2] - a[hit, 2]) + v[hit] * (b[hit, 2] - a[hit, 2])
        res[i] = (z > p[2]).sum() % 2 == 1
    return res
m = (T[:, :, 0].max(1) > 20) & (T[:, :, 1].min(1) < 25)
ins = inside(Q, T[m])
out = dict(n_tested=int(len(Q)), n_inside=int(ins.sum()), examples=Q[ins][:10].round(2).tolist(),
           x_range_inside=[float(Q[ins][:, 0].min()), float(Q[ins][:, 0].max())] if ins.any() else None,
           y_range_inside=[float(Q[ins][:, 1].min()), float(Q[ins][:, 1].max())] if ins.any() else None,
           z_range_inside=[float(Q[ins][:, 2].min()), float(Q[ins][:, 2].max())] if ins.any() else None)
print(json.dumps(out, indent=1)); json.dump(out, open("v_deck2.json", "w"), indent=1)

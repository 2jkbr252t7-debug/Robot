"""VERIFIER: arm pebble geometry (tip distance, centroid of the shell, gravity torque) from the T3 shape via armgeo placement."""
import sys, json, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
import armgeo as AG
rows = AG.pebble_rows(400, 360)
W = AG.to_world(rows.reshape(-1, 3), dx=-1.0)
r_ax = np.hypot(W[:, 1] - 3.0, W[:, 2] + 17.0)
out = dict(L=float(AG.L), tip_dist_max=round(float(r_ax.max()), 2), tip_at=W[int(r_ax.argmax())].round(2).tolist(),
           x_range=[round(float(W[:, 0].min()), 2), round(float(W[:, 0].max()), 2)], z_min=round(float(W[:, 2].min()), 2))
# shell centroid (uniform-thickness shell ~ area weighted) in the rest pose; horizontal (+90) lever = distance in y-z from the axis
tris = AG.pebble_tris(300, 240)
Tw = AG.to_world(tris.reshape(-1, 3), dx=-1.0).reshape(-1, 3, 3)
A = 0.5 * np.linalg.norm(np.cross(Tw[:, 1] - Tw[:, 0], Tw[:, 2] - Tw[:, 0]), axis=1)
C = Tw.mean(1)
cg = (C * A[:, None]).sum(0) / A.sum()
lever = math.hypot(cg[1] - 3.0, cg[2] + 17.0)
out["shell_area_mm2"] = round(float(A.sum()), 1)
out["shell_cg"] = cg.round(2).tolist(); out["cg_lever_mm"] = round(lever, 2)
for m in (11.0, 13.0, 15.0):
    out[f"gravity_torque_horizontal_{m:.0f}g"] = round(m * 1e-3 * 9.81 * lever * 1e-3, 5)
# coins at 60 mm: does 60 mm from the axis lie on the arm (tip distance)?
out["coins_60mm_on_arm"] = bool(r_ax.max() > 62.0)
print(json.dumps(out, indent=1))
json.dump(out, open("v_arm.json", "w"), indent=1)

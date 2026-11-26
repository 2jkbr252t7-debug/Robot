"""VERIFIER: merged column fill (left) vs T_paluba (trimmed lobe x <= 31.0): static distance and the deck's assembly path
(T3: deck lowered along -Z, removal +Z).  Fill voxel corners from colfill_B1merge_L.npz."""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib
FV = np.load("/tmp/claude-0/gapwf/fin/R2c/oprava/colfill_fix_L.npz")["P"].astype(float)
off = np.array([[dx, dy, dz] for dx in (-0.25, 0.25) for dy in (-0.25, 0.25) for dz in (-0.25, 0.25)])
Q = np.unique(np.round((FV[:, None, :] + off[None]).reshape(-1, 3), 3), axis=0)
S = vlib.sample_surface(vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_paluba.stl"), 0.08)
S = S[S[:, 0] <= 31.0]
d, j = cKDTree(S).query(Q)
out = dict(static_min=round(float(d.min()), 3), at=Q[int(d.argmin())].round(2).tolist(), deck_pt=S[j[int(d.argmin())]].round(2).tolist(),
           n_corners_below_0p3=int((d < 0.3).sum()))
# deck removal along +Z: a fill corner q is swept if a deck point s lies below it (s_z <= q_z) -> horizontal distance
t2 = cKDTree(S[:, :2]); best = (9.9, None)
for i, li in enumerate(t2.query_ball_point(Q[:, :2], 1.0)):
    if not li: continue
    s = S[li]; dp = np.hypot(s[:, 0] - Q[i, 0], s[:, 1] - Q[i, 1]); ah = Q[i, 2] - s[:, 2]
    dd = np.where(ah >= 0, dp, np.hypot(dp, ah)); k = int(dd.argmin())
    if dd[k] < best[0]: best = (float(dd[k]), Q[i].round(2).tolist())
out["deck_removal_path_min"] = round(best[0], 3); out["deck_removal_path_at"] = best[1]
print(json.dumps(out, indent=1)); json.dump(out, open("/tmp/claude-0/gapwf/fin/R2c/oprava/v_deck_fix.json", "w"), indent=1)

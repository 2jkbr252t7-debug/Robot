"""VERIFIER: merged column fill voxels that block the deck (T_paluba, trimmed x <= 31.0; T3 = lowered along -Z).
A fill voxel blocks if trimmed-deck surface material lies below it within 0.3 mm horizontally."""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
import vlib
FV = np.load("/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_R.npz")["P"].astype(float)
S = vlib.sample_surface(vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_paluba.stl"), 0.08)
lobe = np.hypot(S[:, 0] - 29.5, S[:, 1] - 4.0) <= 3.15
S = S
t2 = cKDTree(S[:, :2])
blk = []
for i, li in enumerate(t2.query_ball_point(FV[:, :2], 0.25 + 0.3)):
    if not li: continue
    s = S[li]
    # voxel spans x,y +-0.25 ; deck point below the voxel bottom
    dx = np.maximum(np.abs(s[:, 0] - FV[i, 0]) - 0.25, 0); dy = np.maximum(np.abs(s[:, 1] - FV[i, 1]) - 0.25, 0)
    below = s[:, 2] <= FV[i, 2] - 0.25 + 1e-6
    if np.any(below & (np.hypot(dx, dy) < 0.3)):
        blk.append(FV[i])
blk = np.array(blk)
out = dict(n_blocking_voxels=int(len(blk)))
if len(blk):
    out.update(x=[float(blk[:, 0].min()), float(blk[:, 0].max())], y=[float(blk[:, 1].min()), float(blk[:, 1].max())],
               z=[float(blk[:, 2].min()), float(blk[:, 2].max())], volume_mm3=round(len(blk) * 0.125, 1),
               by_band=dict(front=int((blk[:, 1] < 0).sum()), back=int((blk[:, 1] > 0).sum())),
               z_levels=sorted(set(np.round(blk[:, 2], 2).tolist())))
print(json.dumps(out, indent=1)); json.dump(out, open("v_deck3_R.json", "w"), indent=1)

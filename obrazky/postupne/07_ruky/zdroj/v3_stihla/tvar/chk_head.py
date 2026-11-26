"""R3/tvar: sanity check arm vs head/neck (B/stl CELOK_* poses, pan 0 / +-30 about Z through the origin) over the raise
angles 60..142 deg, per variant.  Mesh vertices + triangle centroids vs the arm SDF (approximate: an upper bound of the
true distance by about the mesh edge length).  Purpose: the slim variants must not come closer to the head than variant 0."""
import sys, os, json, math, struct
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import variants as VA


def load_stl(p):
    with open(p, "rb") as f:
        f.read(80); n = struct.unpack("<I", f.read(4))[0]
        a = np.frombuffer(f.read(50 * n), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    v = a["v"].astype(float)
    return np.concatenate([v.reshape(-1, 3), v.mean(1)])


poses = {k: load_stl(f"/tmp/claude-0/gapwf/fin/B/stl/CELOK_{k}.stl") for k in ("pokoj", "naklon40", "vysunute")}
ANG = np.r_[np.arange(60.0, 135.1, 2.5), 135.0, 140.5]
out = {}
for vid in VA.VIDS:
    rows, top, bot = VA.pebble_rows(vid, 330, 230)
    Cl = np.concatenate([rows.reshape(-1, 3), [top, bot]])
    tree = cKDTree(Cl)
    res = {}
    for pk, Pw in poses.items():
        Pw = Pw[Pw[:, 2] > 6.0]          # head + neck only (the old B torso in CELOK is not the T4 torso)
        for pan in (-30.0, 0.0, 30.0):
            c, s = math.cos(math.radians(pan)), math.sin(math.radians(pan))
            Q = Pw @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T
            Q = Q[Q[:, 0] > 30.0]
            best = (99.0, None, None)
            at135 = None
            for a in ANG:
                L = VA.to_local(VA.swing(Q, -a))
                d, j = tree.query(L, distance_upper_bound=12.0)
                ins = VA.inside_local(vid, L)
                d = np.where(ins, -d, d)
                k = int(np.argmin(d))
                if a == 140.5:
                    at140 = round(min(float(d[k]), 12.0), 2); continue
                if d[k] < best[0]:
                    jj = min(int(j[k]), len(Cl) - 1)
                    best = (float(d[k]), float(a), round(float(-Cl[jj, 2] / VA.L), 2))
            res[f"{pk}_pan{int(pan)}"] = dict(min_le135=round(min(best[0], 12.0), 2), angle=best[1], arm_u=best[2], at140_5=at140)
    out[vid] = res
    print(vid, res, flush=True)
json.dump(out, open(os.path.join(HERE, "chk_head.json"), "w"), indent=1)

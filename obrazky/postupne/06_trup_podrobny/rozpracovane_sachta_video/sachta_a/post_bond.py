"""bond (gear <-> well) force distribution by radius band and the edge line load; usage: post_bond.py case"""
import sys, json, numpy as np
import fe3d, fe_build as FB
from post import internal_forces, m, RES
X = m.X; nb = m.node_body
for case in sys.argv[1:]:
    U = np.load(f"{RES}/{case}.npz")["U"].astype(np.float64)
    fg = internal_forces(U, "gear")
    bond = np.flatnonzero((nb == 0) & (np.abs(X[:, 2] + 41.9) < 1e-6) & (np.linalg.norm(fg, axis=1) > 0) & (np.hypot(X[:, 0], X[:, 1]) > 5.0))
    r = np.hypot(X[bond, 0], X[bond, 1]); fz = fg[bond, 2]; fs = np.hypot(fg[bond, 0], fg[bond, 1])
    out = dict(case=case, Fz=round(float(fz.sum()), 2), tension_sum=round(float(fz[fz > 0].sum()), 2), compression_sum=round(float(fz[fz < 0].sum()), 2))
    bands = [(5, 6.6), (6.6, 8), (8, 10), (10, 12.0), (12.0, 13.4), (13.4, 15.3)]
    out["bands"] = {f"r {a}-{b}": dict(n=int(((r >= a) & (r < b)).sum()), Fz_tension=round(float(fz[(r >= a) & (r < b) & (fz > 0)].sum()), 2),
                                       Fz_comp=round(float(fz[(r >= a) & (r < b) & (fz < 0)].sum()), 2), shear=round(float(fs[(r >= a) & (r < b)].sum()), 2))
                    for a, b in bands}
    # by angle sector (tension) inside r <= 13.4
    az = np.degrees(np.arctan2(X[bond, 1], X[bond, 0])) % 360
    out["tension_by_az_r<=13.4"] = {f"{a}-{a+45}": round(float(fz[(az >= a) & (az < a + 45) & (fz > 0) & (r <= 13.4)].sum()), 2) for a in range(0, 360, 45)}
    # peel stress inside the root circle only (r <= 13.4), node value and 1.2 mm mean
    m_in = r <= 13.4
    tz = fz / m.h ** 2
    from scipy.spatial import cKDTree
    t = cKDTree(X[bond][:, :2])
    avg = np.array([tz[t.query_ball_point(X[bond[i], :2], 0.6)].mean() for i in range(len(bond))])
    k = np.argmax(np.where(m_in, avg, -1e9))
    out["peel_root_circle_avg0.6"] = round(float(avg[k]), 3); out["at"] = [round(float(v), 2) for v in X[bond[k]]]
    k2 = np.argmax(np.where(m_in, tz, -1e9)); out["peel_root_circle_node"] = round(float(tz[k2]), 3)
    print(json.dumps(out, indent=1))
    json.dump(out, open(f"{RES}/{case}_bond.json", "w"), indent=1)

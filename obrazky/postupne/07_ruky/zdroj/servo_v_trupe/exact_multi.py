"""multi-start exact optimisation (exact_fit.run objective) - writes exact_multi_<tag>.json"""
import sys, os, json, time
sys.dont_write_bytecode = True
import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import exact_fit as E
L, W, Hh = (float(v) for v in sys.argv[1:4]); x0 = np.array([float(v) for v in sys.argv[4:10]]); tag = sys.argv[10]
S = E.box_surface(L, W, Hh, h=1.0)
def f(x):
    Pw, _, _ = E.pose_pts(x, S); m = E.margins(Pw)
    return -float(m.min()) - 0.05 * float(np.mean(np.minimum(m, 0.0)))
rng = np.random.default_rng(3); best = (1e9, None); t0 = time.time(); log = []
starts = [x0] + [x0 + np.concatenate([rng.normal(0, 2.0, 3), rng.normal(0, 0.15, 3)]) for _ in range(3)]
for k, s in enumerate(starts):
    r = minimize(f, s, method="Nelder-Mead", options=dict(xatol=0.02, fatol=0.002, maxiter=260, adaptive=True))
    Pw, c, R = E.pose_pts(r.x, S); m, w = E.margins(Pw, True)
    log.append(dict(start=k, worst=round(float(m.min()), 3), centre=[round(float(v), 2) for v in c], nfev=int(r.nfev)))
    print(log[-1], f"{time.time()-t0:.0f}s", flush=True)
    if -m.min() < best[0]: best = (-float(m.min()), r.x, w)
Pw, c, R = E.pose_pts(best[1], E.box_surface(L, W, Hh, h=0.4)); m, w = E.margins(Pw, True)
res = dict(case=[L, W, Hh], best_worst_margin_fine=round(float(m.min()), 3), centre=[round(float(v), 2) for v in c], rotvec=[round(float(v), 4) for v in best[1][3:]],
           axes_world={"L": R[:, 0].round(3).tolist(), "W": R[:, 1].round(3).tolist(), "H (shaft)": R[:, 2].round(3).tolist()},
           per_part=dict(sorted(((k, round(v, 2)) for k, v in w.items()), key=lambda kv: kv[1])[:8]), contained=E.contained_parts(c, R, (L, W, Hh)), starts=log)
json.dump(res, open(os.path.join(HERE, f"exact_multi_{tag}.json" if tag != "kst" else "exact_kst.json"), "w"), indent=1); print(json.dumps(res)[:1500])

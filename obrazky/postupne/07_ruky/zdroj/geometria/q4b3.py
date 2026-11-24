import json
from armgeo import *
exec(open("q4_common.py").read())
exec(open("q4b2.py").read().split("out = dict(B=[], A_b=[])")[0].split('t0 = time.time()')[1])
res = []
for nm in ["S4", "S3"]:
    L_, W_, H_, s = CASES[nm]
    for on in ("up", "down", "fwd"):
        for d in (10.0, 13.0, 16.0):
            eL = ORI[on]; eH = np.array([1.0, 0, 0]); eW = np.cross(eH, eL); sp = AXP + d * DYZ
            ls = np.linspace(-s, L_ - s, 30); ws = np.linspace(-W_ / 2, W_ / 2, 15)
            G = np.array([sp + l * eL + w * eW for l in ls for w in ws]); xi = inner_x(G[:, 1], G[:, 2])
            if np.isnan(xi).any(): print(nm, on, d, "footprint leaves the pebble"); continue
            x0 = float(xi.max())
            P, F, hh = box_h(sp + np.array([x0, 0, 0]), eL, eW, eH, L_, W_, H_, s)
            sd = sdf_world(P, dmax=30.0)
            r = dict(case=nm, ori=on, d=d, x0=round(x0, 2), x1=round(x0 + H_, 2),
                     m_band2=round(float((-sd[hh >= 2] - 2).min()), 2), m_band3=round(float((-sd[hh >= 3] - 2).min()), 2),
                     outer_face=round(float((-sd[hh >= H_ - 1e-6] - 2).min()), 2), inner_prot=round(float(sd[hh <= 1e-6].max()), 2),
                     klb_now=round(float(klb_clear(P).min()), 2), klb_cut=round(float(klb_clear(P, X_CUT).min()), 2),
                     box_top_r=round(float(np.hypot(P[:, 1] - SH_Y, P[:, 2] - ZS).min()), 2))
            res.append(r); print(r, flush=True)
json.dump(res, open("q4b3_S4S3_out.json", "w"), indent=1)

"""layout A 'flush' (d = 0: shaft on the axis, case face moved out until it is flush with the inner skin -> needed T_klb cut x)
and thickness growth kt for the best layout-B / A-flush configurations (outer criterion: 2.0 wall for case points >= 3 mm
from the window face; nothing outside the skin)"""
import json
from armgeo import *
exec(open("q4_common.py").read())
exec(open("q4b2.py").read().split("out = dict(B=[], A_b=[])")[0].split('t0 = time.time()')[1])


def ev(nm, d, on, kt=1.0, h=0.5, th=0.15):
    L_, W_, H_, s = CASES[nm]; eL = ORI[on]; eH = np.array([1.0, 0, 0]); eW = np.cross(eH, eL); sp = AXP + d * DYZ
    ls = np.linspace(-s, L_ - s, 30); ws = np.linspace(-W_ / 2, W_ / 2, 15)
    G = np.array([sp + l * eL + w * eW for l in ls for w in ws]); xi = inner_x(G[:, 1], G[:, 2], kt)
    if np.isnan(xi).any(): return None
    x0 = float(xi.max())
    P, F, hh = box_h(sp + np.array([x0, 0, 0]), eL, eW, eH, L_, W_, H_, s, h)
    sd = sdf_world(P, kt, dmax=30.0, h=th)
    return dict(case=nm, d=d, ori=on, kt=kt, x0=round(x0, 2), x1=round(x0 + H_, 2), m3=round(float((-sd[hh >= 3] - 2).min()), 2),
                outer_face=round(float((-sd[hh >= H_ - 1e-6] - 2).min()), 2), klb_now=round(float(klb_clear(P).min()), 2),
                klb_cut_needed_x=round(x0 - 0.3, 2))


out = []
for nm in CASES:
    for on in ("down", "up", "fwd"):
        r = ev(nm, 0.0, on)
        if r is None: print(nm, on, "footprint leaves the pebble"); continue
        print("A-flush", r, flush=True); out.append(r)
cfg = [("S1", 0.0, "down"), ("S2", 0.0, "down"), ("S3", 0.0, "down"), ("S4", 0.0, "down"),
       ("S1", 10.0, "up"), ("S2", 10.0, "up"), ("S3", 10.0, "up"), ("S4", 16.0, "down"), ("S4", 10.0, "down")]
for nm, d, on in cfg:
    need_kt = None
    for kt in np.round(np.arange(1.0, 1.801, 0.02), 3):
        r = ev(nm, d, on, kt, h=1.0, th=0.25)
        if r and r["m3"] >= 0:
            need_kt = r; break
    print("kt for %s d %.0f %s:" % (nm, d, on), None if need_kt is None else (need_kt["kt"], "growth %.2f mm" % ((need_kt["kt"] - 1) * 23.021), need_kt), flush=True)
    out.append(dict(cfg=[nm, d, on], kt=need_kt))
json.dump(out, open("q4b4_out.json", "w"), indent=1)

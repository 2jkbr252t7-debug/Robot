"""layout C: best wall margin (centred box, optimal height on the arm) for every case / orientation + kt / kw needed when it fails"""
import json
from armgeo import *
exec(open("q4_common.py").read())
ex, ey, ez = np.eye(3)
ORIC = (("shaft up the arm", ez, ey), ("shaft fore-aft", -ey, ez))
res = []
for nm, (L_, W_, H_, s) in CASES.items():
    for on, eH_, eL_ in ORIC:
        eW_ = np.cross(eH_, eL_)
        def m_at(cz, kt=1.0, kw=1.0, cx=0.0, h=0.5, th=0.15):
            c = np.array([cx, 0.0, cz]); o = c - (H_ / 2) * eH_ - ((L_ / 2) - s) * eL_
            P, F = box_surface(o, eL_, eW_, eH_, L_, W_, H_, s, h)
            return float((-sdf_local(P, kt, kw, h=th, dmax=10.0) - 2.0).min())
        zs = np.arange(-60.0, -8.0, 0.5)
        ms = [m_at(z, h=1.0, th=0.25) for z in zs]
        z0 = zs[int(np.argmax(ms))]
        zf = np.arange(z0 - 1, z0 + 1.01, 0.1); mf = [m_at(z) for z in zf]
        zb = float(zf[int(np.argmax(mf))]); mb = max(mf)
        rec = dict(case=nm, ori=on, best_cz=round(zb, 2), u_centre=round(-zb / L, 3), margin=round(mb, 3))
        if mb < 0:
            for nmk, kk in (("kt", "t"), ("kw", "w"), ("k_both", "b")):
                rec[nmk] = None
                for k in np.round(np.arange(1.01, 1.4001, 0.01), 3):
                    kt = k if kk in "tb" else 1.0; kw = k if kk in "wb" else 1.0
                    if max(m_at(z, kt, kw, h=1.0, th=0.25) for z in np.arange(zb - 3, zb + 3.01, 0.5)) >= 0:
                        rec[nmk] = float(k); break
        res.append(rec); print(rec, flush=True)
json.dump(res, open("q4c2_out.json", "w"), indent=1)

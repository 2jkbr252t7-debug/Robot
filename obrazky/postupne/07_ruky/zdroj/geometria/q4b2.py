"""Q4 layout B (and A-b) re-evaluated with an inner WINDOW: the case face toward the torso is flush with the pebble inner skin
(no inner wall), so the 2.0 wall is required only for case points >= 2.0 mm from that face; nothing may stick out of the skin."""
import json, time
from armgeo import *
exec(open("q4_common.py").read())
t0 = time.time()
BAND = 2.0


def inner_x(Y, Z, kt=1.0):
    xs = np.arange(40.0, 80.0, 0.5)
    Q = np.stack(np.broadcast_arrays(xs[None, :], Y[:, None], Z[:, None]), -1).reshape(-1, 3)
    ins = inside_local(to_local(Q, kt), kt).reshape(len(Y), len(xs))
    ok = ins.any(1); f = ins.argmax(1)
    lo = xs[np.maximum(f - 1, 0)]; hi = xs[f]
    for _ in range(12):
        m = 0.5 * (lo + hi)
        im = inside_local(to_local(np.column_stack([m, Y, Z]), kt), kt)
        hi = np.where(im, m, hi); lo = np.where(im, lo, m)
    return np.where(ok, hi, np.nan)


def box_h(o, eL, eW, eH, L_, W_, H_, s, h=0.5):
    P, F = box_surface(o, eL, eW, eH, L_, W_, H_, s, h)
    hh = (P - o) @ eH
    return P, F, hh


def evalB(nm, d, on, kt=1.0, h=0.5):
    L_, W_, H_, s = CASES[nm]; eL = ORI[on]; eH = np.array([1.0, 0, 0]); eW = np.cross(eH, eL)
    sp = AXP + d * DYZ
    ls = np.linspace(-s, L_ - s, 30); ws = np.linspace(-W_ / 2, W_ / 2, 15)
    G = np.array([sp + l * eL + w * eW for l in ls for w in ws])
    xi = inner_x(G[:, 1], G[:, 2], kt)
    if np.isnan(xi).any(): return None
    x0 = float(xi.max())
    P, F, hh = box_h(sp + np.array([x0, 0, 0]), eL, eW, eH, L_, W_, H_, s, h)
    sd = sdf_world(P, kt, dmax=30.0)
    m = hh >= BAND - 1e-9
    marg = float((-sd[m] - WALL).min()); prot = float(sd.max())
    return dict(case=nm, d=float(d), ori=on, kt=kt, x0=round(x0, 3), x1=round(x0 + H_, 3), skin_x_range=[round(float(xi.min()), 2), round(x0, 2)],
                margin=round(marg, 3), protrusion=round(prot, 3), worst=np.round(P[m][(-sd[m]).argmin()], 2).tolist(),
                klb_now=round(float(klb_clear(P).min()), 2), klb_cut=round(float(klb_clear(P, X_CUT).min()), 2))


out = dict(B=[], A_b=[])
for nm in CASES:
    recs = [r for d in np.arange(10.0, 16.01, 1.0) for on in ("down", "up", "fwd") for r in [evalB(nm, d, on)] if r]
    best = max(recs, key=lambda r: r["margin"])
    print("%s B: best d %.0f %-4s x0 %.2f..%.2f margin(window) %+.3f protrusion %+.3f T_klb now %.2f cut %.2f worst %s" %
          (nm, best["d"], best["ori"], best["x0"], best["x1"], best["margin"], best["protrusion"], best["klb_now"], best["klb_cut"], best["worst"]), flush=True)
    for r in sorted(recs, key=lambda r: -r["margin"])[:4]:
        print("      d %.0f %-4s margin %+.3f klb cut %.2f now %.2f" % (r["d"], r["ori"], r["margin"], r["klb_cut"], r["klb_now"]))
    kt_need = None
    if best["margin"] < 0:
        for kt in np.round(np.arange(1.02, 1.801, 0.02), 3):
            r = evalB(nm, best["d"], best["ori"], kt, h=1.0)
            if r and r["margin"] >= 0 and r["protrusion"] <= 0.05:
                kt_need = dict(kt=float(kt), growth_mm=round((kt - 1) * 23.021, 2), x0=r["x0"], x1=r["x1"]); break
    print("     kt needed:", kt_need, "(%.0f s)" % (time.time() - t0), flush=True)
    out["B"].append(dict(best=best, top=sorted(recs, key=lambda r: -r["margin"])[:6], kt_needed=kt_need))
# A-b with the window criterion (case face at x 51.2 sits against the cut T_klb; the pebble inner skin is opened there)
for nm, (L_, W_, H_, s) in CASES.items():
    for on in ("down", "up", "fwd"):
        eL = ORI[on]; eH = np.array([1.0, 0, 0]); eW = np.cross(eH, eL)
        o = AXP + np.array([X_CUT + 0.3, 0, 0])
        P, F, hh = box_h(o, eL, eW, eH, L_, W_, H_, s)
        sd = sdf_world(P, dmax=30.0); m = hh >= BAND - 1e-9
        rec = dict(case=nm, ori=on, margin_window=round(float((-sd[m] - WALL).min()), 3), protrusion=round(float(sd.max()), 3),
                   outer_face_margin=round(float((-sd[hh >= H_ - 1e-6] - WALL).min()), 3))
        out["A_b"].append(rec)
        print("A-b %s %-4s margin(window) %+.3f  outer face only %+.3f  max protrusion out of the skin %+.3f" % (nm, on, rec["margin_window"], rec["outer_face_margin"], rec["protrusion"]), flush=True)
json.dump(out, open("q4b2_out.json", "w"), indent=1)
print("done %.0f s" % (time.time() - t0))

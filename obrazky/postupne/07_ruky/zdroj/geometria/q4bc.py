"""Q4 layouts B (offset parallel shaft) and C (flat case in the arm).  Rest pose, left arm, frame B."""
import json, time, itertools
from armgeo import *
exec(open("q4_common.py").read())
t0 = time.time()
OUT = {"B": [], "C": []}


def inner_x(Y, Z, x_lo=44.0, x_hi=80.0, step=0.01):
    """x of the pebble inner surface (first entry along +X) on lines || X through (Y, Z); nan if missed"""
    xs = np.arange(x_lo, x_hi, step)
    out = np.full(len(Y), np.nan)
    for i0 in range(0, len(Y), 200):
        yy = Y[i0:i0 + 200]; zz = Z[i0:i0 + 200]
        Q = np.stack(np.broadcast_arrays(xs[None, :], yy[:, None], zz[:, None]), -1).reshape(-1, 3)
        ins = inside_local(to_local(Q)).reshape(len(yy), len(xs))
        f = ins.argmax(1); ok = ins.any(1)
        out[i0:i0 + 200] = np.where(ok, xs[f], np.nan)
    return out


# ------------------------------------------------------------------ layout B
print("=== LAYOUT B: shaft || shoulder axis, d below it on the arm line; case from the pebble inner surface outward ===")
eH = np.array([1.0, 0, 0])
for nm, (L_, W_, H_, s) in CASES.items():
    allrec = []
    for d in np.arange(10.0, 16.01, 0.5):
        for on, eL in ORI.items():
            eW = np.cross(eH, eL)
            sp = AXP + d * DYZ                                # shaft point in y-z
            ls = np.linspace(-s, L_ - s, 25); ws = np.linspace(-W_ / 2, W_ / 2, 13)
            G = np.array([sp + l * eL + w * eW for l in ls for w in ws])
            xi = inner_x(G[:, 1], G[:, 2])
            if np.isnan(xi).any():
                continue
            xi_shaft = inner_x(np.array([sp[1]]), np.array([sp[2]]))[0]
            for mode, x0 in (("flush_max", xi.max()), ("flush_shaft", xi_shaft)):
                P, F = box_surface(sp + x0 * eH, eL, eW, eH, L_, W_, H_, s)
                mo, pin, at = margin(P, F)
                kc_now = float(klb_clear(P).min()); kc_cut = float(klb_clear(P, X_CUT).min())
                allrec.append(dict(case=nm, d=float(d), ori=on, mode=mode, x0=round(float(x0), 3), x1=round(float(x0 + H_), 3), margin_wall=round(mo, 3),
                                   shaft_face_protrusion=round(pin, 3), klb_clear_now=round(kc_now, 3), klb_clear_cut=round(kc_cut, 3),
                                   worst_at=np.round(at, 2).tolist(), inner_skin_x_range=[round(float(np.nanmin(xi)), 2), round(float(xi.max()), 2)]))
    # best: flush_max, by margin then by klb clearance (cut)
    fm = [r for r in allrec if r["mode"] == "flush_max"]
    best = max(fm, key=lambda r: (r["margin_wall"] >= 0 and r["klb_clear_cut"] >= 0.3, r["margin_wall"]))
    best_now = max(fm, key=lambda r: (min(r["margin_wall"], r["klb_clear_now"] - 1.5)))
    fits = sorted({(r["d"], r["ori"]) for r in fm if r["margin_wall"] >= 0})
    fits_cut = sorted({(r["d"], r["ori"]) for r in fm if r["margin_wall"] >= 0 and r["klb_clear_cut"] >= 0.3})
    fits_now = sorted({(r["d"], r["ori"]) for r in fm if r["margin_wall"] >= 0 and r["klb_clear_now"] >= 1.5})
    sh = [r for r in allrec if r["mode"] == "flush_shaft" and r["d"] == best["d"] and r["ori"] == best["ori"]][0]
    rec = dict(best=best, best_flush_at_shaft=sh, best_with_klb_now=best_now, n_fit_wall=len(fits), fit_wall=fits[:60], fit_with_klb_cut=fits_cut[:60], fit_with_klb_now_hub=fits_now[:60])
    # growth for the best (if it fails)
    if best["margin_wall"] < 0:
        eL = ORI[best["ori"]]; eW = np.cross(eH, eL); sp = AXP + best["d"] * DYZ
        P, F = box_surface(sp + best["x0"] * eH, eL, eW, eH, L_, W_, H_, s)
        Pc, Fc = box_surface(sp + best["x0"] * eH, eL, eW, eH, L_, W_, H_, s, 1.0)
        rec["kt_needed"] = None
        for k in np.round(np.arange(1.0, 2.001, 0.02), 3):
            if float((-sdf_world(Pc[~Fc], k, dmax=2.6, h=0.25) - WALL).min()) >= 0:
                rec["kt_needed"] = float(k); break
    OUT["B"].append(rec)
    print("%s: best %s d %.1f %s x0 %.2f..%.2f wall margin %+.3f | flush at shaft: x0 %.2f margin %+.3f protrusion %+.3f | T_klb clear now %.2f cut %.2f | fits(wall) %d combos, with cut T_klb %d, with T_klb now + hub 1.5: %d  kt %s  (%.0f s)" %
          (nm, best["mode"], best["d"], best["ori"], best["x0"], best["x1"], best["margin_wall"], sh["x0"], sh["margin_wall"], sh["shaft_face_protrusion"],
           best["klb_clear_now"], best["klb_clear_cut"], len(fits), len(fits_cut), len(fits_now), rec.get("kt_needed"), time.time() - t0), flush=True)
    print("     fit list (d, ori):", fits)
json.dump(OUT, open("q4bc_out.json", "w"), indent=1)

# ------------------------------------------------------------------ layout C
print("\n=== LAYOUT C: flat case, thin W along the arm thickness (local x), 2.0 walls both sides ===")
ex, ey, ez = np.eye(3)


def fit_local(c, eL, eW, eH, L_, W_, H_, s, h):
    o = c - (H_ / 2) * eH - ((L_ / 2) - s) * eL        # shaft point on the h = 0 face such that the box centre is c
    P, F = box_surface(o, eL, eW, eH, L_, W_, H_, s, h)
    return P, F, o


for nm, (L_, W_, H_, s) in CASES.items():
    res = []
    # orientations: shaft up the arm (eH = +z local), shaft forward (eH = -y), shaft back (+y); eW = local x
    for on, eH_, eL_ in (("up, shaft front", ez, -ey), ("up, shaft back", ez, ey), ("fwd, shaft top", -ey, ez), ("fwd, shaft bottom", -ey, -ez),
                         ("back, shaft top", ey, ez), ("back, shaft bottom", ey, -ez)):
        eW_ = np.cross(eH_, eL_)
        # shaft exit point = o + H eH (top face) ; grid over the box centre
        cands = []
        for cz in np.arange(-L + 1, 0, 0.5):
            for cy in np.arange(-8.0, 8.01, 1.0):
                for cx in np.arange(-5.0, 5.01, 1.0):
                    cands.append((cx, cy, cz))
        cands = np.array(cands)
        # coarse: corners + face centres (fast reject)
        Pc, Fc, _ = fit_local(np.zeros(3), eL_, eW_, eH_, L_, W_, H_, s, 4.0)
        ok = np.ones(len(cands), bool)
        for i0 in range(0, len(cands), 4000):
            C_ = cands[i0:i0 + 4000]
            Q = (C_[:, None, :] + Pc[None, :, :]).reshape(-1, 3)
            pre = inside_local(Q, inset=1.7).reshape(len(C_), len(Pc)).all(1)       # analytic section inset: fast pre-filter
            okk = np.zeros(len(C_), bool)
            if pre.any():
                Qp = (C_[pre][:, None, :] + Pc[None, :, :]).reshape(-1, 3)
                okk[pre] = (sdf_local(Qp, dmax=2.6) <= -WALL).reshape(pre.sum(), len(Pc)).all(1)
            ok[i0:i0 + 4000] = okk
        good = cands[ok]
        if not len(good):
            # fit failure: best margin candidate
            res.append(dict(case=nm, ori=on, fits=False)); continue
        # shaft exit point for every good candidate
        o_rel = -(H_ / 2) * eH_ - ((L_ / 2) - s) * eL_
        tip = good + o_rel + H_ * eH_ if not np.allclose(eH_, ez) or True else None
        # the shaft exit point on the face h = H (the shaft points along +eH)
        TW = to_world(tip)
        dax = np.hypot(TW[:, 1] - SH_Y, TW[:, 2] - ZS)
        order = np.argsort(dax)
        best = None; best_cut = None
        for j in order[:4000]:
            P, F, o = fit_local(good[j], eL_, eW_, eH_, L_, W_, H_, s, 0.5)
            sd = sdf_local(P, dmax=30.0)
            if (sd > -WALL).any():
                continue
            PW = to_world(P)
            kn = float(klb_clear(PW).min()); kc = float(klb_clear(PW, X_CUT).min())
            r = dict(case=nm, ori=on, centre_local=good[j].round(2).tolist(), shaft_exit_world=TW[j].round(2).tolist(), dist_axis=round(float(dax[j]), 2),
                     wall_margin=round(float(-sd.max() - WALL), 3), klb_clear_now=round(kn, 2), klb_clear_cut=round(kc, 2),
                     u_range=[round(float(-(good[j][2] + 0.5 * abs(np.dot([L_, W_, H_], np.abs([eL_[2], eW_[2], eH_[2]])))) / L), 3),
                              round(float(-(good[j][2] - 0.5 * abs(np.dot([L_, W_, H_], np.abs([eL_[2], eW_[2], eH_[2]])))) / L), 3)])
            if best is None and kn >= 1.5:
                best = r
            if best_cut is None and kc >= 0.3:
                best_cut = r
            if best is not None and best_cut is not None:
                break
        zr = [float(good[:, 2].min()), float(good[:, 2].max())]
        res.append(dict(case=nm, ori=on, fits=True, n_centres=int(len(good)), centre_z_range=zr, best_klb_now=best, best_klb_cut=best_cut))
        print("%s %-20s fits at %5d centres, centre z %.1f..%.1f (u %.2f..%.2f) | nearest shaft exit to the axis: T_klb now (>=1.5 hub) %s | T_klb cut 50.9 %s (%.0f s)" %
              (nm, on, len(good), zr[0], zr[1], -zr[1] / L, -zr[0] / L, None if best is None else (best["dist_axis"], best["centre_local"], best["shaft_exit_world"]),
               None if best_cut is None else (best_cut["dist_axis"], best_cut["centre_local"], best_cut["shaft_exit_world"]), time.time() - t0), flush=True)
    OUT["C"].append(res)
json.dump(OUT, open("q4bc_out.json", "w"), indent=1)
print("done")

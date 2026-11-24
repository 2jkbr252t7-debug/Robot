"""Q4 layout C (flat case in the arm, arm-local frame): fit search + shaft exit nearest to the shoulder axis"""
import json, time
from armgeo import *
exec(open("q4_common.py").read())
t0 = time.time()
OUT = {"C": []}
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
    for on, eH_, eL_ in (("shaft up the arm", ez, ey), ("shaft fore-aft, near top end", -ey, ez), ("shaft fore-aft, near bottom end", -ey, -ez)):
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
            Pq, _, _ = fit_local(good[j], eL_, eW_, eH_, L_, W_, H_, s, 1.0)
            PWq = to_world(Pq)
            need_now = best is None and float(klb_clear(PWq).min()) >= 1.45
            need_cut = best_cut is None and float(klb_clear(PWq, X_CUT).min()) >= 0.25
            if not (need_now or need_cut):
                continue
            P, F, o = fit_local(good[j], eL_, eW_, eH_, L_, W_, H_, s, 0.5)
            sd = sdf_local(P, dmax=2.6)
            if (sd > -WALL).any():
                continue
            PW = to_world(P)
            kn = float(klb_clear(PW).min()); kc = float(klb_clear(PW, X_CUT).min())
            r = dict(case=nm, ori=on, centre_local=good[j].round(2).tolist(), shaft_exit_world=TW[j].round(2).tolist(), dist_axis=round(float(dax[j]), 2),
                     wall_margin=round(float(-sdf_local(P, dmax=30.0).max() - WALL), 3), klb_clear_now=round(kn, 2), klb_clear_cut=round(kc, 2),
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
json.dump(OUT, open("q4c_out.json", "w"), indent=1)
print("done")

"""seam bookkeeping: half thicknesses from the seam (cover to, inner ti) along u, where each half is thinner than seam gap +
wall (solid there), the seam step (REV / LIP) along u, and the half_rows of variants_b vs the own skin (max deviation)"""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB
OUT = {}
us = np.linspace(0.001, 0.999, 999)
for vid in ["B0", "B1", "B2", "B3"]:
    c, ti, to, wi, wo, ni, no = AS.secf(vid, us)
    R = dict(cover_solid_u=[round(float(us[to < 0.25 + 1.2].max(initial=0) if (to[us < 0.5] < 1.45).any() else 0), 3)],
             cover_thinner_than_1p45_u=[round(float(us[(to < 1.45) & (us < 0.5)].max()), 3) if ((to < 1.45) & (us < 0.5)).any() else None,
                                        round(float(us[(to < 1.45) & (us > 0.5)].min()), 3) if ((to < 1.45) & (us > 0.5)).any() else None],
             inner_thinner_than_1p85_u=[round(float(us[(ti < 1.85) & (us < 0.5)].max()), 3) if ((ti < 1.85) & (us < 0.5)).any() else None,
                                        round(float(us[(ti < 1.85) & (us > 0.5)].min()), 3) if ((ti < 1.85) & (us > 0.5)).any() else None],
             seam_step_mm=[round(float((wi - wo).min()), 3), round(float((wi - wo).max()), 3)],
             seam_step_at_u0_22=round(float(np.interp(0.22, us, wi - wo)), 3))
    # half_rows (export / render geometry) vs own skin
    S, lab, U = AS.cloud(vid, 0.08)
    for half, lb in (("vonk", 1), ("vnut", 0)):
        rows, a, b = VB.half_rows(vid, half, 170, 120)
        P = rows.reshape(-1, 3)
        cc = AS.secf(vid, np.clip(-P[:, 2] / 72, 0, 1))[0]
        dome = np.abs(P[:, 0] - cc) > 0.3            # skip the seam chord points
        d, _ = cKDTree(S[lab == lb]).query(P[dome])
        R[f"half_rows_{half}_vs_skin_max"] = round(float(d.max()), 3)
        R[f"half_rows_{half}_u_range"] = [round(float(-rows[0, 0, 2] / 72), 4), round(float(-rows[-1, 0, 2] / 72), 4)]
    OUT[vid] = R
    print(vid, R, flush=True)
json.dump(OUT, open("out/seam.json", "w"), indent=1)

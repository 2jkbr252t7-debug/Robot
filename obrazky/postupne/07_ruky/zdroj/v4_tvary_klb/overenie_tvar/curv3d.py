"""3-D principal curvatures (implicit level-set, central differences) of the shelled part of each arm (above the black tip
plane), per half: min convex radius and where.  Points within 0.01 of the seam plane are skipped (both halves meet with
a common tangent there; checked separately)."""
import sys, json
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB; L = 72.0
OUT = {}
for vid in ["B0", "B1", "B2", "B3"]:
    def F(P):
        uu = np.clip(-P[:, 2] / L, 1e-9, 1 - 1e-9)
        c, ti, to, wi, wo, ni, no = AS.secf(vid, uu)
        dx = P[:, 0] - c; out = dx >= 0
        t = np.where(out, to, ti); w = np.where(out, wo, wi); n = np.where(out, no, ni)
        return (np.abs(dx) / t) ** n + (np.abs(P[:, 1]) / w) ** n - 1.0
    S, lab, U = AS.cloud(vid, 0.15)
    pt, nrm_t = VB.tip_plane_local(vid)
    c_ = AS.secf(vid, np.clip(U, 1e-9, 1 - 1e-9))[0]
    hh = 2e-3
    keep = (lab < 2) & (np.abs(S[:, 0] - c_) > 0.01) & (U > 3e-4) & ((S - pt) @ nrm_t < 0)
    P = S[keep]; lb = lab[keep]; Uk = U[keep]
    E = np.eye(3) * hh
    f0 = F(P)
    g = np.stack([(F(P + E[i]) - F(P - E[i])) / (2 * hh) for i in range(3)], 1)
    H = np.zeros((len(P), 3, 3))
    for i in range(3):
        for j in range(i, 3):
            if i == j:
                H[:, i, i] = (F(P + E[i]) - 2 * f0 + F(P - E[i])) / hh ** 2
            else:
                v = (F(P + E[i] + E[j]) - F(P + E[i] - E[j]) - F(P - E[i] + E[j]) + F(P - E[i] - E[j])) / (4 * hh * hh)
                H[:, i, j] = H[:, j, i] = v
    gn = np.linalg.norm(g, axis=1); nn = g / gn[:, None]
    Pm = np.eye(3)[None] - nn[:, :, None] * nn[:, None, :]
    ev = np.sort(np.linalg.eigvalsh(Pm @ H @ Pm / gn[:, None, None]), axis=1)
    kmax = ev[:, 2]
    R = {}
    for lbv, name in ((0, "inner"), (1, "outer")):
        m = (lb == lbv) & np.isfinite(kmax)
        j = int(np.argmax(np.where(m, kmax, -1)))
        R[name] = dict(min_convex_radius=round(float(1 / kmax[j]), 3), at_u=round(float(Uk[j]), 3), at_local=P[j].round(2).tolist(),
                       r_p999=round(float(1 / np.quantile(kmax[m], 0.999)), 3),
                       area_frac_radius_below_1p9=round(float((kmax[m] > 1 / 1.9).mean()), 4),
                       concave=round(float(ev[m, 0].min()), 4))
        for lo_, hi_ in ((0, 0.1), (0.1, 0.5), (0.5, 0.8), (0.8, 1.0)):
            mm = m & (Uk >= lo_) & (Uk < hi_)
            if mm.any():
                R[name][f"min_r_u{lo_}-{hi_}"] = round(float(1 / kmax[mm].max()), 3)
    OUT[vid] = R
    print(vid, json.dumps(R), flush=True)
json.dump(OUT, open("out/curv3d.json", "w"), indent=1)

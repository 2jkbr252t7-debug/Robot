"""smoothness of the R4 arm variants (own numerics, CAD venv):
 A  outline curves along the arm (outer face line x = c + to, inner face line x = c - ti, side outlines y = wi / wo, seam
    x = c) as plane curves over z = -72 u: curvature kappa(z); C1 / C2 breaks found from one-sided differences at two step
    sizes (a real jump keeps its size when the step shrinks, a continuous fast change does not)
 B  section curves (each u): curvature along the closed section, min radius per half, curvature on both sides of the seam
 C  principal curvatures of the 3-D surface (implicit level-set formula, central differences) -> min convex radius per half
    (offset-ability of a 1.2 cover / 1.6 inner wall), incl. both dome ends"""
import sys, json, math
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/overenie_tvar"); import armsurf_own as AS
VB = AS.VB
L = VB.L
vids = sys.argv[1].split(",") if len(sys.argv) > 1 else ["B0", "B1", "B2", "B3"]
OUT = {}


def lines(vid, u):
    c, ti, to, wi, wo, ni, no = AS.secf(vid, u)
    return dict(outer=c + to, inner=c - ti, side_in=wi, side_out=wo, seam=c, n_in=ni, n_out=no)


def kappa(f, u):
    """curvature of the plane curve (z = -L u, f(u)) (1/mm), f in mm"""
    z = -L * u
    f1 = np.gradient(f, z); f2 = np.gradient(f1, z)
    return f2 / (1 + f1 ** 2) ** 1.5, f1


def breaks(vid, key, lo=0.02, hi=0.98):
    """C1 / C2 break search: second derivative from the left vs from the right at every grid point (one-sided 3-point
    stencils), steps du = 1e-3 and 2.5e-4; reports the largest |jump| in d2f/dz2 (1/mm) that does not shrink with the step"""
    res = []
    for du in (1e-3, 2.5e-4):
        u = np.arange(lo, hi, du / 4)
        fm = lambda k: lines(vid, u + k * du)[key]
        f0, fl1, fl2, fr1, fr2 = fm(0), fm(-1), fm(-2), fm(1), fm(2)
        dz = L * du
        d2l = (f0 - 2 * fl1 + fl2) / dz ** 2; d2r = (f0 - 2 * fr1 + fr2) / dz ** 2
        d1l = (3 * f0 - 4 * fl1 + fl2) / (2 * dz); d1r = -(-3 * f0 + 4 * fr1 - fr2) / (2 * dz)
        res.append((u, np.abs(d2l - d2r), np.abs(d1l - d1r)))
    (u1, j1, s1), (u2, j2, s2) = res
    k = int(np.argmax(j2)); kk = int(np.argmin(np.abs(u1 - u2[k])))
    w = slice(max(0, kk - 8), kk + 9)
    return dict(u=round(float(u2[k]), 4), d2_jump_fine=round(float(j2[k]), 5), d2_jump_coarse=round(float(j1[w].max()), 5),
                slope_jump_fine=round(float(s2.max()), 5), slope_jump_at_u=round(float(u2[int(np.argmax(s2))]), 4))


for vid in vids:
    R = {}
    u = np.linspace(0.0005, 0.9995, 400001)
    Ls = lines(vid, u)
    R["A"] = {}
    for key in ("outer", "inner", "side_in", "side_out", "seam"):
        k, f1 = kappa(Ls[key], u)
        kk = np.abs(k)
        m = (u > 0.01) & (u < 0.99)
        R["A"][key] = dict(max_abs_kappa=round(float(kk[m].max()), 4), at_u=round(float(u[m][np.argmax(kk[m])]), 4),
                           min_radius_mm=round(float(1 / kk[m].max()), 2), **breaks(vid, key))
    # exponent functions
    R["A"]["exponents"] = dict(n_in=[round(float(Ls["n_in"].min()), 3), round(float(Ls["n_in"].max()), 3)],
                               n_out=[round(float(Ls["n_out"].min()), 3), round(float(Ls["n_out"].max()), 3)])
    # B sections
    worst = {0: (1e9, None), 1: (1e9, None)}
    seamk = []
    for uu in np.linspace(0.01, 0.99, 197):
        c, ti, to, wi, wo, ni, no = [float(np.ravel(v)[0]) for v in AS.secf(vid, np.array([uu]))]
        for lb, (t, w, n) in enumerate(((ti, wi, ni), (to, wo, no))):
            a = np.linspace(-np.pi / 2, np.pi / 2, 200001)
            x = t * np.abs(np.cos(a)) ** (2 / n); y = w * np.sign(np.sin(a)) * np.abs(np.sin(a)) ** (2 / n)
            x1, y1 = np.gradient(x, a), np.gradient(y, a); x2, y2 = np.gradient(x1, a), np.gradient(y1, a)
            kap = np.abs(x1 * y2 - y1 * x2) / (x1 ** 2 + y1 ** 2) ** 1.5
            inner = (np.abs(a) < np.pi / 2 - 1e-3)
            j = int(np.argmax(np.where(inner, kap, 0)))
            if 1 / kap[j] < worst[lb][0]:
                worst[lb] = (1 / kap[j], dict(u=round(uu, 3), t=round(t, 2), w=round(w, 2), n=round(n, 2)))
        seamk.append(uu)
    R["B"] = {"min_section_radius_inner": [round(worst[0][0], 3), worst[0][1]], "min_section_radius_outer": [round(worst[1][0], 3), worst[1][1]]}
    # C principal curvatures via the implicit function F (branch by side; points kept >= 3 h from the seam plane)
    def F(P):
        uu = np.clip(-P[:, 2] / L, 1e-9, 1 - 1e-9)
        c, ti, to, wi, wo, ni, no = AS.secf(vid, uu)
        dx = P[:, 0] - c
        out = dx >= 0
        t = np.where(out, to, ti); w = np.where(out, wo, wi); n = np.where(out, no, ni)
        return (np.abs(dx) / t) ** n + (np.abs(P[:, 1]) / w) ** n - 1.0
    S, lab, U = AS.cloud(vid, 0.25)
    keep = (lab < 2)
    c_ = AS.secf(vid, np.clip(U, 1e-9, 1 - 1e-9))[0]
    hh = 2e-3
    keep &= np.abs(S[:, 0] - c_) > 4 * hh
    keep &= (U > 2e-4) & (U < 1 - 2e-4)
    P = S[keep]; lb = lab[keep]; Uk = U[keep]
    E = np.eye(3) * hh
    g = np.stack([(F(P + E[i]) - F(P - E[i])) / (2 * hh) for i in range(3)], 1)
    H = np.zeros((len(P), 3, 3))
    f0 = F(P)
    for i in range(3):
        for j in range(i, 3):
            if i == j:
                H[:, i, i] = (F(P + E[i]) - 2 * f0 + F(P - E[i])) / hh ** 2
            else:
                v = (F(P + E[i] + E[j]) - F(P + E[i] - E[j]) - F(P - E[i] + E[j]) + F(P - E[i] - E[j])) / (4 * hh * hh)
                H[:, i, j] = H[:, j, i] = v
    gn = np.linalg.norm(g, axis=1)
    nrm = g / gn[:, None]
    # shape operator on the tangent plane: -(I - nn) H (I - nn) / |g|  -> eigenvalues = principal curvatures (convex > 0 with outward n)
    Pm = np.eye(3)[None] - nrm[:, :, None] * nrm[:, None, :]
    Sh = Pm @ H @ Pm / gn[:, None, None]
    ev = np.linalg.eigvalsh(Sh)
    # two non-trivial eigenvalues = the ones with the largest |value| apart from the ~0 one along n
    ev_sorted = np.sort(ev, axis=1)
    kmax = ev_sorted[:, 2]
    ok = np.isfinite(kmax)
    for lbv, name in ((0, "inner"), (1, "outer")):
        m = ok & (lb == lbv)
        j = int(np.argmax(np.where(m, kmax, -1)))
        R.setdefault("C", {})[name] = dict(max_convex_kappa=round(float(kmax[j]), 4), min_convex_radius=round(float(1 / kmax[j]), 3),
                                           at_local=P[j].round(2).tolist(), at_u=round(float(Uk[j]), 4),
                                           radius_p01=round(float(1 / np.quantile(kmax[m], 0.999)), 3),
                                           concave_min_kappa=round(float(ev_sorted[m, 0].min()), 4))
        for lo_, hi_ in ((0, 0.05), (0.05, 0.95), (0.95, 1.0)):
            mm = m & (Uk >= lo_) & (Uk < hi_)
            if mm.any():
                R["C"][name][f"min_radius_u{lo_}-{hi_}"] = round(float(1 / kmax[mm].max()), 3)
    OUT[vid] = R
    print(vid, json.dumps(R, indent=None), flush=True)
json.dump(OUT, open("out/smooth_%s.json" % "_".join(vids), "w"), indent=1)

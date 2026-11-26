"""Magnetic preload of the B1 arm clutch.  Axially magnetised NdFeB disc (D x h) attracting a soft-steel washer.
Model: surface-charge (Coulomb) model of the disc, perfect-permeability plate replaced by the image magnet (attraction,
face gap 2g).  Force between two coaxial uniformly charged discs by numerical double integration.
The ideal-plate result is then (a) checked against published catalogue pull forces at contact and (b) scaled with the
gap ratio F(g)/F(0) of the model -> per-magnet force through the printed 0.3 mm skin.  A thin washer (1.6-2.0 mm)
saturates partially: a knock-down factor KW is applied (range given).
Run: /opt/venv/cad/bin/python magnets.py -> magnets.json"""
import math, json
import numpy as np

MU0 = 4e-7 * math.pi


def disc_pts(a, n=26):
    """quadrature points (r, phi) with area weights on a disc of radius a (mm)"""
    r_edges = np.linspace(0, a, n + 1)
    pts, w = [], []
    for i in range(n):
        r0, r1 = r_edges[i], r_edges[i + 1]
        rc = 0.5 * (r0 + r1)
        m = max(6, int(2 * math.pi * rc / (a / n)))
        ph = (np.arange(m) + 0.5) * 2 * math.pi / m
        area = math.pi * (r1 ** 2 - r0 ** 2) / m
        pts.append(np.c_[rc * np.cos(ph), rc * np.sin(ph)]); w.append(np.full(m, area))
    return np.concatenate(pts), np.concatenate(w)


P, Wt = disc_pts(1.0)


def disc_force(a, d, sig1=1.0, sig2=1.0):
    """axial force (N) between two coaxial discs radius a (mm) at axial distance d (mm), surface charge sig (A/m)
    F = mu0 sig1 sig2 / (4 pi) * int int d / |r|^3 dA1 dA2   (positive = repulsive for like signs)"""
    p = P * a; w = Wt * a * a
    dx = p[:, None, 0] - p[None, :, 0]; dy = p[:, None, 1] - p[None, :, 1]
    r2 = dx * dx + dy * dy + d * d
    I = np.sum(w[:, None] * w[None, :] * d / r2 ** 1.5)          # mm^4 / mm^3 = mm
    return MU0 * sig1 * sig2 / (4 * math.pi) * I * 1e-6             # I in mm^2 -> m^2


def magnet_plate(D, h, Br, g):
    """attraction (N) of a disc magnet (D, h mm, remanence Br T) to an ideal soft-iron half-space at face gap g (mm)"""
    M = Br / MU0                       # A/m
    a = D / 2
    # magnet faces: near face (+M) at 0, far face (-M) at -h.  Image: near face (-M) at 2g, far face (+M) at 2g + h
    F = 0.0
    for z1, s1 in ((0.0, 1), (-h, -1)):
        for z2, s2 in ((2 * g, -1), (2 * g + h, 1)):
            d = z2 - z1
            F += disc_force(a, d, s1 * M, s2 * M)                 # >0 repulsive
    # convert: disc_force uses mm for lengths; sigma in A/m -> mu0 sig^2 * mm^2 = T*A/m*mm^2 = N/m * 1e-6 m^2 / m... handled
    return -F


if __name__ == "__main__":
    # unit check: large thin discs -> pressure B^2/(2mu0) ... use catalogue data instead (more relevant)
    cat = {"4x2 N35": (4, 2, 1.19, (2.8, 3.7)), "5x2 N38": (5, 2, 1.23, (4.9, 4.9)), "5x2 N52": (5, 2, 1.44, (6.7, 6.7))}
    out = {}
    for k, (D, h, Br, pull) in cat.items():
        f0 = magnet_plate(D, h, Br, 0.02)
        rows = {f"{g:.2f}": round(magnet_plate(D, h, Br, g) / f0, 3) for g in (0.02, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 2.0, 3.0)}
        out[k] = dict(ideal_contact_N=round(f0, 2), catalogue_pull_N=pull, catalogue_over_ideal=round(pull[0] / f0, 2),
                      gap_ratio=rows)
        print(k, "ideal contact %.2f N, catalogue %s N" % (f0, pull), "ratio F(g)/F(0):", rows)
    # B1 clutch: 8 pockets at r 8.0 mm for 5x2 discs, 0.25 mm printed skin, DIN 125 M10 washer (10.5x20x2.0) in the arm hub
    KW = (0.6, 0.85)                   # finite 2.0 mm washer, partial saturation (alternating poles); 1.0 = thick plate
    mu = (0.15, 0.25, 0.40)            # printed resin skin on zinc-plated steel: graphite ... clean dry ... worst dry
    r = 0.0077
    skin = 0.25
    out["clutch"] = {}
    for k in ("5x2 N38", "5x2 N52"):
        D, h, Br, pull = cat[k]
        f0 = magnet_plate(D, h, Br, 0.02)
        gr = magnet_plate(D, h, Br, skin) / f0
        F = [pull[0] * gr * kw for kw in KW]
        tab = {}
        for n in range(3, 9):
            lo = n * F[0] * mu[0] * r; mid = n * 0.5 * (F[0] + F[1]) * mu[1] * r; hi = n * F[1] * mu[2] * r
            tab[n] = dict(T_low=round(lo, 4), T_mid=round(mid, 4), T_high=round(hi, 4), F_total_mid=round(n * 0.5 * (F[0] + F[1]), 1))
        out["clutch"][k] = dict(gap_ratio_skin=round(gr, 3), per_magnet_N=[round(f, 2) for f in F], slip_torque_by_count=tab)
        print(k, "per magnet through %.2f skin: %s N" % (skin, [round(f, 2) for f in F]))
        for n, v in tab.items():
            print(f"   {n} magnets: slip {v['T_low']:.4f} .. {v['T_mid']:.4f} .. {v['T_high']:.4f} N.m  (total pull ~{v['F_total_mid']} N)")
    out["clutch"]["assumptions"] = dict(KW=KW, mu=mu, r_m=r, skin=skin, catalogue_pull="research B / first4magnets (unverified)")
    json.dump(out, open("magnets.json", "w"), indent=1)

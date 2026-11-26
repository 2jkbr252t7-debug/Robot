"""VERIFIER: magnet clutch of B1+ - own surface-charge model of a 5x2 axially magnetised NdFeB disc against an ideal
(mu -> inf) plate by the image method, force vs gap; calibration to catalogue contact values; per-magnet slip torque at
r 7.7; how many magnets the window 0.0124..0.0170 N.m needs; coin test arithmetic; torque order vs the tooth limit.
Writes v_magnet.json"""
import json, math
import numpy as np

mu0 = 4e-7 * math.pi
def disc_pts(a, n_r=40, z=0.0):
    pts, w = [], []
    edges = np.linspace(0, a, n_r + 1)
    for i in range(n_r):
        r0, r1 = edges[i], edges[i + 1]; rm = 0.5 * (r0 + r1)
        nt = max(6, int(2 * math.pi * rm / (a / n_r)))
        th = np.linspace(0, 2 * math.pi, nt, endpoint=False) + (i % 2) * math.pi / nt
        area = math.pi * (r1 ** 2 - r0 ** 2) / nt
        pts.append(np.c_[rm * np.cos(th), rm * np.sin(th), np.full(nt, z)]); w.append(np.full(nt, area))
    return np.concatenate(pts), np.concatenate(w)

def force_on_plate(Br, D, L, g, n_r=40):
    """attraction (N) of a disc magnet (diameter D, length L, mm) whose face is g (mm) from an ideal plate"""
    a = D / 2 * 1e-3; L *= 1e-3; g *= 1e-3
    M = Br / mu0
    P, W = disc_pts(a, n_r)
    # magnet faces: +M at z = g (near face), -M at z = g + L ; images (opposite sign) at -g and -(g + L)
    src = [(+1, g), (-1, g + L)]
    img = [(-1, -g), (+1, -(g + L))]
    F = 0.0
    for s1, z1 in src:
        for s2, z2 in img:
            # force on charges s1 (in magnet) from s2 (image), axial component, point-pairs
            dz = z1 - z2
            dx = P[:, None, 0] - P[None, :, 0]; dy = P[:, None, 1] - P[None, :, 1]
            r3 = (dx ** 2 + dy ** 2 + dz ** 2) ** 1.5
            fz = (mu0 / (4 * math.pi)) * (s1 * M) * (s2 * M) * (W[:, None] * W[None, :]) * dz / r3
            F += fz.sum()
    return -F      # positive = attraction toward the plate

OUT = {}
Br = 1.24     # N38 nominal 1.22-1.26 T
gaps = [0.0, 0.05, 0.10, 0.15, 0.25, 0.30, 0.35, 0.45, 0.65, 0.85]
Fid = {g: force_on_plate(Br, 5.0, 2.0, max(g, 0.01), n_r=36) for g in gaps}
OUT["ideal_force_N"] = {str(g): round(v, 3) for g, v in Fid.items()}
# NOTE: the point-pair model is not converged at g -> 0 (element 0.07 mm), so no contact value is used.  Per-magnet force =
# ideal force at the effective gap (0.27..0.35 = 0.25 skin + roughness / zinc) x real-plate factor 0.5..0.85 (finite 2 mm washer,
# zinc, flatness, catalogue-vs-ideal experience).
res = {}
for ge in (0.27, 0.35):
    Fi = float(np.interp(ge, gaps[1:], [Fid[g] for g in gaps[1:]]))
    for kf in (0.5, 0.85):
        res[f"gap {ge} factor {kf}"] = round(Fi * kf, 3)
OUT["per_magnet_force_N"] = res
Fmin, Fmax = min(res.values()), max(res.values())
r_m = 7.7e-3
OUT["per_magnet_slip_Nm"] = dict(min=round(Fmin * 0.25 * r_m, 4), max=round(Fmax * 0.40 * r_m, 4))
win = (0.0124, 0.0170)
tab = {}
for F in (Fmin, 1.5, 2.0, 2.5, 3.0, Fmax):
    for mu in (0.25, 0.32, 0.40):
        t = F * mu * r_m
        ns = [n for n in range(1, 9) if win[0] <= n * t <= win[1]]
        tab[f"F {F:.2f} mu {mu}"] = dict(per_magnet=round(t, 4), counts_in_window=ns)
OUT["counts"] = tab
# coin test arithmetic (EUR coins: 2E 8.50 g, 50c 7.80 g, 20c 5.74 g, 10c 4.10 g)
g0 = 9.81
def Tcoin(m, r=0.060): return m * 1e-3 * g0 * r
OUT["coin"] = dict(hold_2E_20c_coins_only=round(Tcoin(14.24), 5), slip_2E_50c_20c_coins_only=round(Tcoin(22.04), 5),
                   arm_gravity_assumed=0.004, hold_total=round(Tcoin(14.24) + 0.004, 5), slip_total=round(Tcoin(22.04) + 0.004, 5),
                   note="window depends 1:1 on the arm's own gravity torque at horizontal (assumed 0.004); +-0.001 error shifts both ends")
json.dump(OUT, open("/tmp/claude-0/gapwf/fin/R2c/overenie_geo/v_magnet.json", "w"), indent=1)
print(json.dumps(OUT, indent=1))

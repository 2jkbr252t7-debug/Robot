"""search: SCS0009 standing (shaft +Z) with its shaft on the vertical line through (xs, ys) - the line that meets the shoulder axis
(ys = 3).  Case rotation theta about Z, top z_top.  Screening on k3map.npz (ds >= 0.3+0.25 to HARD, dm >= 1.0+0.25 to MOVING).
usage: fit_vert.py side(L|R) H_case ears(0|1) [ys]"""
import sys, os, json, math, itertools
sys.dont_write_bytecode = True
import numpy as np
from scipy.ndimage import map_coordinates
HERE = os.path.dirname(os.path.abspath(__file__))
D = np.load(os.path.join(HERE, "k3map.npz"))
lo, h = D["lo"], float(D["h"]); ds, dm = D["ds"], D["dm"]
side = sys.argv[1]; Hc = float(sys.argv[2]); ears = int(sys.argv[3]); ys = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
sgn = 1.0 if side == "L" else -1.0
Lc, Wc, SH = 23.2, 12.1, 5.9


def servo_pts(Hc, ears, step=0.5):
    """local frame: shaft axis = z, top face z=0, case x in [-SH, Lc-SH], y in [-W/2, W/2], z in [-Hc, 0]"""
    P = []
    xs = np.arange(-SH, Lc - SH + 1e-6, step); ysl = np.arange(-Wc / 2, Wc / 2 + 1e-6, step); zs = np.arange(-Hc, 1e-6, step)
    G = np.array(list(itertools.product(xs, ysl, zs)))
    on = (np.isclose(G[:, 0], xs[0]) | np.isclose(G[:, 0], xs[-1]) | np.isclose(G[:, 1], ysl[0]) | np.isclose(G[:, 1], ysl[-1]) |
          np.isclose(G[:, 2], zs[0]) | np.isclose(G[:, 2], zs[-1]))
    P.append(G[on])
    # boss + spline on top (boss d7 x 1, spline d4 x 3.75)
    for r, z0, z1 in ((3.5, 0.0, 1.0), (2.0, 1.0, 4.75)):
        th = np.linspace(0, 2 * np.pi, 24, endpoint=False)
        for z in np.arange(z0, z1 + 1e-6, step):
            P.append(np.c_[r * np.cos(th), r * np.sin(th), np.full_like(th, z)])
    if ears:
        ex = np.arange(-SH - 4.55, Lc - SH + 4.55 + 1e-6, step); ez = np.arange(-6.8, -4.3 + 1e-6, step)
        E = np.array(list(itertools.product(ex, ysl, ez)))
        E = E[(E[:, 0] < -SH) | (E[:, 0] > Lc - SH)]
        P.append(E)
    # cable exit at the far end, bottom: 3 x 4 x 3 lump
    cx = np.arange(Lc - SH, Lc - SH + 3.0 + 1e-6, step); cy = np.arange(-2.0, 2.0 + 1e-6, step); cz = np.arange(-Hc, -Hc + 3.0 + 1e-6, step)
    P.append(np.array(list(itertools.product(cx, cy, cz))))
    return np.concatenate(P)


P0 = servo_pts(Hc, ears)
def check(xs, th, zt):
    c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
    Q = np.c_[xs + c * P0[:, 0] - s * P0[:, 1], ys + s * P0[:, 0] + c * P0[:, 1], zt + P0[:, 2]]
    I = ((Q - lo) / h - 0.5).T
    a = map_coordinates(ds, I, order=1, mode="nearest"); b = map_coordinates(dm, I, order=1, mode="nearest")
    return float((a - 0.55).min()), float((b - 1.25).min())
res = []
for xs in np.arange(35.0, 43.01, 0.5):
    for th in range(0, 360, 10):
        for zt in np.arange(-56.0, -27.9, 1.0):
            a, b = check(sgn * xs, th, zt)
            res.append((min(a, b), xs, th, zt, a, b))
res.sort(reverse=True)
ok = [r for r in res if r[0] >= 0]
print(f"side {side} Hc {Hc} ears {ears}: feasible {len(ok)} / {len(res)}")
best_top = {}
for r in ok:
    k = (r[1], r[2])
    if k not in best_top or r[3] > best_top[k][3]: best_top[k] = r
hi = sorted(best_top.values(), key=lambda r: -r[3])[:15]
for r in hi: print("  xs %5.2f th %3d z_top %6.1f  margin_hard %5.2f margin_move %5.2f" % (r[1], r[2], r[3], r[4], r[5]))
print("best margins:", [tuple(round(v, 2) for v in r) for r in res[:5]])
json.dump(dict(side=side, Hc=Hc, ears=ears, feasible=len(ok), highest=[list(map(float, r)) for r in hi], best=[list(map(float, r)) for r in res[:20]]),
          open(os.path.join(HERE, f"fit_vert_{side}_{Hc}_{ears}.json"), "w"), indent=1)

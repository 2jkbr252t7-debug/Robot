import sys, numpy as np
sys.path.insert(0, "."); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
from dd_shift import case_pts
import armgeo as G
xs = np.linspace(40, 110, 3501)
def skins(yz, dx):
    Q = np.stack([xs, np.full_like(xs, yz[0]), np.full_like(xs, yz[1])], 1)
    ins = G.inside_local(G.to_local(Q, dx=dx))
    if not ins.any(): return None, None
    i = np.where(ins)[0]; return xs[i[0]], xs[i[-1]]
cases = {"KST X06 20x7x16.6 s5": (20.0, 7.0, 16.6, 5.0), "KST X08 23.5x8x16.8 s5.5": (23.5, 8.0, 16.8, 5.5),
         "ES9052MD 19.9x8.8x23.1 s4.7": (19.9, 8.8, 23.1, 4.7), "SCS0009 case 21.5 (if 25.25 incl. spline)": (23.2, 12.1, 21.5, 5.9),
         "SCS0009 case 25.25": (23.2, 12.1, 25.25, 5.9), "MG90S 22.8x12.2x22.7 s5.9": (22.8, 12.2, 22.7, 5.9)}
for k, (Lc, Wc, Hc, s) in cases.items():
    P = case_pts(Lc, Wc, Hc, s, 59.056, n=12)
    res = None
    for dx in np.arange(0.0, 20.01, 0.25):
        okw = G.inside_local(G.to_local(P, dx=dx), inset=2.0)
        bad = 0; inb = 0.0; rmax_inb = 0.0
        for p, o in zip(P, okw):
            si, so = skins(p[1:], dx)
            if si is None:
                if not o: bad += 1
                continue
            if not o and p[0] > 0.5 * (si + so): bad += 1
            if p[0] < si:
                inb = max(inb, si - p[0]); rmax_inb = max(rmax_inb, np.hypot(p[1] - 3.0, p[2] + 17.0))
        if bad == 0:
            res = (dx, inb, rmax_inb); break
    if res:
        print(f"{k:42s} outward shift {res[0]:5.2f} mm; case reaches {res[1]:4.1f} mm inboard of the white skin, up to r {res[2]:4.1f} from the axis there")
    else:
        print(f"{k:42s} no fit up to 20 mm")

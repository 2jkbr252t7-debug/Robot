"""fine search at fixed |xs| (vertical servo coaxial with the drive shaft), theta 230..310 step 2, z_top step 0.25"""
import sys, os, math
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
side, Hc, ears, xs = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
sys.argv = [sys.argv[0], side, Hc, ears, "3.0"]
src = open(os.path.join(HERE, "fit_vert.py")).read().split("res = []")[0]
exec(src)
best = []
for th in range(230, 311, 2):
    for zt in np.arange(-56.0, -41.9, 0.25):
        a, b = check(sgn * xs, th, zt)
        best.append((min(a, b), th, zt, a, b))
ok = [r for r in best if r[0] >= 0]
print(f"{side} Hc {Hc} ears {ears} xs {xs}: feasible {len(ok)}")
if ok:
    top = max(r[2] for r in ok); print("  highest top z", top, [tuple(round(v, 2) for v in r) for r in ok if r[2] == top][:4])
    m = max(ok); print("  max margin", tuple(round(v, 2) for v in m))
    for zt in (-44.0, -45.0, -46.0, -47.0, -48.0):
        rr = [r for r in ok if abs(r[2] - zt) < 1e-6]
        if rr: r = max(rr); print("   top %.1f best th %d margin hard %.2f move %.2f" % (zt, r[1], r[3], r[4]))

import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); import os; os.chdir("/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
# inner x at (y,z): march inward along x until the point is >= WALL from the outer surface (use inner_section)
ys = [-28, -24, -20, -16, -12, -8, -4, 0, 3, 6, 10, 14, 18, 22, 26]
print("z \\ y " + " ".join(f"{y:6d}" for y in ys))
for z in [-10, -17, -24, -31, -35, -40, -45, -50, -55, -60, -65, -70, -75, -78, -80]:
    sec = C.inner_section(z)   # (count,3) inner points
    # interpolate inner x at y for x>0 side
    P = sec[sec[:, 0] > 0]
    row = []
    for y in ys:
        # find crossing of y on polyline P (x>0)
        o = np.argsort(P[:, 1]); yy = P[o, 1]; xx = P[o, 0]
        row.append(np.interp(y, yy, xx) if yy.min() <= y <= yy.max() else np.nan)
    print(f"{z:5d} " + " ".join(f"{v:6.2f}" for v in row), f"   outer y=3: {C.x_surface(3, z):.2f}")

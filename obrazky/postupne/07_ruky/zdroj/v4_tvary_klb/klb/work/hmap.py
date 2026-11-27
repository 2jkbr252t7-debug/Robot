import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import t4_common as C
vid = "B"
xs = np.arange(44.0, 70.0, 0.02)
def arm_x(y, z):
    L = np.c_[xs, np.full_like(xs, y), np.full_like(xs, z)]
    ins = VA.inside_local(vid, VA.to_local(L))
    return xs[ins].min() if ins.any() else np.nan
print("arm inner face x at rest (B), rows r, cols az 0(back) 30 60 90(up) ... ")
for r in (0, 4, 7, 8, 9, 10, 11, 12, 13, 13.5, 14, 15, 16):
    row = []
    for a in range(0, 360, 30):
        t = np.radians(a); y = 3 + r*np.cos(t); z = -17 + r*np.sin(t)
        row.append(arm_x(y, z))
    print(f"r {r:5.1f}", " ".join(f"{v:6.2f}" for v in row), " min %.2f" % np.nanmin(row))
# min arm x per radius ring (fine)
print("min over az of arm inner x per r:")
for r in np.arange(0, 17.1, 1.0):
    vals = []
    for a in np.arange(0, 360, 3):
        t = np.radians(a); vals.append(arm_x(3 + r*np.cos(t), -17 + r*np.sin(t)))
    vals = np.array(vals); k = np.nanargmin(vals)
    print(f"r {r:4.1f} min {np.nanmin(vals):6.2f} at az {k*3}  max {np.nanmax(vals):6.2f}")

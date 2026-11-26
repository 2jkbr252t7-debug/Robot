"""probe the official SC09 horn STEP: per solid, slice areas along the hub axis to see where the arm sits on the hub"""
import sys, numpy as np
from build123d import import_step, Box, Pos
f = "/tmp/claude-0/gapwf/fin/R2c/prieskum_tlacene/dl/z2/SC09-ARM.step"
S = import_step(f)
for i, so in enumerate(S.solids()):
    bb = so.bounding_box()
    sz = (bb.size.X, bb.size.Y, bb.size.Z)
    ax = int(np.argmin(sz))      # thin direction = hub axis
    print("solid", i, "size", np.round(sz, 2), "axis", "XYZ"[ax], "min", np.round([bb.min.X, bb.min.Y, bb.min.Z], 2))
    lo = [bb.min.X, bb.min.Y, bb.min.Z][ax]; hi = [bb.max.X, bb.max.Y, bb.max.Z][ax]
    c = bb.center()
    for t in np.linspace(lo + 0.1, hi - 0.1, 8):
        d = [400, 400, 400]; d[ax] = 0.05
        p = [c.X, c.Y, c.Z]; p[ax] = t
        cut = so & (Pos(*p) * Box(*d))
        try:
            b2 = cut.bounding_box(); a = cut.volume / 0.05
            print("   at %.2f  slice area %.1f  extent %s" % (t - lo, a, np.round([b2.size.X, b2.size.Y, b2.size.Z], 2)))
        except Exception as e:
            print("   at %.2f  empty" % (t - lo))

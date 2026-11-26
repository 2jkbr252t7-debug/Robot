"""inner bore profile of the horns along the hub axis (Y): spline vs screw counterbore position relative to the arm plate"""
import numpy as np
from build123d import import_step, Box, Pos
S = import_step("/tmp/claude-0/gapwf/fin/R2c/prieskum_tlacene/dl/z2/SC09-ARM.step")
for i, so in enumerate(S.solids()[:2]):
    bb = so.bounding_box()
    # hub centre: the arm extends in -Z from the hub; hub circle at the max-Z end
    cx = (bb.min.X + bb.max.X) / 2; cz = bb.max.Z - bb.size.X / 2
    print("solid", i, "hub centre x %.2f z %.2f" % (cx, cz))
    for y in np.linspace(0.05, bb.size.Y - 0.05, 14):
        th = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        rin = []
        for t in th:
            # march outward from the centre along direction t until inside material
            for r in np.arange(0.5, 3.6, 0.025):
                p = (cx + r * np.cos(t), y, cz + r * np.sin(t))
                if so.is_inside(p):
                    rin.append(r); break
            else:
                rin.append(np.nan)
        rin = np.array(rin)
        print("   y %.2f  inner r min %.3f max %.3f  mean %.3f" % (y, np.nanmin(rin), np.nanmax(rin), np.nanmean(rin)))

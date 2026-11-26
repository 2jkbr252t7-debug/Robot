import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as VL
for f in ("/tmp/claude-0/gapwf/fin/T4/stl/T_bok_L.stl", "stl_mod/T_bok_L.stl"):
    tr = VL.vlib.load_stl(f)
    g = VL.Grid((36, -3, -36), (46, 9, -24), 0.25)
    m = VL.vox_solid(tr, g, surface=False)
    xs, ys, zs = g.axis(0), g.axis(1), g.axis(2)
    print(f, m.sum())
    j = np.argmin(abs(ys - 3.0))
    for k in range(len(zs) - 1, -1, -3):
        print("%6.2f " % zs[k] + "".join("#" if m[i, j, k] else "." for i in range(len(xs))))

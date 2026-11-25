import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as VL
tr = VL.vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_spodok.stl")
g = VL.Grid((24, -32, -82), (46, 32, -3), 1.0)
m = VL.vox_solid(tr, g)
np.save("spodok_L.npy", m)
xs, ys, zs = g.axis(0), g.axis(1), g.axis(2)
for z in (-75, -70, -65, -58, -52, -48, -44, -38, -30, -24, -17, -10, -5):
    k = np.argmin(abs(zs - z))
    print("z", zs[k], "  x 24..46 ->, rows y from +31 to -31")
    for j in range(len(ys) - 1, -1, -2):
        print("%5.1f " % ys[j] + "".join("#" if m[i, j, k] else "." for i in range(len(xs))))

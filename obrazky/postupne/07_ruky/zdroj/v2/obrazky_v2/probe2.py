import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as VL
tr = VL.vlib.load_stl("/tmp/claude-0/gapwf/fin/T4/stl/T_spodok.stl")
print("tris", len(tr))
g = VL.Grid((-46, -32, -104), (46, 32, -3), 1.0)
m = VL.vox_solid(tr, g)
np.save("spodok_all.npy", m)
xs, ys, zs = g.axis(0), g.axis(1), g.axis(2)
for z in (-100,-90,-84, -80, -77, -73):
    k = np.argmin(abs(zs - z))
    print("z", zs[k], "  x -46..46 ->, rows y from +31 to -31")
    for j in range(len(ys) - 1, -1, -2):
        print("%5.1f " % ys[j] + "".join("#" if m[i, j, k] else "." for i in range(0,len(xs),1)))

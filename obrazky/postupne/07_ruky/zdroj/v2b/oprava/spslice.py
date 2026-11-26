import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/trup_servo")
import voxlib as VL
tr = VL.vlib.load_stl("/tmp/claude-0/gapwf/fin/R1/img_v2/work/stl_mod/T_spodok.stl")
g = VL.Grid((20, -30, -75), (50, 24, 0), 0.5)
m = VL.vox_solid(tr, g)
np.save("spodok_mod_L.npy", m)
xs, ys, zs = g.axis(0), g.axis(1), g.axis(2)
F = np.load("/tmp/claude-0/gapwf/fin/R2c/vyber/B2c/colfill_B1merge_L.npz")["P"].astype(float)
for zq in [float(a) for a in sys.argv[1:]]:
    k = int(np.argmin(abs(zs - zq))); z = zs[k]
    fz = F[abs(F[:, 2] - z) < 0.26]
    fill = set((int(round((p[0]-xs[0])/0.5)), int(round((p[1]-ys[0])/0.5))) for p in fz)
    print(f"\nz {z:.2f}  x {xs[0]}..{xs[-1]} ->, rows y +24..-30  '#'=T_spodok_mod  'f'=fill  '*'=both")
    for j in range(len(ys)-1, -1, -1):
        r = ""
        for i in range(len(xs)):
            a = m[i, j, k]; b = (i, j) in fill
            r += "*" if a and b else "#" if a else "f" if b else "."
        print("%6.2f " % ys[j] + r)

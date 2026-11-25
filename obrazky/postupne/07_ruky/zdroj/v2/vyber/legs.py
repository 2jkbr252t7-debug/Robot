"""JUDGE: room for the new shoulder-column legs (K3 map: removable parts deleted).  For candidate leg boxes report the
smallest distance to HARD (kept static / outside the shell) and to the moving sweep, per z band."""
import numpy as np, json, sys
M = np.load("/tmp/claude-0/gapwf/fin/R1/K3_preusporiadanie/k3map.npz")
lo, h, n = M["lo"], float(M["h"]), M["n"]; ds, dm = M["ds"], M["dm"]
def box_min(x0,x1,y0,y1,z0,z1, sg=1):
    xs = np.arange(x0+h/2, x1, h); ys = np.arange(y0+h/2, y1, h); zs = np.arange(z0+h/2, z1, h)
    X,Y,Z = np.meshgrid(xs*sg, ys, zs, indexing="ij")
    I = np.floor((np.c_[X.ravel(),Y.ravel(),Z.ravel()] - lo)/h).astype(int)
    a = ds[I[:,0],I[:,1],I[:,2]]; b = dm[I[:,0],I[:,1],I[:,2]]
    return round(float(a.min())-h/2,2), round(float(b.min())-h/2,2)
out = {}
for sg, s in ((1,"L"),(-1,"R")):
    for nm, (y0,y1) in (("front", (-26.0,-19.2)), ("back", (13.8,20.8))):
        rows = []
        for xa, xb in ((34.4,43.4),(34.4,42.0),(34.4,44.5)):
            for z0, z1 in ((-78,-66),(-66,-52),(-52,-40),(-40,-30)):
                if sg < 0: xa_, xb_ = xa, xb
                rows.append(((xa,xb,z0,z1), box_min(xa,xb,y0,y1,z0,z1, sg)))
        out[f"{s} {nm} y {y0}..{y1}"] = rows
for k,v in out.items():
    print(k)
    for r in v: print("   x %.1f..%.1f z %d..%d" % r[0], " ds(hard) %.2f  dm(moving) %.2f" % r[1])

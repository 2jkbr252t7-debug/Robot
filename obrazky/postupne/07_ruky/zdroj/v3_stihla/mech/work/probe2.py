import sys, math
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/home/user/Robot/obrazky/postupne/07_ruky/zdroj/geometria")
import armgeo as A
DX = -1.0
xs = np.arange(44, 80, 0.02)
for kt in (1.0, 0.85, 0.70, 0.57):
    print(f"--- kt {kt}: outer skin x at (r, az) [az 0=+Y(back), 90=+Z(up), 180=front, 270=down]; then min over az; inner skin min/max over az")
    rows=[]
    for r in (0, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):
        xo=[]; xi=[]
        for az in range(0, 360, 15):
            y = 3 + r*math.cos(math.radians(az)); z = -17 + r*math.sin(math.radians(az))
            Q = np.c_[xs, np.full_like(xs, y), np.full_like(xs, z)]
            ins = A.inside_local(A.to_local(Q, kt, DX), kt)
            i = np.where(ins)[0]
            if len(i)==0: xo.append(np.nan); xi.append(np.nan); continue
            xo.append(xs[i[-1]]); xi.append(xs[i[0]])
        xo=np.array(xo); xi=np.array(xi)
        k=int(np.nanargmin(xo))
        print(f" r {r:4.1f}: out min {np.nanmin(xo):6.2f} at az {15*k:3d}  out@az0/90/180/270 {xo[0]:.2f}/{xo[6]:.2f}/{xo[12]:.2f}/{xo[18]:.2f} | in max {np.nanmax(xi):6.2f} in min {np.nanmin(xi):.2f}")

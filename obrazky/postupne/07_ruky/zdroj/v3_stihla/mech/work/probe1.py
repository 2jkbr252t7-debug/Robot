import sys, math
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/home/user/Robot/obrazky/postupne/07_ruky/zdroj/geometria")
import armgeo as A
DX = -1.0
for kt in (1.0, 0.85, 0.70, 0.57):
    xs = np.arange(40, 90, 0.005)
    Q = np.c_[xs, np.full_like(xs, 3.0), np.full_like(xs, -17.0)]
    ins = A.inside_local(A.to_local(Q, kt, DX), kt)
    i = np.where(ins)[0]
    # mid-plane local x=0 on axis
    L = A.to_local(Q, kt, DX)
    xm = xs[np.argmin(abs(L[:, 0]))]
    # local u at the axis
    hw, ht = A.prof(A.U_ATT, kt)
    print(f"kt {kt}: max thickness {2*ht:.2f} (at U_ATT), axis skins {xs[i[0]]:.3f} .. {xs[i[-1]]:.3f} chord {xs[i[-1]]-xs[i[0]]:.2f}, midplane x {xm:.2f}, a_loc {A.a_loc(kt).round(3)}")
# real max thickness
us = np.linspace(0, 1, 2001); hw, ht = A.prof(us)
print("max 2ht", 2*ht.max(), "at u", us[ht.argmax()], "max 2hw", 2*hw.max(), "at", us[hw.argmax()])
print("att world", A.att_world(dx=DX), "R", A.R.round(4))

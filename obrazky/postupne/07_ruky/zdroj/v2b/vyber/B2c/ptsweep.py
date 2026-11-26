"""JUDGE: exact sweep clearance (pan +-90.3, lift 0..20) of small static test bodies: original and K3-relocated F3a_2 screw head"""
import sys, numpy as np, math
import geo as G
D = np.load("mov.npz")
R, L = D["R"].astype(float), D["L"].astype(float); Rt, Lt = D["Rt"], D["Lt"]
lifts = np.arange(0, 20.001, 0.25)
LL = (L[:, None, :] + np.c_[np.zeros_like(lifts), np.zeros_like(lifts), lifts][None]).reshape(-1, 3)
LLt = np.repeat(Lt, len(lifts))
M = np.r_[R, LL]; MT = np.r_[Rt, LLt]
r_m, t_m, z_m = np.hypot(M[:, 0], M[:, 1]), np.degrees(np.arctan2(M[:, 1], M[:, 0])), M[:, 2]
def clr(Q):
    best = (1e9, None)
    for q in Q:
        rq, tq = math.hypot(q[0], q[1]), math.degrees(math.atan2(q[1], q[0]))
        m = (np.abs(r_m - rq) < 3) & (np.abs(z_m - q[2]) < 3)
        if not m.any(): continue
        dth = (tq - t_m[m] + 180) % 360 - 180; a = np.maximum(np.abs(dth) - 90.3, 0)
        d = np.sqrt(np.maximum(rq**2 + r_m[m]**2 - 2*rq*r_m[m]*np.cos(np.radians(a)), 0) + (q[2]-z_m[m])**2)
        k = d.argmin()
        if d[k] < best[0]: best = (float(d[k]), str(MT[m][k]))
    return best
for nm, (x, y) in (("F3a_2 T4 (30.6, 4.0)", (30.6, 4.0)), ("F3a_2 K3 (23.0, 11.5)", (23.0, 11.5)), ("F3a_1 T4 (26.0,-11.7)", (26.0, -11.7))):
    Q = G.tube("z", x, y, 0, 2.35, -46.2, -44.3, 0.2)
    print(nm, "head r 2.35 z -46.2..-44.3 -> sweep clearance %.2f (%s)" % clr(Q[::2]))

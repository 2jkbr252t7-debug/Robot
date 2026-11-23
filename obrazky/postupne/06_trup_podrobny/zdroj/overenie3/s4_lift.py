# lift stroke 0..20: lift group translates +z, crank rotates about the servo shaft (x axis through y 23.2, z -24.2); stage frame
import json, os, sys, numpy as np, time, math
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
YL, ZL, RC = 23.2, -24.2, 10.0
TRANS = ["L_pata", "L_ucho", "DPS_krk", "kolik_F12", "skr_F12_1"]
CRANK = ["rameno_zdvih", "cap_kluky", "skr_ramena"]
STAT = ["P_sachta", "P_drziak_serva", "servo_zdvih", "kolik_F10", "skr_F10_A", "skr_F10_B", "podl_F10_A", "podl_F10_B", "skr_F11", "podl_F11", "matica_F11",
        "skr_F15", "pd_F15", "konektor_zdvih"] + [f"ptfe_pasik_{i}" for i in range(1, 9)]
SM = {n: part(n, 'stl', 0.2) for n in STAT}
for n in STAT: SM[n].samp
MP = {n: sample_surface(load_stl(f"{T4}/stl/{n}.stl"), 0.25, thin=0.8) for n in TRANS + CRANK}
def crank_rot(P, th):
    a = math.radians(th); Q = P.copy(); y = P[:, 1] - YL; z = P[:, 2] - ZL
    Q[:, 1] = YL + y * math.cos(a) + z * math.sin(a); Q[:, 2] = ZL - y * math.sin(a) + z * math.cos(a)
    return Q
res = {}
lifts = [0, 0.05, 0.1, 0.2, 0.35] + list(np.arange(0.5, 20.01, 0.5))
for lift in lifts:
    th = math.degrees(math.acos(max(-1.0, min(1.0, 1.0 - lift / RC))))
    for m in TRANS + CRANK:
        Q = MP[m] + np.array([0, 0, lift]) if m in TRANS else crank_rot(MP[m], th)
        for s in STAT:
            M = SM[s]
            if np.any(Q.min(0) > M.bb[3:] + 1.5) or np.any(Q.max(0) < M.bb[:3] - 1.5): continue
            d, _ = M.dist(Q, dmax=1.5)
            if not np.isfinite(d).any(): continue
            k = np.argmin(d)
            near = d < 0.4
            ins = M.inside(Q[near]) if near.any() else np.zeros(0, bool)
            depth = float(d[near][ins].max()) if ins.any() else 0.0
            res.setdefault((m, s), []).append((lift, th, float(d[k]), Q[k].round(2).tolist(), int(ins.sum()), depth))
print("pair: min clearance over the stroke (lift, crank deg, point) | value at lift 0 | penetration")
for (m, s), L in sorted(res.items()):
    k = int(np.argmin([x[2] for x in L])); l0 = [x for x in L if x[0] == 0]
    pen = max(L, key=lambda x: x[5])
    print(f"{m:14s} x {s:16s} min {L[k][2]:.3f} at lift {L[k][0]:5.2f} (crank {L[k][1]:6.1f}) pt {L[k][3]} | lift 0: {('%.3f' % l0[0][2]) if l0 else '-'}"
          + (f" | INSIDE: max depth {pen[5]:.3f} at lift {pen[0]} ({pen[4]} pts)" if pen[4] else ""))

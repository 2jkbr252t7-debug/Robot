import os, sys, numpy as np, math, json
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
D = load_stl(f"{T4}/stl/P_drziak_serva.stl")
c1 = np.array([-12.89, 27.09]); ph = math.radians(38.0); n = np.array([math.cos(ph), math.sin(ph)]); t = np.array([n[1], -n[0]]); p = c1 - 1.5 * n
# ---- cw face: triangles lying on the plane through p with normal n
dv = (D[:, :, :2] - p) @ n
on = np.abs(dv).max(1) < 2e-3
F = D[on]; s = (F[:, :, :2] - p) @ t
print(f"cw face (38 deg plane): {on.sum()} triangles, area {area(F):.2f} mm2, s (along the face, 0 = contact line) {s.min():.2f} .. {s.max():.2f}, z {F[:,:,2].min():.2f} .. {F[:,:,2].max():.2f}")
for zc in (-47.0, -46.0, -45.0, -44.7, -44.3, -44.0, -43.7):
    m = (F[:, :, 2].min(1) <= zc) & (F[:, :, 2].max(1) >= zc)
    if m.any(): print(f"    at z {zc}: s {s[m].min():.2f} .. {s[m].max():.2f}")
ends = p[None] + np.array([[s.min()], [s.max()]]) * t[None]
print("    face end points (stage xy):", ends.round(2).tolist(), " r:", np.hypot(ends[:, 0], ends[:, 1]).round(2), " az:", np.degrees(np.arctan2(ends[:, 1], ends[:, 0])).round(2))
# ---- ccw face: plane x = -19.56, normal -x
xf = -21.06 + 1.5
on2 = np.abs(D[:, :, 0] - xf).max(1) < 2e-3
G = D[on2]
print(f"ccw face (x = {xf}): {on2.sum()} triangles, area {area(G):.2f}, y {G[:,:,1].min():.2f} .. {G[:,:,1].max():.2f} (contact line y 21.37), z {G[:,:,2].min():.2f} .. {G[:,:,2].max():.2f}")
for zc in (-47.0, -46.0, -45.0, -44.7, -44.3, -44.0):
    m = (G[:, :, 2].min(1) <= zc) & (G[:, :, 2].max(1) >= zc)
    if m.any(): print(f"    at z {zc}: y {G[m][:,:,1].min():.2f} .. {G[m][:,:,1].max():.2f}")
# ---- lug region fine samples + vertices
low = D[D[:, :, 2].min(1) < -41.85]
P = np.concatenate([low.reshape(-1, 3), sample_surface(low, 0.06, thin=0.8)]); P = P[P[:, 2] < -41.85]
v = low.reshape(-1, 3); print("module below z -41.85: x", v[:,0].min().round(2), v[:,0].max().round(2), "y", v[:,1].min().round(2), v[:,1].max().round(2), "z", v[:,2].min().round(2), "r", np.hypot(v[:,0], v[:,1]).min().round(2), np.hypot(v[:,0], v[:,1]).max().round(2), "az", np.degrees(np.arctan2(v[:,1], v[:,0])).min().round(2), np.degrees(np.arctan2(v[:,1], v[:,0])).max().round(2))
STA = ["T_paluba", "T_spodok", "T_most", "kolik_dorazu_1", "kolik_dorazu_2", "skr_F3a_1", "skr_F3a_2", "pd_F3a_1", "pd_F3a_2", "pastorok_pan", "servo_pan", "servo_J1", "skr_F3b_1", "skr_F3b_2",
       "ptfe_podlozka", "ffc_A_nosic", "ffc_B_nosic", "T_stred", "podlozka_J1_1", "podlozka_J1_2"]
SM = {k: part(k, 'stl', 0.15) for k in STA}
def report(a, skip=()):
    Q = rotz(P, a); rows = []
    for k, M in SM.items():
        if k in skip: continue
        d, C = M.dist(Q, dmax=3.0)
        if np.isfinite(d).any():
            i = np.argmin(d); rows.append((float(d[i]), k, Q[i].round(2).tolist(), C[i].round(2).tolist()))
    rows.sort(); return rows
for a in (-90.0, 90.0, -90.3, 90.3, -89.0, 89.0):
    print(f"pan {a}: nearest static parts to the module below -41.85:")
    for r in report(a)[:5]: print(f"     {r[0]:.3f}  {r[1]:16s} module pt {r[2]} static pt {r[3]}")
# pin contact line: samples of the lug within 0.02 of pin at the end positions
for a, pin in ((-90.0, "kolik_dorazu_1"), (90.0, "kolik_dorazu_2")):
    Q = rotz(P, a); d, C = SM[pin].dist(Q, dmax=1.0); m = d < 0.012
    print(f"pan {a}: lug points within 0.012 of {pin}: {m.sum()}, z {Q[m][:,2].min():.2f} .. {Q[m][:,2].max():.2f}, xy spread {np.ptp(Q[m][:, :2], axis=0).round(3)}; inside pin: {int(SM[pin].inside(Q).sum())}")
# ---- over-travel with the pin missing
ALLD = np.concatenate([D.reshape(-1, 3), sample_surface(D, 0.2, thin=0.8)])
S = load_stl(f"{T4}/stl/P_sachta.stl"); ALLS = sample_surface(S, 0.25, thin=0.8)
for sgn, pin in ((-1, "kolik_dorazu_1"), (1, "kolik_dorazu_2")):
    hit = None
    for dlt in np.arange(0.1, 40.01, 0.1):
        a = sgn * (90.0 + dlt); Q = rotz(ALLD, a); Q2 = rotz(ALLS, a)
        for k, M in SM.items():
            if k == pin: continue
            for nm, X in (("P_drziak_serva", Q), ("P_sachta", Q2)):
                if np.any(X.min(0) > M.bb[3:]) or np.any(X.max(0) < M.bb[:3]): continue
                ins = M.inside(X)
                if ins.any():
                    hit = (dlt, nm, k, X[ins].mean(0).round(2).tolist()); break
            if hit: break
        if hit: break
    print(f"pin {pin} missing: first collision after {hit[0]:.1f} deg of over-travel: {hit[1]} x {hit[2]} near {hit[3]}" if hit else f"pin {pin} missing: no collision within 40 deg")

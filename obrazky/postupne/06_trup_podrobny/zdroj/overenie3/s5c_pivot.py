import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
def profile(name, az, r0, r1, z0, z1, dr=0.01, dz=0.01, d='stl'):
    M = part(name, d, 0.2)
    rs = np.arange(r0, r1 + 1e-9, dr); zs = np.arange(z0, z1 + 1e-9, dz)
    R, Z = np.meshgrid(rs, zs, indexing='ij'); a = np.radians(az)
    P = np.stack([R.ravel() * np.cos(a), R.ravel() * np.sin(a), Z.ravel()], 1)
    return rs, zs, M.inside(P).reshape(R.shape)
def spans(v, m):
    out = []; on = False
    for i, f in enumerate(m):
        if f and not on: s = v[i]; on = True
        if on and (not f or i == len(m) - 1): out.append((round(float(s), 2), round(float(v[i - (0 if f else 1)]), 2))); on = False
    return out
print("P_sachta radial section near the pivot: material spans in r at given z, 4 azimuths")
for az in (0, 90, 200, 300):
    rs, zs, I = profile('P_sachta', az, 2.5, 14.0, -42.0, -40.4)
    for z in (-41.85, -41.7, -41.62, -41.55, -41.2, -40.95, -40.9, -40.8, -40.7, -40.6):
        k = int(round((z - zs[0]) / 0.01)); print(f"  az {az:3d} z {z:7.2f}: {spans(rs, I[:, k])}")
    # lip top: highest z with material at r = 4.0
    k = int(round((4.0 - rs[0]) / 0.01)); print(f"  az {az}: material z spans at r 4.00: {spans(zs, I[k])}; at r 4.6: {spans(zs, I[int(round((4.6 - rs[0]) / 0.01))])}; at r 8: {spans(zs, I[int(round((8 - rs[0]) / 0.01))])}")
for n in ('pd_F15', 'pd_F15_d1', 'pd_F15_d2', 'skr_F15', 'T_cap', 'ptfe_cap', 'koleso_pan', 'T_most'):
    M = part(n, 'stl', 0.2); v = M.tr.reshape(-1, 3); r = np.hypot(v[:, 0], v[:, 1])
    print(f"{n:10s} r {r.min():.3f}..{r.max():.3f}  z {v[:,2].min():.3f}..{v[:,2].max():.3f}")
rs, zs, I = profile('T_cap', 37, 0.5, 6.0, -46.3, -41.7)
for z in (-46.15, -45.9, -45.5, -45.0, -44.0, -42.2, -41.85):
    print(f"  T_cap z {z}: r spans {spans(rs, I[:, int(round((z - zs[0]) / 0.01))])}")
rs, zs, I = profile('koleso_pan', 37, 2.5, 9.0, -46.0, -41.8)
for z in (-45.85, -45.7, -45.3, -44.0, -42.0):
    print(f"  koleso_pan z {z}: r spans {spans(rs, I[:, int(round((z - zs[0]) / 0.01))])}")
rs, zs, I = profile('T_most', 37, 0.5, 6.0, -48.3, -46.1)
print("  T_most z -47.2: r spans", spans(rs, I[:, int(round((-47.2 - zs[0]) / 0.01))]))
for n in ('servo_J1', 'podlozka_J1_1', 'T_spodok'):
    M = part(n, 'stl', 0.2); d, Q = M.dist(np.array([[0, 0, -48.0], [0, 0, -48.29]]), dmax=6.0); print(f"  screw tip (0,0,-48.0 / -48.29) to {n}: {d.round(3)} nearest {Q.round(2).tolist()}")

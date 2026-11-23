# T9: lift module slides along -Y into its pocket (translate +y by t, t = 50 .. 0); also F12 screw path and F10 tool channels
import json, os, sys, numpy as np, time, math
sys.path.insert(0, os.path.dirname(__file__))
from vlib import *
p = json.load(open(T4 + '/parts.json')); info = {q['name']: q for q in p['parts']}
MOD = ["P_drziak_serva", "servo_zdvih", "rameno_zdvih", "cap_kluky", "skr_ramena", "L_ucho", "kolik_F12", "skr_F11", "podl_F11", "matica_F11"]
ABSENT = set(MOD) | {"T_dvere", "skr_F10_A", "skr_F10_B", "podl_F10_A", "podl_F10_B", "skr_F12_1", "konektor_zdvih", "kabel_zdvih", "ffc_par", "pigtail_zdvih",
                     "magnet_dvierka_1", "magnet_dvierka_2", "magnet_dvierka_3", "magnet_dvierka_4"}
mb = np.array([info[n]['bbox'] for n in MOD]); lo = mb[:, [0, 2, 4]].min(0); hi = mb[:, [1, 3, 5]].max(0); hi_sw = hi + np.array([0, 50, 0])
OTH = [n for n, q in info.items() if n not in ABSENT and q['group'] in ('T', 'P', 'L')
       and all(q['bbox'][2 * i] < hi_sw[i] + 1.5 and q['bbox'][2 * i + 1] > lo[i] - 1.5 for i in range(3))]
print("others:", OTH)
SM = {n: part(n, 'stl', 0.2) for n in OTH}
MP = {n: sample_surface(load_stl(f"{T4}/stl/{n}.stl"), 0.25, thin=0.8) for n in MOD}
res = {}
ts = [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0] + list(np.arange(1.5, 12.01, 0.5)) + list(np.arange(13, 50.1, 1.0))
for t in ts:
    for m in MOD:
        Q = MP[m] + np.array([0, t, 0])
        for s in OTH:
            M = SM[s]
            if np.any(Q.min(0) > M.bb[3:] + 1.2) or np.any(Q.max(0) < M.bb[:3] - 1.2): continue
            d, _ = M.dist(Q, dmax=1.2)
            if not np.isfinite(d).any(): continue
            k = np.argmin(d); near = d < 0.5
            ins = M.inside(Q[near]) if near.any() else np.zeros(0, bool)
            dp = d[near][ins]
            depth = float(dp.max()) if ins.any() else 0.0
            at = Q[near][ins][np.argmax(dp)].round(2).tolist() if ins.any() else None
            res.setdefault((m, s), []).append((t, float(d[k]), Q[k].round(2).tolist(), int((dp > 0.02).sum()), depth, at))
print("pair: min clearance on the way (t > 0.3) | at t = 0 | deepest penetration on the way")
for (m, s), L in sorted(res.items()):
    way = [x for x in L if x[0] > 0.3]; t0 = [x for x in L if x[0] == 0]
    k = min(way, key=lambda x: x[1]) if way else None
    pen = max(L, key=lambda x: x[4])
    print(f"{m:14s} x {s:16s} " + (f"way min {k[1]:.3f} at t {k[0]:5.2f} pt {k[2]}" if k else "way -") + f" | t0: {('%.3f' % t0[0][1]) if t0 else '-'}"
          + (f" | PEN depth {pen[4]:.3f} at t {pen[0]} at {pen[5]} ({pen[3]} pts > 0.02); t range with pen > 0.03: {[x[0] for x in L if x[4] > 0.03][:1]}..{[x[0] for x in L if x[4] > 0.03][-1:]}" if pen[4] > 0.02 else ""))
# ---- F12 screw (T11): withdraw along +y with the module SEATED
print("\nF12 screw path along +y, module seated:")
scr = sample_surface(load_stl(f"{T4}/stl/skr_F12_1.stl"), 0.2, thin=0.8)
BL = {n: part(n, 'stl', 0.2) for n in ["P_drziak_serva", "P_sachta", "servo_zdvih", "rameno_zdvih", "cap_kluky", "L_ucho", "L_pata", "kolik_F12", "skr_ramena"]}
for t in [0, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 7, 8, 10, 15, 20, 25]:
    Q = scr + np.array([0, t, 0]); row = []
    for n, M in BL.items():
        ins = M.inside(Q)
        if ins.any():
            d, _ = M.dist(Q[ins]); row.append(f"{n}: {int(ins.sum())} pts inside, depth {d.max():.2f}")
    print(f"  t {t:5.1f}: " + ("; ".join(row) if row else "free"))
# ---- tool channels of F10_A / F10_B: free radius about the screw axis behind the head (module seated, door off)
print("\nfree radius about the F10 screw axes for y = head .. 70 (all parts except the screw / washer themselves and the door):")
for nm, (x, z), yh in (("F10_A", (4.2, -15.8), 18.7), ("F10_B", (18.0, -33.3), 18.4)):
    bbx = info["skr_" + nm]['bbox']; x = (bbx[0] + bbx[1]) / 2; z = (bbx[4] + bbx[5]) / 2; yh = bbx[3]
    ys = np.arange(yh + 0.1, 70, 0.1); axis = np.stack([np.full(len(ys), x), ys, np.full(len(ys), z)], 1)
    rows = []
    for n, q in info.items():
        if n in ("skr_" + nm, "podl_" + nm, "T_dvere", "kabel_zdvih", "konektor_zdvih") or n.startswith("magnet_dv") or q['group'] not in ('T', 'P', 'L'): continue
        b = q['bbox']
        if b[0] > x + 4 or b[1] < x - 4 or b[4] > z + 4 or b[5] < z - 4 or b[3] < yh: continue
        M = part(n, 'stl', 0.2); d, Qc = M.dist(axis, dmax=4.0)
        if np.isfinite(d).any():
            k = np.argmin(d); rows.append((float(d[k]), n, float(ys[k]), Qc[k].round(2).tolist()))
    rows.sort()
    print(f"  {nm} axis x {x:.2f} z {z:.2f}, head back y {yh:.2f}:")
    for r in rows[:6]: print(f"     free radius {r[0]:.3f} limited by {r[1]} at y {r[2]:.1f} (nearest point {r[3]})")

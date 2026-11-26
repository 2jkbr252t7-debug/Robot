"""FIXER: lowered clutch window + new coin test at a reachable radius.
Window target 0.0080..0.0115 N.m at the arm (pinion <= 7.0 MPa with Kf x Km 1.25 at the top; D-key 3.4 MPa; >= 2x the 0.004 running limit).
Coin test: arm horizontal forward (+90 deg), servo holding; coins taped together, hung on a thread from the printed tip clip (hole on
the arm axis R_h = 55.0 mm from the shoulder axis).  Arm shell gravity torque from v_arm.json (CG lever 14.75 mm): 11 g 0.00159,
13 g 0.00188, 15 g 0.00217 N.m; clip 0.6 g at 54 mm (estimate, CAD volume x 1.2 g/cm3 to be confirmed) 0.00032 N.m.
Magnet tuning: per-magnet slip torque p 0.0018..0.0092 N.m (judge B1 model .. verifier upper), symmetric patterns n = 2/4/6/8 of
8 pockets, printed spacers under the magnets 0/0.2/0.4/0.6/0.8 (force factors 1/0.72/0.54/0.41/0.33, judge ratio table)."""
import json, math, itertools
import numpy as np
g = 9.81; R = 0.055
coins = {"1c": 2.30, "2c": 3.06, "5c": 3.92, "10c": 4.10, "20c": 5.74, "50c": 7.80, "1E": 7.50, "2E": 8.50}
arm = {"11g": 0.00159, "13g": 0.00188, "15g": 0.00217}; clip = 0.00032
WIN = (0.0080, 0.0115)
out = dict(window_target=WIN, R_hook_m=R, arm_torque=arm, clip_torque=clip)
# all coin sets of up to 3 coins
sets = {}
names = list(coins)
for k in (1, 2, 3):
    for c in itertools.combinations_with_replacement(names, k):
        m = sum(coins[x] for x in c); sets["+".join(c)] = m
def tot(m, a): return m * 1e-3 * g * R + arm[a] + clip
hold = sorted([(k, m) for k, m in sets.items() if tot(m, "11g") >= WIN[0] and tot(m, "15g") <= WIN[0] + 0.0012], key=lambda q: q[1])
slip = sorted([(k, m) for k, m in sets.items() if tot(m, "15g") <= WIN[1] and tot(m, "11g") >= WIN[1] - 0.0012], key=lambda q: -q[1])
out["hold_candidates"] = [(k, round(m, 2), round(tot(m, "11g"), 5), round(tot(m, "15g"), 5)) for k, m in hold[:6]]
out["slip_candidates"] = [(k, round(m, 2), round(tot(m, "11g"), 5), round(tot(m, "15g"), 5)) for k, m in slip[:6]]
H, S = "2c+2E", "50c+2E"
out["chosen"] = dict(hold=H, hold_g=sets[H], hold_Nm=[round(tot(sets[H], a), 5) for a in arm],
                     slip=S, slip_g=sets[S], slip_Nm=[round(tot(sets[S], a), 5) for a in arm])
out["verified_window"] = [round(tot(sets[H], "11g"), 5), round(tot(sets[S], "15g"), 5)]
# magnet tuning coverage
fac = [1.0, 0.72, 0.54, 0.41, 0.33]
lo, hi = out["verified_window"][0], out["verified_window"][1]
cover = {}
for p in np.round(np.arange(0.0018, 0.00921, 0.0002), 5):
    best = None
    for n in (2, 4, 6, 8):
        for f in fac:
            T = p * n * f
            if lo + 0.0003 <= T <= hi - 0.0003:
                cand = (abs(T - (lo + hi) / 2), n, f, round(T, 5))
                best = cand if best is None or cand < best else best
    cover[str(p)] = None if best is None else dict(n=best[1], spacer_factor=best[2], T=best[3])
out["tuning_symmetric"] = cover
out["uncovered_p"] = [p for p, v in cover.items() if v is None]
# tooth / key stresses at the window top (gear_fix ha 0.8 numbers: pinion 5.58 x Kf, 6.97 x Kf x Km1.25 at 0.0115)
out["at_top_0.0115"] = dict(pinion_lewis_Kf=5.58, pinion_Kf_Km1p25=6.97, gear_Kf=4.73, Dkey_torsion=round(5.0 * 0.0115 / 0.017, 2))
print(json.dumps(out, indent=1))
json.dump(out, open("clutch_win.json", "w"), indent=1)

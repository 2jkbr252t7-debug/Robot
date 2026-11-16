"""T4 fit study (numeric, numpy): pack layout vs the new shell ("before") and the T4 space reservation ("after").
Run: /opt/venv/cad/bin/python fit/fit2.py   -> fit/fit_report.json + stdout"""
import sys, json, math, time, numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/fit")
import t4_common as C
import fitlib as F
T0 = time.time()
REP = {}
PANS = list(range(-85, 86, 5)); LIFTS = [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20]
C.outer_cloud()

# ------------------------------------------------------------------------------------------------ A. before
import os
L = json.load(open("/tmp/claude-0/gapwf/fin/T1/pack/layout.json"))
rows = []
for c in ([] if os.environ.get("SKIP_A") else L["comps"]):
    g = c["group"]
    if g not in ("T", "P", "L") or c["name"] == "T_shell":
        continue
    P = F.comp_pts(c, 1.0)
    P = P[P[:, 2] > C.Z_FLOOR + 0.05]                       # parts below the cap floor belong to the base interface
    if not len(P):
        continue
    best = (9e9, None, 0, 0)
    for lift in (LIFTS if g == "L" else [0]):
        for pan in (PANS if g in ("P", "L") else [0]):
            Q = C.np_rot_z(P + np.array([0, 0, lift]), pan)
            cl = C.clearance_to_shell(Q); k = int(cl.argmin())
            if cl[k] < best[0]:
                best = (float(cl[k]), Q[k].round(1).tolist(), pan, lift)
    rows.append(dict(name=c["name"], group=g, clearance=round(best[0], 2), at=best[1], pan=best[2], lift=best[3],
                     r_max=round(float(np.hypot(P[:, 0], P[:, 1]).max()), 1)))
rows.sort(key=lambda r: r["clearance"])
if not os.environ.get("SKIP_A"):
    REP["before_pack_vs_new_shell"] = rows
print("A. pack layout (z_B = z_w - 129) vs the T4 shell inner surface (true offset 2.2); need >= 1.0 moving / >= 0.3 static")
for r in rows[:16]:
    print(f"   {r['name']:22s} {r['group']} {r['clearance']:6.2f} at {r['at']} pan {r['pan']} lift {r['lift']}")

# ------------------------------------------------------------------------------------------------ B. after
E = C.envelopes()
PTS = {e["name"]: C.env_points(e, 1.0) for e in E}


def dist_env(e, Q):
    if e["kind"] == "box":
        d = [np.maximum(np.maximum(e[k][0] - Q[:, i], Q[:, i] - e[k][1]), 0) for i, k in enumerate("xyz")]
        return np.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    ax = "xyz".index(e["axis"]); o = [i for i in range(3) if i != ax]
    rho = np.hypot(Q[:, o[0]] - e["c"][0], Q[:, o[1]] - e["c"][1])
    dr = np.maximum(np.maximum(rho - e["r"], e.get("ri", 0.0) - rho), 0)
    da = np.maximum(np.maximum(e["rng"][0] - Q[:, ax], Q[:, ax] - e["rng"][1]), 0)
    return np.hypot(dr, da)


def sweep(e, pans=PANS, lifts=LIFTS):
    P = PTS[e["name"]]
    for lift in (lifts if e["group"] == "L" else [0]):
        for pan in (pans if e["group"] in ("P", "L") else [0]):
            yield pan, lift, C.np_rot_z(P + np.array([0, 0, lift]), pan)


# B1 / B2: everything vs the shell
SHELL_MOUNTED = {"reproduktor", "led_box", "rura_goliera", "klb_L", "klb_L_krk", "klb_L_cap", "klb_P", "klb_P_krk", "klb_P_cap"}
rows = []
for e in E:
    if e["group"] == "Z" or e["name"] in SHELL_MOUNTED or e["name"] in ("krk", "golier_kotuc"):
        continue
    best = (9e9, None, 0, 0)
    for pan, lift, Q in sweep(e):
        Q = Q[Q[:, 2] > C.Z_FLOOR + 0.05]
        if not len(Q):
            continue
        cl = C.clearance_to_shell(Q); k = int(cl.argmin())
        if cl[k] < best[0]:
            best = (float(cl[k]), Q[k].round(1).tolist(), pan, lift)
    if best[1] is not None:
        rows.append(dict(name=e["name"], owner=e["owner"], group=e["group"], clearance=round(best[0], 2), at=best[1],
                         pan=best[2], lift=best[3]))
rows.sort(key=lambda r: r["clearance"])
REP["after_vs_shell"] = rows
print("\nB1. T4 envelopes vs the shell inner surface (wall 2.2):")
for r in rows[:22]:
    print(f"   {r['name']:22s} {r['owner']:4s} {r['group']} {r['clearance']:6.2f} at {r['at']} pan {r['pan']} lift {r['lift']}")

# B3: moving (P, L) vs static (T)
ALLOW = {("cap_otocny", "rura_goliera"), ("golier_kotuc", "rura_goliera"), ("vrch_stola", "rura_goliera"),
         ("sachta", "rura_goliera"), ("koleso_pan", "pastorok_pan"), ("koleso_pan", "ptfe"), ("koleso_pan", "cap_pan"),
         ("sachta_naboj", "cap_pan"), ("koleso_pan", "paluba"), ("koleso_pan", "paluba_zad"), ("koleso_pan", "fpc_pan"),
         ("sachta_naboj", "ptfe"), ("pata", "cap_pan"), ("sachta", "cap_pan"), ("sachta_dno_zad", "cap_pan")}
import os
SKIP_A = bool(os.environ.get("SKIP_A"))
stat = [e for e in E if e["group"] == "T"]
rows = []
for e in E:
    if e["group"] not in ("P", "L"):
        continue
    for s in stat:
        if (e["name"], s["name"]) in ALLOW:
            continue
        best = (9e9, None, 0, 0)
        for pan, lift, Q in sweep(e):
            d = dist_env(s, Q); k = int(d.argmin())
            if d[k] < best[0]:
                best = (float(d[k]), Q[k].round(1).tolist(), pan, lift)
        if best[0] < 3.0:
            rows.append(dict(moving=e["name"], static=s["name"], gap=round(best[0], 2), at=best[1], pan=best[2], lift=best[3]))
rows.sort(key=lambda r: r["gap"])
REP["after_moving_vs_static"] = rows
print("\nB3. moving (pan -85..85, lift 0..20) vs static envelopes, gaps < 3.0 (need >= 1.0):")
for r in rows[:24]:
    print(f"   {r['moving']:20s} {r['static']:20s} {r['gap']:5.2f} at {r['at']} pan {r['pan']} lift {r['lift']}")

# B4: tower vs the white lip (T_stred lowered straight down) and vs the cap tub
lip = C.lip_outline(C.Z_WHITE, C.WALL, 720)
lth = np.arctan2(lip[:, 1], lip[:, 0]); lr = np.hypot(lip[:, 0], lip[:, 1]); o = np.argsort(lth)
lth, lr = lth[o], lr[o]
rows = []
for e in stat:
    if e["owner"] != "ram":
        continue
    P = PTS[e["name"]]
    P = P[(np.abs(P[:, 0]) <= C.X_BAND + 0.3) & (P[:, 2] > C.Z_WHITE)]
    if not len(P):
        continue
    r = np.hypot(P[:, 0], P[:, 1]); th = np.arctan2(P[:, 1], P[:, 0])
    gap = np.interp(th, lth, lr, period=2 * np.pi) - r; k = int(gap.argmin())
    rows.append(dict(name=e["name"], lip_gap=round(float(gap[k]), 2), at=P[k].round(1).tolist()))
rows.sort(key=lambda r: r["lip_gap"])
REP["tower_vs_lip"] = rows
print(f"\nB4. tower (ram, |x| <= {C.X_BAND}) vs the white lip inner outline at z {C.Z_WHITE} (need >= {C.TOWER_CLEAR}):")
for r in rows[:10]:
    print(f"   {r['name']:22s} {r['lip_gap']:6.2f} at {r['at']}")
# B4b: tower vs the 4 vertical prisms swept by the T_stred screw bosses
bad = []
for e in stat:
    if e["owner"] != "ram" or e["name"] in ("pastorok_pan",):
        continue
    P = PTS[e["name"]]; P = P[P[:, 2] > C.Z_WHITE]
    m = (np.abs(P[:, 0]) > C.BOSS_KEEPOUT["x"][0]) & (np.abs(P[:, 0]) < C.BOSS_KEEPOUT["x"][1]) & (np.abs(P[:, 1]) > C.BOSS_KEEPOUT["y_min"])
    if m.any():
        bad.append(dict(name=e["name"], n=int(m.sum()), at=P[m][0].round(1).tolist()))
REP["tower_in_boss_prisms"] = bad
print("B4b. tower parts inside the T_stred boss prisms (must be empty):", bad)
rows = []
for e in stat:
    if e["owner"] != "ram":
        continue
    P = PTS[e["name"]]; P = P[(P[:, 2] < C.SPIGOT["z"][1]) & (P[:, 2] > C.Z_FLOOR - 0.01)]
    if not len(P):
        continue
    r = np.hypot(P[:, 0], P[:, 1]); th = np.arctan2(P[:, 1], P[:, 0])
    gap = C.se_r(*C.TUB_SE, th) - r; k = int(gap.argmin())
    rows.append(dict(name=e["name"], tub_gap=round(float(gap[k]), 2), at=P[k].round(1).tolist()))
rows.sort(key=lambda r: r["tub_gap"])
REP["tower_vs_tub"] = rows
print("    vs the cap tub (inner face of the spigot), z < -78:")
for r in rows[:6]:
    print(f"   {r['name']:22s} {r['tub_gap']:6.2f} at {r['at']}")

# B5: pan envelope table, B6: stage through the bore
LATE = {"servo_zdvih", "servo_zdvih_veza", "servo_zdvih_lalok", "servo_zdvih_ucho", "servo_zdvih_kabel", "kluka_naboj",
        "kluka_obalka", "drziak_serva", "drziak_serva_dno", "fpc_zdvih", "golier_kotuc"}
rows = []; bore = []
for e in E:
    if e["group"] not in ("P", "L"):
        continue
    P = PTS[e["name"]]
    P = P[P[:, 2] >= C.Z_WALL_BOT - 0.01] if e["name"] not in ("koleso_pan", "sachta_naboj", "sachta_dno_zad", "drziak_serva", "drziak_serva_dno") else P
    worst = 9e9
    for lift in (LIFTS if e["group"] == "L" else [0]):
        Q = P + np.array([0, 0, lift]); r = np.hypot(Q[:, 0], Q[:, 1])
        for z0, z1, rm in C.PAN_ENV:
            m = (Q[:, 2] > z0 + 1e-6) & (Q[:, 2] < z1 - 1e-6)
            if m.any():
                worst = min(worst, float(rm - r[m].max()))
    rows.append(dict(name=e["name"], margin_to_PAN_ENV=round(worst, 2), r_max=round(float(np.hypot(P[:, 0], P[:, 1]).max()), 2)))
    if e["group"] == "P" and e["name"] not in LATE:
        bore.append(dict(name=e["name"], r_max=round(float(np.hypot(P[:, 0], P[:, 1]).max()), 2)))
REP["pan_env_margin"] = rows; REP["stage_through_bore"] = bore
print("\nB5. pan-stage parts vs PAN_ENV (margin >= 0):", {r["name"]: r["margin_to_PAN_ENV"] for r in rows})
print(f"B6. stage dropped through the bore r {C.R_BORE}:", {b["name"]: b["r_max"] for b in bore})

# B7: shell vs PAN_ENV (the envelope itself must stay >= 1.0 inside the shell, back 260 deg)
rows = []
for z0, z1, rm in C.PAN_ENV:
    for z in np.linspace(z0, z1, 6):
        if z > C.Z_IN_TOP or z < -45.9:
            continue
        ai, bi = C.inner_half(float(z))
        rows.append((round(float(z), 2), rm, round(bi - rm, 2)))
REP["pan_env_vs_shell"] = rows
print("B7. shell inner half depth b_i(z) - PAN_ENV r_max (need >= 1.0 where the envelope is beyond the bore tube):",
      min(r[2] for r in rows if r[0] < C.Z_BORE_BOT), "min at", min((r for r in rows if r[0] < C.Z_BORE_BOT), key=lambda r: r[2]))

# B8: lift module internal (L vs P at the same pan)
rows = []
for e in E:
    if e["group"] != "L":
        continue
    for s in E:
        if s["group"] != "P" or s["name"] in ("sachta", "vrch_stola", "cap_otocny", "golier_kotuc", "koleso_pan"):
            continue
        P = PTS[e["name"]]; best = 9e9
        for lift in np.arange(0, 20.01, 0.5):
            Q = P + np.array([0, 0, lift])
            if s["name"] == "kluka_obalka":              # crank position at this lift: arm from the hub to the pin
                th = math.acos(1 - lift / C.R_CRANK)
                py, pz = C.Y_LIFT - C.R_CRANK * math.sin(th), C.Z_LIFT - C.R_CRANK * math.cos(th)
                t = np.linspace(0, 1, 21)[:, None, None]
                cy, cz = C.Y_LIFT + t * (py - C.Y_LIFT), C.Z_LIFT + t * (pz - C.Z_LIFT)
                dx = np.maximum(np.maximum(s["rng"][0] - Q[:, 0], Q[:, 0] - s["rng"][1]), 0)[None, :, None]
                dr = np.maximum(np.hypot(Q[None, :, 1:2] - cy, Q[None, :, 2:3] - cz) - C.CRANK["tip_r"], 0)
                d = np.hypot(dx, dr).min()
            else:
                d = dist_env(s, Q).min()
            best = min(best, float(d))
        if best < 3.0:
            rows.append(dict(lift_part=e["name"], pan_part=s["name"], gap=round(best, 2)))
rows.sort(key=lambda r: r["gap"])
REP["lift_vs_stage"] = rows
print("B8. lift parts vs pan-stage parts over the stroke:", [(r["lift_part"], r["pan_part"], r["gap"]) for r in rows])

REP["time_s"] = round(time.time() - T0, 1)
fn = "/tmp/claude-0/gapwf/fin/T4/fit/fit_report.json"
if os.environ.get("SKIP_A") and os.path.exists(fn):
    old = json.load(open(fn)); REP["before_pack_vs_new_shell"] = old.get("before_pack_vs_new_shell")
json.dump(REP, open(fn, "w"), indent=1)
print("done", REP["time_s"], "s")

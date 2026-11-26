"""Judge hand checks for the merged design (B1 drive + fixes): coin window, magnet steps + spacer tuning, drive-hub press
force vs MR74 axial capacity, inward-wedge tooth load (why A2 must be bonded), gear runout vs backlash, arm tip play,
homing stop geometry (two-sided), B2 comparison numbers.  Writes judge_calc.json"""
import json, math
g = 9.81
out = {}
# ---------------------------------------------------------------- 1 coin window (B1 geometry: coins at 60 mm from the axis)
coins = {"1c": 2.30, "2c": 3.06, "5c": 3.92, "10c": 4.10, "20c": 5.74, "50c": 7.80, "1E": 7.50, "2E": 8.50}
T_arm = 0.004
def T(mass_g, r=0.060): return T_arm + mass_g * 1e-3 * g * r
win = {"B1 hold 2E+50c": T(8.5 + 7.8), "B1 slip 2E+50c+10c": T(8.5 + 7.8 + 4.1),
       "JUDGE hold 2E+20c": T(8.5 + 5.74), "JUDGE slip 2E+50c+20c": T(8.5 + 7.8 + 5.74)}
out["coin_window_Nm"] = {k: round(v, 4) for k, v in win.items()}
# tooth limit from gear_judge (tip-direction Lewis x Kf(rho)): pinion 5.52 MPa at 16 N.mm -> Kf 1.436
s_per_Nmm = 5.52 / 16.0 * 1.436
out["B1_pinion_MPa_at_judge_slip"] = round(win["JUDGE slip 2E+50c+20c"] * 1000 * s_per_Nmm, 2)
out["B1_T_at_8p5_tipdirKf_Nm"] = round(8.5 / s_per_Nmm / 1000, 4)
# ---------------------------------------------------------------- 2 magnet steps
# per-magnet normal force through the 0.25 skin on the 2 mm washer: B1 model 0.93-1.32 N; judge upper estimate with the
# catalogue-to-ideal loss treated as an effective extra gap (ideal 5x2 N38 11.3 N at contact, ratio 0.43 = ideal at g0 ~0.10)
ratio = {0.02: 1.0, 0.10: 0.427, 0.20: 0.347, 0.30: 0.289, 0.40: 0.245, 0.50: 0.21, 0.75: 0.147, 1.00: 0.106}
def interp(g_):
    ks = sorted(ratio)
    for a, b in zip(ks, ks[1:]):
        if a <= g_ <= b:
            return ratio[a] + (ratio[b] - ratio[a]) * (g_ - a) / (b - a)
    return ratio[ks[-1]]
F_ideal0 = 11.3
F_hi = F_ideal0 * interp(0.25 + 0.10) * 0.85            # effective-gap model, washer factor 0.85
F_lo = 0.93
r_m = 7.7e-3
steps = {}
for F in (F_lo, 1.32, F_hi):
    for mu in (0.25, 0.4):
        per = F * mu * r_m
        n_lo = math.ceil(win["JUDGE hold 2E+20c"] / per); n_hi = math.floor(win["JUDGE slip 2E+50c+20c"] / per)
        steps[f"F {F:.2f} N mu {mu}"] = dict(per_magnet_Nm=round(per, 4), n_window=[n_lo, n_hi], fits_integer=n_lo <= n_hi, n_le_8=n_lo <= 8)
out["magnet_steps"] = steps
# printed spacer under a magnet raises the gap: force factor vs extra gap (B1 ratio table, from 0.25 skin)
out["spacer_factor"] = {s: round(interp(0.25 + s) / interp(0.25), 2) for s in (0.2, 0.4, 0.6)}
# ---------------------------------------------------------------- 3 drive-hub press fit on the M4 head (thin printed ring)
E = 2000.0; d = 7.0; L = 4.0; wall = 1.0
press = {}
for dint in (0.01, 0.02, 0.03, 0.05):
    p = E * (dint / d) * (wall / (d / 2)) / 2          # thin ring: hoop strain = dint/d, p = sigma_h * t / r (half for ring + head knurl compliance)
    for mu in (0.2, 0.3):
        press[f"interf {dint} mu {mu}"] = round(mu * p * math.pi * d * L, 1)
out["press_force_N"] = press
C0_MR74 = 107.0
out["MR74_axial_limits_N"] = dict(C0=C0_MR74, continuous_0p25C0=0.25 * C0_MR74, static_event_C0=C0_MR74)
# ---------------------------------------------------------------- 4 inward wedge (B1 as submitted: outer races free inward)
alpha = math.radians(25); d2 = math.radians(56.31)
for Fa in (6.0, 9.0, 30.0):
    Wn = Fa / (2 * math.sin(alpha) * math.sin(d2))      # both flanks wedged
    Wt_eq = Wn * math.cos(alpha)
    out[f"wedge_Fa_{Fa:.0f}N"] = dict(Wn_per_flank_N=round(Wn, 1), Wt_equiv_N=round(Wt_eq, 1),
                                      x_design_max_Wt=round(Wt_eq / (17.0 / 4.835), 1),
                                      pinion_MPa_tipdirKf=round(Wt_eq / 3.31 * 5.52 * 1.436, 1))
# ---------------------------------------------------------------- 5 gear runout vs backlash
jn = 4 * 0.02
for e in (0.035, 0.065, 0.10):
    out[f"runout_e{e}"] = dict(backlash_swing_mm=round(2 * e * math.tan(alpha), 3), j_design=jn,
                               j_min=round(jn - 2 * e * math.tan(alpha), 3), arm_deg_max=round(math.degrees((jn + 2 * e * math.tan(alpha)) / math.cos(alpha) / 6.0), 2))
# ---------------------------------------------------------------- 6 arm tip play (B1 vs B2), tip 72 mm
Fm = (6.0, 9.0); r_face = 10.0
out["B1_tilt_threshold_tip_N"] = [round(f * r_face / 72.0, 2) for f in Fm]
out["B1_tilt_after_threshold_tip_mm"] = round((0.03 / 4.0 + math.radians(0.15)) * 72.0, 2)
out["B2_tilt_threshold_tip_N"] = [round(f * 13.2 / 72.0, 2) for f in (1.1, 1.5)]
out["B2_tilt_tip_mm"] = [0.53, 0.89]
jt = jn / math.cos(alpha)
out["B1_swing_play_deg"] = dict(gear=round(math.degrees(jt / 6.0), 2), servo_0p5to1deg_at_arm=[0.33, 0.67],
                                total=[round(math.degrees(jt / 6.0) + 0.33, 2), round(math.degrees(jt / 6.0) + 0.67, 2)])
# ---------------------------------------------------------------- 7 two-sided homing stop (rib 4.0/7.0 rad, lug sector)
W_RIB = math.degrees(4.0 / 7.0)
for top in (139.0, 140.5):
    W_LUG = 360.0 - W_RIB - (top - (-51.0))
    out[f"lug_for_top_{top}"] = dict(rib_deg=round(W_RIB, 1), lug_deg=round(W_LUG, 1), span_deg=top + 51.0,
                                     drive_spare_deg=round(200.0 - (top + 51.0), 1),
                                     rib_lug_gap_at_135_mm=round(5.5 * math.radians(top - 135.0), 2),
                                     rib_lug_gap_at_m45_mm=round(5.5 * math.radians(6.0), 2),
                                     servo_range_needed_deg=round((top + 51.0) * 1.5, 0))
# ---------------------------------------------------------------- 8 B2 jam / plain-journal friction (for the comparison)
out["B2_gear_torque_at_slip_13p4"] = {"mu0.15": round(13.4 / 0.795, 1), "mu0.25": round(13.4 / 0.659, 1)}
json.dump(out, open("/tmp/claude-0/gapwf/fin/R2c/vyber/judge_calc.json", "w"), indent=1)
print(json.dumps(out, indent=1))

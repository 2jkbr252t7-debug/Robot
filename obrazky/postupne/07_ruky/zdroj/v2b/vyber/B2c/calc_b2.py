"""B2 (max print) - hand calculations: torque chain, magnetic single-position detent clutch, servo settings, plain-bearing
loads / wear / backlash growth, arm play, strength of the printed and bonded parts.  All numbers mm, N, N.mm unless noted.
Inputs that are NOT verified are listed in UNVERIFIED and carried as ranges.  writes calc_b2.json"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gears as G
import magnets as MG

OUT = {}
UNVERIFIED = []
# ------------------------------------------------------------------ 0. inputs
ALLOW = 8.5          # MPa, project long-term allowable (Elegoo Tough)
UTS = 32.1           # MPa (Amazon.de listing, +-10 %)              -> unverified
T_ARM = 4.0          # N.mm, arm gravity torque at horizontal (13 g shell)
STALL = (190.0, 226.0)   # N.mm servo locked-rotor torque (v2 5 V value / Waveshare 6 V)
RATIO = 18 / 12
R_TIP = 72.0         # arm tip radius about the shoulder axis
UNVERIFIED += ["Elegoo Tough strength 32 MPa / E ~2.0-2.5 GPa (no official TDS reached)",
               "friction resin-on-resin mu 0.10-0.25 (greased / dry), no data for Elegoo Tough",
               "wear coefficient k 1e-5..1e-3 mm3/(N.m) for Tough on Tough (no data)",
               "magnet pull on a 2 mm DIN 9021 washer: ideal-steel model x k_sat 0.6..0.9",
               "SCS0009 internal backlash (not published) taken 0.3..1.0 deg at the output",
               "SCS0009 torque-limit register behaviour at 10 % (EEPROM 'max torque')"]

# ------------------------------------------------------------------ 1. printed bevel pair (fine raster)
_rt = G.rack_tooth
G.rack_tooth = lambda zv, a, x=0.0, **k: _rt(zv, a, x, n=420, nroll=380)
bv = G.bevel(0.65, 12, 18, 2.5, 25.0, 0.25)
OUT["gear"] = {k: bv[k] for k in ("m", "z1", "z2", "b", "alpha", "x1", "x2", "ratio", "delta1", "delta2", "d1", "d2", "Re", "b_over_R",
                                  "m_mean", "rm2", "zv1", "zv2", "crown1", "crown2", "eps", "T_arm_at_allow")}
OUT["gear"]["Y1"] = bv["Y1"]; OUT["gear"]["Y2"] = bv["Y2"]
T85 = bv["T_arm_at_allow"] * 1000.0          # N.mm at the gear giving 8.5 MPa (Lewis, weaker member)
OUT["gear"]["T_gear_at_8.5MPa_Nmm"] = round(T85, 2)
OUT["gear"]["note"] = ("Lewis form factor from a rack-generated tooth (gears.py); about 8 % below Shigley's table for "
                       "alpha 20 (conservative). Kf = Dolan-Broghamer fillet factor reported separately.")

# ------------------------------------------------------------------ 2. friction between the gear and the clutch (spindle)
# gear mean point x 42.5; inner land D6 x 44.4..47.8 (centre 46.1), outer land D6 x 57.2..61.0 (centre 59.1)
rj = 3.0; a_over = 46.1 - 42.5; span = 59.1 - 46.1
R1f = 1 + a_over / span; R2f = a_over / span
al = math.radians(25.0); d2 = math.radians(bv["delta2"])
Fcomb = math.hypot(1.0, math.tan(al) * math.cos(d2))          # |F_radial-plane| / Ft
Fa_over_Ft = math.tan(al) * math.sin(d2)
def c_loss(mu):
    """fraction of the gear torque lost in the spindle journals + gear-back thrust (r 4.5) before the clutch"""
    return mu * ((R1f + R2f) * Fcomb * rj + Fa_over_Ft * 4.5) / bv["rm2"]
OUT["spindle_friction"] = {f"mu {mu}": round(c_loss(mu), 3) for mu in (0.10, 0.15, 0.20, 0.25)}

# ------------------------------------------------------------------ 3. magnetic single-position detent clutch
BETA = 30.0; RT = 13.2; E_ENG = 0.3; G0 = 1.2
N_MAG = 3
def F1(g):    # one D4x2 N35 on thick ideal steel at gap g (model)
    return MG.pair_force(2.0, 2.0, 2.0, 2.0, 2 * g, 1.18, 1.18)
f0, f1 = F1(G0), F1(G0 + E_ENG)
dfdg = (F1(G0 + 0.05) - F1(G0 - 0.05)) / 0.1
def Tslip(n, ksat, mu, dg=0.0):
    return n * (f0 + dfdg * dg) * ksat * RT * math.tan(math.radians(BETA) + math.atan(mu))
cl = dict(teeth="3 V-teeth on the disc at r 12.4..14.0 (r_m 13.2), angles 0/100/220 deg -> engage in ONE relative position",
          beta_deg=BETA, engagement_mm=E_ENG, gap_seated_mm=G0, magnets=f"{N_MAG} (pockets for 4) x D4x2 N35 axial in the hub",
          washer="DIN 9021 M8 (8.4x24x2) zinc-plated steel, bonded in the disc",
          F1_model_N=round(f0, 3), F1_after_climb_N=round(f1, 3), dF_dgap_N_per_mm=round(dfdg, 3))
rows = {}
for n in (2, 3, 4):
    lo_ = Tslip(n, 0.6, 0.12, +0.05); nom = Tslip(n, 0.75, 0.18); hi_ = Tslip(n, 0.9, 0.25, -0.05)
    rows[n] = dict(T_slip_min=round(lo_, 2), T_slip_nom=round(nom, 2), T_slip_max=round(hi_, 2))
cl["T_slip_Nmm_by_magnets"] = rows
# coin test (arm horizontal, servo holding, coins taped at the arm tip r 72): window after tuning
coin = {"1 EUR": 7.5, "20 c": 5.74, "50 c": 7.8, "2 EUR": 8.5}
T_hold = T_ARM + coin["1 EUR"] * 9.81e-3 * R_TIP
T_slipt = T_ARM + (coin["1 EUR"] + coin["20 c"]) * 9.81e-3 * R_TIP
cl["coin_test"] = dict(must_hold="1 EUR coin (7.5 g) at the tip: %.1f N.mm incl. arm" % T_hold,
                       must_slip="1 EUR + 20 c (13.2 g) at the tip: %.1f N.mm incl. arm" % T_slipt,
                       window_Nmm=[round(T_hold, 1), round(T_slipt, 1)],
                       tuning="slips with 1 EUR -> add a magnet or use the steeper disc; holds with 1 EUR + 20 c -> remove a magnet or use the flatter disc")
# fine tuning: disc printed with flank angle 25 / 30 / 35 deg (cheap part) x magnet count 2 / 3 / 4
cl["tuning_matrix_Tslip_nom_Nmm"] = {f"{n} magnets, beta {b}": round(n * f0 * 0.75 * RT * math.tan(math.radians(b) + math.atan(0.18)), 1)
                                    for n in (2, 3, 4) for b in (25, 30, 35)}
Tmax_s = T_slipt
# drag while slipping (crests on the land, gap G0 + e), and the hanging angle below which a free arm stays put
drag = N_MAG * f1 * 0.75 * 0.18 * RT
cl["drag_while_slipping_Nmm"] = round(drag, 2)
cl["free_arm_stays_if_abs_angle_below_deg"] = round(math.degrees(math.asin(min(1.0, (drag + 0.2) / T_ARM))), 1)
cl["windup_below_slip"] = "none (magnet-preloaded V-teeth, no compliance except resin elasticity)"
OUT["clutch"] = cl

# ------------------------------------------------------------------ 4. tooth stresses (gear torque = arm-side torque / (1 - c))
def sig(Tg):
    s = G.stress(bv, Tg / 1000.0)
    return dict(T_gear_Nmm=round(Tg, 2), lewis_pinion=s["s1"], lewis_gear=s["s2"], with_Kf_max=max(s["s1_Kf"], s["s2_Kf"]))
cases = {}
cases["normal: arm gravity 4.0, mu 0.15"] = sig(T_ARM / (1 - c_loss(0.15)))
cases["slip nominal 12.0, mu 0.15"] = sig(12.0 / (1 - c_loss(0.15)))
cases["slip at the coin-test upper limit %.1f, mu 0.25" % Tmax_s] = sig(Tmax_s / (1 - c_loss(0.25)))
tl = 0.08 * STALL[1] * RATIO
cases["clutch stuck, servo at the 8 %% torque limit (%.1f at the gear)" % tl] = sig(tl)
cases["clutch stuck AND no torque limit (full stall %.0f at the gear)" % (STALL[1] * RATIO)] = sig(STALL[1] * RATIO)
OUT["tooth_stress_MPa"] = cases
OUT["torque_order_Nmm"] = dict(arm_need=T_ARM, homing_sync_sweep=round(T_ARM / (1 - c_loss(0.25)), 2),
                               clutch_slip_window=[round(T_hold, 1), round(T_slipt, 1)],
                               gear_at_8p5MPa=round(T85, 1), servo_limit_8pct_at_gear=round(tl, 1),
                               servo_limit_8pct_at_gear_min_needed=round(T_slipt / (1 - c_loss(0.25)), 1),
                               note="homing = sync sweep at normal torque: the arm load never exceeds arm need + friction; "
                                    "the gear is capped by the clutch; the 8 % limit (EEPROM) is only the back-up if the clutch jams. "
                                    "Short-term allowable for that fault case taken as UTS/2.5 = 12.8 MPa (engineering judgement, "
                                    "usual polymer practice: short-term load SF 2-3 on strength; not verified for Elegoo Tough)")

# ------------------------------------------------------------------ 5. contact stress (Hertz, virtual spur pair at the mean section)
E = 2000.0; nu = 0.38
Es = E / (2 * (1 - nu ** 2))
rv1 = bv["zv1"] * bv["m_mean"] / 2; rv2 = bv["zv2"] * bv["m_mean"] / 2
rho = 1 / (1 / (rv1 * math.sin(al)) + 1 / (rv2 * math.sin(al)))
def hertz(Tg):
    Ft = Tg / bv["rm2"]; w = Ft / math.cos(al) / bv["b"]
    return round(math.sqrt(w * Es / (math.pi * rho)), 1)
OUT["contact_MPa"] = {"normal": hertz(T_ARM / (1 - c_loss(0.15))), "slip max": hertz(Tmax_s / (1 - c_loss(0.25)))}

# ------------------------------------------------------------------ 6. plain bearings: loads, PV, wear, backlash growth
moves_day, arm_deg, days = 3000, 60.0, 365
Tg_avg = 2.8 / (1 - c_loss(0.15))           # average gear torque during motion (gravity * |sin|, gestures)
Ft_avg = Tg_avg / bv["rm2"]
brg = {}
# spindle inner land D6 x 3.4 (static ring bore wears in a fixed ~90 deg sector)
R1 = R1f * Fcomb * Ft_avg; s_sp = math.radians(arm_deg) * rj * moves_day * days / 1000.0
brg["spindle inner land D6x3.4"] = dict(load_avg_N=round(R1, 2), p_MPa=round(R1 / (6 * 3.4), 3), sliding_m_per_year=round(s_sp),
                                        area_mm2=round(3.4 * math.pi * 6 / 4, 1))
# U-insert D4.1 x 2.8 (pinion shaft; pinion mean point 3.65 above the insert centre, servo spline 16.5 below)
Fp = Ft_avg * math.hypot(1.0, math.tan(al) * math.cos(math.radians(bv["delta1"])))
Rins = Fp * (16.5 + 3.65) / 16.5
s_ins = math.radians(arm_deg * RATIO) * 2.0 * moves_day * days / 1000.0
brg["U-insert D4.1x2.8"] = dict(load_avg_N=round(Rins, 2), p_MPa=round(Rins / (4 * 2.8), 3), sliding_m_per_year=round(s_ins),
                                area_mm2=round(2.8 * math.pi * 4 / 4, 1))
# collar thrust on the insert (servo 21 g hangs on it + pinion axial force)
Fa1 = Ft_avg * math.tan(al) * math.sin(math.radians(bv["delta1"]))
Fcol = 0.206 + 0.01 + Fa1
s_col = math.radians(arm_deg * RATIO) * 2.4 * moves_day * days / 1000.0
brg["collar thrust r2.05..2.7"] = dict(load_avg_N=round(Fcol, 2), p_MPa=round(Fcol / (math.pi * (2.7 ** 2 - 2.05 ** 2)), 3),
                                       sliding_m_per_year=round(s_col), area_mm2=round(math.pi * (2.7 ** 2 - 2.05 ** 2), 1))
# arm hub journal D12.5 x 8.4 (arm weight only)
s_hub = math.radians(arm_deg) * 6.25 * moves_day * days / 1000.0
brg["arm hub D12.5x8.4"] = dict(load_avg_N=0.19, p_MPa=round(0.19 / (12.5 * 8.4), 4), sliding_m_per_year=round(s_hub),
                                area_mm2=round(8.4 * math.pi * 12.5 / 2, 1))
for k, b in brg.items():
    for kw in (1e-5, 1e-4, 1e-3):
        V = kw * b["load_avg_N"] * b["sliding_m_per_year"]
        b[f"depth_mm_per_year_k{kw:g}"] = round(V / b["area_mm2"], 4)
OUT["bearings"] = brg
# backlash growth at the gear pitch circle per year (radial shifts ~0.7 x depth, collar wear 0.52 x depth, teeth 2 x depth)
tooth_area = 2.5 * 1.1
eng_per_year = moves_day * days * arm_deg * RATIO / 360.0          # engagements per pinion tooth
s_tooth = 0.3e-3 * eng_per_year
grow = {}
for kw in (1e-5, 1e-4, 1e-3):
    teeth = 2 * 2 * kw * 0.6 * s_tooth / tooth_area        # both flanks of both members ~ backlash
    radial = 0.7 * (brg["spindle inner land D6x3.4"][f"depth_mm_per_year_k{kw:g}"] + brg["U-insert D4.1x2.8"][f"depth_mm_per_year_k{kw:g}"])
    collar = 0.52 * brg["collar thrust r2.05..2.7"][f"depth_mm_per_year_k{kw:g}"]
    tot = teeth + radial + collar
    grow[f"k {kw:g}"] = dict(backlash_mm_per_year=round(tot, 3), arm_deg_per_year=round(math.degrees(tot / 5.85), 2))
OUT["backlash_growth"] = grow
OUT["life_note"] = ("replace the U-insert / pinion-shaft / gear-spindle when the arm free play at hanging exceeds about 2 deg; "
                    "with k 1e-4 that is several years, with k 1e-3 about one year (k unknown -> endurance test)")

# ------------------------------------------------------------------ 7. arm play
play = {}
for c_h, p_ax in ((0.05, 0.1), (0.06, 0.15), (0.08, 0.2)):
    tilt = c_h / 8.4
    play[f"hub clearance {c_h}, axial play {p_ax}"] = dict(
        tilt_rad=round(tilt, 4), tip_X_total_mm=round(tilt * R_TIP + p_ax, 2), gap_point_r14_total_mm=round(tilt * 14 + p_ax, 2),
        min_gap_at_135_if_pushed_in=round(1.00 - (tilt * 14 / 2 + p_ax / 2), 2))
OUT["arm_play_X"] = play
tang = {}
for jt in (0.05, 0.08):
    for sb in (0.3, 1.0):
        a = math.degrees(jt / 5.85) + sb / RATIO
        tang[f"gear backlash {jt} + servo {sb} deg"] = dict(arm_deg=round(a, 2), tip_mm=round(math.radians(a) * R_TIP, 2))
OUT["arm_play_tangential_at_hanging"] = tang

# ------------------------------------------------------------------ 8. strength of other parts
st = {}
M_L5 = 10.0 * R_TIP            # 720 N.mm arm moment (T4 load L5: 10 N along X at the tip)
for name, do, di in (("ring root D13/6.1", 13.0, 6.1), ("ring at the journal D12.5/6.1", 12.5, 6.1)):
    Z = math.pi * (do ** 4 - di ** 4) / (32 * do)
    st[name] = dict(Z=round(Z, 1), sigma_MPa=round(M_L5 / Z, 2), sigma_Kt1p5=round(1.5 * M_L5 / Z, 2))
st["hub journal edge load under L5"] = dict(F_N=round(M_L5 / 8.4, 1), p_MPa=round(M_L5 / 8.4 / (12.5 * 1.5), 2), note="rare load")
Tsh = tl / RATIO
st["pinion-shaft torsion D4 at the 8 % limit"] = dict(T_Nmm=round(Tsh, 1), tau_MPa=round(16 * Tsh / (math.pi * 4 ** 3), 2))
Fslip_p = (Tmax_s / (1 - c_loss(0.25))) / bv["rm2"] * 1.07
st["pinion-shaft bending at the insert, slip max"] = dict(M_Nmm=round(Fslip_p * 3.65, 2), sigma_MPa=round(32 * Fslip_p * 3.65 / (math.pi * 64), 2))
st["printed spline coupler (20 teeth x 0.25 x 2.2 bearing) at the 8 % limit"] = dict(p_MPa=round(Tsh / 1.85 / (20 * 0.25 * 2.2), 2))
st["printed spline coupler at full stall (fault)"] = dict(p_MPa=round(STALL[1] / 1.85 / (20 * 0.25 * 2.2), 1))
Fsl = Tmax_s / (3 * RT)
st["clutch V-tooth bending (per tooth)"] = dict(F_N=round(Fsl, 2), sigma_MPa=round(Fsl * E_ENG / (1.6 * 2.1 ** 2 / 6), 2))
Rt = R1f * Fcomb * (Tmax_s / (1 - c_loss(0.25))) / bv["rm2"]
st["spindle inner land at slip max"] = dict(R_N=round(Rt, 2), p_MPa=round(Rt / (6 * 3.4), 3))
Rtg = (Fslip_p) * (16.5 + 3.65) / 16.5
st["tongue (solid back) bearing at slip max"] = dict(R_N=round(Rtg, 2), p_MPa=round(Rtg / (4 * 2.8), 3))
st["M2 insert in the spindle (glued, OD 3.5 x 4) at 0.10 N.m tightening"] = dict(
    F_N=round(0.10 / (0.2 * 0.002), 0), tau_bond_MPa=round(0.10 / (0.2 * 0.002) / (math.pi * 3.5 * 4.0), 2),
    note="borderline vs epoxy-on-resin 5..10 MPa -> tighten gently (torque not needed: the hex carries the torque), Loctite 222")
st["magnet bond (D4x2 in a pocket, epoxy on the side)"] = dict(F_N=round(f0, 2), tau_MPa=round(f0 / (math.pi * 4 * 2), 3))
OUT["strength"] = st
OUT["unverified"] = UNVERIFIED
json.dump(OUT, open(os.path.join(HERE, "calc_b2.json"), "w"), indent=1, default=float)
for k, v in OUT.items():
    print("==", k); print(json.dumps(v, indent=1, default=float)[:2500])

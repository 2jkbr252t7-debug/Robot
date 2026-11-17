"""m05 - every derived number quoted in zjednodusenie.md that is not a direct STL measurement (m01..m04).
Inputs are either measured (m01..m04 json), taken from t4_common / T4_spec, from the task brief, or from catalogue data
found by web search (marked SRC). Run: /opt/venv/cad/bin/python m05_numbers.py"""
import json, math
from zj_lib import OUT, dump, say

m01 = json.load(open(OUT + "/m01_stage_radius.json"))
m02 = json.load(open(OUT + "/m02_pan_duct.json"))
R = {}

# ---- 1. collar / slim stage -------------------------------------------------------------------------------------
ring_in = m01["golier_prstenec"]["r_min"]           # 26.748 measured
disc_r = m01["golier_kotuc"]["r_max"]               # 26.5 measured
bore_new = 26.65                                      # proposed journal bore in T_stred below the ring seat
stage_r = 26.50                                       # proposed max stage radius (journal incl. 0.13 PTFE tape)
R["collar"] = dict(ring_inner_r=ring_in, disc_r=disc_r, journal_bore_r=bore_new, stage_r=stage_r,
                   journal_radial_clearance=round(bore_new - stage_r, 3),
                   stage_vs_ring_radial=round(ring_in - stage_r, 3),
                   bore_wall_new=round(30.6 - bore_new, 2), bore_wall_now=round(30.6 - 28.35, 2),
                   added_resin_g=round(math.pi * (28.35 ** 2 - bore_new ** 2) * 8.5 * 1.15e-3, 1))
# pivot tilt if the collar disc alone were the upper guide (fix (a) as written by the verifier)
pin_clear_r = 3.024 - 3.0          # hub / gear bore r 3.024 (m02) on the D6 pin
bore_len = -41.0 - -44.0           # gear bore from the underside recess (z -44.0) to the hub top (z -41.0)
tilt = 2 * pin_clear_r / bore_len
R["disc_as_bearing"] = dict(pin_radial_clear=round(pin_clear_r, 3), bore_length=bore_len,
                            tilt_deg=round(math.degrees(tilt), 2),
                            lateral_at_disc_mm=round(tilt * (-2.0 - -41.0), 2), seam=0.25)

# ---- 2. pivot + retention (proposed) ------------------------------------------------------------------------------
# sleeve on the deck boss (boss top raised -44.2 -> -44.0), top 0.10 above the hub disc top (-41.0)
sleeve = dict(od=6.0, z=(-44.0, -40.9))
washer = dict(name="DIN 9021 M2.5 (d2 8.0, h 0.8)", od=8.0, h=0.8)
head = dict(name="ISO 7380-1 M2.5 button head", dk=4.7, k=1.375)     # catalogue nominal, verify
stack_top = sleeve["z"][1] + washer["h"] + head["k"]
foot_under = -40.5
R["pivot"] = dict(sleeve=sleeve, washer=washer, head=head, top_of_head=round(stack_top, 3),
                  foot_underside=foot_under, counterbore_depth_needed=round(stack_top - foot_under + 0.5, 2),
                  foot_left_over_counterbore=round(4.0 - (stack_top - foot_under + 0.5), 2),
                  axial_play=round(sleeve["z"][1] - -41.0, 2))
# loads (L1 15 N x SF 2 = 30 N up through the washer)
F1 = 30.0
ann = math.pi * (washer["od"] ** 2 - 6.05 ** 2) / 4
R["pivot"]["L1_washer_bearing_MPa"] = round(F1 / ann, 2)
R["pivot"]["L1_hub_punch_MPa"] = round(F1 / (math.pi * washer["od"] * 1.2), 2)
ins_area = math.pi * 3.5 * 3.5                # bonded M2.5 insert OD 3.5 x 3.5 deep
R["pivot"]["L1_insert_bond_MPa"] = round(F1 / ins_area, 2)
# radial bearing on the sleeve: L3 46.1 N, L8 67.8 N (overenie_pevnost p08) over D6 x 3.0
for k, F in (("L3", 46.1), ("L8", 67.8)):
    R["pivot"][f"{k}_sleeve_bearing_MPa"] = round(F / (6.0 * bore_len), 2)

# ---- 3. journal pressure under a 10 N side push at the head ---------------------------------------------------------
lever_head = 40.0 - -42.5       # head centre ~z +40 (rest) above the pivot plane (assumed)
lever_journal = -6.75 - -42.5
Fj = 10.0 * lever_head / lever_journal
R["journal"] = dict(side_push_N=10.0, journal_reaction_N=round(Fj, 1),
                    pressure_MPa=round(Fj / (2 * stage_r * 7.5), 3))

# ---- 4. FFC (stock) vs custom FPC ----------------------------------------------------------------------------------
# SRC: Wurth WR-FFC 6876 6-way 0.5 mm: width 3.5, conductor 0.035, 0.5 A (search snippet, RS listing);
#      Molex 0.50 mm FFC: conductor resistance <= 2.2 ohm/m (JIS C 3102), 60 V; GCT/Assmann 0.5 A per conductor
w6 = 3.5
w_n = lambda n: w6 + (n - 6) * 0.5            # same 0.5 pitch; 5-pole = 3.0 (derived, verify)
rho = 2.2                                     # ohm/m max per conductor
duct = [a for a in m02["annuli"] if a["r"] == [16, 23.5] or a["r"] == (16, 23.5)][0]
L_pan = 0.15; L_full = 0.20                   # m: carrier -> riser (pan only) / carrier -> neck board (pan + lift loop)
I_peak = 0.5 + 0.7 + 0.2                      # head + one MG90S stall + other MG90S holding (task brief values)
I_typ = 0.4
def drop(n_per_rail, L, I):
    return 2 * rho * L / n_per_rail * I
R["ffc"] = dict(width_5p=w_n(5), width_6p=w6, width_8p=w_n(8), duct_h_min=duct["h_min"], duct_h_median=duct["h_median"],
                rated_per_rail_A=3 * 0.5, I_peak_A=I_peak, I_typ_A=I_typ,
                drop_peak_V=round(drop(3, L_full, I_peak), 2), drop_typ_V=round(drop(3, L_full, I_typ), 2),
                uturn_R_pan=round((23.5 - 15.7) / 2, 2), R_over_t_pan=round((23.5 - 15.7) / 2 / 0.1, 0),
                lift_loop_R_flat=3.0, R_over_t_lift=round(3.0 / 0.1, 0),
                copper_strain_pct=round(100 * (0.035 / 2) / ((23.5 - 15.7) / 2), 2))
# present custom FPC: 0.45 mm x 12 um traces, 2 per rail (verifier M15: 0.48 ohm per 150 mm per trace)
r_fpc = 0.0172 / (0.45 * 0.012)               # ohm/m
R["fpc_custom"] = dict(ohm_per_m=round(r_fpc, 2), drop_peak_V=round(2 * r_fpc * L_full / 2 * I_peak, 2),
                       copper_strain_pct_verifier=1.5)
# J1 (base round): 2 x 5p -> VBAT x4, GND x4; torso peak about 3 A (assumed: STS3215 + buck input)
R["j1_ffc"] = dict(rail_conductors=4, rated_A=2.0, I_peak_assumed_A=3.0,
                   drop_peak_V=round(drop(4, 0.20, 3.0), 2), note="base round: prefer 1.0 mm pitch FFC or 3 x 0.5 mm")

# ---- 5. well corner at r 26.5 (m01) --------------------------------------------------------------------------------
R["well_corner"] = m01["trim_26_5"]

# ---- 6. loose wires in the pan duct (fallback) ------------------------------------------------------------------------
R["loose_wires_pan"] = dict(wire_od=0.8, R=round((23.5 - 15.7) / 2, 2), R_over_D=round((23.5 - 15.7) / 2 / 0.8, 1),
                            layers_needed_in_3_4mm=math.ceil(10 / math.floor(3.4 / 0.8)))

# ---- 7. crank on the supplied horn (assumed arm 1.6 thick, 4.0 wide at r 10; B montaz: arms 1.6) ----------------------
F = 30.0
R["horn_crank"] = dict(arm_t=1.6, arm_w_assumed=4.0, net_tension_MPa=round(F / ((4.0 - 2.0) * 1.6), 1),
                       pin_bearing_MPa=round(F / (2.0 * 1.6), 1), note="nylon/POM horn, compare with ~50 MPa yield")
dump("m05_numbers.json", R)
for k, v in R.items():
    say(k, v)

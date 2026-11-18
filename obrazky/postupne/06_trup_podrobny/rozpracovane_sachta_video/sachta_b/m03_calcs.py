"""m03: lens-B ("what breaks in real life") hand calculations for P_sachta and the parts at its bottom.
Every input is either measured here (m01/m02/m02b/m00 json), taken from the design (T4_spec 17.x / K12 rows, cited), or an
ASSUMPTION (marked A: in the json).  Allowables (T4_zivica Z2): normal 8.5, sustained / unfilleted notch 4.3, abuse 12.9 MPa
(incl. Kt); epoxy 8 MPa assumed ultimate, 2.7 design.  Writes m03_calcs.json and prints the summary table."""
import json, math
OUT = "/tmp/claude-0/gapwf/fin/T4/sachta_b"
m01 = json.load(open(f"{OUT}/m01_measure.json"))
m02 = json.load(open(f"{OUT}/m02_overhang.json"))
m02b = json.load(open(f"{OUT}/m02b_sections.json"))
m00 = json.load(open(f"{OUT}/m00_headmass.json"))

UTS = 25.8; ALW_N, ALW_S, ALW_A = 8.5, 4.3, 12.9; EPOXY_U, EPOXY_D = 8.0, 2.7
E_RES = 1600.0                       # A: E of cured Elegoo Tough, 1.5-1.8 GPa (Z2 "assumed")
g = 9.81
R = {}; rows = []


def row(feature, case, value, allow, unit="MPa", note="", kind="stress"):
    m = None if (value is None or allow is None or value == 0) else round(allow / value, 2)
    # kind "capacity": value = demand (force), allow = capacity -> margin = capacity / demand (same formula)
    rows.append(dict(feature=feature, case=case, value=value, allowable=allow, unit=unit, margin=m, note=note))


# ======================================================================================================================
# 1. PRINT (documented orientation: top plate z -2 toward the build plate, raised 3 mm, supports only on the top plate)
# ======================================================================================================================
hub = [r for r in m02["all_levels"] if abs(r["z"] + 40.65) < 0.01][0]
R["print_overhang_hub_floor"] = hub
R["print_support_length_mm"] = round(-2.0 - (-40.65) + 3.0, 2)        # top plate face to hub top + 3 mm raise
# peel / suction on the largest layers (A: 0.5 .. 2 N/cm2 separation pressure for a flat FEP release without tilt;
# the Saturn 4 Ultra tilt release is lower -> upper bound)
A_max = max(m02b["section_area_mm2"].values()); A_hub = m02b["section_area_mm2"]["-40.7"]
R["peel"] = dict(A_hub_layer_mm2=A_hub, F_hub_layer_N=[round(0.005 * A_hub, 1), round(0.02 * A_hub, 1)],
                 A_wall_min_mm2=min(v for k, v in m02b["section_area_mm2"].items() if -40 < float(k) < -11),
                 note="A: 0.5..2 N/cm2; the walls carry it at < 0.1 MPa; the risk is the UNSUPPORTED first hub layer (420 mm2 film), not the peel force")
R["peel"]["wall_stress_MPa"] = round(R["peel"]["F_hub_layer_N"][1] / R["peel"]["A_wall_min_mm2"], 3)
# first hub layer as a cantilever film: 0.05 thick, attached on one edge, peel pressure p over the free length L
t_l, L_c = 0.05, hub["max_cantilever_mm"]
for p in (0.005, 0.02):                       # N/mm2
    s = 6 * (p * L_c ** 2 / 2) / t_l ** 2        # root bending stress of a 1 mm wide strip of the green layer
    R.setdefault("first_hub_layer_root_stress_MPa", []).append(round(s, 0))
R["first_hub_layer_note"] = ("a 0.05 mm green layer cantilevered 11.4 mm from the walls sees ~10^3-10^4 MPa (nonsense = it cannot "
                             "carry the peel): it tears off or bends with the FEP -> sagged / delaminated hub disc. Needs supports.")

# ======================================================================================================================
# 2. F15 pivot screw - thread engagement in the 2.0 aluminium bridge
# ======================================================================================================================
Le_nom = m01["F15_engagement_in_T_most"]                                  # 0.8 measured (tip -47.0, T_most top -46.2)
An = math.pi * 2 * 2.874 * (0.25 + 0.57735 * (2.874 - 2.775))             # FED-STD-H28 internal-thread shear area per mm, M3 6g/6H
tau = {"5754-H22 (Rm 220)": 0.6 * 220, "6061-T6 (Rm 290)": 0.6 * 290}      # A: tau = 0.6 Rm (EN 485 minima)
Le_eff = Le_nom - 0.3 - 0.1                                                # A: screw-end chamfer ~0.3 (to d3) + tapped-hole entry burr/chamfer 0.1
strip = {f"{k} Le {Le}": round(An * Le * t) for k, t in tau.items() for Le in (Le_eff, Le_nom)}
pre = lambda T, K=0.2, d=3.0: T * 1000 / (K * d)                           # F = T / (K d)
R["F15"] = dict(engaged_nominal=Le_nom, engaged_effective_A=round(Le_eff, 2), An_per_mm=round(An, 3), strip_N=strip,
                preload_N={f"{T} N.m K{K}": round(pre(T, K)) for T in (0.1, 0.3, 0.6) for K in (0.2, 0.15)},
                note="0.10 = documented fingertip rule; 0.3 = normal screwdriver; 0.6 = 2.0 L-key turned by its long arm (A)")
s_lo, s_hi = min(strip.values()), max(strip.values())
R["F15"]["torque_to_strip_Nm"] = [round(s_lo * 0.2 * 3 / 1000, 3), round(s_hi * 0.2 * 3 / 1000, 3)]
row("F15 M3 thread in T_most (0.8 engaged)", "fingertip 0.10 N.m + L1x2 30 N", round(pre(0.1) + 30), s_lo, "N", f"strip {s_lo}..{s_hi} N", kind="capacity")
row("F15 M3 thread in T_most (0.8 engaged)", "normal screwdriver 0.3 N.m", round(pre(0.3)), s_lo, "N", f"strip {s_lo}..{s_hi} N -> likely stripped", kind="capacity")
row("F15 M3 thread in T_most (0.8 engaged)", "2.0 L-key 0.6 N.m", round(pre(0.6)), s_lo, "N", f"strip {s_lo}..{s_hi} N -> stripped", kind="capacity")
# fix: M3 x 8 + 2 x DIN 125 M3 (0.5) under the head: tip -48.0, engaged 1.8
Le_fix = 1.8; strip_fix = [round(An * (Le_fix - 0.4) * tau["5754-H22 (Rm 220)"]), round(An * Le_fix * tau["6061-T6 (Rm 290)"])]
R["F15_fix"] = dict(screw="ISO 7380 M3 x 8 + 2 x DIN 125 M3 (Ø7 x 0.5) stacked on the DIN 9021", tip_z=-48.0, engaged=Le_fix,
                    strip_N=strip_fix, head_top_z=-41.0 + 1.0 + 1.65, head_to_neck_bottom=round(-36.5 - (-41.0 + 1.0 + 1.65), 2),
                    din125_r=3.5, din125_to_foot_hole=round(5.5 - 3.5, 2), head_to_foot_hole=round(5.5 - 2.85, 2),
                    din125_to_hub_bore=round(6.5 - 3.5, 2), tip_to_T_most_underside=0.2,
                    torque_to_strip_Nm=[round(s * 0.2 * 3 / 1000, 3) for s in strip_fix])
row("F15 fix M3x8 + 1.0 washers (1.8 engaged)", "normal screwdriver 0.3 N.m", round(pre(0.3)), strip_fix[0], "N", f"strip {strip_fix[0]}..{strip_fix[1]} N", kind="capacity")
# T_cap compression under F15 preload (washer on the T_cap end face 37.5 mm2, K12 S06)
A_cap = math.pi / 4 * (7.7 ** 2 - 3.4 ** 2)
R["T_cap_compression_MPa"] = {f"{T} N.m": round(pre(T) / A_cap, 2) for T in (0.05, 0.1, 0.3, 0.6)}
row("T_cap end face under F15 preload (sustained)", "fingertip 0.10 N.m", round(pre(0.1) / A_cap, 2), ALW_S, note="sustained limit 4.3 -> creep only adds axial play (bonded, located)")
row("T_cap end face under F15 preload (short-term crush)", "normal screwdriver 0.3 N.m", round(pre(0.3) / A_cap, 2), UTS, note="crush vs 25.8")
# T_cap creep -> axial play (A: creep strain 0.3..1 % of 4.4 mm over months at 15-50 % UTS)
R["T_cap_creep_play_mm"] = [round(0.003 * 4.4, 3), round(0.01 * 4.4, 3)]
# washer overlap on the gear bore edge vs a bought-gear bore chamfer (A: 0 .. 0.5)
ov = m01["washer_overlap_on_gear"]
R["washer_overlap"] = {f"chamfer {c}": dict(overlap=round(ov - c, 2), p_L1x2_MPa=round(30 / (math.pi * (4.5 ** 2 - (4.0 + c) ** 2)), 2) if ov - c > 0.01 else None)
                       for c in (0.0, 0.2, 0.3, 0.4, 0.5)}

# ======================================================================================================================
# 3. F10 lift module -> well at a normal screwdriver
# ======================================================================================================================
A_ins = math.pi * 4.0 * 4.0; F_ins = A_ins * EPOXY_U
for T in (0.1, 0.3):
    F = pre(T, 0.2, 2.0)
    row(f"F10 bonded insert M2x4xØ4 pull-out", f"{T} N.m", round(F), round(F_ins), "N", "capacity = epoxy 8 MPa x 50.3 mm2", kind="capacity")
    row(f"F10 DIN 433 washer on the pocket plate (9.7 mm2)", f"{T} N.m", round(F / 9.7, 1), UTS, note="crush (short-term) 25.8")
R["F10_0.3Nm"] = dict(preload_N=round(pre(0.3, 0.2, 2.0)), insert_capacity_N=round(F_ins),
                      consequence="bond shears, the insert is pulled against the pocket plate (OD 4.0 > hole Ø2.3): the plate stays clamped, "
                                  "the well pad is no longer clamped - module located only by the dowel + tongue/rail; plate may crack under the washer")

# ======================================================================================================================
# 4. L1 head used as a handle (30 N = 2 x 15 N) and 2 x L2 (60 N down)
# ======================================================================================================================
row("gear bond L1 (stage pulled up through the gear)", "L1 x2 30 N, x3 peel", round(3 * 30 / 442, 3), EPOXY_D, note="A 442 mm2 (K12 H2)")
# K12 rows scaled linearly to 2 x L2 = 60 N (these are the design's own section calcs, x 2)
row("hub disc ring under the Al foot (lift 0)", "2 x L2 60 N", round(60 / 305.5, 2), ALW_A, note="landed area 305.5 mm2 (overenie2)")
row("back floor 0.95 over the FFC groove (K12 H18 x2)", "2 x L2 60 N lift 0", round(4.25 * 2, 2), ALW_A, note="0.95 < 1.2 local-skin rule Z3.1 while loaded")
row("rail lips 2.5 (K12 H12/H13 x2)", "2 x L2 60 N lift 20", round(6.9 * 2, 2), ALW_A, note="exceeds abuse 12.9; lower-bound break at ~112 N")
R["rail_break_force_N"] = round(30 * UTS / 6.9)
row("F10 pad root r 3.65 + R1 (K12 H16 x2 -> 30 N lateral)", "2 x L2 60 N", round(1.19 * 2, 2), ALW_A)
row("T_most Al bridge (17.10: 19.9 MPa at 30 N, x2)", "2 x L2 60 N", 39.8, 130.0, note="metal (5754 yield ~130)")

# ======================================================================================================================
# 5. DROP 0.3 m of the stage (service S3: P_sachta + bonded gear + inserts + FFC)
# ======================================================================================================================
m_stage = 15.37 + 20.12 + 2 * 0.35 + 1.0          # g; A: 2 inserts 0.35 g each, FFC pair ~1 g
h = 0.30; v = math.sqrt(2 * g * h); Ek = m_stage / 1000 * g * h
R["drop"] = dict(mass_g=round(m_stage, 1), v_mps=round(v, 2), energy_mJ=round(Ek * 1000, 1))
k_desk = 5e5                                        # A: local stiffness of a wooden / laminate desk under an edge, N/m
m_eff = 0.4 * m_stage / 1000                        # A: effective mass of an edge / corner-first impact (rotation absorbs the rest)
def impact(k_feat):
    k = 1 / (1 / k_feat + 1 / k_desk)
    return v * math.sqrt(k * m_eff)
# (a) drum shroud tip, hit radially-inward component at 11..21 deg tilt (geometry: the shroud outer-bottom corner is the first
#     contact for a tilt between the gear-edge line 11.3 deg and the floor-edge line 20.7 deg toward the shroud side)
t_s, L_s = 1.2, 3.75; b_eff = 2 * L_s              # A: effective width of a point-loaded cantilever plate edge = 2 L
I_s = b_eff * t_s ** 3 / 12
k_s = 3 * E_RES * I_s / L_s ** 3 * 1000              # N/m
F_fs = UTS * b_eff * t_s ** 2 / (6 * L_s)            # N at the lower-bound strength (sharp root: no fillet measured -> Kt ignored here)
d_fs = F_fs / (k_s / 1000)                           # mm
R["drop"]["tilt_window_deg"] = [round(math.degrees(math.atan(0.3 / 1.5)), 1), round(math.degrees(math.atan(3.7 / 9.8)), 1)]
F_imp_s = impact(k_s) * math.sin(math.radians(16))  # radial share at a mid-window tilt of 16 deg
R["drop"]["shroud"] = dict(k_N_per_mm=round(k_s / 1000), F_break_N=round(F_fs, 1), deflection_at_break_mm=round(d_fs, 3),
                           gap_to_gear_tips_mm=0.30, energy_to_break_mJ=round(0.5 * F_fs * d_fs, 2),
                           impact_force_radial_N=round(F_imp_s, 1))
row("drum shroud tip (1.2 x 3.75, sharp root) hit at 11-21 deg tilt", "drop 0.3 m, stage 37 g", round(F_imp_s, 1), round(F_fs, 1), "N",
    "capacity < demand -> a local chip is possible; the gear tips (0.30 behind) back it only after 0.30 > break deflection", kind="capacity")
# (b) slim corner of the top ring (1.21 x 8.0 tall, z -10..-2) hit radially at its outer surface (stage lying on its side)
t_c, h_c, L_c2 = 1.21, 8.0, 6.0                      # A: span between the thicker sections either side of the corner minimum ~6 mm
I_c = h_c * t_c ** 3 / 12
k_c = 192 * E_RES * I_c / L_c2 ** 3 * 1000
F_fc = UTS * (h_c * t_c ** 2 / 6) / (L_c2 / 8)
F_imp_c = impact(k_c)
R["drop"]["slim_corner_ring"] = dict(k_N_per_mm=round(k_c / 1000), F_break_N=round(F_fc, 1), impact_force_N=round(F_imp_c, 1),
                                     energy_to_break_mJ=round(0.5 * F_fc ** 2 / k_c * 1000, 2))
row("slim top-ring corner 1.21 x 8 (point hit, side drop)", "drop 0.3 m, stage 37 g", round(F_imp_c, 1), round(F_fc, 1), "N", "corner-first point hit only; a line contact along the corner spreads it", kind="capacity")
# (c) lower slim corner (1.34) hit along a line of ~30 mm (stage on its side): per-mm load
q = impact(1e7) / 30.0                              # A: line contact over 30 mm, stiff
M = q * 6.0 / 8; s_c3 = 6 * M / 1.342 ** 2
R["drop"]["lower_corner_line_hit_MPa"] = round(s_c3, 1)
row("lower slim corner 1.34 (line hit over 30 mm)", "drop 0.3 m, side", round(s_c3, 1), UTS, note="vs the lower-bound strength")

# ======================================================================================================================
# 6. GEAR BOND misalignment (eccentric bond e, wedge w)
# ======================================================================================================================
L_b = -6.5 - (-43.9)                                 # journal centre z -6.5 .. gear mid-plane -43.9
c_journal = 0.145                                    # 17.16-3 radial play of the upper journal
R["bond_misalignment"] = {}
for e in (0.05, 0.1, 0.2, 0.3):
    R["bond_misalignment"][f"e {e}"] = dict(mesh_change="none (the gear runs concentric on T_cap)",
                                            stage_tilt_deg=round(math.degrees(e / L_b), 3),
                                            shroud_gap_min=round(0.30 - e, 2),
                                            journal_play_left=round(c_journal - e, 3))
R["bond_misalignment"]["gear_tilt_freedom_on_T_cap_deg"] = [round(math.degrees(2 * 0.02 / 4.0), 2), round(math.degrees(2 * 0.07 / 4.0), 2)]
for w in (0.05, 0.1, 0.2):                         # uneven glue line over the 25 mm hub disc
    a = w / 25.2
    R["bond_misalignment"][f"wedge {w}"] = dict(stage_tilt_deg=round(math.degrees(a), 2), top_offset_mm=round(a * L_b, 3),
                                                exceeds_journal_play=a * L_b > c_journal)
# thermal mismatch brass gear <-> resin hub (A: resin CTE 70e-6, brass 19e-6, epoxy G 1.0 GPa, glue 0.1; or G 0.5 GPa, glue 0.2)
for (G_a, t_a, tag) in ((1000.0, 0.1, "rigid epoxy, 0.1 glue"), (500.0, 0.2, "toughened epoxy, 0.2 glue")):
    for dT in (20.0, 30.0):
        da = (70e-6 - 19e-6) * dT
        N_inf = E_RES * 1.25 * da / (1 - 0.35)            # N/mm, biaxial
        lam = math.sqrt(G_a / t_a * (1 / (E_RES * 1.25) + 1 / (100000.0 * 4.0)))
        R.setdefault("thermal_mismatch", {})[f"{tag}, dT {dT}"] = dict(resin_stress_MPa=round(N_inf / 1.25, 2),
                                                                       edge_shear_MPa=round(N_inf * lam, 1),
                                                                       decay_length_mm=round(1 / lam, 2))

# ======================================================================================================================
# 7. LONG TERM: creep, PTFE wear, heat
# ======================================================================================================================
m_head = m00["TOTAL_head_neck_g"]
m_rot = m_head + 15.37 + 20.12 + 3.15 + 13.4 + 5.0          # + module + ear/arm (A: 5 g)
R["creep"] = dict(head_neck_g=m_head, rotating_g=round(m_rot, 1),
                  back_wall_comp_MPa=round(m_head / 1000 * g / (2.0 * 30.0), 3),
                  ptfe_thrust_MPa=round(m_rot / 1000 * g / 389.0, 4),
                  note="the hub disc carries NO sustained load at rest (rest gap 0.15; weight goes F10 -> back wall -> floor -> bond in compression)")
row("back wall / floor under the head weight (sustained)", "creep", R["creep"]["back_wall_comp_MPa"], ALW_S)
row("F10 insert bond under preload (sustained)", "0.10 N.m fingertip", 4.97, EPOXY_U, note="62 % of the assumed epoxy strength, sustained -> relaxes; no Loctite on F10")
# PTFE wear on the static pivot (A: unfilled PTFE film k 1e-4 .. 1e-3 mm3/Nm dry; normal-use radial load 4 N = mesh at 0.05 N.m
#   + head-moment couple; 1000 moves of +-45 deg per day; wear concentrated on 1/3 of the circumference (load direction static))
F_use = 0.05 / 0.0144 / math.cos(math.radians(20)) + 0.6
s_day = 1000 * 2 * (math.pi / 4) * 4.0 / 1000           # m/day at r 4.0
A_wear = math.pi * 7.96 / 3 * 4.0
R["ptfe_pivot_wear"] = dict(F_N=round(F_use, 1), sliding_m_per_year=round(s_day * 365), contact_mm2=round(A_wear, 1))
for k in (1e-4, 1e-3):
    depth = k * F_use * s_day * 365 / A_wear
    R["ptfe_pivot_wear"][f"k {k:g}"] = dict(depth_mm_per_year=round(depth, 3), years_to_wear_tape=round(0.13 / depth, 1))
R["ptfe_pivot_wear"]["grease_note"] = "A: a PTFE-compatible grease or a UHMW-PE tape lowers k by ~10-100x"
# PTFE thrust washer (24 x 10 x 0.3) under the gear
s_th = s_day * 365 * 8.5 / 4.0
R["ptfe_thrust_wear"] = {f"k {k:g}": round(k * m_rot / 1000 * g * s_th / 389.0, 4) for k in (1e-4, 1e-3)}
# MG90S stall heating (A: 0.7 A x 5 V = 3.5 W at stall; case 25.5 cm2, h 10 W/m2K -> 39 K/W; heat capacity 13.4 g x 0.8 J/gK)
Rth = 1 / (10 * 25.5e-4); C = 13.4 * 0.8; tau_t = Rth * C
R["mg90s_heat"] = dict(Rth_K_per_W=round(Rth), tau_s=round(tau_t), dT_stall_60s=round(3.5 * Rth * (1 - math.exp(-60 / tau_t)), 1),
                       dT_stall_180s=round(3.5 * Rth * (1 - math.exp(-180 / tau_t)), 1), dT_hold_0p6W_steady=round(0.6 * Rth, 1),
                       distance_case_to_P_sachta_mm=round(17.1 - 15.1, 1))

# ======================================================================================================================
# 8. 6805 in T_spodok (J1) - brief (A: catalogue class 61805: C ~4.3 kN, C0 ~2.6 kN - from memory, UNVERIFIED)
# ======================================================================================================================
R["b6805"] = dict(C0_N=2600, axial_2xL2_plus_weight_N=70, ratio=round(70 / 2600, 3), K12_shoulder_L2_MPa=0.24, K12_bond_L1x2_MPa=0.04)

# ======================================================================================================================
# 9. Crude bracket: wall bending at a guide land under the twist (lens A's 3-D FE decides)
# ======================================================================================================================
arm = 27.5                                            # front land x -15 / back land x +12.5 couple arm (measured land positions)
for T, tag in ((0.6, "L3"), (0.88, "L8")):
    F = T * 1000 / arm
    q_full = F / 34.0                                 # A: neck bears uniformly on the 34 mm land
    s_fixed = 6 * (4.41 * q_full) / 1.342 ** 2         # fixed at the corner 6 mm away (corner 1.34)
    s_hinged = 6 * (5.14 * q_full) / 2.3 ** 2          # hinged corners, moment under the land (wall + land 2.3)
    R.setdefault("land_bracket", {})[tag] = dict(F_land_N=round(F, 1), s_corner_fixed=round(s_fixed, 1), s_span_hinged=round(s_hinged, 1))

json.dump(dict(results=R, table=rows), open(f"{OUT}/m03_calcs.json", "w"), indent=1, default=str)
for r in rows:
    print(f"{r['feature'][:58]:58s} | {r['case'][:30]:30s} | {r['value']} / {r['allowable']} {r['unit']} | margin {r['margin']}")
print(json.dumps(R, indent=1, default=str)[:6000])

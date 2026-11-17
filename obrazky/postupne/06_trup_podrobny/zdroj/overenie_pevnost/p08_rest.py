"""p08 - stage axial path (L1), deck / pivot (L2, mesh force), shoulder (L5, L6), J1 (L4, L8), door (L6, L7), fasteners (L7).
Inputs: measured sections from p02/p06/p07 logs (quoted in the comments), constants of t4_common / T4_spec, bought-part data
(see the report).  Every assumption is printed."""
import math, numpy as np, pv_lib as L
log = L.Log("p08_rest")
G = 9.80665; rows = []
def row(feature, case, section, stress, allow, abuse=False, note=""):
    if isinstance(stress, (int, float)) and isinstance(allow, (int, float)):
        v = L.verdict(stress, allow, abuse); v.pop("sigma")
        rows.append(dict(feature=feature, case=case, section=section, stress=round(stress, 2), note=note, **v))
    else:
        rows.append(dict(feature=feature, case=case, section=section, stress=stress, allow=allow, note=note))

# ======================= L1 path: is the stage retained axially? ======================================================
# journal cone: r 28.07 at z -4.5 -> r 26.5 at z -3.0; ring golier_prstenec r 26.75..28.25, bottom z -2.0
z_cone_at_ring = -3.0 - (26.75 - 26.5) / (28.07 - 26.5) * 1.5
gap = -2.0 - z_cone_at_ring
log("L1: stage rises %.3f mm (analytic; overenie_geometria g01 measured 1.237) until the journal cone meets the ring inner edge r 26.75" % gap)
pin_eng = 0.70
log("    stop pin engagement in the deck groove %.2f mm -> the +-90 deg hard stop is LOST after %.2f mm of the %.2f mm rise" % (pin_eng, pin_eng, gap))
face0 = 3.2; face1 = (-42.3) - max(-45.5, -45.7 + gap)
log("    gear mesh face width 3.20 -> %.2f mm when the stage is up (tooth stress x %.2f)" % (face1, face0 / face1))
row("pan hard stop under L1 (stage lifted)", "L1 15 N", "pin engagement 0.70 vs rise 1.24", "stop disengaged", "engaged", note="functional failure")
# ring contact: line contact along r 26.75 circumference, 15 N
Lc = 2 * math.pi * 26.75
log("    ring corner on the cone: line load %.3f N/mm over %.0f mm; ring glue (OD 56.5 x 6) shear %.3f MPa" % (15 / Lc, Lc, 15 / (math.pi * 56.5 * 6)))
row("golier_prstenec glue (only axial retention of the stage)", "L1 15 N", "Ø56.5 x 6 bond", 15 / (math.pi * 56.5 * 6), 8 / 3, True)
# with the fix of montaz M01 (M3 shoulder screw + Ø7 washer on the 1.2 hub disc)
tau = 15 / (math.pi * 7 * 1.2)
log("    fix M01(a) check: M3 shoulder screw + Ø7 steel washer on the 1.2 hub disc: punching shear %.2f MPa (L1), M3 insert bond %.2f MPa" %
    (tau, 15 / (math.pi * 4.2 * 4.0)))
row("[fix check] hub disc 1.2 under a Ø7 washer (M3 shoulder screw)", "L1 15 N", "π·7·1.2", tau, 12 * 0.6, True)

# ======================= L2 path below the stage ======================================================================
A_ptfe = math.pi * (12.0 ** 2 - 6.2 ** 2)
log("L2: PTFE washer pressure %.2f MPa (30 N + stage 0.4 N on %.0f mm2)" % (30.4 / A_ptfe, A_ptfe))
row("PTFE washer / gear underside", "L2 30 N", "annulus r 6.2..12.0", 30.4 / A_ptfe, 5.0, True)
# deck strip across the stop groove at azimuth 45 deg, NOT counting the foam (one-way strip between the cradle walls, span 25.1)
p = 30.4 / A_ptfe
x45 = 13.5 * math.cos(math.radians(45)); ylim = math.sqrt(12 ** 2 - x45 ** 2)
Wstrip = p * 2 * ylim; R = Wstrip / 2; yg = 13.5 * math.sin(math.radians(45))
Mg = R * (12.55 - yg)
s_groove = Mg / (0.6 ** 2 / 6)
s_full = (R * 12.55 - p * ylim * ylim / 2) / (1.8 ** 2 / 6)
log("    deck strip at x %.1f: line load %.2f N/mm, moment at the groove (y %.1f) %.2f N.mm/mm -> 0.6 floor %.0f MPa (unbacked); "
    "1.8 plate centre %.1f MPa; the J1 servo + 0.5 PORON below take an UNQUANTIFIED share" % (x45, Wstrip, yg, Mg, s_groove, s_full))
row("T_paluba 0.6 floor under the stop groove (unbacked by the foam)", "L2 30 N", "0.6 x 1 mm strip, span 25.1", s_groove, 12.0, True, "foam / servo backing not counted")
row("T_paluba 1.8 plate (unbacked)", "L2 30 N", "1.8 strip", s_full, 12.0, True)
# pivot pin: mesh force at the gear -> pivot (1.04 x, the journal takes -0.04)
for nm, Tg in (("L3 hand 0.6 N.m", 0.6), ("L8 STS3032 stall 0.883 N.m", 2 * 4.5 * G / 100)):
    Ft = Tg * 1000 / 14.4; Fr = Ft * math.tan(math.radians(20)); F = 1.04 * math.hypot(Ft, Fr)
    p_run = F / (6.0 * 2.8)
    M = F * 1.6; p_seat = F / (6 * 3.5) + 6 * M / (6 * 3.5 ** 2)
    log("pivot %s: radial %.1f N; running bearing in the gear/hub bore %.1f MPa (6 x 2.8); press seat in the deck boss %.1f MPa (6 x 3.5, lever 1.6)"
        % (nm, F, p_run, p_seat))
    row("pivot Ø6 running in the P_koleso / hub bore", nm, "6 x 2.8 projected", p_run, 5.0, False, "Z3.8 sliding limit 5")
    row("pivot Ø6 seat in the T_paluba boss (resin)", nm, "6 x 3.5, lever 1.6", p_seat, 12.0, True)

# ======================= shoulder (left; measured p06) ================================================================
Z_neck = 964.0                   # T_klb_L x 38.6..40.2 (r 5.1..11.0, 3 x Ø2.3 holes)
x_hub = 54.8                     # arm hub centre on the Ø22 step (x 51.556..57.956)
Kt_step = 2.5                    # sharp step r 11.0 -> 13.5 (R 0 measured) - assumed Kt
for nm, M, abuse in (("L5 10 N at 72 mm along X (0.72 N.m)", 720.0, True), ("lifted by one arm 15 N (radial at the hub)", 15 * (x_hub - 38.4), True)):
    s = M / Z_neck
    row("T_klb neck x 38.4..40.6 (+ sharp step Kt 2.5)", nm, "Z 964 mm3 measured", s * Kt_step, 12.0, abuse)
    log("T_klb neck %s: M %.0f N.mm -> %.2f MPa nominal, %.2f with Kt %.1f" % (nm, M, s, s * Kt_step, Kt_step))
# F8 bolts: 3 x M2 on r 7.5, compression toe at r 11 (neck OD)
d = [11 + 7.5 * math.sin(math.radians(a)) for a in (90, 210, 330)]
for nm, M in (("L5 0.72 N.m", 720.0), ("lifted by one arm 15 N", 15 * (x_hub - 38.4))):
    Fb = M * max(d) / sum(q * q for q in d)
    tb = Fb / (math.pi * 3.2 * 3.0)
    log("F8 %s: max bolt tension %.1f N -> bonded M2 insert (Ø3.2 x 3.0) %.2f MPa" % (nm, Fb, tb))
    row("F8 M2 insert bond in the column boss", nm, "Ø3.2 x 3.0 knurl", tb, 8.0 / 3, True, "epoxy 8 MPa assumed")
# L6: impact force on the arm hub (radial) that the shoulder survives at the static allowable (one-off impact, no SF 2)
F_neck = 12.0 * Z_neck / (Kt_step * (x_hub - 38.4))
F_f8 = (8.0 * math.pi * 3.2 * 3.0) * sum(q * q for q in d) / (max(d) * (x_hub - 38.4))
log("L6: radial impact force on the arm hub that brings the T_klb neck to 12 MPa: %.0f N; that pulls an F8 insert at 8 MPa bond: %.0f N" % (F_neck, F_f8))
# energy estimate: robot 1.0 kg toppling sideways, CoG drop ~ 0.07 m (assumed), stopping distance 1..3 mm
E = 1.0 * G * 0.07
log("L6 estimate: toppling energy %.2f J -> mean impact force %.0f N (3 mm stop) .. %.0f N (1 mm stop) if the shoulder takes it alone (ASSUMED values)" %
    (E, E / 0.003, E / 0.001))
row("T_klb + F8 under a sideways topple (L6)", "L6 (estimate)", "capacity %.0f N (neck) / %.0f N (F8 bond)" % (F_neck, F_f8),
    "impact %.0f..%.0f N (assumed)" % (E / 0.003, E / 0.001), "-")
# column (left) - propped by the bridges at z -55 (cradle walls extended, 2 x 1.6 x 10), fixed at the foot
for nm, Mz55, Z, abuse in (("L5 10 N along X at the arm tip, arm up/down (0.72 N.m + 10 N x 38 mm)", 720 + 10 * 38, 47.2, True),
                           ("lifted by one arm 15 N (vertical at x 54.8)", 15 * (x_hub - 36.5), 45.1, True)):
    s = Mz55 / Z
    log("column %s: M %.0f N.mm at the bridge level / above -> %.1f MPa (Z %.1f, bending in x) - column alone, cap shell share not counted" % (nm, Mz55, s, Z))
    row("T_ram column (U channel) above the bridges", nm, "Z %.1f (z -55 / -35 measured)" % Z, s, 12.0, abuse, "cap shell share not counted")
# torsion of the open U column from a Y force at the arm tip (lever x 18.3)
J = (24 * 2.0 ** 3 + 2 * 7.6 * 1.6 ** 3) / 3
tau = 10 * 18.3 * 2.0 / J
log("column torsion from 10 N along Y at the hub: tau %.1f MPa (open U, J %.0f mm4)" % (tau, J))
row("T_ram column torsion (open U)", "L5 10 N along Y", "J %.0f mm4" % J, tau, 12 * 0.6, True)

# ======================= J1 ===========================================================================================
T_C001_74 = 19.5 * G / 100; T_84 = T_C001_74 * 8.4 / 7.4; T_12V = 30 * G / 100
log("STS3215 stall: C001 19.5 kg.cm @ 7.4 V = %.2f N.m; scaled to 8.4 V (2S full) %.2f N.m (ASSUMED linear); 12 V version 30 kg.cm = %.2f N.m" % (T_C001_74, T_84, T_12V))
for nm, T, abuse in (("L4 clutch slip 0.25 N.m", 0.25, False), ("L8 STS3215 stall 2.17 N.m (clutch locked)", T_84, True)):
    Ft = T * 1000 / 9.0
    s_brass = Ft / (3.2 * 1.0 * 0.309)
    F_wall = T * 1000 / 45.2
    s_wall10 = (F_wall / 34.5) * 34.5 ** 2 / 8 / (10 * 1.6 ** 2 / 6)
    s_wall20 = s_wall10 / 2
    log("J1 %s: pinion Ft %.0f N -> brass m1 18T b 3.2 Lewis %.0f MPa; servo-case couple %.0f N on the 1.6 cradle walls -> %.0f..%.0f MPa (10..20 mm strip)"
        % (nm, Ft, s_brass, F_wall, s_wall20, s_wall10))
    row("J1 brass pinion / sun m1 18T (bought)", nm, "b 3.2, Y 0.309", s_brass, 100.0, abuse, "brass bending allowable ~100 assumed")
    row("T_ram cradle walls 1.6 (STS3215 reaction couple)", nm, "plate strip 10..20 x 1.6, span 34.5", s_wall10, 12.0, abuse)
# stop lug (r 18.5..21, 2.5 x 2.5, root sharp R 0)
for nm, T, abuse in (("L4 clutch-limited 0.25 N.m", 0.25, False), ("L4 hand forcing the stop 0.6 N.m", 0.6, True)):
    F = T * 1000 / 19.75
    s = F * 1.15 / (2.5 * 2.5 ** 2 / 6)
    log("J1 stop lug %s: F %.1f N, root bending %.1f MPa nominal, x Kt 2 (sharp root) %.1f" % (nm, F, s, 2 * s))
    row("T_spodok J1 stop lug 2.5 x 2.5 (sharp root)", nm, "2.5 x 2.5, lever 1.15", s, 6.0 if not abuse else 12.0, abuse, "unfilleted root -> notch allowable")
# floor membrane 1.2 under the STS3215 (inside the plinth r 17), L2 share 15 N, simply supported disc (upper bound with the passage hole x2)
W = 15.0; s_disc = 3 * (3 + 0.38) * W / (8 * math.pi * 1.2 ** 2)
log("cap floor 1.2 under the STS3215 (disc r 17, 15 N of L2): %.1f MPa; with the pinion passage notch ~x2 -> %.1f MPa (estimate)" % (s_disc, 2 * s_disc))
row("T_spodok floor 1.2 under the STS3215", "L2 30 N (half on r<17)", "disc r 17 x 1.2 (passage ~x2)", 2 * s_disc, 12.0, True, "estimate")
# skirt disc 1.0 x 4.5 (handled; edge knock 20 N assumed)
s_sk = 20 * 4.5 / (10 * 1.0 ** 2 / 6)
row("T_spodok skirt disc 1.0 (handled, edge knock 20 N assumed)", "L6/L7 handling", "1.0 x 10 effective, lever 4.5", s_sk, 12.0, True)
log("skirt 1.0: 20 N edge knock -> %.0f MPa" % s_sk)

# ======================= door =========================================================================================
Fm = 6.0   # N per magnet pair at 0.2 mm gap - ASSUMED (supermagnete S-05-02-N52N: 6.67 N on steel in contact)
z_hook, z_up, z_lo, z_pull = -11.0, -24.0, -60.0, -70.0
Mmag = 2 * Fm * (z_hook - z_lo) + 2 * Fm * (z_hook - z_up)
Fpull = Mmag / (z_hook - z_pull)
Rh = 4 * Fm - Fpull
s_hook = 6 * (Rh / 2) * 1.25 / (8 * 0.85 ** 2)
log("door: 4 magnet pairs x %.1f N (assumed); opening by levering the bottom: pull %.1f N, hook reaction %.1f N total -> hook tab %.1f MPa per opening" % (Fm, Fpull, Rh, s_hook))
row("T_dvere hook tab 0.85 x 8 (100 openings)", "L7 door opening (lever the bottom)", "0.85 x 8, lever 1.25", s_hook, 6.0, False, "repeated -> 6 MPa")
s_hook_top = 6 * (Fm + 5.0) * 1.25 / (8 * 0.85 ** 2)
row("T_dvere hook tab 0.85 x 8", "pulled at the top (wrong handling): magnet 6 N + hand 5 N per hook", "0.85 x 8", s_hook_top, 12.0, True)
log("door pulled at the top: per hook %.1f N -> %.1f MPa" % (Fm + 5, s_hook_top))
tau_m = Fm / (math.pi * 5 * 2 + math.pi * 2.5 ** 2)
row("door / frame magnet bond (pull-off 100x)", "L7", "Ø5 x 2 pocket, side + bottom", tau_m, 8.0 / 3, False)

# ======================= fasteners: L7 tightening =====================================================================
def preload(T, d, K=0.2):
    return T / (K * d / 1000)
cases = [  # name, thread, T (N.m), insert OD x L or None, engagement for thread-forming, head dk, wall
    ("F1 T_spodok->T_stred, M2.5 into bonded insert (wall 1.4)", 2.5, 0.30, (3.5, 4.0), None, 4.7),
    ("F2 T_spodok->T_ram, M2.5 into insert (wall 1.2 / 1.1)", 2.5, 0.30, (3.5, 4.0), None, 4.7),
    ("F3 T_paluba->T_ram, M2.5 pan head into insert", 2.5, 0.30, (3.5, 4.0), None, 4.5),
    ("F8 T_klb->column, M2 into insert", 2.0, 0.15, (3.2, 3.0), None, 3.8),
    ("F10 bracket->pads, M2x4 into insert (2.3 engaged)", 2.0, 0.15, (3.2, 3.0), None, 3.8),
    ("F4 pan servo, M2 thread-forming (3.55)", 2.0, 0.15, None, 3.55, 3.8),
    ("F11 MG90S tab, M2 thread-forming (3.55)", 2.0, 0.15, None, 3.55, 3.8),
    ("F12 ear->foot, M2 thread-forming (5.44)", 2.0, 0.15, None, 5.44, 3.8),
    ("F7 controller, M2 thread-forming (2.43)", 2.0, 0.15, None, 2.43, 3.8),
    ("FPC clamp, M2 thread-forming (1.80)", 2.0, 0.15, None, 1.80, 3.8),
]
TAU_EPOXY, TAU_RESIN = 8.0, 0.6 * 35.0
for nm, d, T, ins, Le, dk in cases:
    K = 0.2 if ins else 0.3
    F = preload(T, d, K)
    A_head = math.pi / 4 * (dk ** 2 - (d + 0.3) ** 2)
    p_head = F / A_head
    if ins:
        A = math.pi * ins[0] * ins[1]; cap = TAU_EPOXY * A
        Tsafe = (cap / 2) * K * d / 1000
        log("L7 %s: %.2f N.m -> preload %.0f N; bond capacity %.0f N (8 MPa on %.0f mm2); head bearing %.0f MPa; torque for SF 2 on the bond: %.3f N.m"
            % (nm, T, F, cap, A, p_head, Tsafe))
        row(nm, "L7 %.2f N.m" % T, "bond Ø%.1f x %.1f" % ins, F / A, TAU_EPOXY, True, "max torque %.3f N.m" % Tsafe)
    else:
        A = math.pi * d * Le * 0.5; cap = TAU_RESIN * A
        Tsafe = (cap / 2) * K * d / 1000
        log("L7 %s: %.2f N.m -> preload %.0f N (K 0.3); thread strip-out %.0f N (21 MPa on %.1f mm2); head bearing %.0f MPa; torque for SF 2: %.3f N.m"
            % (nm, T, F, cap, A, p_head, Tsafe))
        row(nm, "L7 %.2f N.m" % T, "thread π·d·L/2 = %.1f mm2" % A, F / A, TAU_RESIN, True, "max torque %.3f N.m" % Tsafe)
    row(nm + " - head on resin", "L7 %.2f N.m" % T, "head Ø%.1f" % dk, p_head, 12.0, False, "washer needed")
# thread-forming hoop factor relative to a rule boss (OD 2.5 d)
a = 0.85
def kh(wall):
    b = a + wall; return 2 * a * a / (b * b - a * a)
k_rule = kh(2.5 - 0.85)
for nm, wall in (("F12 foot", 1.15), ("F4 post", 1.20), ("F11 post", 1.30), ("FPC clamp", 0.83), ("F7 standoff", 1.65), ("LED/speaker bosses (T_stred)", 1.30)):
    log("thread-forming boss %s: wall %.2f -> OD hoop factor %.2f x the rule boss" % (nm, wall, kh(wall) / k_rule))
    rows.append(dict(feature="thread-forming boss hoop (Z3.4b)", case=nm, section="wall %.2f around Ø1.7" % wall, stress="x %.2f of a rule boss" % (kh(wall) / k_rule), allow="x 1.00", ok=bool(kh(wall) <= k_rule)))
# countersunk crank screw in the 1.18 hub wall: hoop from the 90 deg cone
F = preload(0.3, 2.5)
Th = F / (2 * math.pi)
s = Th / (1.18 * 1.5)
log("crank M2.5 countersunk in the 1.18 hub wall at 0.3 N.m: preload %.0f N, cone hoop force %.0f N -> %.0f MPa" % (F, Th, s))
row("P_kluka hub wall 1.18 around the M2.5 countersunk head", "L7 0.3 N.m", "1.18 x 1.5 ring", s, 12.0, True)
log.rows = rows; log.save("p08_rest")

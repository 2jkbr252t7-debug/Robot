"""p04 - statics of the lift module: MG90S in its bracket (ledge, tab post F11), bracket -> stage (F10 pads), ear -> foot (F12),
foot plate, MG90S output shaft.  Geometry numbers measured in p02_probe.log (sections / chords on the STL)."""
import math, numpy as np, pv_lib as L
log = L.Log("p04_lift_joints")
G = 9.80665; rows = []
W_HEAD = 0.17 * G
x_load = -18.65                  # ear mid-plane = line of action of the pin force on the crank (pin x -19.9..-14.5)
x_ledge0, x_ledge1 = -6.35, 16.0  # ledge under the servo (z -41.9..-41.1, y 17.1..26.2)
x_tab = -1.25                    # MG90S tab x -2.5..0, screw along +X into the post x 0..5 at (y 23.2, z -15.85)
y_load, y_plate = 23.2, 17.1     # crank plane / servo axis y; bracket plate face
Z_POST = 17.6                    # post section y 17.5..23.2: 5.0 (x) x 4.6 (z), Z 17.6 / 17.3 mm3 (p02)
Z_LEDGE_PER_MM = 0.8 ** 2 / 6    # ledge 0.8 thick (measured z -41.9..-41.1)


def servo_supports(Fz):
    """vertical force Fz (+ up) on the crank at x_load; supports: ledge (push up only, at one of its ends) + tab screw (+/-)."""
    for xl in (x_ledge0, x_ledge1):
        # R1 + R2 + Fz = 0 ; R1*xl + R2*x_tab + Fz*x_load = 0
        A = np.array([[1, 1], [xl, x_tab]]); b = np.array([-Fz, -Fz * x_load])
        R1, R2 = np.linalg.solve(A, b)
        if R1 >= -1e-9:
            return xl, R1, R2
    return None


for nm, Fz, abuse, sust in (("L2 30 N down (mid lift / lift 20; lift 0 until the foot lands)", -30.0, True, False),
                            ("L1 15 N up", 15.0, True, False),
                            ("L8 MG90S stall 0.216 N.m (pin force 21.6 N, worst direction)", -21.6, True, False),
                            ("head weight 1.67 N (sustained)", -W_HEAD, False, True)):
    xl, R1, R2 = servo_supports(Fz)
    lever = y_load - y_plate
    s_post = abs(R2) * lever / Z_POST
    p_pilot = abs(R2) / (2.0 * 5.0)
    # ledge: R1 concentrated at its end, effective width 5 mm (45 deg spread over the 6.1 cantilever is cut by the end)
    s_ledge = R1 * lever / (5.0 * Z_LEDGE_PER_MM) if R1 > 0 else 0.0
    log("%s: ledge reaction %.1f N at x %.2f, tab screw %.1f N -> post bending %.1f MPa, F11 pilot bearing %.1f MPa, ledge (5 mm wide) %.0f MPa"
        % (nm, R1, xl, R2, s_post, p_pilot, s_ledge))
    allow = L.A_NOTCH if sust else L.A_STATIC
    for feat, s in (("P_drziak_serva tab post (F11 host) root", s_post), ("F11 M2 thread-forming pilot in the post (bearing)", p_pilot),
                    ("P_drziak_serva ledge 0.8 under the servo", s_ledge)):
        v = L.verdict(s, allow, abuse)
        rows.append(dict(feature=feat, case=nm, section={"P_drziak_serva tab post (F11 host) root": "5.0 x 4.6, Z 17.6, lever 6.1",
                                                          "F11 M2 thread-forming pilot in the post (bearing)": "Ø2 x 5 projected",
                                                          "P_drziak_serva ledge 0.8 under the servo": "0.8 thick, 5 mm effective, lever 6.1"}[feat],
                         stress=round(s, 1), **{k: q for k, q in v.items() if k != "sigma"}))
# ledge deflection that closes the 0.4 mm (0.5 foot gap - 0.1 slot play) at lift 0: stress at that deflection
E = L.E_MOD; Lc = 6.1; t = 0.8
s_at = 3 * E * 0.4 * (t / 2) / Lc ** 2
log("ledge as a cantilever (6.1 long, 0.8 thick): bending stress when its end has deflected the 0.4 mm that lands the foot on the hub disc at lift 0: %.0f MPa" % s_at)
rows.append(dict(feature="P_drziak_serva ledge, deflection-limited (lift 0, foot lands after 0.4)", case="L2 at lift 0", section="0.8 x 6.1 cantilever",
                 stress=round(s_at, 1), **{k: q for k, q in L.verdict(s_at, L.A_STATIC, True).items() if k != "sigma"}))

# ---- bracket -> stage: 2 x F10 (M2x4 in bonded M2 inserts of the pads), slots +-1 in x ---------------------------------
P1, P2 = np.array([19.5, -31.7]), np.array([8.0, -14.5])
c = (P1 + P2) / 2; d = np.linalg.norm(P1 - P2)
for nm, Fz, abuse in (("L2 30 N", -30.0, True), ("L1 15 N", 15.0, True), ("L8 MG90S stall 21.6 N", -21.6, True)):
    M = Fz * (x_load - c[0])                       # moment about y (x-z plane), N.mm
    # each screw: direct Fz/2 in z + moment share perpendicular to P1-P2
    e = (P2 - P1) / d; n = np.array([-e[1], e[0]])
    Fm = M / d
    F1 = np.array([0, Fz / 2]) + Fm * n * (+1); F2 = np.array([0, Fz / 2]) - Fm * n
    Fmax = max(np.linalg.norm(F1), np.linalg.norm(F2)); Fx = max(abs(F1[0]), abs(F2[0]))
    # pad: r 3.0 boss, 2.8 long from the wall (y 12.6 -> 15.4), insert hole 3.3: section at y 13.0 A 19.7, I 57.76 (p02)
    s_pad = Fmax * 2.8 / (57.76 / 3.0)
    p_ins = Fmax / (3.2 * 3.2)
    # x component by friction only (slots +-1.0 in x): needed clamp per screw with mu 0.3
    N_need = Fx / 0.3
    # resin under an M2 socket head (dk 3.8) on the 0.85 land: max clamp at 12 MPa
    A_head = math.pi / 4 * (3.8 ** 2 - 2.3 ** 2)
    N_max = 12.0 * A_head
    log("%s: moment about y %.0f N.mm, screw shear max %.1f N (x part %.1f): pad root bending %.1f MPa, insert bearing on the pad %.1f MPa; "
        "x share by friction needs a clamp of %.0f N per screw, the resin under the head allows %.0f N (12 MPa on %.1f mm2)"
        % (nm, M, Fmax, Fx, s_pad, p_ins, N_need, N_max, A_head))
    for feat, s, sec in (("P_sachta bracket pad root (r 3.0 boss on the 1.6 wall)", s_pad, "annulus r 1.65..3.0 at y 13.0, lever 2.8"),
                         ("F10 insert bearing in the pad", p_ins, "insert Ø3.2 x 3.2")):
        v = L.verdict(s, L.A_STATIC, abuse)
        rows.append(dict(feature=feat, case=nm, section=sec, stress=round(s, 1), **{k: q for k, q in v.items() if k != "sigma"}))
    rows.append(dict(feature="F10 slots (+-1 in x): x-load by friction only (Z3.7)", case=nm, section="2 x M2, mu 0.3",
                     stress="needs %.0f N clamp, resin allows %.0f N" % (N_need, N_max), ok=bool(N_need <= N_max / 2)))

# ---- ear -> foot (F12: one M2 thread-forming + dowel Ø1.5), prying about x ------------------------------------------
y_face = 9.8; lever_pry = 2.0      # screw at z -38.5 in a 4.0 flange/foot (z -40.5..-36.5): 2.0 to either edge
for nm, F, ypin, abuse in (("L1 15 N, lift 0 / 20 (pin y 23.2)", 15.0, 23.2, True), ("L2 30 N, lift 0 / 20", 30.0, 23.2, True),
                           ("L2 30 N, mid lift (pin y 13.2)", 30.0, 13.2, True), ("head weight 1.67 N sustained, lift 0 / 20", W_HEAD, 23.2, False)):
    T = F * (ypin - y_face) / lever_pry
    L_eng = 5.44; d = 2.0
    tau = T / (math.pi * d * L_eng * 0.5)                  # thread shear on the cylinder at the major diameter, 50 % material
    A_head = math.pi / 4 * (3.8 ** 2 - 2.3 ** 2)
    p_head = T / A_head
    # in-plane (x-z) moment: load at x -18.65, screw x -10, dowel x -15.5 -> couple
    Mxz = F * abs(x_load - (-12.75)); Fc = Mxz / 5.5
    p_dowel = (F / 2 + Fc) / (1.5 * 2.6)
    log("%s: prying screw tension %.0f N -> thread shear in the foot %.1f MPa (M2 x %.2f), head bearing on the ear flange %.0f MPa; "
        "dowel Ø1.5 bearing in the 2.6 flange %.1f MPa" % (nm, T, tau, L_eng, p_head, p_dowel))
    sust = "sustained" in nm
    for feat, s, sec, allow in (("F12 M2 thread in L_pata (pull-out, shear)", tau, "π·2·5.44·0.5 = 17.1 mm2", (L.A_NOTCH if sust else L.A_STATIC) * 0.6),
                                ("F12 screw head on the ear flange (bearing)", p_head, "pan head Ø3.8 on Ø2.3 hole", L.A_NOTCH if sust else L.A_STATIC),
                                ("ear dowel Ø1.5 in the flange (bearing)", p_dowel, "Ø1.5 x 2.6", L.A_NOTCH if sust else L.A_STATIC)):
        v = L.verdict(s, allow, abuse)
        rows.append(dict(feature=feat, case=nm, section=sec, stress=round(s, 1), **{k: q for k, q in v.items() if k != "sigma"}))
# ---- foot plate (L_pata, 4.0) bending at the bond edge y 0 (front neck half bonded, back half only in contact) ----------
for nm, F, abuse in (("L1 15 N (neck pulls up, ear holds the foot down)", 15.0, True),):
    M = F * (23.2 - 0.0)
    # effective width: ear flange x -19.9..-7.5 (12.4) + 2 x 9.8 (45 deg spread to y 0)
    beff = 12.4 + 2 * 9.8; Z = beff * 4.0 ** 2 / 6
    s = M / Z
    log("L_pata at the bond edge y 0, %s: M %.0f N.mm, effective width %.1f, sigma %.1f MPa (full-width Z 98 -> %.1f)" % (nm, M, beff, s, M / 98.0))
    rows.append(dict(feature="L_pata plate at the bond edge (y 0)", case=nm, section="4.0 x %.1f effective" % beff, stress=round(s, 1),
                     **{k: q for k, q in L.verdict(s, L.A_STATIC, abuse).items() if k != "sigma"}))
# neck bond (epoxy on the front neck half bottom, assumed 45 x 10 solid): peel from the L1 moment
A = 45 * 10; Zb = 45 * 10 ** 2 / 6
M = 15.0 * (23.2 + 5.0)
log("neck bond (front half 45 x 10, assumed solid): L1 15 N, M %.0f N.mm -> peel %.2f MPa + %.2f MPa direct" % (M, M / Zb, 15 / A))
rows.append(dict(feature="L_pata / neck epoxy bond (front half)", case="L1 15 N", section="45 x 10 assumed", stress=round(M / Zb + 15 / A, 2),
                 allow="epoxy peel on resin ~ 2 (assumed)", ok=bool(M / Zb + 15 / A < 1.0)))
# ---- MG90S output shaft: radial load with overhang -------------------------------------------------------------------
for nm, F in (("L1 15 N", 15.0), ("L2 30 N", 30.0)):
    ov = abs(x_load - (-12.5))          # from the turret face x -12.5 to the ear mid-plane
    log("MG90S output: radial %.0f N at %.2f mm beyond the turret face -> moment %.0f N.mm on the output bearing (no datasheet value; "
        "9 g servo outputs are typically not rated for side load)" % (F, ov, F * ov))
    rows.append(dict(feature="MG90S output shaft / bearing (bought)", case=nm, section="overhang %.2f" % ov, stress="%.0f N, %.0f N.mm" % (F, F * ov),
                     allow="not published (UNVERIFIED)", ok=None))
log.rows = rows; log.save("p04_lift_joints")

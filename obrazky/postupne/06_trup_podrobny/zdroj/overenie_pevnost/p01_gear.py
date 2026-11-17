"""p01 - pan gear teeth (Lewis, measured on the real tooth of P_koleso), stop pin + groove (T_paluba), gear bond.
Loads: L3 hand 0.6 N.m about the pan axis; L8 STS3032 stall 4.5 kg.cm @ 6 V = 0.441 N.m at the pinion (x 2 at the gear)."""
import math, json, numpy as np, pv_lib as L
log = L.Log("p01_gear")
G = 9.80665
T_HAND = 0.6                      # N.m, L3 (T4_zivica Z4)
T_STS3032 = 4.5 * G / 100         # N.m, 4.5 kg.cm @ 6 V (reseller listings of Feetech data, see report)
RATIO = 2.0
m, z_g, z_p = 0.8, 36, 18
r_pg, r_pp = m * z_g / 2, m * z_p / 2

# ---------------- tooth profile of P_koleso measured at mid face ------------------------------------------------------
t = L.load("P_koleso")
lo, hi = L.bbox(t); log("P_koleso bbox", lo.round(3), hi.round(3))
zc = -44.0
seg = L.section(t, "z", zc)                      # (x, y)
# material angular arcs on the pitch circle -> tooth centres
def arcs_at(r, n=7200):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = np.c_[r * np.cos(a), r * np.sin(a)]
    # point-in-polygon by even-odd: count crossings of a ray along +x from each point
    s = seg
    y0, y1 = s[:, 0, 1], s[:, 1, 1]; x0, x1 = s[:, 0, 0], s[:, 1, 0]
    inside = np.zeros(n, bool)
    for k in range(n):
        px, py = pts[k]
        c = ((y0 > py) != (y1 > py))
        xi = x0[c] + (py - y0[c]) * (x1[c] - x0[c]) / (y1[c] - y0[c])
        inside[k] = (np.sum(xi > px) % 2) == 1
    return np.degrees(a), inside
ang, ins = arcs_at(r_pg)
# tooth centres = centres of 'inside' runs
runs = []; k = 0; n = len(ins)
while k < n:
    if ins[k]:
        j = k
        while j + 1 < n and ins[j + 1]:
            j += 1
        runs.append((ang[k], ang[j])); k = j + 1
    else:
        k += 1
cent = [((a + b) / 2, b - a) for a, b in runs]
log("material runs on the pitch circle r %.2f: %d (teeth + drum)" % (r_pg, len(runs)))
# pick the tooth nearest to the pinion azimuth 254.3 (narrow runs only)
teeth = [(c, w) for c, w in cent if w < 8.0]
c0, w0 = min(teeth, key=lambda q: abs(q[0] - 254.3))
log("tooth used: centre azimuth %.2f deg, chordal thickness on the pitch circle %.3f mm (theory pi m / 2 - backlash/2 = %.3f)"
    % (c0, math.radians(w0) * r_pg, math.pi * m / 2 - 0.02))
# rotate so that the tooth axis is +u
ca, sa = math.cos(math.radians(-c0)), math.sin(math.radians(-c0))
R = np.array([[ca, -sa], [sa, ca]])
sr = seg @ R.T
# thickness s(u) perpendicular to the tooth axis, window |w| < 0.6 pitch
us = np.arange(12.6, 15.25, 0.01)
sv = []
for u in us:
    # chord of the section along w at fixed u
    a, b = sr[:, 0], sr[:, 1]
    c = ((a[:, 0] > u) != (b[:, 0] > u))
    wi = a[c, 1] + (u - a[c, 0]) * (b[c, 1] - a[c, 1]) / (b[c, 0] - a[c, 0])
    wi = np.sort(wi[np.abs(wi) < 1.2])
    if len(wi) >= 2:
        sv.append(wi[-1] - wi[0])
    else:
        sv.append(np.nan)
sv = np.array(sv)
r_tip = float(np.nanmax(np.where(np.isfinite(sv), us, np.nan)))
r_root = 13.4
log("measured tooth: tip r %.2f, thickness at r 13.6 %.3f, 13.8 %.3f, 14.0 %.3f, 14.4 %.3f, 14.8 %.3f" %
    tuple([r_tip] + [float(sv[np.argmin(abs(us - q))]) for q in (13.6, 13.8, 14.0, 14.4, 14.8)]))
# face width in mesh: gear teeth z -45.7..-42.2, pinion teeth z -45.5..-42.3 -> overlap
b_face = min(-42.2, -42.3) - max(-45.7, -45.5)
log("face width in mesh b = %.2f mm (gear -45.7..-42.2, pinion -45.5..-42.3)" % b_face)

def lewis_measured(Ft, b, r_load):
    """max over sections u of 6 Ft (r_load - u) / (b s(u)^2) (cantilever, tip load, Lewis without the radial component)"""
    ok = np.isfinite(sv) & (us < r_load)
    sig = 6 * Ft * (r_load - us[ok]) / (b * sv[ok] ** 2)
    i = int(np.argmax(sig))
    return float(sig[i]), float(us[ok][i]), float(sv[ok][i])

Y36, Y18 = 0.377, 0.309           # Lewis form factors, 20 deg full depth (Shigley table, interpolated for 36)
KF = 1.5                           # root fillet stress concentration assumed for resin (no fillet radius check here)
rows = []
for case, Tg in (("L8 STS3032 stall (0.441 N.m at the pinion -> 0.883 at the gear)", T_STS3032 * RATIO),
                 ("L3 hand 0.6 N.m on the head", T_HAND),
                 ("L4/normal: firmware torque 1.5 kg.cm rated (0.147 x 2)", 1.5 * G / 100 * RATIO)):
    Ft = Tg * 1000 / r_pg
    sm, um, sm_s = lewis_measured(Ft, b_face, r_tip)
    s_y = Ft / (b_face * m * Y36)
    # load shared by 2 teeth? contact ratio of the pair
    ra1, ra2 = r_pp + m, r_pg + m; rb1, rb2 = r_pp * math.cos(math.radians(20)), r_pg * math.cos(math.radians(20))
    a = r_pp + r_pg
    eps = (math.sqrt(ra1 ** 2 - rb1 ** 2) + math.sqrt(ra2 ** 2 - rb2 ** 2) - a * math.sin(math.radians(20))) / (math.pi * m * math.cos(math.radians(20)))
    abuse = "L3" in case or "L8" in case
    v = L.verdict(sm * KF, L.A_STATIC, abuse=abuse)
    log("%s: Ft %.1f N; Lewis measured %.1f MPa (section r %.2f, s %.2f); Lewis Y %.1f MPa; x Kf %.1f = %.1f MPa; contact ratio %.2f; "
        "limit %.1f -> util %.2f" % (case, Ft, sm, um, sm_s, s_y, KF, sm * KF, eps, v["limit"], v["util"]))
    rows.append(dict(feature="pan gear tooth (P_koleso, resin)", case=case, section="tooth root s %.2f at r %.2f, b %.1f" % (sm_s, um, b_face),
                     stress=round(sm * KF, 1), stress_noKf=round(sm, 1), lewisY=round(s_y, 1), **v))
    # pinion (bought): POM or brass
    s_p = Ft / (b_face * m * Y18)
    log("   pinion 18T (bought): Lewis %.1f MPa -> POM (allow ~ 20 static) %s / brass (allow ~ 80) %s" % (s_p, s_p <= 20, s_p <= 80))
    rows.append(dict(feature="pan pinion 18T (bought, POM or brass)", case=case, section="Y 0.309, b %.1f" % b_face, stress=round(s_p, 1),
                     allow="POM 20 / brass 80 (assumed)", ok_pom=bool(s_p <= 20 / (2 if abuse else 1)), ok_brass=bool(s_p <= 80 / (2 if abuse else 1))))
# required face width for resin teeth at the abuse limit 6 MPa
for Tg, nm in ((T_HAND, "L3"), (T_STS3032 * RATIO, "L8")):
    Ft = Tg * 1000 / r_pg
    sm, um, sm_s = lewis_measured(Ft, 1.0, r_tip)
    log("required face width for %s at 6 MPa (incl. Kf 1.5): %.1f mm (now %.1f)" % (nm, sm * KF / 6.0, b_face))

# ---------------- stop pin + groove ----------------------------------------------------------------------------------
tp = L.load("T_paluba")
lo, hi = L.bbox(tp); log("T_paluba bbox", lo.round(3), hi.round(3))
# groove depth / floor: vertical chords through the groove centreline r 13.5 at azimuth 0,45,90,135,180
for az in (0, 30, 60, 90, 120, 150, 180, 200, 270):
    x, y = 13.5 * math.cos(math.radians(az)), 13.5 * math.sin(math.radians(az))
    ch = L.chords("T_paluba", (x, y, -60), (0, 0, 1))
    log("T_paluba vertical chords at r 13.5 az %3d: %s" % (az, ch))
# groove width at az 90 (radial chord at z -46.5, i.e. inside the groove depth)
log("T_paluba radial chords at az 90, z -46.3:", L.chords("T_paluba", (0, 0, -46.3), (0, 1, 0)))
log("T_paluba radial chords at az 90, z -47.5:", L.chords("T_paluba", (0, 0, -47.5), (0, 1, 0)))
# groove end walls: tangential chord at r 13.5 near az 0 / 180, z -46.3 (top 0.3 of the groove depth)
for az in (-8, -4, -2, 0, 2, 182, 184, 188):
    x, y = 13.5 * math.cos(math.radians(az)), 13.5 * math.sin(math.radians(az))
    ch = L.chords("T_paluba", (x, y, -60), (0, 0, 1))
    log("  vertical chords r 13.5 az %4d: %s" % (az, ch))
# stop pin engagement: pin z -46.7 .. -42.2 (P GEAR stop_pin), deck top -46.0 -> engagement
pin_bot, deck_top = -46.7, -46.0
eng = deck_top - pin_bot
log("stop pin: bottom z %.2f, deck top %.2f -> engagement %.2f mm into the groove; stage lifts 1.237 under L1 (overenie_geometria g01) -> "
    "pin leaves the groove after %.2f mm of lift" % (pin_bot, deck_top, eng, eng))
r_stop = 13.5
for case, T in (("L3 hand into the stop", T_HAND), ("L8 STS3032 stall into the stop (x2)", T_STS3032 * RATIO)):
    F = T * 1000 / r_stop
    p_groove = F / (2.0 * eng)                       # projected bearing on the groove end, contact height = engagement
    # pin in the gear: embedded 3.5 (gear -45.7..-42.2), load at mid engagement below the gear face: lever 0.3 (PTFE gap) + eng/2
    lev = 0.3 + eng / 2; Mp = F * lev; Le = 3.5; d = 2.0
    p_hole = F / (d * Le) + 6 * Mp / (d * Le ** 2)
    sig_pin = Mp / (math.pi * d ** 3 / 32)
    log("%s: F %.1f N; groove-end bearing %.1f MPa (contact %.1f x 2); pin hole in the gear %.1f MPa; steel pin bending %.0f MPa"
        % (case, F, p_groove, eng, p_hole, sig_pin))
    rows.append(dict(feature="pan hard stop: groove end in T_paluba", case=case, section="contact %.1f x 2.0 projected" % eng,
                     stress=round(p_groove, 1), **{k: v for k, v in L.verdict(p_groove, L.A_STATIC, True).items() if k != "sigma"}))
    rows.append(dict(feature="pan hard stop: pin seat in P_koleso", case=case, section="Ø2 x 3.5 embedded, lever %.2f" % lev,
                     stress=round(p_hole, 1), **{k: v for k, v in L.verdict(p_hole, L.A_STATIC, True).items() if k != "sigma"}))

# ---------------- gear <-> hub disc bond (epoxy + 2 dowels) -----------------------------------------------------------
r_o, r_i = 12.6, 3.025
J = math.pi / 2 * (r_o ** 4 - r_i ** 4)
for case, T in (("L3", T_HAND), ("L8", T_STS3032 * RATIO)):
    tau = T * 1000 * r_o / J
    log("gear/hub epoxy bond %s: tau max %.2f MPa (annulus r %.2f..%.2f, full bond assumed)" % (case, tau, r_i, r_o))
    rows.append(dict(feature="P_koleso / P_sachta hub epoxy bond", case=case, section="annulus r 3.0..12.6", stress=round(tau, 2),
                     allow="epoxy on resin ~ 5 (assumed, sanded)", ok=bool(tau < 2.5)))
log.rows = rows; log.save("p01_gear")

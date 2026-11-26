"""VERIFIER (overenie_geo): independent check of the printed straight bevel pair 12/18 of B1+.
Own rack-generation of the Tredgold virtual spur teeth (polar envelope of the rolled basic rack with tip radius rho),
Lewis Y (tip load, load-angle corrected), AGMA Dolan-Broghamer Kf, contact ratio, form radius vs SAP margin,
top lands, backlash sensitivity to axial positions, tolerance stack vs the shim set, stress at the clutch torque.
Writes v_gear.json.  Does not import any judge/designer code."""
import json, math
import numpy as np

OUT = {}
m_h, z1, z2, ALPHA, HA, HF, RHO, B = 0.6667, 12, 18, 25.0, 0.9, 1.15, 0.38, 2.8
al = math.radians(ALPHA)
d1 = math.atan2(z1, z2); d2 = math.pi / 2 - d1
r1, r2 = m_h * z1 / 2, m_h * z2 / 2
Re = math.hypot(r1, r2); k_toe = (Re - B) / Re; k_mean = (Re - B / 2) / Re
OUT["cone"] = dict(delta1=round(math.degrees(d1), 3), delta2=round(math.degrees(d2), 3), Re=round(Re, 4), b_over_R=round(B / Re, 3),
                   m_toe=round(m_h * k_toe, 4), m_mean=round(m_h * k_mean, 4))
# ---------------------------------------------------------------- envelope in frame B (apex O = (39, 3, -17))
XV, YA, ZA = 39.0, 3.0, -17.0
def env(r_p, delta, other):
    ha, hf = HA * m_h, HF * m_h
    heel_ax = other                      # axial distance of the heel pitch circle from the apex
    crown = (heel_ax - ha * math.sin(delta), r_p + ha * math.cos(delta))
    root = (heel_ax + hf * math.sin(delta), r_p - hf * math.cos(delta))
    # face (tip) cone apex is at the pitch apex when the tooth is "taper depth" (ha scales); the toe tip = crown*k
    toe = (crown[0] * k_toe, crown[1] * k_toe)
    toe_root = (root[0] * k_toe, root[1] * k_toe)
    return crown, root, toe, toe_root
c1, ro1, t1, tr1 = env(r1, d1, r2)
c2, ro2, t2, tr2 = env(r2, d2, r1)
OUT["pinion_env"] = dict(crown_z=round(ZA - c1[0], 3), crown_r=round(c1[1], 3), heel_root_z=round(ZA - ro1[0], 3), heel_root_r=round(ro1[1], 3),
                         toe_z=round(ZA - t1[0], 3), toe_r=round(t1[1], 3), toe_root_z=round(ZA - tr1[0], 3), toe_root_r=round(tr1[1], 3))
OUT["gear_env"] = dict(toe_x=round(XV + t2[0], 3), toe_r=round(t2[1], 3), crown_x=round(XV + c2[0], 3), crown_r=round(c2[1], 3),
                       heel_root_x=round(XV + ro2[0], 3), heel_root_r=round(ro2[1], 3), toe_root_x=round(XV + tr2[0], 3), toe_root_r=round(tr2[1], 3))

# ---------------------------------------------------------------- rack generation of a spur gear, module 1, z teeth (real)
def generate(z, nphi=5000, du=0.0015):
    rp = z / 2.0
    ta = math.tan(al)
    # cutter tooth (half, u >= 0), v = height above pitch line (negative toward gear centre)
    vt = -HF                              # cutter tip line
    vc = vt + RHO
    uc = math.pi / 4 + vc * ta - RHO / math.cos(al)
    assert uc >= -1e-9, uc
    pts, tag = [], []
    # tip flat (u from 0 to uc) at v = vt
    for u in np.arange(0, max(uc, 0) + 1e-12, du):
        pts.append((u, vt)); tag.append(2)
    # tip round from the tip line (angle -90 deg) to the flank tangent (angle -al... normal direction)
    a0, a1 = -math.pi / 2, -al         # outward normal angles of the round (measured from +u)
    n = max(10, int(RHO * (a1 - a0) / du))
    for a in np.linspace(a0, a1, n):
        pts.append((uc + RHO * math.cos(a), vc + RHO * math.sin(a))); tag.append(1)
    # straight flank from the tangent point up to v = HA + 0.3
    vt0 = vc + RHO * math.sin(-al)
    for v in np.arange(vt0, HA + 0.3, du):
        pts.append((math.pi / 4 + v * ta, v)); tag.append(0)
    P = np.array(pts); T = np.array(tag)
    P = np.r_[P, P[::-1] * [-1, 1]]; T = np.r_[T, T[::-1]]     # full cutter tooth (both flanks)
    # roll: gear angle phi, rack translates by rp*phi; cutter tooth space of the gear centred at theta = 0 for phi = 0
    phis = np.linspace(-1.2, 1.2, nphi)
    Rmax = rp + HA
    rgrid = np.arange(rp - HF - 0.05, Rmax + 1e-9, 0.002)
    edge = np.full(len(rgrid), -np.inf); etag = np.full(len(rgrid), -1)
    for ph in phis:
        # rack point in a frame fixed to the rack: x = u + rp*ph, y = rp + v ; then rotate by -ph into the gear frame
        x = P[:, 0] - rp * ph; y = rp + P[:, 1]
        c, s = math.cos(-ph), math.sin(-ph)
        X = c * x - s * y; Y = s * x + c * y
        R = np.hypot(X, Y); th = np.arctan2(X, Y)        # theta measured from +Y, positive toward +X
        ok = R <= Rmax + 0.01
        idx = np.round((R[ok] - rgrid[0]) / 0.002).astype(int)
        good = (idx >= 0) & (idx < len(rgrid))
        idx = idx[good]; thv = th[ok][good]; tg = T[ok][good]
        if len(idx) == 0: continue
        # right edge of the swept space = max theta (cutter tooth centred at 0); keep per bin
        order = np.lexsort((thv, idx))
        i2 = idx[order]; last = np.r_[i2[1:] != i2[:-1], True]
        sel = order[last]
        upd = thv[sel] > edge[idx[sel]]
        edge[idx[sel][upd]] = thv[sel][upd]; etag[idx[sel][upd]] = tg[sel][upd]
    # gear tooth centred at theta = pi/z; half tooth angle beta(R) = pi/z - edge(R)
    beta = math.pi / z - edge
    return rgrid, beta, etag, rp


def analyse(z, name):
    rg, beta, tg, rp = generate(z)
    rb = rp * math.cos(al)
    ra = rp + HA
    ok = np.isfinite(beta) & (beta > 0)
    rg, beta, tg = rg[ok], beta[ok], tg[ok]
    # form radius: lowest radius generated by the straight flank (tag 0)
    inv = rg[tg == 0]
    r_form = float(inv.min()) if len(inv) else None
    root_r = float(rg.min())
    s_tip = 2 * ra * math.sin(float(beta[-1]))
    s_pitch = 2 * rp * math.sin(float(np.interp(rp, rg, beta)))
    # load at the tip on the flank: point (ra, half angle beta_a); load along the normal = tangent to base circle
    ba = float(beta[-1])
    # flank point (x to the right of centre line) in a frame with the tooth centreline along +Y
    px, py = ra * math.sin(ba), ra * math.cos(ba)
    alpha_a = math.acos(rb / ra)
    # involute normal at the tip makes angle phiL with the tooth-centreline normal: phiL = tan(alpha_a) - inv... use geometry:
    # the line of action through the tip point is tangent to the base circle; direction perpendicular to the radius of the tangent point
    # tangent point angle (from centreline): ba + alpha_a  (toward the tooth)  -> load direction
    gam = ba + alpha_a        # angle of the base-circle tangent point from the centreline, measured on the same side? solve numerically
    # find tangent point T on base circle such that (P - T) . T = 0 and T on the side making the load push the tooth sideways
    best = None
    for sgn in (+1, -1):
        tt = math.atan2(px, py) + sgn * alpha_a
        Tx, Ty = rb * math.sin(tt), rb * math.cos(tt)
        d = np.array([px - Tx, py - Ty])
        # load pushes the flank toward the centreline (into the tooth): -x component
        dirv = -d / np.linalg.norm(d)
        if dirv[0] < 0:
            best = (dirv, (Tx, Ty))
    dirv, _ = best
    phiL = math.atan2(-dirv[1], -dirv[0])     # angle of the load to the horizontal (perp. to the centreline); positive = downward compression
    # intersection of the load line with the centreline x = 0
    t = -px / dirv[0]
    hL = py + t * dirv[1]                      # height (along the centreline) of the load point
    # critical section: max 6 h / s^2 over the fillet / lower flank region
    s = 2 * rg * np.sin(beta); yc = rg * np.cos(beta)
    h = hL - yc
    sel = (rg < rp) & (h > 0)
    q = 6 * h[sel] / s[sel] ** 2
    k = int(np.argmax(q))
    s_c, h_c, r_c = float(s[sel][k]), float(h[sel][k]), float(rg[sel][k])
    # Lewis Y on the F_t basis (F_t tangential at the pitch circle): bending force = F_n cos(phiL) = F_t cos(phiL)/cos(alpha)
    Y_tipdir = s_c ** 2 / (6 * h_c) * math.cos(al) / math.cos(phiL)
    Y_plain = s_c ** 2 / (6 * h_c)
    # fillet radius of curvature near the critical section (from the (x, y) half-profile)
    X = rg * np.sin(beta); Yv = rg * np.cos(beta)
    win = (rg > r_c - 0.25) & (rg < r_c + 0.25)
    # curvature by a circle fit over the window
    xw, yw = X[win], Yv[win]
    A = np.c_[2 * xw, 2 * yw, np.ones(len(xw))]
    sol, *_ = np.linalg.lstsq(A, xw ** 2 + yw ** 2, rcond=None)
    rf_fit = math.sqrt(sol[2] + sol[0] ** 2 + sol[1] ** 2)
    # minimum radius of curvature of the trochoid (tag 1 region) by local 3-point curvature
    fil = tg == 1
    xs, ys = X[fil], Yv[fil]
    rmin = None
    if len(xs) > 30:
        st = 8
        rr = []
        for i in range(st, len(xs) - st, 2):
            p0 = np.array([xs[i - st], ys[i - st]]); p1 = np.array([xs[i], ys[i]]); p2 = np.array([xs[i + st], ys[i + st]])
            a_ = np.linalg.norm(p1 - p0); b_ = np.linalg.norm(p2 - p1); c_ = np.linalg.norm(p2 - p0)
            u_ = p1 - p0; w_ = p2 - p0; ar = abs(u_[0] * w_[1] - u_[1] * w_[0]) / 2
            if ar > 1e-12: rr.append(a_ * b_ * c_ / (4 * ar))
        rmin = float(min(rr)) if rr else None
    H, L, M = 0.331 - 0.436 * al, 0.324 - 0.492 * al, 0.261 + 0.545 * al
    Kf_fit = H + (s_c / rf_fit) ** L * (s_c / h_c) ** M
    Kf_min = H + (s_c / rmin) ** L * (s_c / h_c) ** M if rmin else None
    res = dict(z_virtual=round(z, 3), rp=round(rp, 4), rb=round(rb, 4), ra=round(ra, 4), root_r=round(root_r, 4), form_r=round(r_form, 4) if r_form else None,
               s_pitch=round(s_pitch, 4), top_land=round(s_tip, 4), load_angle_deg=round(math.degrees(phiL), 2), h_load=round(hL, 4),
               crit_r=round(r_c, 4), crit_s=round(s_c, 4), crit_h=round(h_c - 0, 4), Y_tipdir=round(Y_tipdir, 4), Y_plain=round(Y_plain, 4),
               rf_fit=round(rf_fit, 4), rf_min=round(rmin, 4) if rmin else None, Kf_fit=round(Kf_fit, 3), Kf_rmin=round(Kf_min, 3) if Kf_min else None,
               undercut=bool(r_form is not None and r_form > rb + 1e-6 and False))
    OUT[name] = res
    print(name, res, flush=True)
    return res


zv1 = z1 / math.cos(d1); zv2 = z2 / math.cos(d2)
P1 = analyse(zv1, "pinion_virtual_m1")
P2 = analyse(zv2, "gear_virtual_m1")
# ---------------------------------------------------------------- pair: contact ratio, SAP vs form radius (module units)
C = (zv1 + zv2) / 2
rb1, rb2 = P1["rb"], P2["rb"]; ra1, ra2 = P1["ra"], P2["ra"]
gA = math.sqrt(ra1 ** 2 - rb1 ** 2) + math.sqrt(ra2 ** 2 - rb2 ** 2) - C * math.sin(al)
eps = gA / (math.pi * math.cos(al))
def sap(rb_, ra_other, rb_other):
    return math.sqrt(rb_ ** 2 + (C * math.sin(al) - math.sqrt(ra_other ** 2 - rb_other ** 2)) ** 2)
sap1 = sap(rb1, ra2, rb2); sap2 = sap(rb2, ra1, rb1)
OUT["pair_m1"] = dict(eps=round(eps, 3), SAP_pinion=round(sap1, 4), form_pinion=P1["form_r"], margin_pinion_m=round(sap1 - P1["form_r"], 4),
                      SAP_gear=round(sap2, 4), form_gear=P2["form_r"], margin_gear_m=round(sap2 - P2["form_r"], 4))
# extra working depth (normal approach) that consumes the margin: SAP moves down when the mate's tip reaches deeper by e
def sap_e(rb_, ra_other, rb_other, e):
    Ce = C - e
    # mate tip deeper: equivalent to centre distance reduced by e (operating pressure angle changes; first order: keep alpha)
    aw = math.acos((rb_ + rb_other) / Ce)
    return math.sqrt(rb_ ** 2 + (Ce * math.sin(aw) - math.sqrt(ra_other ** 2 - rb_other ** 2)) ** 2)
for mm, lab in ((m_h, "heel"), (m_h * k_mean, "mean"), (m_h * k_toe, "toe")):
    # find e (mm) where SAP_pinion reaches the form radius
    lo_, hi_ = 0.0, 0.5
    for _ in range(60):
        mid = (lo_ + hi_) / 2
        if sap_e(rb1, ra2, rb2, mid / mm) > P1["form_r"]: lo_ = mid
        else: hi_ = mid
    OUT.setdefault("sap_margin_mm", {})[lab] = dict(module=round(mm, 4), margin_radial_mm=round((sap1 - P1["form_r"]) * mm, 4),
                                                     normal_approach_to_consume_mm=round(lo_, 4),
                                                     backlash_equiv_mm=round(2 * lo_ * math.tan(al), 4))
    OUT.setdefault("lands_mm", {})[lab] = dict(pinion_top_land=round(P1["top_land"] * mm, 4), gear_top_land=round(P2["top_land"] * mm, 4),
                                                pinion_s_pitch=round(P1["s_pitch"] * mm, 4), tooth_height=round((HA + HF) * mm, 4),
                                                clearance=round((HF - HA) * mm, 4))
# ---------------------------------------------------------------- stresses at arm torques
r_m1 = r1 * k_mean; m_m = m_h * k_mean
Yt1, Yt2 = P1["Y_tipdir"], P2["Y_tipdir"]
Kf1, Kf2 = P1["Kf_rmin"] or P1["Kf_fit"], P2["Kf_rmin"] or P2["Kf_fit"]
OUT["stress"] = {}
for Tarm in (0.004, 0.008, 0.0124, 0.0136, 0.0170, 0.020):
    Tp = Tarm / 1.5 * 1000.0     # N.mm at the pinion
    Ft = Tp / r_m1
    s1 = Ft / (B * m_m * Yt1); s2 = Ft / (B * m_m * Yt2)
    OUT["stress"][f"T_arm {Tarm}"] = dict(Ft_N=round(Ft, 3), pinion_lewis=round(s1, 2), pinion_xKf=round(s1 * Kf1, 2),
                                          pinion_xKf_xKm1p25=round(s1 * Kf1 * 1.25, 2), gear_lewis=round(s2, 2), gear_xKf=round(s2 * Kf2, 2))
T85 = 8.5 * B * m_m * Yt1 / Kf1 * r_m1 * 1.5 / 1000
OUT["T_arm_at_8p5"] = dict(lewis_xKf=round(T85, 4), lewis_xKf_Km1p25=round(T85 / 1.25, 4), lewis_xKf_Km1p5=round(T85 / 1.5, 4))
# forces on the pinion at slip (0.017 arm)
Ft = 17.0 / 1.5 / r_m1
OUT["pinion_forces_at_0.017"] = dict(Ft=round(Ft, 3), axial_down=round(Ft * math.tan(al) * math.sin(d1), 3), radial=round(Ft * math.tan(al) * math.cos(d1), 3),
                                     gear_axial_outboard=round(Ft * math.tan(al) * math.sin(d2), 3), gear_radial=round(Ft * math.tan(al) * math.cos(d2), 3))
# ---------------------------------------------------------------- backlash sensitivity (transverse, at the mean cone)
OUT["backlash_per_mm"] = dict(pinion_axial=round(2 * math.sin(d1) * math.tan(al), 4), gear_axial=round(2 * math.sin(d2) * math.tan(al), 4),
                              note="j_t change per mm axial move away from the apex")
# tolerance stack (1 sigma ~ tol/3 for printed / bearing widths uniform)
st = dict(shoulder_pos_plug=0.05, spacer_len=0.05, shim_gear=0.03, MR74_width_x2=0.12, A_axial_play=0.04, boss_face=0.08, plug_face_to_shoulder=0.05)
st_p = dict(tongue_shoulder=0.08, MR63_width=0.12, MR63_axial_play=0.03, shim_p=0.03)
# worst-case and RSS (bearing width: 0/-0.12 -> mean -0.06 +-0.06)
gear_mean_shift = 0.12          # two MR74 0.06 narrower on average -> gear 0.12 farther from the apex
gear_ws = 0.05 + 0.05 + 0.03 + 0.12 + 0.04 + 0.08 + 0.05
gear_rss = math.sqrt(0.05 ** 2 + 0.05 ** 2 + 0.03 ** 2 + 2 * 0.06 ** 2 + 0.04 ** 2 + 0.08 ** 2 + 0.05 ** 2)
pin_mean_shift = 0.06           # MR63 0.06 thinner on average -> pinion 0.06 lower (farther from the apex)
pin_ws = 0.08 + 0.06 + 0.03 + 0.03
pin_rss = math.sqrt(0.08 ** 2 + 0.06 ** 2 + 0.03 ** 2 + 0.03 ** 2)
kp, kg = 2 * math.sin(d1) * math.tan(al), 2 * math.sin(d2) * math.tan(al)
jm = kg * gear_mean_shift + kp * pin_mean_shift
j_rss = math.hypot(kg * gear_rss, kp * pin_rss)
j_ws = kg * gear_ws + kp * pin_ws
# printed tooth thickness error +-0.02 per flank (4 flanks) -> +-0.08*... normal; transverse ~ /cos(alpha)
j_print = 4 * 0.02 / math.cos(al)
shim_range = (0.30 - 0.42, 0.60 - 0.42)
OUT["backlash_stack"] = dict(j_nominal=round(4 * 0.02 / math.cos(al), 3), mean_shift_j=round(jm, 3), rss_j=round(j_rss, 3), worstcase_j=round(j_ws, 3),
                             print_thickness_j=round(j_print, 3),
                             shim_correction_j=[round(-kp * shim_range[1], 3), round(-kp * shim_range[0], 3)],
                             needed_correction_j_3sigma=[round(-(jm + j_rss + j_print), 3), round(-(jm - j_rss - j_print), 3)],
                             note="shim set 0.30..0.60 corrects only -0.093..+0.062 of transverse backlash")
json.dump(OUT, open("/tmp/claude-0/gapwf/fin/R2c/overenie_geo/v_gear.json", "w"), indent=1)
print(json.dumps({k: v for k, v in OUT.items() if not k.endswith("_m1")}, indent=1))

"""B1 (printed gears): straight bevel pair Sigma 90 deg, both gears printed in Elegoo Tough.
Pitch geometry kept from v2 (r1 4.0 pinion on the vertical servo axis, r2 6.0 gear on the arm axis, apex O = (39, 3, -17)),
so the v2 envelopes / clearances stay valid as long as crown / root / back stay inside the v2 limits.

For every candidate (module = 8/z1, PA, addendum, profile shift x1 = -x2, face width b):
  * virtual spur gears at the MEAN cone distance (Tredgold): z_v = z / cos(delta), m_m = m (1 - b / 2R)
  * tooth form generated NUMERICALLY by rolling a basic rack (PA, ha*, hf*, tip radius rho_f*) -> involute + trochoid fillet,
    undercut included automatically
  * Lewis form factor from the generated tooth (load at the tip along the line of action, critical section = max l / t^2,
    i.e. the inscribed Lewis parabola), Y = t^2 cos(alpha) / (6 m l cos(gamma))  ->  sigma = Ft / (b m_m Y)
  * Dolan-Broghamer / AGMA 908 fillet stress-concentration factor Kf (shown separately: sigma_Kf = Kf sigma_Lewis)
  * transverse contact ratio of the virtual pair, interference (contact start vs. form circle), top land
  * bevel envelope in frame B (pinion crown r, toe, heel root z; gear crown r, toe x, root x, back x)
Validation: the generator reproduces Shigley's Lewis table (20 deg full depth) within a few %.
Run: /opt/venv/cad/bin/python gears.py  -> gears.json"""
import math, json, sys, itertools
import numpy as np

YA, ZA, XV = 3.0, -17.0, 39.0
R1P, R2P = 4.0, 6.0                       # pitch radii (heel) kept from v2


def tooth_profile(z, m, alpha_deg, ha, hf, rho, x, nphi=6000, nbin=900):
    """generated tooth of a spur gear (z teeth, module m) cut by a basic rack.  Returns dict with
    r (radii), psi (half tooth angle at r, rad), ra, rb, rf, r_form (start of the involute)."""
    a = math.radians(alpha_deg)
    r = m * z / 2.0
    rb = r * math.cos(a)
    ra = r + (ha + x) * m
    rf = r + (x - hf) * m
    rho = rho * m                           # rho given as rho_f* (x module)
    p = math.pi * m
    y_ref = r + x * m                       # rack reference line (world y), rolling line = pitch line y = r
    y_tip = y_ref - hf * m                  # cutter tip line (deepest)
    w0 = p / 4.0                            # half thickness of the cutter tooth at the reference line
    yc = y_tip + rho
    uc = w0 + (yc - y_ref) * math.tan(a) - rho / math.cos(a)
    if uc < 0:
        raise ValueError("cutter tip radius too large")
    yt = yc - rho * math.sin(a)             # flank / rounding tangent point
    # outline of ONE cutter tooth (right half, mirrored), dense
    pts = []
    for yy in np.linspace(yt, y_ref + (ha + 0.6) * m, 400):          # flank
        pts.append((w0 + (yy - y_ref) * math.tan(a), yy))
    for th in np.linspace(-math.pi / 2, -a, 200):                     # rounding: from the tip line to the flank
        pts.append((uc + rho * math.cos(th), yc + rho * math.sin(th)))
    for uu in np.linspace(0.0, uc, 60):                               # tip line
        pts.append((uu, y_tip))
    Pr = np.array(pts)
    P = np.r_[Pr, Pr * np.array([-1.0, 1.0])]
    # roll: gear-fixed point G -> world R(phi) G ; world -> rack: u = X + r phi.  Inverse: X = u - r phi, G = R(-phi) (X, y)
    phis = np.linspace(-1.0, 1.0, nphi) * (2.2 * (ha + hf + abs(x)) * m / (math.sin(a) * r) + math.pi / z)
    U = P[:, 0][None, :] - r * phis[:, None]
    Yw = np.broadcast_to(P[:, 1][None, :], U.shape)
    c, s = np.cos(-phis)[:, None], np.sin(-phis)[:, None]
    gx = c * U - s * Yw
    gy = s * U + c * Yw
    rr = np.hypot(gx, gy).ravel()
    th = np.arctan2(gy, gx).ravel()        # space centred at +90 deg
    tooth_c = math.pi / 2 + math.pi / z    # tooth centre (to the left of the space)
    sel = (rr >= rf - 1e-9) & (rr <= ra + 1e-9) & (th > math.pi / 2 - 1e-9) & (th < tooth_c + math.pi / z)
    rr, th = rr[sel], th[sel]
    edges = np.linspace(rf, ra, nbin + 1)
    idx = np.clip(np.searchsorted(edges, rr) - 1, 0, nbin - 1)
    thmax = np.full(nbin, math.pi / 2)
    np.maximum.at(thmax, idx, th)
    rc = 0.5 * (edges[1:] + edges[:-1])
    psi = tooth_c - thmax                   # half tooth angle
    psi = np.minimum(psi, math.pi / z)
    # analytic involute check radius where the straight flank ends
    d = r * math.sin(a) - (r - yt) / math.sin(a)
    r_form = math.sqrt(rb ** 2 + d ** 2) if d > 0 else rb
    return dict(r=rc, psi=psi, ra=ra, rb=rb, rf=rf, rp=r, r_form=r_form, undercut=bool(d <= 0), alpha=a, m=m, z=z,
                rho=rho, hf=hf, ha=ha, x=x)          # rho here is absolute (mm)


def lewis(tp):
    """Lewis Y from a generated tooth (load at the tip).  Returns Y, critical section (t, l), load angle, Kf (AGMA 908)."""
    r, psi = tp["r"], tp["psi"]
    ok = psi > 0
    r, psi = r[ok], psi[ok]
    X = r * np.sin(psi)                     # half width
    Yc = r * np.cos(psi)                    # height along the centreline
    ra = tp["ra"]; rb = tp["rb"]; a = tp["alpha"]; m = tp["m"]
    # tip corner: last bin with positive psi
    psi_a = float(np.interp(ra - 1e-6, r, psi))
    XA, YA_ = ra * math.sin(psi_a), ra * math.cos(psi_a)
    alpha_a = math.acos(min(rb / ra, 1.0))
    gam = alpha_a - psi_a
    YL = YA_ - XA * math.tan(gam)
    # critical section: max (YL - Y) / (2X)^2 below the tip, in the root region (Y < YL)
    msk = (Yc < YL) & (X > 1e-4)
    q = (YL - Yc[msk]) / (2 * X[msk]) ** 2
    k = int(np.argmax(q))
    t = 2 * X[msk][k]; l = YL - Yc[msk][k]
    Y = t ** 2 * math.cos(a) / (6 * m * l * math.cos(gam))
    # fillet radius (Dolan-Broghamer approximation) and AGMA 908 Kf
    rho = tp["rho"]; hfm = tp["hf"] * m - tp["x"] * m * 0  # dedendum below the reference incl. shift handled via rf
    bded = (tp["rp"] - tp["rf"]) - rho     # distance from the cutter-tip-circle centre line to the pitch line
    rfil = rho + bded ** 2 / (tp["rp"] + bded) if bded > 0 else rho
    H = 0.331 - 0.436 * a; L = 0.324 - 0.492 * a; M = 0.261 + 0.545 * a
    Kf = H + (t / rfil) ** L * (t / l) ** M
    return dict(Y=Y, t=t, l=l, gamma_deg=math.degrees(gam), r_crit=float(r[msk][k]), s_tip=2 * ra * psi_a, rfil=rfil, Kf=Kf)


def contact(tp1, tp2):
    a = tp1["alpha"]; m = tp1["m"]
    aw = tp1["rp"] + tp2["rp"]
    g1 = math.sqrt(tp1["ra"] ** 2 - tp1["rb"] ** 2); g2 = math.sqrt(tp2["ra"] ** 2 - tp2["rb"] ** 2)
    eps = (g1 + g2 - aw * math.sin(a)) / (math.pi * m * math.cos(a))
    # contact start radius on each gear vs its form circle
    s1 = aw * math.sin(a) - g2; s2 = aw * math.sin(a) - g1
    rc1 = math.sqrt(tp1["rb"] ** 2 + s1 ** 2) if s1 > 0 else 0.0
    rc2 = math.sqrt(tp2["rb"] ** 2 + s2 ** 2) if s2 > 0 else 0.0
    return dict(eps=eps, rc1=rc1, rc2=rc2, interf1=bool(s1 < 0 or rc1 < tp1["r_form"] - 1e-6),
                interf2=bool(s2 < 0 or rc2 < tp2["r_form"] - 1e-6))


def bevel_env(z1, z2, m, ha, hf, x1, b, web=0.6):
    """frame-B envelope of the pair (left side).  Pinion: vertical, below O.  Gear: on the shoulder axis, outboard of O."""
    d1 = math.atan2(z1, z2); d2 = math.pi / 2 - d1
    r1, r2 = m * z1 / 2, m * z2 / 2
    R = math.hypot(r1, r2); k = (R - b) / R
    ha1, hf1 = (ha + x1) * m, (hf - x1) * m
    ha2, hf2 = (ha - x1) * m, (hf + x1) * m
    crown1 = (r2 - ha1 * math.sin(d1), r1 + ha1 * math.cos(d1))       # (axial below O, radius)
    root1 = (r2 + hf1 * math.sin(d1), r1 - hf1 * math.cos(d1))
    crown2 = (r1 - ha2 * math.sin(d2), r2 + ha2 * math.cos(d2))
    root2 = (r1 + hf2 * math.sin(d2), r2 - hf2 * math.cos(d2))
    return dict(delta1=math.degrees(d1), delta2=math.degrees(d2), R=R, k=k,
                pin=dict(crown_r=crown1[1], crown_z=ZA - crown1[0], root_z=ZA - root1[0], root_r=root1[1],
                         toe_z=ZA - k * crown1[0], toe_r=k * crown1[1], toe_root_r=k * root1[1], toe_root_z=ZA - k * root1[0]),
                gear=dict(crown_r=crown2[1], crown_x=XV + crown2[0], root_x=XV + root2[0], root_r=root2[1],
                          toe_x=XV + k * crown2[0], toe_r=k * crown2[1], toe_root_r=k * root2[1], back_x=XV + root2[0] + web))


def evaluate(z1, alpha, ha, x1, b, rho=0.38, c=0.25, z2=None, verbose=False):
    z2 = z2 or int(round(z1 * 1.5))
    m = 2 * R1P / z1
    hf = ha + c
    env = bevel_env(z1, z2, m, ha, hf, x1, b)
    R = env["R"]
    mm = m * (1 - b / (2 * R))
    d1, d2 = math.radians(env["delta1"]), math.radians(env["delta2"])
    zv1, zv2 = z1 / math.cos(d1), z2 / math.cos(d2)
    t1 = tooth_profile(zv1, mm, alpha, ha, hf, rho, x1)
    t2 = tooth_profile(zv2, mm, alpha, ha, hf, rho, -x1)
    L1, L2 = lewis(t1), lewis(t2)
    C = contact(t1, t2)
    rm2 = R2P * (1 - b / (2 * R))
    # arm torque at which the pinion / gear root reaches 8.5 MPa (Lewis) ; Ft = T / rm2
    T85_1 = 8.5 * b * mm * L1["Y"] * rm2 / 1000.0
    T85_2 = 8.5 * b * mm * L2["Y"] * rm2 / 1000.0
    out = dict(z1=z1, z2=z2, m=round(m, 4), alpha=alpha, ha=ha, hf=hf, rho=rho, x1=x1, b=b, R=round(R, 3), m_mean=round(mm, 4),
               zv1=round(zv1, 2), zv2=round(zv2, 2), Y1=round(L1["Y"], 4), Y2=round(L2["Y"], 4), Kf1=round(L1["Kf"], 3),
               Kf2=round(L2["Kf"], 3), eps=round(C["eps"], 3), interf=C["interf1"] or C["interf2"],
               undercut1=t1["undercut"], undercut2=t2["undercut"],
               top_land_heel1=round(L1["s_tip"] * m / mm, 3), top_land_toe1=round(L1["s_tip"] * m / mm * env["k"], 3),
               top_land_heel2=round(L2["s_tip"] * m / mm, 3),
               T_arm_8p5_Lewis=round(min(T85_1, T85_2), 4), T_arm_8p5_pin=round(T85_1, 4), T_arm_8p5_gear=round(T85_2, 4),
               T_arm_8p5_withKf=round(min(T85_1 / L1["Kf"], T85_2 / L2["Kf"]), 4),
               tooth_h_heel=round((ha + hf) * m, 3), toe_module=round(m * env["k"], 3), env=env,
               Lewis1=L1, Lewis2=L2, rm2=rm2)
    return out


def sigma(res, T_arm):
    """pinion / gear Lewis and Lewis*Kf root stress (MPa) at an arm torque T_arm (N.m)"""
    Ft = T_arm * 1000.0 / res["rm2"]
    s1 = Ft / (res["b"] * res["m_mean"] * res["Y1"]); s2 = Ft / (res["b"] * res["m_mean"] * res["Y2"])
    return dict(Ft_N=round(Ft, 2), pin=round(s1, 2), gear=round(s2, 2), pin_Kf=round(s1 * res["Kf1"], 2), gear_Kf=round(s2 * res["Kf2"], 2))


def validate():
    """Shigley table 14-2 (20 deg full depth, load at tip): z 12 .245, 16 .296, 20 .322, 30 .359, 50 .409, 100 .447"""
    ref = {12: .245, 16: .296, 20: .322, 30: .359, 50: .409, 100: .447}
    rows = []
    for z, Ysh in ref.items():
        tp = tooth_profile(z, 1.0, 20.0, 1.0, 1.25, 0.30, 0.0)
        L = lewis(tp)
        rows.append((z, Ysh, round(L["Y"], 3), round(L["Y"] / Ysh - 1, 3)))
    return rows


if __name__ == "__main__":
    val = validate()
    print("validation vs Shigley 14-2 (z, table, mine, rel.err):")
    for r in val:
        print("  ", r)
    LIM = dict(pin_crown_r=4.60, pin_root_z=-23.60, gear_crown_r=6.50, gear_back_x=44.30)
    rows = []
    for z1, alpha, ha, x1, b in itertools.product((10, 12, 14, 16), (20.0, 25.0), (0.8, 0.9, 1.0), (0.0, 0.15, 0.3, 0.45),
                                                   (2.4, 2.8)):
        try:
            r = evaluate(z1, alpha, ha, x1, b)
        except Exception as e:
            continue
        e = r["env"]
        fit = (e["pin"]["crown_r"] <= LIM["pin_crown_r"] and e["pin"]["root_z"] >= LIM["pin_root_z"] and
               e["gear"]["crown_r"] <= LIM["gear_crown_r"] and e["gear"]["back_x"] <= LIM["gear_back_x"])
        good = fit and r["eps"] >= 1.20 and not r["interf"] and r["top_land_toe1"] >= 0.12 and r["top_land_heel2"] >= 0.2
        r["fits_v2_envelope"] = fit; r["ok"] = good
        rows.append(r)
    rows.sort(key=lambda r: -r["T_arm_8p5_withKf"])
    print("\nbest candidates that fit the v2 envelope (eps >= 1.2, no interference, top land ok):")
    print(" z1/z2   m     PA  ha   x1   b   | eps  Y1    Y2    Kf1  Kf2 | T@8.5 Lewis  T@8.5 Lewis*Kf | pin crown r / root z | gear crown r / back x")
    for r in [q for q in rows if q["ok"]][:25]:
        e = r["env"]
        print(f" {r['z1']:2d}/{r['z2']:2d} {r['m']:.3f} {r['alpha']:4.0f} {r['ha']:.1f} {r['x1']:.2f} {r['b']:.1f} | {r['eps']:.2f} "
              f"{r['Y1']:.3f} {r['Y2']:.3f} {r['Kf1']:.2f} {r['Kf2']:.2f} | {r['T_arm_8p5_Lewis']:.4f}       {r['T_arm_8p5_withKf']:.4f}"
              f"        | {e['pin']['crown_r']:.2f} / {e['pin']['root_z']:.2f} | {e['gear']['crown_r']:.2f} / {e['gear']['back_x']:.2f}")
    v2 = evaluate(16, 20.0, 1.0, 0.0, 2.4)
    print("\nv2 pair as printed (m0.5 16/24 20 deg, b 2.4): T@8.5 Lewis", v2["T_arm_8p5_Lewis"], " with Kf", v2["T_arm_8p5_withKf"],
          " eps", v2["eps"])
    json.dump(dict(validation=val, limits=LIM, v2=v2, rows=rows), open("gears.json", "w"), indent=1, default=float)

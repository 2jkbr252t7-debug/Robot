"""p03 - 2-D plane-stress FE on the real sections of L_ucho (ear plate), P_kluka (crank arm) and one P_koleso tooth.
Stress reported as the max of the 0.25 x 0.25 mm patch mean (5 x 5 elements, h 0.05) outside the 0.4 mm contact zone
(patch averaging ~ critical distance for a brittle polymer; the raw element maxima at sharp corners are mesh dependent)."""
import math, json, numpy as np, pv_lib as L, fe2d
log = L.Log("p03_fe_lift")
G = 9.80665
rows = []
H = 0.05


def patch_max(m, what="s1", skip=None, k=5):
    a = getattr(m, what)
    nw, nu_ = m.M.shape
    img = np.full((nw, nu_), np.nan)
    J, I = np.nonzero(m.M)
    img[J, I] = a
    if skip is not None:
        bad = np.array([skip(u, w) for u, w in m.cent])
        img[J[bad], I[bad]] = np.nan
    best = (-1e9, None)
    r = k // 2
    for j in range(r, nw - r):
        row = img[j - r:j + r + 1]
        for i in range(r, nu_ - r):
            blk = row[:, i - r:i + r + 1]
            if np.isnan(blk[r, r]):
                continue
            v = np.nanmean(blk)
            if np.sum(np.isfinite(blk)) >= 12 and v > best[0]:
                best = (v, (m.u0 + (i + .5) * m.h, m.w0 + (j + .5) * m.h))
    return round(float(best[0]), 2), (round(best[1][0], 2), round(best[1][1], 2))


def run_case(name, part, axis, val, win, t, fixfn, load_sel, force, skipfn, pic=None):
    seg = L.section(L.load(part), axis, val)
    u0, u1, w0, w1 = win
    M = fe2d.raster(seg, u0, u1, w0, w1, H)
    m = fe2d.Model(M, u0, w0, H, t)
    nf = m.fix_where(fixfn)
    b = m.boundary_nodes(); p = m.xy(m.nodes[b])
    sel = b[load_sel(p[:, 0], p[:, 1])]
    m.load_on(sel, force); m.solve()
    pm, at = patch_max(m, "s1", skipfn)
    raw = m.top(1, "s1", skip_near=skipfn)[0]
    comp = float(np.percentile(m.s2, 0.2))
    if pic:
        m.picture(L.OUT + "/" + pic, "s1", vmax=max(pm, 1.0) * 1.2)
    log("%-58s A %.1f mm2, %d fixed, %d load nodes, F (%.1f, %.1f) N: sigma1 patch %.1f MPa at %s (raw element %.1f at %s); "
        "sigma2 0.2%% %.1f" % (name, M.sum() * H * H, nf, len(sel), force[0], force[1], pm, at, raw[0], raw[1:], comp))
    return pm, at, raw, m


# ================= L_ucho: plate section at x -18.65 (y, z), thickness 2.5 =============================================
win = (9.6, 25.4, -40.8, -31.6)
yp_dead, yp_mid = 23.2, 13.2
up_fl, lo_fl = -33.1, -35.3            # slot flanks (g02)
fix_ear = lambda y, z: y <= 12.4 + 1e-6
def ear_load(yp, flank):
    return lambda y, z: (np.abs(y - yp) <= 0.45) & (np.abs(z - flank) <= 0.06)
def ear_skip(yp, flank):
    return lambda y, z: (abs(y - yp) < 0.6 and abs(z - flank) < 0.4)
W_HEAD = 0.17 * G      # head + neck + foot, assumed 0.17 kg (STATUS_pan C)
for nm, F, yp, fl, sgn, abuse, sust in (
        ("ear L2 30 N down, lift 0 / 20 (pin at y 23.2, upper flank)", 30.0, yp_dead, up_fl, +1, True, False),
        ("ear L2 30 N down, mid lift (pin at y 13.2, upper flank)", 30.0, yp_mid, up_fl, +1, True, False),
        ("ear L1 15 N up, lift 0 / 20 (pin at y 23.2, lower flank)", 15.0, yp_dead, lo_fl, -1, True, False),
        ("ear L1 15 N up, mid lift (pin at y 13.2, lower flank)", 15.0, yp_mid, lo_fl, -1, True, False),
        ("ear head weight 1.67 N sustained, lift 0 / 20", W_HEAD, yp_dead, up_fl, +1, False, True)):
    pm, at, raw, m = run_case(nm, "L_ucho", "x", -18.65, win, 2.5, fix_ear, ear_load(yp, fl), (0.0, sgn * F), ear_skip(yp, fl),
                              pic="fe_ucho_%s.png" % nm.split()[1] if "30 N" in nm and yp == yp_dead else None)
    allow = L.A_NOTCH if sust else L.A_STATIC
    v = L.verdict(pm, allow, abuse)
    rows.append(dict(feature="L_ucho ear plate (resin, 2.5)", case=nm, section="2-D FE, real section x -18.65", stress=pm, at=at, **{k: q for k, q in v.items() if k != "sigma"}))
    if "L2" in nm and yp == yp_dead:
        log("   -> force at which the ear reaches 35 MPa (UTS): %.1f N; reaches 12 MPa: %.1f N" % (30 * 35 / pm, 30 * 12 / pm))

# ================= P_kluka: arm section at x -15.75 (y, z), thickness 2.5 ============================================
# (u, w) = (y, z); in the rest geometry the arm points -z from the hub; 'mid stroke' = force across the arm = along y
win = (19.4, 27.0, -36.8, -20.4)
YL, ZL, RC = 23.2, -24.2, 10.0
fix_crank = lambda y, z: np.hypot(y - YL, z - ZL) <= 2.45          # spline zone rigid
pin = (YL, ZL - RC)
def pin_side(dy, dz):
    """boundary nodes of the pin hole on the side the pin pushes (force direction (dy, dz) on the crank)"""
    return lambda y, z: (np.hypot(y - pin[0], z - pin[1]) <= 1.1) & (((y - pin[0]) * dy + (z - pin[1]) * dz) > 0.35 * np.hypot(y - pin[0], z - pin[1]))
crank_skip = lambda y, z: math.hypot(y - pin[0], z - pin[1]) < 1.35
MG90S_STALL = 2.2 * G / 100     # 6 V
for nm, F, d, abuse in (("crank L2 30 N at mid stroke (force across the arm)", 30.0, (1, 0), True),
                        ("crank L1 15 N at mid stroke", 15.0, (-1, 0), True),
                        ("crank MG90S stall 0.216 N.m (21.6 N at r 10) L8", MG90S_STALL * 1000 / RC, (1, 0), True),
                        ("crank L2 30 N at lift 0 (pin pulled away from the hub)", 30.0, (0, -1.0001), True),
                        ("crank L1 15 N at lift 20 (pin pulled away from the hub, TDC mirror)", 15.0, (0, -1.0001), True)):
    dd = np.array(d, float); dd /= np.linalg.norm(dd)
    # the 'at lift 0' cases: force along the arm; in the rest geometry the arm points -z from the hub
    if "lift 0" in nm or "lift 20" in nm:
        dd = np.array([0.0, -1.0])
    pm, at, raw, m = run_case(nm, "P_kluka", "x", -15.75, win, 2.5, fix_crank, pin_side(*dd), tuple(F * dd), crank_skip,
                              pic="fe_kluka_mid.png" if nm.startswith("crank L2 30 N at mid") else None)
    v = L.verdict(pm, L.A_STATIC, abuse)
    rows.append(dict(feature="P_kluka crank arm (resin, 2.5)", case=nm, section="2-D FE, real section x -15.75", stress=pm, at=at, **{k: q for k, q in v.items() if k != "sigma"}))
# pin seat in the crank: eccentric load (ear mid-plane 1.65 outside the arm face), projected bearing incl. the moment
for nm, F in (("L1 15 N", 15.0), ("L2 30 N", 30.0), ("L8 MG90S stall 21.6 N", MG90S_STALL * 1000 / RC), ("head weight 1.67 N (sustained)", W_HEAD)):
    d_, Le, e = 2.0, 2.5, 1.65
    p = F / (d_ * Le) + 6 * F * e / (d_ * Le ** 2)
    allow = L.A_NOTCH if "sustained" in nm else L.A_STATIC
    v = L.verdict(p, allow, "sustained" not in nm)
    log("crank pin seat %s: bearing incl. eccentricity %.1f MPa (Ø2 x 2.5, e 1.65)" % (nm, p))
    rows.append(dict(feature="crank pin seat Ø2 in P_kluka (2.5 long, cantilevered pin)", case=nm, section="Ø2 x 2.5, e 1.65", stress=round(p, 1), **{k: q for k, q in v.items() if k != "sigma"}))
# ear slot: steel pin bearing on the 2.5 resin plate (Z3.8: <= 5 MPa projected for sliding)
for nm, F in (("L1 15 N", 15.0), ("L2 30 N", 30.0), ("running, head weight 1.67 N", W_HEAD), ("running, MG90S stall 21.6 N", MG90S_STALL * 1000 / RC)):
    p = F / (2.0 * 2.5)
    log("ear slot projected pressure %s: %.2f MPa (limit Z3.8 5 MPa sliding)" % (nm, p))
    rows.append(dict(feature="ear slot / steel pin contact (Z3.8)", case=nm, section="Ø2 x 2.5 projected", stress=round(p, 2), allow=5.0, ok=bool(p <= 5.0)))

# ================= P_koleso tooth at z -44 (rotated: u radial, w tangential), b 3.2 ====================================
seg = L.section(L.load("P_koleso"), "z", -44.0)
c0 = math.radians(254.3)
R = np.array([[math.cos(-c0), -math.sin(-c0)], [math.sin(-c0), math.cos(-c0)]])
segr = seg @ R.T
u0, u1, w0, w1 = 11.0, 15.4, -1.9, 1.9
M = fe2d.raster(segr, u0, u1, w0, w1, 0.025)
m0 = fe2d.Model(M, u0, w0, 0.025, 3.2)
r_tip = 15.19; phi_t = math.acos(14.4 * math.cos(math.radians(20)) / r_tip)
for nm, T, abuse in (("tooth L3 hand 0.6 N.m", 0.6, True), ("tooth L8 STS3032 stall 0.883 N.m at the gear", 2 * 4.5 * G / 100, True),
                     ("tooth normal: STS3032 rated 1.5 kg.cm (0.294 at the gear)", 2 * 1.5 * G / 100, False)):
    Ft = T * 1000 / 14.4
    m = fe2d.Model(M, u0, w0, 0.025, 3.2)
    m.fix_where(lambda u, w: u <= 11.6)
    b = m.boundary_nodes(); p = m.xy(m.nodes[b])
    sel = b[(p[:, 0] >= r_tip - 0.35) & (p[:, 1] > 0)]           # flank tip zone on the +w side
    m.load_on(sel, (-Ft * math.tan(phi_t), -Ft)); m.solve()
    skip = lambda u, w: u > r_tip - 0.5
    pm, at = patch_max(m, "s1", skip)
    raw = m.top(1, "s1", skip_near=skip)[0]
    log("%-50s Ft %.1f N (tip pressure angle %.1f deg): sigma1 patch %.1f MPa at %s (raw %.1f at %s)" % (nm, Ft, math.degrees(phi_t), pm, at, raw[0], raw[1:]))
    if "L3" in nm:
        m.picture(L.OUT + "/fe_zub_L3.png", "s1", vmax=pm * 1.2)
    v = L.verdict(pm, L.A_STATIC, abuse)
    rows.append(dict(feature="P_koleso tooth (resin, m0.8, b 3.2)", case=nm, section="2-D FE, real section z -44", stress=pm, at=at, **{k: q for k, q in v.items() if k != "sigma"}))
log.rows = rows; log.save("p03_fe_lift")

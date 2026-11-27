"""NOVA mini - R4/tvar: modern roundings for the chosen slim arm B.  Pure numpy (CAD venv AND Blender's python).

Same API as R3/tvar/variants.py (VIDS, params, section, profile, faces, thickness, seam_x, pebble_rows, pebble_cloud,
inside_local, half_rows, tip_plane_local, to_world, to_local, dir_world, swing, swing_matrix, _base, L, SEAM, DX) so the
render pipeline, fit.py and the gap checker can swap modules.

Frame B: mm, Z up, FRONT = -Y, robot LEFT = +X.  Shoulder axis || X through (y 3.0, z -17.0).  LEFT arm at rest; the right
arm is the mirror x -> -x.  Placement / swing / local frame are IMPORTED from R3/tvar/variants.py (identical for every
variant): local x = thickness (outer +, inner - = towards the torso), y = fore-aft width, z = 0 top .. -72 tip, u = -z/72.

"B0" = R3 variant "B" exactly (asserted at import on a u grid, and fully in __main__).

Every variant is the B construction with optional modifiers (all smooth, C2 in u):
    section at u:  equator / seam at x = c(u) (= B's seam for every variant: parting line A_vonk / A_vnut unchanged)
        inner half (x <= c):  |(x - c) / ti|^ni + |y / wi|^ni <= 1
        outer half (x >= c):  |(x - c) / to|^no + |y / wo|^no <= 1      wo = w - REV (seam reveal: the cover sits REV
                                                                       inside the inner half's edge -> a crisp shadow step)
                                                                       or wi = w - LIP (the cover's rim overhangs the tray)
    ti(u) = B's ti * gi(u)                      (gi = 1 in the zone near the torso: the inner face / gap stay as in B)
    to(u) = To * bump2(u, pt, mt_top, mt_bot) * (1 - at u) + J(u)     (outer cover profile; J = joint fullness)
    wi(u) = Wh * bump2(u, pw, mw_top, mw_bot) * (1 - aw u)             (side outline seen from outside)
    ni(u), no(u): body exponent blended (smoothstep) to a tip exponent near both ends -> smooth domes
bump2 = the approved T3 'bump' (superellipse in a warped u, peak at u = peak) with separate exponents above / below the
peak (m_top = m_bot reproduces the approved bump exactly; m > 2 on both sides keeps the peak C2)."""
import sys, math
import numpy as np

sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as _R3  # noqa: E402  (R3 shape module: B + placement, read only)

S = _R3.S
L = _R3.L
N0 = _R3.N0
SH_Y, ZS, AX = _R3.SH_Y, _R3.ZS, _R3.AX
X_SH_T4 = _R3.X_SH_T4
SPLAY, SWING, U_ATT, INB = _R3.SPLAY, _R3.SWING, _R3.U_ATT, _R3.INB
DX = _R3.DX
SEAM = _R3.SEAM
U_TIP = _R3.U_TIP
# placement = R3 (identical objects, not copies)
Rmat, R, A_LOC, att = _R3.Rmat, _R3.R, _R3.A_LOC, _R3.att
to_world, to_local, dir_world = _R3.to_world, _R3.to_local, _R3.dir_world
swing, swing_matrix = _R3.swing, _R3.swing_matrix
_base, _smooth, stations, _se_r = _R3._base, _R3._smooth, _R3.stations, _R3._se_r

B_R3 = _R3.VARIANTS["B"]
# B's profiles written in the bump2 family (exact: same formula, approved constants)
_W_B = (0.40, 2.6, 2.6, 0.12, B_R3["kw"] * S.ARM_W / 2)          # half width
_TO_B = (0.34, 2.7, 2.7, 0.24, B_R3["ko"] * S.ARM_T / 2)          # outer half thickness (from the seam)

# ---------------------------------------------------------------------------------------------------- the variants
# B0 = R3 "B".  New variants (all keys required except J / REV / UTIP):
#   W  = (uc, m_top, p_top, m_bot, p_bot, taper, width)   side outline: half width wi(u) = width/2 * F(u) / max F
#   T  = (uc, m_top, p_top, m_bot, p_bot, taper)          thickness shape (normalised to max 1), used by the outer half and
#                                                          by the inner half near the tips
#        F(u) = (1 - |s|^m)^(1/p) * (1 - taper u),  s = (u - uc)/uc above, (u - uc)/(1 - uc) below the crest
#        m > 2 keeps the crest C2 (no crease); p sets the end domes (p 2 = round, p = m = the approved superellipse type)
#   TO = outer half max thickness (from the seam);  TI = inner half max thickness used near the tips
#   E  = (a0, a1, b0, b1): ti = B's ti EXACTLY for a1 <= u <= b0 (zone near the torso: inner face and gap as in B), blended
#        (smootherstep, C2) to TI * T(u) below a0 / above b1
#   TIK = factor on B's ti inside the plateau (< 1 moves the inner face away from the torso; used to pay for a flatter
#        inner section so the gap does not get worse)
#   J  = (amp, u0, sigma): gaussian fullness added to the outer half over the joint (wide -> invisible)
#   NI / NO = (n_body, n_tip, ua, ub): section exponents, n_body for ua <= u <= ub, blended to n_tip at both ends
#   REV = seam reveal: the outer cover is REV narrower than the inner half (fades out at the two tips)
#   LIP = cover overhang: the inner tray is LIP narrower than the cover (the cover's rim sits proud, shadow line below it)
#   UTIP = black tip plane station
VARIANTS = {
    "B0": dict(name="B0 – dnešná B", base=True),
    "B1": dict(name="B1 – squircle",
               W=(0.225, 2.4, 2.0, 3.4, 2.0, 0.07, 30.9), T=(0.21, 2.9, 2.0, 2.8, 2.0, 0.30), TO=6.95, TI=9.3, TIK=0.997,
               E=(0.03, 0.12, 0.50, 0.90), NI=(2.6, 2.4, 0.10, 0.85), NO=(3.8, 2.4, 0.10, 0.85), UTIP=0.85),
    "B2": dict(name="B2 – kvapka",
               W=(0.225, 2.3, 2.0, 2.0, 2.5, 0.24, 31.2), T=(0.20, 2.6, 2.0, 2.0, 2.5, 0.36), TO=7.0, TI=9.3,
               E=(0.03, 0.12, 0.42, 0.95), NI=(2.2, 2.3, 0.10, 0.85), NO=(2.6, 2.3, 0.10, 0.85), REV=0.35, UTIP=0.82),
    "B3": dict(name="B3 – plochý kryt",
               W=(0.225, 2.3, 2.0, 2.4, 2.0, 0.12, 31.0), T=(0.22, 3.4, 2.0, 4.0, 2.0, 0.26), TO=6.85, TI=9.3,
               E=(0.03, 0.12, 0.50, 0.90), NI=(2.2, 2.3, 0.10, 0.85), NO=(4.8, 2.5, 0.10, 0.85), LIP=0.35, UTIP=0.85),
    "B4": dict(name="B4 – oblý kameň (vyradený: len zaoblenejšia B0)",
               W=(0.225, 2.3, 2.0, 2.4, 2.0, 0.10, 30.7), T=(0.21, 2.9, 2.0, 2.4, 2.0, 0.28), TO=6.95, TI=9.3,
               E=(0.03, 0.12, 0.50, 0.90), NI=(2.2, 2.3, 0.10, 0.85), NO=(2.45, 2.3, 0.10, 0.85), UTIP=0.85),
}
VIDS = ("B0", "B1", "B2", "B3")          # B4 kept in VARIANTS for the record (dropped after the previews)
_NORM = {}


def params(vid):
    return VARIANTS[str(vid)]


def bump2(u, peak, m_top, m_bot):
    """approved T3 bump with separate exponents above (u < peak) / below the peak (only used to verify B0)"""
    k = np.log(0.5) / np.log(peak)
    v = np.clip(np.asarray(u, float), 0, 1) ** k
    s = 2 * v - 1
    m = np.where(s < 0, m_top, m_bot)
    return np.clip(1 - np.abs(s) ** m, 0, 1) ** (1 / m)


def _prof(u, P):
    peak, mt, mb, a, sc = P
    return sc * bump2(u, peak, mt, mb) * (1 - a * np.asarray(u, float))


def _F(u, P):
    uc, mt, pt, mb, pb, a = P[:6]
    u = np.clip(np.asarray(u, float), 0.0, 1.0)
    top = u < uc
    s = np.where(top, (u - uc) / uc, (u - uc) / (1.0 - uc))
    m = np.where(top, mt, mb); p = np.where(top, pt, pb)
    return np.clip(1.0 - np.abs(s) ** m, 0.0, 1.0) ** (1.0 / p) * (1.0 - a * u)


def _Fn(u, P):
    key = tuple(P[:6])
    if key not in _NORM:
        g = np.linspace(0, 1, 20001)
        _NORM[key] = float(_F(g, P).max())
    return _F(u, P) / _NORM[key]


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (6 * t - 15) + 10)          # smootherstep: C2


def _plateau(u, a0, a1, b0, b1):
    return _sstep((u - a0) / (a1 - a0)) * _sstep((b1 - u) / (b1 - b0))


def _nprof(u, P):
    nb, nt, ua, ub = P
    u = np.asarray(u, float)
    return nt + (nb - nt) * _plateau(u, 0.0, ua, ub, 1.0)


def _section_full(vid, u):
    """(c, ti, to, wi, wo, ni, no) at u (arrays)"""
    p = params(vid)
    u = np.asarray(u, float)
    c, ti, to, w, ni, no = _R3.section("B", u)          # B (exact)
    if p.get("base"):
        return c, ti, to, w, w, ni, no
    T = _Fn(u, p["T"])
    w = 0.5 * p["W"][6] * _Fn(u, p["W"])
    to = p["TO"] * T
    if "J" in p:
        a, u0, sg = p["J"]
        to = to + a * np.exp(-0.5 * ((u - u0) / sg) ** 2) * T
    e = _plateau(u, *p["E"])
    ti = e * p.get("TIK", 1.0) * ti + (1 - e) * p["TI"] * T
    ni = _nprof(u, p["NI"])
    no = _nprof(u, p["NO"])
    rev, lip = p.get("REV", 0.0), p.get("LIP", 0.0)
    wo = w - rev * np.tanh(w / max(rev, 1e-9) / 2.0) if rev > 0 else w           # cover inset (reveal)
    wi = w - lip * np.tanh(w / max(lip, 1e-9) / 2.0) if lip > 0 else w           # inner tray inset (cover overhangs)
    return c, ti, to, np.maximum(wi, 1e-6), np.maximum(wo, 1e-6), ni, no


def section(vid, u):
    """(c, ti, to, w, ni, no) at u (arrays): equator x c, inner / outer half thickness from the equator, half width (= the
    larger of the two halves: see half_widths()), exponents (arrays for the new variants, floats for B0)"""
    c, ti, to, wi, wo, ni, no = _section_full(vid, u)
    return c, ti, to, np.maximum(wi, wo), ni, no


def profile(vid, u):
    c, ti, to, w, _, _ = section(vid, u)
    return w, ti, to


def seam_x(vid, u):
    return section(vid, u)[0]


def faces(vid, u):
    c, ti, to, _, _, _ = section(vid, u)
    return c - ti, c + to, c


def thickness(vid, u):
    _, ti, to = profile(vid, u)
    return ti + to


def _row(vid, u, th, inset=0.0, floor=0.05):
    c, ti, to, wi, wo, ni, no = [np.asarray(a, float) for a in _section_full(vid, u)]
    ti, to = max(float(ti) - inset, floor), max(float(to) - inset, floor)
    wi, wo = max(float(wi) - inset, floor), max(float(wo) - inset, floor)
    outer = np.cos(th) >= 0
    r = np.where(outer, _se_r(to, wo, float(no), th), _se_r(ti, wi, float(ni), th))
    return np.stack([float(c) + r * np.cos(th), r * np.sin(th), np.full(len(th), -L * float(u))], 1)


def pebble_rows(vid, nu=150, nth=200, inset=0.0):
    """closed pebble rows (local frame) like R3 variants.pebble_rows; with a reveal the row has a 'rev' step at the seam"""
    if params(vid).get("base"):
        return _R3.pebble_rows("B", nu, nth, inset)
    us = stations(nu)
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    rows = np.array([_row(vid, u, th, inset) for u in us])
    c0, c1 = float(seam_x(vid, 0.0)), float(seam_x(vid, 1.0))
    return rows, np.array((c0, 0.0, -inset)), np.array((c1, 0.0, -L + inset))


def pebble_cloud(vid, du=0.2):
    rows, top, bot = pebble_rows(vid, int(1.6 * L / du), int(110 / du))
    return np.concatenate([rows.reshape(-1, 3), [top, bot]])


def inside_local(vid, P, inset=0.0):
    """analytic point-in-arm test (local frame); inset reduces ti, to, w (both halves)"""
    if params(vid).get("base"):
        return _R3.inside_local("B", P, inset)
    P = np.atleast_2d(np.asarray(P, float))
    u = -P[:, 2] / L
    ok = (u > 0) & (u < 1)
    c, ti, to, wi, wo, ni, no = _section_full(vid, np.clip(u, 1e-9, 1 - 1e-9))
    ti = np.maximum(ti - inset, 1e-9); to = np.maximum(to - inset, 1e-9)
    wi = np.maximum(wi - inset, 1e-9); wo = np.maximum(wo - inset, 1e-9)
    dx = P[:, 0] - c
    outer = dx >= 0
    with np.errstate(over="ignore"):
        f = np.where(outer, (np.abs(dx) / to) ** no + (np.abs(P[:, 1]) / wo) ** no,
                     (np.abs(dx) / ti) ** ni + (np.abs(P[:, 1]) / wi) ** ni)
    return ok & (f < 1.0)


def half_rows(vid, half, nu=150, nth=120, gap=SEAM):
    """rows of ONE closed half solid (local frame): half = 'vonk' (outer cover, x >= c + gap) or 'vnut' (x <= c - gap);
    same construction as R3 variants.half_rows (dome arc from seam chord to seam chord, closed along the flat seam face)"""
    if params(vid).get("base"):
        return _R3.half_rows("B", half, nu, nth, gap)
    us = stations(nu)
    out = []
    for u in us:
        c, ti, to, wi, wo, ni, no = [float(np.asarray(a)) for a in _section_full(vid, u)]
        t, w, n = (to, wo, no) if half == "vonk" else (ti, wi, ni)
        if t <= gap * 1.05:
            continue
        lo, hi = 0.0, math.pi / 2
        for _ in range(60):
            m = 0.5 * (lo + hi)
            if _se_r(t, w, n, np.array([m]))[0] * math.cos(m) > gap:
                lo = m
            else:
                hi = m
        a = np.linspace(-lo, lo, nth)
        r = _se_r(t, w, n, a)
        xx = r * np.cos(a); yy = r * np.sin(a)
        if half == "vnut":
            xx = -xx; yy = yy[::-1]; xx = xx[::-1]
        out.append(np.stack([c + xx, yy, np.full(nth, -L * float(u))], 1))
    R_ = np.array(out)
    return R_, R_[0].mean(0), R_[-1].mean(0)


def tip_plane_local(vid):
    """black tip plane on the inner lower front: R3 normal, point on this variant's seam at u = UTIP"""
    if params(vid).get("base"):
        return _R3.tip_plane_local("B")
    ut = params(vid).get("UTIP", U_TIP)
    c = float(seam_x(vid, ut))
    pt = np.array([c, 0.0, -L * ut])
    n = np.array([-0.50, -0.35, -0.79])
    return pt, n / np.linalg.norm(n)


def reveal(vid):
    """seam step (mm): + = the cover sits inside the inner half's edge (reveal), - = the cover overhangs the inner tray (lip)"""
    return float(params(vid).get("REV", 0.0)) - float(params(vid).get("LIP", 0.0))


def half_widths(vid, u):
    """(inner half width, outer cover half width) at u"""
    c, ti, to, wi, wo, ni, no = _section_full(vid, u)
    return wi, wo


# ---------------------------------------------------------------------------------------------------- B0 == R3 B
def _assert_b0(n=4001):
    us = np.linspace(0, 1, n)
    a = _R3.section("B", us); b = section("B0", us)
    dev = max(float(np.max(np.abs(np.asarray(x, float) - np.asarray(y, float)))) for x, y in zip(a, b))
    # the generic family (bump2) reproduces B's profiles to machine precision too
    dw = float(np.max(np.abs(_prof(us, _W_B) - a[3])))
    dt = float(np.max(np.abs(_prof(us, _TO_B) - a[2])))
    assert dev == 0.0 and dw < 1e-9 and dt < 1e-9, (dev, dw, dt)
    return dev, dw, dt


_assert_b0(401)


if __name__ == "__main__":
    print("B0 == R3 B (section, bump2 family):", _assert_b0())
    rng = np.random.default_rng(3)
    Pt = np.c_[rng.uniform(-14, 10, 300000), rng.uniform(-17, 17, 300000), rng.uniform(-73, 1, 300000)]
    assert (inside_local("B0", Pt) == _R3.inside_local("B", Pt)).all()
    r0 = _R3.pebble_rows("B", 150, 200)[0]; r1 = pebble_rows("B0", 150, 200)[0]
    assert np.abs(r0 - r1).max() == 0.0
    h0 = _R3.half_rows("B", "vonk")[0]; h1 = half_rows("B0", "vonk")[0]
    assert np.abs(h0 - h1).max() == 0.0
    print("B0 inside / rows / half rows identical to R3 B")
    us = np.linspace(0, 1, 4001)
    for v in VIDS:
        T = thickness(v, us); w, ti, to = profile(v, us)
        print(f"{v:3s} T max {T.max():6.2f} @u {us[T.argmax()]:.3f}  T@0.22 {float(thickness(v, 0.22)):6.2f}  "
              f"W max {2 * w.max():6.2f} @u {us[w.argmax()]:.3f}  to@.18 {float(profile(v, .18)[2]):5.2f}  "
              f"ti@.22 {float(profile(v, .22)[1]):5.2f}")

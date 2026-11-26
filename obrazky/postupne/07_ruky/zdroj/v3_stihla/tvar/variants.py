"""NOVA mini - slimmer arm shape variants (R3/tvar).  Pure numpy, no scipy: importable from the CAD venv AND Blender's python.

Frame B: mm, Z up, FRONT = -Y, robot LEFT = +X.  Shoulder axis || X through (y 3.0, z -17.0).  LEFT arm at rest; the right
arm is the mirror x -> -x.  Placement and swing are exactly those of armgeo.py / v1geo.py (SPLAY 12, SWING 3, U_ATT 0.22,
INB 5, attachment = 5 mm inside the ORIGINAL inner face at u 0.22) with the arm shift dx = -1.0.

LOCAL frame (identical to v1geo / armgeo for every variant):
    x = thickness direction (outer = +, inner = - = towards the torso), y = fore-aft width, z = 0 at the top .. -72 at the tip,
    u = -z / 72.

Section of a variant at u (an ASYMMETRIC superellipse; variant "0" = the approved symmetric T3 pebble):
    equator / seam (widest fore-aft line, parting line between the outer cover A_vonk and the inner half A_vnut) at x = c(u)
    inner half  x <= c :  |(x - c) / ti|^ni + |y / w|^ni <= 1        inner face on the centre line  x = c - ti
    outer half  x >= c :  |(x - c) / to|^no + |y / w|^no <= 1        outer face on the centre line  x = c + to
with, for each variant, constant factors on the approved profile (ht, hw) = shape.arm_profile(u):
    ti = ki * ht,   to = ko * ht,   w = kw * hw,   c = -(1 - ki) * H(u)
    H = ht for u1 <= u <= u2   ->   inner face  c - ti = -ht  (UNCHANGED there: the whole zone near the torso)
so the inner face on the centre line, the attachment point and the local frame stay exactly where they are and the arm
gets thinner from the OUTSIDE (outer cover flatter, seam moved inwards).  ni / kw are chosen so that every section in
[u1, u2] lies inside the approved section (subset -> the gap there can only grow).  Towards the two tips H is blended to a
constant so the tips follow the slimmer body (the tips then sit up to (1-ki)*ht inside the old mid-plane, i.e. slightly
outside the old pebble towards the torso, far from it: checked numerically in chk_variants.py)."""
import sys, math
import numpy as np

sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T3")
import shape as S  # noqa: E402  (approved T3 profile, pure numpy)

L = S.ARM_L                       # 72
N0 = 2.3                          # approved section exponent
SH_Y, ZS = 3.0, -17.0
AX = np.array([0.0, SH_Y, ZS])
X_SH_T4 = 46.756
SPLAY, SWING, U_ATT, INB = 12.0, 3.0, 0.22, 5.0
DX = -1.0                         # current arm shift (1 mm closer to the torso than T3/T4)
SEAM = 0.25                       # half seam gap (0.5 seam), as v1geo
U_TIP = 0.86                      # black tip plane station (as v1geo.tip_plane_local)

# ---------------------------------------------------------------------------------------------------- the variants
# ki, ko: inner / outer half thickness (from the seam) as a fraction of the approved half thickness ht(u)
# kw: fore-aft width factor;  ni, no: section exponents of the inner / outer half
# u1, u2: the inner face on the centre line is kept EXACTLY (x = -ht) for u1 <= u <= u2 (the zone that comes close to
#         the torso at rest and over the swing); towards both tips the seam / centre line is blended (smoothstep) to a
#         constant, so the two tips move inwards with the slimmer body instead of staying on the old mid-plane (otherwise
#         the outer contour becomes a straight blade).  hb: bottom-tip centre as a fraction of ht(u2) (1 = constant).
VARIANTS = {
    "0": dict(ki=1.00, ko=1.00, kw=1.00, ni=2.3, no=2.3, u1=0.04, u2=0.50, hb=1.0, utip=0.86, name="súčasná ruka (T3)"),
    "A": dict(ki=1.00, ko=0.62, kw=0.95, ni=2.3, no=2.3, u1=0.04, u2=0.50, hb=1.0, utip=0.86, name="A – mierne štíhlejšia"),
    "B": dict(ki=0.80, ko=0.55, kw=0.90, ni=2.2, no=2.3, u1=0.03, u2=0.50, hb=1.25, utip=0.85, name="B – štíhla"),
    "C": dict(ki=0.63, ko=0.46, kw=0.85, ni=2.2, no=2.3, u1=0.03, u2=0.50, hb=1.4, utip=0.84, name="C – najštíhlejšia"),
}
VIDS = ("0", "A", "B", "C")


def params(vid):
    return VARIANTS[str(vid)]


def _base(u):
    hw, ht = S.arm_profile(u)
    return np.asarray(hw, float), np.asarray(ht, float)


def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def H_seam(vid, u):
    """reference half thickness that sets the seam offset c = -(1 - ki) * H: H = ht in [u1, u2], blended to constants
    towards the tips (ht(u1) at the top, hb * ht(u2) at the bottom)"""
    p = params(vid)
    u = np.asarray(u, float)
    _, ht = _base(u)
    _, h1 = _base(p["u1"]); _, h2 = _base(p["u2"])
    bt = _smooth((p["u1"] - u) / p["u1"])
    bb = _smooth((u - p["u2"]) / (1.0 - p["u2"]))
    return ht * (1 - bt) * (1 - bb) + float(h1) * bt + p["hb"] * float(h2) * bb


def section(vid, u):
    """(c, ti, to, w, ni, no) at u (arrays): equator x c, inner / outer half thickness from the equator, half width"""
    p = params(vid)
    hw, ht = _base(u)
    c = -(1.0 - p["ki"]) * H_seam(vid, u) if p["ki"] < 1.0 else np.zeros_like(ht)
    return (c, p["ki"] * ht, p["ko"] * ht, p["kw"] * hw, p["ni"], p["no"])


def profile(vid, u):
    """(half_width, half_thick_inner, half_thick_outer) at u; the two half thicknesses are measured from the seam /
    equator x = seam_x(vid, u) (inner face at seam_x - inner, outer face at seam_x + outer).  Thickness = inner + outer."""
    c, ti, to, w, _, _ = section(vid, u)
    return w, ti, to


def seam_x(vid, u):
    """local x of the equator = seam (parting line A_vonk / A_vnut) at u; 0 for the approved arm"""
    return section(vid, u)[0]


def faces(vid, u):
    """(x of the inner face, x of the outer face, seam x) on the centre line y = 0 (local)"""
    c, ti, to, _, _, _ = section(vid, u)
    return c - ti, c + to, c


def thickness(vid, u):
    _, ti, to = profile(vid, u)
    return ti + to


def _se_r(t, w, n, th):
    c, s = np.abs(np.cos(th)), np.abs(np.sin(th))
    return ((c / t) ** n + (s / w) ** n) ** (-1.0 / n)


def _row(vid, u, th, inset=0.0, floor=0.05):
    c, ti, to, w, ni, no = section(vid, u)
    ti, to, w = max(float(ti) - inset, floor), max(float(to) - inset, floor), max(float(w) - inset, floor)
    outer = np.cos(th) >= 0
    r = np.where(outer, _se_r(to, w, no, th), _se_r(ti, w, ni, th))
    return np.stack([float(c) + r * np.cos(th), r * np.sin(th), np.full(len(th), -L * float(u))], 1)


def stations(nu):
    """the u stations of v1geo / shape.arm_points (denser near both ends, ends excluded)"""
    return (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, nu)))[1:-1]


def pebble_rows(vid, nu=150, nth=200, inset=0.0):
    """closed pebble rows (local frame), returns (rows (nu-2, nth, 3), top point, bottom point) exactly like
    v1geo.pebble_rows (= shape.arm_points); polar angle th from +x (outer) towards +y (back)"""
    us = stations(nu)
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    rows = np.array([_row(vid, u, th, inset) for u in us])
    c0, c1 = float(seam_x(vid, 0.0)), float(seam_x(vid, 1.0))      # the tips sit on the seam line (0 for variants 0 / A)
    return rows, np.array((c0, 0.0, -inset)), np.array((c1, 0.0, -L + inset))


def pebble_cloud(vid, du=0.2):
    rows, top, bot = pebble_rows(vid, int(1.6 * L / du), int(110 / du))
    return np.concatenate([rows.reshape(-1, 3), [top, bot]])


def inside_local(vid, P, inset=0.0):
    """analytic point-in-pebble test (local frame); inset reduces ti, to, w like v1geo.inside_local"""
    P = np.atleast_2d(np.asarray(P, float))
    u = -P[:, 2] / L
    ok = (u > 0) & (u < 1)
    c, ti, to, w, ni, no = section(vid, np.clip(u, 1e-9, 1 - 1e-9))
    ti = np.maximum(ti - inset, 1e-9); to = np.maximum(to - inset, 1e-9); w = np.maximum(w - inset, 1e-9)
    dx = P[:, 0] - c
    outer = dx >= 0
    f = np.where(outer, (np.abs(dx) / to) ** no + (np.abs(P[:, 1]) / w) ** no,
                 (np.abs(dx) / ti) ** ni + (np.abs(P[:, 1]) / w) ** ni)
    return ok & (f < 1.0)


def half_rows(vid, half, nu=150, nth=120, gap=SEAM):
    """rows of ONE closed half solid for rendering / export (local frame): half = 'vonk' (outer cover, x >= c + gap) or
    'vnut' (inner half, x <= c - gap).  Each row = the dome arc from the seam chord to the seam chord (nth points);
    the polygon closes along the flat seam face.  Rows where the half is thinner than the gap are dropped.
    Returns (rows (K, nth, 3), c_first, c_last) with the cap centres for a fan closure."""
    us = stations(nu)
    out = []
    for u in us:
        c, ti, to, w, ni, no = section(vid, u)
        t, n = (float(to), no) if half == "vonk" else (float(ti), ni)
        if t <= gap * 1.05:
            continue
        # polar angle (about the equator point) where |x - c| = gap  (bisection; |x - c| decreases with |th| on [0, pi/2])
        lo, hi = 0.0, math.pi / 2
        for _ in range(60):
            m = 0.5 * (lo + hi)
            if _se_r(t, float(w), n, np.array([m]))[0] * math.cos(m) > gap:
                lo = m
            else:
                hi = m
        thg = lo
        a = np.linspace(-thg, thg, nth)
        r = _se_r(t, float(w), n, a)
        xx = r * np.cos(a)
        yy = r * np.sin(a)
        if half == "vnut":
            xx = -xx; yy = yy[::-1]; xx = xx[::-1]
        out.append(np.stack([float(c) + xx, yy, np.full(nth, -L * float(u))], 1))
    R_ = np.array(out)
    return R_, R_[0].mean(0), R_[-1].mean(0)


def tip_plane_local(vid):
    """black tip (A_spicka) plane on the inner lower front: v1geo normal, point moved onto this variant's seam at u 0.86"""
    ut = params(vid).get("utip", U_TIP)
    c = float(seam_x(vid, ut))
    pt = np.array([c, 0.0, -L * ut])
    n = np.array([-0.50, -0.35, -0.79])
    return pt, n / np.linalg.norm(n)


# ---------------------------------------------------------------------------------------------------- placement (= v1geo / armgeo)
def Rmat():
    a, b = math.radians(-SPLAY), math.radians(-SWING)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return Rx @ Ry


R = Rmat()
_HW0, _HT0 = _base(U_ATT)
A_LOC = np.array([-float(_HT0) + INB, 0.0, -L * U_ATT])     # same for every variant (inner face at u 0.22 unchanged)


def att(dx=DX):
    return np.array([X_SH_T4 + 9.0 + dx, SH_Y, ZS])


def to_world(P, vid=None, dx=DX, sx=1):
    """arm local -> frame B (left arm at rest; sx = -1 gives the right arm).  vid is accepted for symmetry only: all
    variants share the approved local frame and attachment."""
    W = (np.asarray(P, float) - A_LOC) @ R.T + att(dx)
    W = np.array(W, copy=True)
    W[..., 0] *= sx
    return W


def to_local(Q, vid=None, dx=DX):
    return (np.asarray(Q, float) - att(dx)) @ R + A_LOC


def dir_world(v, sx=1):
    w = R @ np.asarray(v, float)
    w = np.array(w); w[0] *= sx
    return w


def swing(Q, deg):
    """rigid rotation about the shoulder axis; + = forward / up (tip moves to -Y)   (= armgeo.swing)"""
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    Q = np.array(Q, float, copy=True)
    y, z = Q[..., 1] - SH_Y, Q[..., 2] - ZS
    Q[..., 1] = c * y - s * z + SH_Y; Q[..., 2] = s * y + c * z + ZS
    return Q


def swing_matrix(deg):
    """4x4 of swing() (= v1geo.swing_matrix)"""
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    M = np.eye(4)
    M[1, 1], M[1, 2], M[2, 1], M[2, 2] = c, -s, s, c
    T = np.eye(4); T[:3, 3] = AX
    Ti = np.eye(4); Ti[:3, 3] = -AX
    return T @ M @ Ti


def subset_margin(vid, nth=4001):
    """max over the section of the approved-section level |X|^2.3 + |Y|^2.3 (normalised by ht, hw) of this variant's
    boundary: <= 1 means every section lies inside the approved one (u-independent because all factors are constant)"""
    p = params(vid)
    C, Ti, To, W = -(1 - p["ki"]), p["ki"], p["ko"], p["kw"]
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    outer = np.cos(th) >= 0
    r = np.where(outer, _se_r(To, W, p["no"], th), _se_r(Ti, W, p["ni"], th))
    X, Y = C + r * np.cos(th), r * np.sin(th)
    return float((np.abs(X) ** N0 + np.abs(Y) ** N0).max())


if __name__ == "__main__":
    sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/img_v1/work")
    import v1geo as V
    rows0, t0, b0 = V.pebble_rows(150, 200)
    rows1, t1, b1 = pebble_rows("0", 150, 200)
    d = float(np.abs(rows0 - rows1).max())
    dw = float(np.abs(V.to_world(rows0.reshape(-1, 3), -1.0) - to_world(rows1.reshape(-1, 3), "0", -1.0)).max())
    print("variant 0 vs v1geo: rows max dev", d, " world max dev", dw)
    assert d < 0.01 and dw < 0.01
    for vid in VIDS:
        print(vid, "subset level (<=1 ok):", round(subset_margin(vid), 5), " thick@0.22", round(float(thickness(vid, 0.22)), 2))

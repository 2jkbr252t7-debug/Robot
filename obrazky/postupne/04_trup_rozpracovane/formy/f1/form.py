"""NOVA mini - exterior form variant f1 "R01 moderny": analytic profile functions (pure python/numpy).
Shared by exterior.py (build123d CAD) and the numeric fit checks.  World mm, Z up, FRONT = -Y, robot RIGHT = -X.

Every visible surface is a loft of horizontal superellipse sections whose semi-axes are C2 functions of z:
  semi-axis = crown(z) - u(z), u = equal inset of the top / bottom round (superellipse quarter, exponent P > 2:
  curvature 0 where the round starts -> G2 to the side, horizontal tangent + zero curvature at the flat -> G2 there).
Smooth blends use the quintic smoothstep (C2)."""
import math
import numpy as np

# ------------------------------------------------------------------ helpers
def sq(s, P):
    """superellipse-quarter inset fraction: 0 at s=0 (flat derivative + zero curvature for P>2), 1 at s=1 (vertical)"""
    s = min(1.0, max(0.0, s))
    return 1.0 - max(0.0, 1.0 - s ** P) ** (1.0 / P)


def close_k(s, M):
    """closing factor of a rounded end: 1 at s=0 (G2 for M>2), 0 at s=1 (vertical tangent)"""
    s = min(1.0, max(0.0, s))
    return max(0.0, 1.0 - s ** M) ** (1.0 / M)


def S5(t):
    """quintic smoothstep 0..1, zero 1st + 2nd derivative at both ends (C2 blend)"""
    t = min(1.0, max(0.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


# ------------------------------------------------------------------ TORSO
TZ0, TZ1 = 43.0, 132.0          # bottom flat (torso floor underside) / top flat (collar ring stands 1.0 proud, top 133)
TN = 2.45                       # plan superellipse exponent
TA0, TB0, TZC, TH = 44.4, 40.4, 88.0, 44.0   # crown: max half width / depth at z 88, quadratic fall-off
TKA, TKB = 1.6, 2.2             # crown drop at |z - 88| = 44 (sides limited by the frame columns: A >= 43.2 z 83..119)
# top round: different insets in X (front view: big soft shoulders) and Y (keeps the flat collar zone >= r 30)
TUTX, TUTY, THT, TPT = 12.5, 7.6, 13.0, 2.5
TUBX, TUBY, THB, TPB = 15.0, 14.0, 13.0, 2.4   # bottom tuck-under (flat bottom >= r 22, skirt shows as plinth)


def torso_crown(z):
    a = TA0 - TKA * ((z - TZC) / TH) ** 2
    b = TB0 - TKB * ((z - TZC) / TH) ** 2
    return a, b


def torso_u(z):
    """(inset x, inset y) of the top / bottom round"""
    if z > TZ1 - THT:
        f = sq((z - (TZ1 - THT)) / THT, TPT)
        return TUTX * f, TUTY * f
    if z < TZ0 + THB:
        f = sq(((TZ0 + THB) - z) / THB, TPB)
        return TUBX * f, TUBY * f
    return 0.0, 0.0


def torso_ab(z):
    a, b = torso_crown(z)
    ux, uy = torso_u(z)
    return a - ux, b - uy


# ------------------------------------------------------------------ BASE (white shell z 10.5 .. 40)
BZ0, BZ1 = 10.5, 40.0           # white shell underside / top flat
BN = 3.4                        # squircle plan (soap bar); >= 3.3 so the cell groups drop out of the bottom opening
BA0, BB0 = 71.0, 55.5           # max half width / depth (at z BZM)
BZM = 23.5                      # widest line
BUT, BPT = 15.0, 2.5            # top round inset 15 over z 23.5..40 (16.5 high)
BUB, BPB = 6.5, 2.2             # lower side tapering in by 6.5 toward the floor, turning under at z 10.5
FOOT_A, FOOT_B, FOOT_Z0, FOOT_Z1 = 62.5, 47.5, 6.0, 10.5   # dark recessed foot = bottom opening (8.5 / 8 inside the max outline)


def base_u(z):
    if z >= BZM:
        return BUT * sq((z - BZM) / (BZ1 - BZM), BPT)
    return BUB * sq((BZM - z) / (BZM - BZ0), BPB)


def base_ab(z):
    u = base_u(z)
    return BA0 - u, BB0 - u


# ------------------------------------------------------------------ ARM (right arm, xi = -x = distance from the axis plane)
AZ_TIP, AZ_TOP, AZ_AX, AY_C = 45.0, 127.5, 112.0, 2.0
AN_IN, AN_OUT = 3.0, 2.3        # section exponents: inner (torso) side flatter, outer side rounder
A_FIN = 0.42                    # inner share of the thickness (widest line nearer the torso)


def arm_body(z):
    """(xi_in, t, b) before the end closures"""
    u = min(1.0, max(0.0, (97.0 - z) / 52.0))
    w = u ** 2.4                              # G2 at z 97 (servo bottom: 2nd derivative ~ u^0.4 -> 0), convex leaf
    #                                           outline without an inflection (an S-blend made the arm look bent)
    xi_in = 46.5 - 1.0 * w                    # inner face follows the torso side (tuck-under) by 1 mm
    t = 23.0 - 10.5 * w                       # thick at the shoulder (servo 21 + wall), 12.5 at the tip
    b = 15.8 - 2.6 * S5((98.0 - z) / 40.0)    # leaf: 15.8 at the shoulder -> 13.2 near the tip
    return xi_in, t, b


def _slope(f, z, h=1e-3):
    return (f(z + h) - f(z - h)) / (2 * h)


def arm_sec(z, w=0.0):
    """section parameters at z: (xi_c, a_in, a_out, b).  w > 0: the cavity (inner skin) of a shell with wall w -
    body semi-axes reduced by w*sqrt(1 + slope^2) (normal wall), end closures shortened by w (the offset of a
    superellipse-quarter end is ~ the quarter with both semi-axes reduced by w)."""
    xi_in, t, b = arm_body(z)
    a_in0, a_out0 = A_FIN * t, (1 - A_FIN) * t
    xi_c = xi_in + a_in0
    if w > 0:
        s_in = _slope(lambda q: arm_body(q)[0], z)
        s_out = _slope(lambda q: arm_body(q)[0] + arm_body(q)[1], z)
        s_b = _slope(lambda q: arm_body(q)[2], z)
        a_in0 -= w * math.sqrt(1 + s_in ** 2)
        a_out0 -= w * math.sqrt(1 + s_out ** 2)
        b -= w * math.sqrt(1 + s_b ** 2)
    top, tip = AZ_TOP - w, AZ_TIP + w
    kb = kin = kout = 1.0
    if z > AZ_AX:                             # top: round in the side view about the shoulder axis
        kb = close_k((z - AZ_AX) / (top - AZ_AX), 2.4)
        kin = close_k((z - (AZ_TOP - 5.0)) / (top - (AZ_TOP - 5.0)), 2.4)
        kout = close_k((z - (AZ_TOP - 9.5)) / (top - (AZ_TOP - 9.5)), 2.4)
    LT = 13.0
    if z < AZ_TIP + LT:                       # tip
        kb = close_k((AZ_TIP + LT - z) / (AZ_TIP + LT - tip), 2.4)
        kin = kout = close_k((AZ_TIP + 9.0 - z) / (AZ_TIP + 9.0 - tip), 2.4)
    return xi_c, a_in0 * kin, a_out0 * kout, b * kb


# ------------------------------------------------------------------ section point generators
def se_pts(a, b, n, count, start=0.0, dense=6000):
    """superellipse |x/a|^n + |y/b|^n = 1, `count` points evenly spaced in ARC LENGTH, first point at polar angle
    `start` (rad, from +x toward +y)"""
    th = start + 2 * np.pi * np.arange(dense + 1) / dense
    c, s = np.cos(th), np.sin(th)
    P = np.column_stack([a * np.sign(c) * np.abs(c) ** (2 / n), b * np.sign(s) * np.abs(s) ** (2 / n)])
    return _resample(P, count)


def arm_pts(xi_c, a_in, a_out, b, count, dense=6000, start=math.pi):
    """asymmetric arm section in (xi, y): outer half (xi > xi_c) exponent AN_OUT, inner half AN_IN; both halves meet
    at the y extremes with a vertical tangent and zero curvature (G2).  First point = inner extreme (start = pi)."""
    th = start + 2 * np.pi * np.arange(dense + 1) / dense
    c, s = np.cos(th), np.sin(th)
    outer = c >= 0
    n = np.where(outer, AN_OUT, AN_IN)
    a = np.where(outer, a_out, a_in)
    P = np.column_stack([xi_c + a * np.sign(c) * np.abs(c) ** (2 / n), AY_C + b * np.sign(s) * np.abs(s) ** (2 / n)])
    return _resample(P, count)


def _resample(P, count):
    """`count` points evenly spaced in arc length along the closed polyline P (P[-1] == P[0])"""
    d = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    S = np.concatenate([[0.0], np.cumsum(d)])
    tg = S[-1] * np.arange(count) / count
    x = np.interp(tg, S, P[:, 0]); y = np.interp(tg, S, P[:, 1])
    return [(float(u), float(v)) for u, v in zip(x, y)]


def stations(fun, z0, z1, ds, n=20000):
    """z stations evenly spaced (ds) along the arc of the profile (fun(z), z)"""
    zz = [z0 + (z1 - z0) * i / n for i in range(n + 1)]
    aa = [fun(z) for z in zz]
    S = [0.0]
    for i in range(1, len(zz)):
        S.append(S[-1] + math.hypot(zz[i] - zz[i - 1], aa[i] - aa[i - 1]))
    m = max(2, int(math.ceil(S[-1] / ds)))
    res, j = [], 0
    for k in range(m + 1):
        tg = S[-1] * k / m
        while j < len(S) - 2 and S[j + 1] < tg:
            j += 1
        f = (tg - S[j]) / max(1e-12, S[j + 1] - S[j])
        res.append(zz[j] + f * (zz[j + 1] - zz[j]))
    return res


if __name__ == "__main__":
    for z in (43, 44, 45.5, 48, 52, 56, 60, 70, 88, 100, 112, 118, 119, 122, 125.5, 128, 131, 132):
        print("torso", z, [round(v, 2) for v in torso_ab(z)])
    for z in (10.5, 12, 15, 20, 23.5, 28.5, 33.2, 36.6, 38, 40):
        print("base", z, [round(v, 2) for v in base_ab(z)])
    for z in (45, 47, 50, 55, 60, 70, 80, 90, 95, 100, 112, 117.25, 118.5, 120, 122.5, 125, 127):
        xc, ai, ao, b = arm_sec(z)
        print("arm", z, "xi", round(xc - ai, 2), round(xc + ao, 2), "b", round(b, 2))

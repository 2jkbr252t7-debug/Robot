"""f2 "Kapsula" - analytic form definition (pure math, no CAD): torso, base and arm section functions.
World mm, Z up, floor z = 0, FRONT = -Y, robot RIGHT = -X.  Every visible surface is a loft of closed periodic
splines through arc-length-sampled section points; the section parameters are smooth (G2) functions of the profile.

TORSO  egg-capsule: plan superellipse a(z) x b(z), exponent n(z) 2.15 at the waist -> 2.0 (circle) at the top and
       bottom; side profile = two superellipse quadrants (p_lo below, p_hi above) meeting at the widest section z_w
       (both curvatures 0 there -> G2), flat bottom r_bot at z 43 (G2: quadrant exponent > 2), top quadrant ends
       horizontal at r_top on z_t (white top), the collar plateau is a separate black trim ring.
       Shoulder dimple: smooth inward x-displacement d(rho) = D (1 - (rho/R)^2)^3 around the shoulder axis (C2 at R),
       weighted by (|x|/a)^4 so only the sides move.
BASE   elliptic pebble: lower roll (foot seam, horizontal) -> widest (vertical) -> upper roll -> crest (horizontal)
       -> concave dish (quintic smoothstep, G2 both ends) -> flat dish floor r 38 at z 40.
ARM    flipper: horizontal composite-superellipse sections (inner half exponent n_i, outer half n_o, meeting at the
       seam x_c with zero curvature -> G2), side-view half-width w(z), thicknesses with superellipse end closures."""
import math
import functools

# ------------------------------------------------------------------------------------------------ helpers


def smooth5(x):
    """quintic smoothstep 0..1 with zero 1st + 2nd derivative at both ends (C2)"""
    x = min(1.0, max(0.0, x))
    return x * x * x * (10 - 15 * x + 6 * x * x)


def se_close(t, m):
    """superellipse end closure k = (1 - t^m)^(1/m), t in 0..1 (k' = k'' = 0 at t = 0 for m > 2)"""
    t = min(1.0, max(0.0, t))
    return max(0.0, 1 - t ** m) ** (1 / m)


def arc_resample(P, count, closed=True):
    """resample a dense polyline (list of (x, y)) to `count` points evenly spaced in arc length"""
    Q = list(P) + ([P[0]] if closed else [])
    S = [0.0]
    for i in range(1, len(Q)):
        S.append(S[-1] + math.hypot(Q[i][0] - Q[i - 1][0], Q[i][1] - Q[i - 1][1]))
    out, j = [], 0
    n = count if closed else count - 1
    for k in range(count):
        tg = S[-1] * k / n
        while j < len(S) - 2 and S[j + 1] < tg:
            j += 1
        f = (tg - S[j]) / max(1e-12, S[j + 1] - S[j])
        out.append((Q[j][0] + f * (Q[j + 1][0] - Q[j][0]), Q[j][1] + f * (Q[j + 1][1] - Q[j][1])))
    return out


@functools.lru_cache(maxsize=8192)
def se_dense(a, b, n, m=4000, start=math.pi / 2):
    """dense superellipse polyline, polar sampling, starting at angle `start` (default +Y = back)"""
    P = []
    for i in range(m):
        th = start + 2 * math.pi * i / m
        c, s = math.cos(th), math.sin(th)
        r = ((abs(c) / a) ** n + (abs(s) / b) ** n) ** (-1.0 / n)
        P.append((r * c, r * s))
    return tuple(P)


# ------------------------------------------------------------------------------------------------ TORSO
T = dict(z_b=43.0, z_w=79.0, z_t=132.0, r_bot=33.0, r_top=31.2, a_w=45.5, b_w=41.0, n_w=2.15,
         p_lo=2.3, p_hi=2.25, D=2.6, R=31.0, SHY=2.0, SHZ=112.0)


def torso_profile_dense(m=6000):
    """dense side profile samples (z, k, part) from the bottom (z_b, k=0) to the top (z_t, k=0); k = 0..1 radial
    factor (0 = r_bot / r_top, 1 = widest).  Returned as list of (z, a, b, n)."""
    out = []
    # lower quadrant: param phi 0..pi/2 (phi=0 at the bottom point, pi/2 at the waist)
    for i in range(m + 1):
        ph = (math.pi / 2) * i / m
        p = T["p_lo"]
        k = math.sin(ph) ** (2 / p)                      # radial factor
        t = math.cos(ph) ** (2 / p)                      # (z_w - z)/(z_w - z_b)
        z = T["z_w"] - t * (T["z_w"] - T["z_b"])
        out.append((z, T["r_bot"] + (T["a_w"] - T["r_bot"]) * k, T["r_bot"] + (T["b_w"] - T["r_bot"]) * k,
                    2.0 + (T["n_w"] - 2.0) * k))
    for i in range(1, m + 1):
        ph = (math.pi / 2) * i / m
        p = T["p_hi"]
        k = math.cos(ph) ** (2 / p)
        t = math.sin(ph) ** (2 / p)
        z = T["z_w"] + t * (T["z_t"] - T["z_w"])
        out.append((z, T["r_top"] + (T["a_w"] - T["r_top"]) * k, T["r_top"] + (T["b_w"] - T["r_top"]) * k,
                    2.0 + (T["n_w"] - 2.0) * k))
    return out


def torso_ab(z):
    """(a, b, n) of the torso section at height z (analytic inverse of the profile)"""
    if z <= T["z_w"]:
        t = (T["z_w"] - z) / (T["z_w"] - T["z_b"])
        k = se_close(t, T["p_lo"])
        r0 = T["r_bot"]
    else:
        t = (z - T["z_w"]) / (T["z_t"] - T["z_w"])
        k = se_close(t, T["p_hi"])
        r0 = T["r_top"]
    return r0 + (T["a_w"] - r0) * k, r0 + (T["b_w"] - r0) * k, 2.0 + (T["n_w"] - 2.0) * k


def dimple(y, z):
    rho = math.hypot(y - T["SHY"], z - T["SHZ"])
    if rho >= T["R"]:
        return 0.0
    return T["D"] * (1 - (rho / T["R"]) ** 2) ** 3


def torso_section_pts(a, b, n, z, count):
    P = se_dense(round(a, 9), round(b, 9), round(n, 9))
    Q = []
    for x, y in P:
        d = dimple(y, z)
        if d > 0:
            w = (abs(x) / a) ** 4
            x = x - math.copysign(d * w, x)
        Q.append((x, y))
    return arc_resample(Q, count)


def stations_from_profile(prof, ds):
    """pick profile samples evenly spaced (ds) in arc length of the (a, z) curve"""
    S = [0.0]
    for i in range(1, len(prof)):
        S.append(S[-1] + math.hypot(prof[i][0] - prof[i - 1][0], prof[i][1] - prof[i - 1][1]))
    m = max(2, int(math.ceil(S[-1] / ds)))
    res, j = [], 0
    for k in range(m + 1):
        tg = S[-1] * k / m
        while j < len(S) - 2 and S[j + 1] < tg:
            j += 1
        f = (tg - S[j]) / max(1e-12, S[j + 1] - S[j])
        res.append(tuple(prof[j][q] + f * (prof[j + 1][q] - prof[j][q]) for q in range(len(prof[j]))))
    return res


# ------------------------------------------------------------------------------------------------ BASE
B = dict(z_f=8.5, a_f=66.0, b_f=51.0, n_f=2.6, z_w=20.0, a_w=72.0, b_w=56.0, n_w=2.05, z_c=45.0, a_c=48.0,
         b_c=46.0, z_d=40.0, r_d=37.0, p1=2.15, p2=2.1)


def base_profile_dense(m=4000):
    """(z, a, b, n) from the foot seam (horizontal) over the widest, the crest, down the dish to the floor"""
    out = []
    for i in range(m + 1):                               # lower roll: foot seam (k=0) -> widest (k=1)
        ph = (math.pi / 2) * i / m
        k = math.sin(ph) ** (2 / B["p1"])
        t = math.cos(ph) ** (2 / B["p1"])
        z = B["z_w"] - t * (B["z_w"] - B["z_f"])
        out.append((z, B["a_f"] + (B["a_w"] - B["a_f"]) * k, B["b_f"] + (B["b_w"] - B["b_f"]) * k,
                    B["n_f"] + (B["n_w"] - B["n_f"]) * k))
    for i in range(1, m + 1):                            # upper roll: widest -> crest (horizontal)
        ph = (math.pi / 2) * i / m
        k = math.cos(ph) ** (2 / B["p2"])
        t = math.sin(ph) ** (2 / B["p2"])
        z = B["z_w"] + t * (B["z_c"] - B["z_w"])
        out.append((z, B["a_c"] + (B["a_w"] - B["a_c"]) * k, B["b_c"] + (B["b_w"] - B["b_c"]) * k, B["n_w"]))
    for i in range(1, m + 1):                            # dish: crest -> floor (G2 smoothstep)
        v = i / m
        z = B["z_c"] - (B["z_c"] - B["z_d"]) * smooth5(v)
        out.append((z, B["a_c"] + (B["r_d"] - B["a_c"]) * v, B["b_c"] + (B["r_d"] - B["b_c"]) * v,
                    B["n_w"] + (2.0 - B["n_w"]) * smooth5(v)))
    return out


def base_top_z(r_x, r_y):
    """height of the base top surface (crest / dish) along X (r_x) or Y (r_y) - used for checks"""
    pass


# ------------------------------------------------------------------------------------------------ ARM (left, +X)
A = dict(y_c=2.0, z_tip=50.0, z_s1=74.0, z_s2=114.0, z_top=129.0, x_c=52.5, n_i=2.8, n_o=2.15, Mb=2.3, Mt=2.2,
         Mtt=2.2)


def arm_params(z, s=0.0):
    """(x_c, y_c, h_i, h_o, w) of the left-arm section at height z; s > 0 = inward offset (inner skin): the body
    sizes shrink by s and the end closures end s earlier (approximate normal offset of the blunt ends)"""
    w_body = 10.5 + 4.5 * smooth5((z - 66.0) / (114.0 - 66.0)) - s           # side-view half width (no prism band)
    x_in = 48.0 - 1.5 * smooth5((z - 84.0) / (98.0 - 84.0)) + 1.1 * s         # inner face (torso side)
    x_out = 60.5 + 10.7 * smooth5((z - 50.0) / (112.0 - 50.0)) - 1.06 * s     # outer face (no constant band)
    z_top, z_tip = A["z_top"] - 1.25 * s, A["z_tip"] + 1.9 * s       # inner skin: end walls >= WALL (verified)
    if z >= A["z_s2"]:
        e = se_close((z - A["z_s2"]) / (z_top - A["z_s2"]), A["Mt"])
    elif z <= A["z_s1"]:
        e = se_close((A["z_s1"] - z) / (A["z_s1"] - z_tip), A["Mb"])
    else:
        e = 1.0
    xc = A["x_c"]
    return xc, A["y_c"], max(0.0, xc - x_in) * e, max(0.0, x_out - xc) * e, max(0.0, w_body) * e


@functools.lru_cache(maxsize=8192)
def _half_se(h, w, n, m=1500):
    """quarter-to-quarter half superellipse x>=0 side: points from (0, +w) over (h, 0) to (0, -w)"""
    P = []
    for i in range(m + 1):
        th = math.pi / 2 - math.pi * i / m
        c, s = math.cos(th), math.sin(th)
        r = ((abs(c) / h) ** n + (abs(s) / w) ** n) ** (-1.0 / n) if (h > 0 and w > 0) else 0.0
        P.append((r * c, r * s))
    return P


def arm_section_pts(z, count, side=+1, s=0.0):
    xc, yc, hi, ho, w = arm_params(z, s)
    outer = _half_se(round(ho, 9), round(w, 9), A["n_o"])                 # (+x side) from +w to -w
    inner = _half_se(round(hi, 9), round(w, 9), A["n_i"])
    P = [(xc + x, yc + y) for x, y in outer]
    P += [(xc - x, yc + y) for x, y in reversed(inner)][1:-1]             # from -w back to +w on the inner side
    P = arc_resample(P, count)
    if side < 0:
        P = [(-x, y) for x, y in reversed(P)]
    return P


def arm_profile_dense(m=4000, s=0.0):
    """(z, size, xc, h_i, h_o, w) samples tip -> top, dense in an arc-like parameter (closures are steep at the ends)"""
    out = []
    zt, z1, z2, zT = A["z_tip"] + 1.9 * s, A["z_s1"], A["z_s2"], A["z_top"] - 1.25 * s
    for i in range(m + 1):                          # bottom closure, parametrised by angle so the tip is resolved
        ph = (math.pi / 2) * i / m
        t = math.cos(ph) ** (2 / A["Mb"])
        out.append(z1 - t * (z1 - zt))
    for i in range(1, m + 1):
        out.append(z1 + (z2 - z1) * i / m)
    for i in range(1, m + 1):
        ph = (math.pi / 2) * i / m
        t = math.sin(ph) ** (2 / A["Mt"])
        out.append(z2 + t * (zT - z2))
    rows = []
    for z in out:
        xc, yc, hi, ho, w = arm_params(z, s)
        rows.append((z, max(w, hi + ho), xc, hi, ho, w))
    return rows

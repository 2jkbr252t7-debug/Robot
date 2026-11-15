"""NOVA torso / arm / base shapes measured from the user's sheets R05 (torso), R02 (arm), R01 (whole robot).
Pure numpy - imported both by the Blender builder and by the check scripts.
Torso frame: B frame of the finished neck (x right-left, y front(-)/back(+), z up, torso top = collar top z = TOP = 4).
The torso is a loft of horizontal superellipse sections |x/a|^n + |y/b|^n = 1 whose half-width a, half-depth b and
exponent n follow profiles traced from R05 'SPREDU' (front) and 'PRAVY BOK' (side), adapted so that the top section
hugs the finished collar ring (r 28.35) - R05's own collar is smaller (about 41 x 38 mm)."""
import os
import numpy as np

COUNT = int(os.environ.get("NOVA_COUNT", 480))      # points per horizontal section
DS = float(os.environ.get("NOVA_DS", 0.7))           # station spacing along the profile (mm)

TOP = 4.0
H_T = 85.0            # white torso height (R01: torso about 105 wide x 86 high for the 110 head)
A_MAX, B_MAX = 52.5, 40.0   # half width / half depth (R05: D / W = 0.76 -> 36; ours 40 for the internals)
XS = 33.3             # seam planes x = +-XS (R05 front + top view: 0.635 of the half width)

# control points: (drop below TOP, half-width a, half-depth b, exponent n)
# front view (R05 SPREDU): shoulder shelf from the collar, rounded shoulder (R01: larger radius than R05), gentle flare to
# the widest level at ~78 % of the height, rounded tuck-under.  side view (R05 PRAVY BOK): egg-like, widest at ~65 %.
CP = np.array([
    # drop     a      b     n
    (0.00, 28.40, 28.40, 2.00),
    (0.25, 29.80, 29.10, 2.02),
    (1.00, 32.60, 30.00, 2.05),
    (2.40, 36.00, 30.90, 2.10),
    (4.40, 39.40, 31.90, 2.16),
    (7.00, 42.20, 33.00, 2.22),
    (10.50, 44.20, 34.20, 2.27),
    (15.00, 45.60, 35.50, 2.30),
    (22.00, 47.00, 37.10, 2.33),
    (32.00, 48.80, 38.70, 2.35),
    (44.00, 50.60, 39.70, 2.36),
    (56.00, 52.00, 40.00, 2.38),
    (66.00, 52.50, 39.40, 2.42),
    (74.00, 52.10, 38.00, 2.47),
    (80.00, 50.60, 35.80, 2.53),
    (83.50, 48.00, 33.00, 2.58),
    (85.00, 45.60, 31.00, 2.60),
    (87.40, 41.50, 27.60, 2.66),
    (88.50, 38.00, 24.60, 2.70),
])
DROP_WHITE = 85.0


class Spline:
    """natural cubic spline y(x), x strictly increasing"""

    def __init__(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        n = len(x)
        h = np.diff(x)
        A = np.zeros((n, n)); r = np.zeros(n)
        A[0, 0] = A[-1, -1] = 1.0
        for i in range(1, n - 1):
            A[i, i - 1], A[i, i], A[i, i + 1] = h[i - 1], 2 * (h[i - 1] + h[i]), h[i]
            r[i] = 6 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
        self.x, self.y, self.m, self.h = x, y, np.linalg.solve(A, r), h

    def __call__(self, t):
        t = np.clip(np.asarray(t, float), self.x[0], self.x[-1])
        i = np.clip(np.searchsorted(self.x, t) - 1, 0, len(self.x) - 2)
        h = self.h[i]; a = (self.x[i + 1] - t) / h; b = (t - self.x[i]) / h
        return a * self.y[i] + b * self.y[i + 1] + ((a ** 3 - a) * self.m[i] + (b ** 3 - b) * self.m[i + 1]) * h * h / 6


def _param(cp):
    d = np.hypot(np.diff(cp[:, 0]), np.diff(cp[:, 1])) + 0.35 * np.abs(np.diff(cp[:, 2]))
    return np.concatenate([[0.0], np.cumsum(np.sqrt(d))])        # centripetal-like parameter


_S = _param(CP)
_SP = [Spline(_S, CP[:, k]) for k in range(4)]
S_END = _S[-1]


def s_of_drop(drop):
    ss = np.linspace(0, S_END, 4000)
    return float(np.interp(drop, _SP[0](ss), ss))


S_WHITE = s_of_drop(DROP_WHITE)


def prof(s):
    """(drop, a, b, n) at profile parameter s (0 .. S_END)"""
    return tuple(float(_SP[k](s)) for k in range(4))


def stations(s0=0.0, s1=None, ds=None):
    """profile parameters evenly spaced (ds mm) along the front-view profile arc"""
    s1 = S_END if s1 is None else s1
    ds = DS if ds is None else ds
    ss = np.linspace(s0, s1, 3000)
    d, a, b = _SP[0](ss), _SP[1](ss), _SP[2](ss)
    L = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(d), np.diff(a)) + 0.3 * np.abs(np.diff(b)))])
    k = max(8, int(L[-1] / ds))
    return np.interp(np.linspace(0, L[-1], k + 1), L, ss)


def se_r(a, b, n, th):
    """polar radius of the superellipse at polar angle th (array)"""
    c, s = np.abs(np.cos(th)), np.abs(np.sin(th))
    return ((c / a) ** n + (s / b) ** n) ** (-1.0 / n)


def section(s, inset=0.0, count=None):
    """section points (count, 3) at profile parameter s, offset inward by `inset` along the profile normal"""
    count = COUNT if count is None else count
    drop, a, b, n = prof(s)
    if inset:
        e = 1e-3
        d0, a0, b0, _ = prof(max(0.0, s - e)); d1, a1, b1, _ = prof(min(S_END, s + e))
        la = np.hypot(a1 - a0, d1 - d0); lb = np.hypot(b1 - b0, d1 - d0)
        # outward normal of the profile (a outward, drop downward): (d', -a') normalised
        a -= inset * (d1 - d0) / la
        b -= inset * (d1 - d0) / lb
        drop -= inset * (-(a1 - a0) / la)          # moves down where the profile heads outward (shelf), up at the bottom
    th = np.linspace(0, 2 * np.pi, count, endpoint=False) - np.pi / 2      # start at the FRONT centre (y < 0)
    r = se_r(a, b, n, th)
    return np.stack([r * np.cos(th), r * np.sin(th), np.full(count, TOP - drop)], axis=1)


def y_front(x, drop):
    """y of the front surface at lateral position x and height TOP - drop"""
    s = s_of_drop(drop)
    _, a, b, n = prof(s)
    return -b * (1 - min(1.0, abs(x) / a) ** n) ** (1 / n)


# ------------------------------------------------------------------------------------------------ arm (R02 / R11)
ARM_L, ARM_W, ARM_T = 72.0, 35.0, 24.5     # length, width (fore-aft), thickness (lateral)


def arm_profile(u):
    """half width, half thickness at u in [0, 1] (0 = top, 1 = bottom tip): egg/pebble with the fat end up"""
    u = np.asarray(u, float)
    def bump(u, peak, m):
        k = np.log(0.5) / np.log(peak)
        v = np.clip(u, 0, 1) ** k
        return np.clip(1 - np.abs(2 * v - 1) ** m, 0, 1) ** (1 / m)
    hw = ARM_W / 2 * bump(u, 0.40, 2.6) * (1 - 0.12 * u)
    ht = ARM_T / 2 * bump(u, 0.34, 2.7) * (1 - 0.24 * u)
    return hw, ht


def arm_points(nu=None, nth=None, inset=0.0):
    """closed pebble: rows along the length; local frame: x thickness (outer +), y width, z from +0 (top) to -ARM_L"""
    nu = nu or (140 if COUNT >= 400 else 80)
    nth = nth or (200 if COUNT >= 400 else 110)
    us = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, nu))            # denser near both ends
    us = us[1:-1]
    hw, ht = arm_profile(us)
    hw, ht = np.maximum(hw - inset, 0.05), np.maximum(ht - inset, 0.05)
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    rows = []
    for u, w, t in zip(us, hw, ht):
        r = se_r(t, w, 2.3, th)
        rows.append(np.stack([r * np.cos(th), r * np.sin(th), np.full(nth, -ARM_L * u)], axis=1))
    return np.array(rows), (0.0, 0.0, -inset), (0.0, 0.0, -ARM_L + inset)


# ------------------------------------------------------------------------------------------------ base (R01)
BASE_W, BASE_D, BASE_H, BASE_N = 146.0, 112.0, 27.0, 4.4      # slab; plan = superellipse (large round corners)
FOOT_H = 3.5
# profile: (inset e from the outline, drop below the base top)
BASE_CP = np.array([(38.0, 0.0), (16.0, 0.0), (13.0, 0.0), (12.5, 0.2), (12.0, 0.5), (9.0, 0.65), (6.0, 0.95), (3.4, 1.7),
                    (1.5, 3.2), (0.45, 5.4), (0.05, 8.5), (0.0, 15.0), (0.25, 21.5), (0.9, 24.8), (2.2, 26.4),
                    (4.5, 27.0)])


def base_stations(ds=None):
    ds = DS if ds is None else ds
    d = np.sqrt(np.hypot(np.diff(BASE_CP[:, 0]), np.diff(BASE_CP[:, 1])))
    S = np.concatenate([[0.0], np.cumsum(d)])
    se, sz = Spline(S, BASE_CP[:, 0]), Spline(S, BASE_CP[:, 1])
    ss = np.linspace(0, S[-1], 3000)
    L = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(se(ss)), np.diff(sz(ss))))])
    k = int(L[-1] / ds)
    q = np.interp(np.linspace(0, L[-1], k + 1), L, ss)
    return se(q), sz(q)


def base_section(e, count=None):
    count = COUNT if count is None else count
    a, b = BASE_W / 2 - e, BASE_D / 2 - e
    th = np.linspace(0, 2 * np.pi, count, endpoint=False) - np.pi / 2
    n = max(2.0, BASE_N * min(1.0, (min(a, b) / (BASE_D / 2)) ** 0.5))
    r = se_r(a, b, n, th)
    return np.stack([r * np.cos(th), r * np.sin(th)], axis=1)


if __name__ == "__main__":
    ss = np.linspace(0, S_END, 2000)
    d, a, b, n = (_SP[k](ss) for k in range(4))
    for nm, v in (("a", a), ("b", b)):
        # convexity: turning direction of the curve (v, d) must not change sign
        t1 = np.stack([np.diff(v), np.diff(d)], 1)
        cr = t1[:-1, 0] * t1[1:, 1] - t1[:-1, 1] * t1[1:, 0]
        print(nm, "max", round(v.max(), 2), "at drop", round(float(d[v.argmax()]), 1), "convex:", bool((cr >= -1e-7).all()),
              "min cross", float(cr.min()), "monotone drop:", bool((np.diff(d) > 0).all()))
    print("S_END", S_END, "S_WHITE", S_WHITE, "stations", len(stations()))

"""Independent re-implementation (verifier) of the variant-A arm and its placement.
Only the approved T3 profile shape.arm_profile is imported; section, placement and sampling are written here from the
numbers in the brief (ki 1.00, ko 0.62, kw 0.95, n 2.3, seam = local plane x = 0; SPLAY 12, SWING 3, U_ATT 0.22, INB 5,
attachment x = 46.756 + 9 - 1).  Frame B, LEFT arm at rest."""
import sys, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T3")
import shape as S  # noqa

L = 72.0
N = 2.3
YA, ZA = 3.0, -17.0
KO, KW = 0.62, 0.95          # variant A (ki = 1 -> seam stays x = 0)


def prof(u):
    hw, ht = S.arm_profile(u)
    return np.asarray(hw, float), np.asarray(ht, float)


def sec(u, ko=KO, kw=KW):
    """(ti, to, w) at u; seam at local x = 0"""
    hw, ht = prof(u)
    return ht, ko * ht, kw * hw


def inside(P, ko=KO, kw=KW, inset=0.0):
    P = np.atleast_2d(P)
    u = -P[:, 2] / L
    ok = (u > 0) & (u < 1)
    ti, to, w = sec(np.clip(u, 1e-9, 1 - 1e-9), ko, kw)
    ti = np.maximum(ti - inset, 1e-9); to = np.maximum(to - inset, 1e-9); w = np.maximum(w - inset, 1e-9)
    t = np.where(P[:, 0] >= 0, to, ti)
    return ok & ((np.abs(P[:, 0]) / t) ** N + (np.abs(P[:, 1]) / w) ** N < 1.0)


def level(P, ko=KO, kw=KW):
    """superellipse level of local points (<1 inside)"""
    P = np.atleast_2d(P)
    u = np.clip(-P[:, 2] / L, 1e-9, 1 - 1e-9)
    ti, to, w = sec(u, ko, kw)
    t = np.where(P[:, 0] >= 0, to, ti)
    return (np.abs(P[:, 0]) / t) ** N + (np.abs(P[:, 1]) / w) ** N


# ---------------------------------------------------------------- placement (from armgeo constants, written again here)
_a, _b = math.radians(-12.0), math.radians(-3.0)
RY = np.array([[math.cos(_a), 0, math.sin(_a)], [0, 1, 0], [-math.sin(_a), 0, math.cos(_a)]])
RX = np.array([[1, 0, 0], [0, math.cos(_b), -math.sin(_b)], [0, math.sin(_b), math.cos(_b)]])
R = RX @ RY
_, HT_ATT = prof(0.22)
A_LOC = np.array([-float(HT_ATT) + 5.0, 0.0, -L * 0.22])
ATT = np.array([46.756 + 9.0 - 1.0, YA, ZA])


def to_world(P):
    return (np.asarray(P, float) - A_LOC) @ R.T + ATT


def to_local(Q):
    return (np.asarray(Q, float) - ATT) @ R + A_LOC


def swing(Q, deg):
    a = math.radians(-deg); c, s = math.cos(a), math.sin(a)
    Q = np.array(Q, float, copy=True)
    y, z = Q[..., 1] - YA, Q[..., 2] - ZA
    Q[..., 1] = c * y - s * z + YA; Q[..., 2] = s * y + c * z + ZA
    return Q


# ---------------------------------------------------------------- parametric surface sampling (no ray bisection)
def u_grid(u0=0.0, u1=1.0, ds=0.06, ko=KO, kw=KW):
    """u stations with max(|dz|, |d to|, |d ti|, |d w|) <= ds (arc-length-like), ends excluded"""
    uu = np.linspace(u0, u1, 200001)
    ti, to, w = sec(uu, ko, kw)
    z = L * uu
    d = np.maximum.reduce([np.abs(np.diff(z)), np.abs(np.diff(ti)), np.abs(np.diff(to)), np.abs(np.diff(w))])
    s = np.r_[0.0, np.cumsum(d)]
    k = int(s[-1] / ds) + 1
    us = np.interp(np.linspace(0, s[-1], k + 1), s, uu)
    us = us[(us > 1e-7) & (us < 1 - 1e-7)]
    return us


def se_pts(t, w, n, m):
    """m points of the half superellipse |x/t|^n+|y/w|^n=1, x>=0, roughly uniform in arc length (param by angle phi
    with x = t cos^(2/n), y = w sin^(2/n) signs)"""
    ph = np.linspace(-np.pi / 2, np.pi / 2, m)
    c, s = np.cos(ph), np.sin(ph)
    x = t * np.abs(c) ** (2.0 / n)
    y = w * np.sign(s) * np.abs(s) ** (2.0 / n)
    return x, y


def surface(u0=0.0, u1=1.0, ds=0.06, ko=KO, kw=KW, m=None):
    """local surface points + half label (True = outer half x >= 0).  Rows by u_grid, each section re-sampled to uniform
    arc length <= ds."""
    us = u_grid(u0, u1, ds, ko, kw)
    P, H = [], []
    for u in us:
        ti, to, w = (float(v) for v in sec(u, ko, kw))
        for sgn, t in ((1, to), (-1, ti)):
            x, y = se_pts(t, w, N, 4001)
            # arc length re-sample
            sl = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
            k = max(8, int(sl[-1] / ds) + 1)
            q = np.linspace(0, sl[-1], k)
            xx, yy = np.interp(q, sl, x), np.interp(q, sl, y)
            P.append(np.c_[sgn * xx, yy, np.full(k, -L * u)])
            H.append(np.full(k, sgn > 0))
    P.append(np.array([[0, 0, 0.0], [0, 0, -L]])); H.append(np.array([True, True]))
    return np.concatenate(P), np.concatenate(H)


if __name__ == "__main__":
    sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
    import variants as VA
    rng = np.random.default_rng(7)
    Pt = np.c_[rng.uniform(-14, 14, 300000), rng.uniform(-19, 19, 300000), rng.uniform(-73, 1, 300000)]
    mis = int((inside(Pt) != VA.inside_local("A", Pt)).sum())
    dw = float(np.abs(to_world(Pt) - VA.to_world(Pt, "A", -1.0)).max())
    dl = float(np.abs(to_local(to_world(Pt)) - Pt).max())
    Q = rng.uniform(-60, 60, (3000, 3))
    dsw = max(float(np.abs(swing(Q, a) - VA.swing(Q, a)).max()) for a in (-45, 60, 135))
    print("inside mismatches vs variants.py:", mis, " world dev:", dw, " roundtrip:", dl, " swing dev:", dsw)
    for u in (0.05, 0.1, 0.22, 0.3, 0.5, 0.86):
        ti, to, w = sec(u)
        print(f"u {u}: inner {float(ti):.3f} outer {float(to):.3f} thick {float(ti + to):.3f} width {2 * float(w):.3f}")
    P, H = surface(0.0, 0.5, 0.1)
    print("surface pts", len(P), "level dev", float(np.abs(level(P[2:-2] if False else P[:-2]) - 1).max()))

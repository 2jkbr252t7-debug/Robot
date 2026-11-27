"""own dense parametric surface of an R4 arm variant (local frame) built from variants_b._section_full only.
Rows at adaptive u stations (surface step <= h), each row = the inner half (x <= c) with (ti, wi, ni) and the outer half
(x >= c) with (to, wo, no), arc-length sampled; plus the flat seam step face x = c between min(wi, wo) and max(wi, wo)
(REV / LIP variants).  Every point carries its half label: 0 inner, 1 outer, 2 step face."""
import sys, math
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R4/tvar")
import variants_b as VB

L = VB.L


def secf(vid, u):
    return [np.asarray(a, float) * np.ones_like(np.asarray(u, float)) for a in VB._section_full(vid, u)]


def stations(vid, u0, u1, h):
    g = np.linspace(u0, u1, 20001)
    c, ti, to, wi, wo, ni, no = secf(vid, g)
    d = np.abs(np.gradient(np.c_[c + to, c - ti, wi, wo], g, axis=0)).max(1)
    rate = np.sqrt(L ** 2 + d ** 2)                       # surface mm per unit u (meridian, worst of the four lines)
    s = np.r_[0, np.cumsum(0.5 * (rate[1:] + rate[:-1]) * np.diff(g))]
    n = max(2, int(s[-1] / h) + 1)
    return np.interp(np.linspace(0, s[-1], n), s, g)


def se_half(t, w, n, h, sgn):
    """quarter-to-quarter superellipse half: points (dx, y) with dx = sgn*t*|cos|^(2/n)... arc-length resampled"""
    a = np.linspace(-np.pi / 2, np.pi / 2, 4001)
    ca, sa = np.cos(a), np.sin(a)
    dx = t * np.sign(ca) * np.abs(ca) ** (2.0 / n)
    y = w * np.sign(sa) * np.abs(sa) ** (2.0 / n)
    s = np.r_[0, np.cumsum(np.hypot(np.diff(dx), np.diff(y)))]
    m = max(8, int(s[-1] / h) + 1)
    q = np.linspace(0, s[-1], m)
    return sgn * np.interp(q, s, dx), np.interp(q, s, y)


def cloud(vid, h=0.1, u0=0.0, u1=1.0):
    us = stations(vid, max(u0, 1e-7), min(u1, 1 - 1e-7), h)
    P, lab, U = [], [], []
    for u in us:
        c, ti, to, wi, wo, ni, no = [float(np.ravel(v)[0]) for v in secf(vid, np.array([u]))]
        z = -L * u
        for (t, w, n, sg, lb) in ((ti, wi, ni, -1, 0), (to, wo, no, 1, 1)):
            dx, y = se_half(t, w, n, h, sg)
            P.append(np.c_[c + dx, y, np.full(len(y), z)]); lab.append(np.full(len(y), lb)); U.append(np.full(len(y), u))
        if abs(wi - wo) > 1e-6:
            for sy in (1, -1):
                yy = np.linspace(min(wi, wo), max(wi, wo), max(2, int(abs(wi - wo) / h) + 2))
                P.append(np.c_[np.full(len(yy), c), sy * yy, np.full(len(yy), z)]); lab.append(np.full(len(yy), 2)); U.append(np.full(len(yy), u))
    return np.concatenate(P), np.concatenate(lab), np.concatenate(U)

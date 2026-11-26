"""Independent verifier (R3/overenie_B): own dense ANALYTIC surface sampling of a shape variant + exact local refinement.
Uses only the variant's section() definition (the source of truth for the shape), NOT the checker's ray-bisection cloud.
Local frame of variants.py: x thickness (outer +), y fore-aft, z = 0 top .. -72 tip, u = -z/72."""
import sys, math
sys.dont_write_bytecode = True
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import minimize

sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
import variants as VA  # noqa: E402

L = VA.L


def se_r(t, w, n, th):
    c, s = np.abs(np.cos(th)), np.abs(np.sin(th))
    return ((c / t) ** n + (s / w) ** n) ** (-1.0 / n)


def surf_pt(vid, u, th):
    """analytic surface point(s) at (u, th); th in (-pi, pi], |th| <= pi/2 = outer (cover) half"""
    u = np.asarray(u, float); th = np.asarray(th, float)
    c, ti, to, w, ni, no = VA.section(vid, u)
    outer = np.cos(th) >= 0
    r = np.where(outer, se_r(to, w, no, th), se_r(ti, w, ni, th))
    return np.stack([c + r * np.cos(th), r * np.sin(th), -L * u], -1)


def u_grid(vid, u0, u1, ds):
    """u stations with meridian arc spacing <= ds (accounts for the steep top / bottom domes)"""
    uu = np.unique(np.r_[np.geomspace(1e-7, 0.02, 20000), np.linspace(0.0, 1.0, 200001)])
    uu = uu[(uu >= u0) & (uu <= u1)]
    c, ti, to, w, _, _ = VA.section(vid, uu)
    a = np.c_[-L * uu, c + to, c - ti, w]
    d = np.abs(np.diff(a, axis=0)).max(1)
    s = np.r_[0.0, np.cumsum(d)]
    k = max(2, int(s[-1] / ds) + 1)
    return np.interp(np.linspace(0, s[-1], k), s, uu)


class ArmSurf:
    def __init__(self, vid, u0=0.0, u1=0.5, ds=0.04):
        self.vid = vid; self.u0, self.u1, self.ds = u0, u1, ds
        us = u_grid(vid, max(u0, 1e-7), min(u1, 1 - 1e-7), ds)
        P, U, TH = [], [], []
        for u in us:
            c, ti, to, w, _, _ = VA.section(vid, u)
            per = 2 * (float(ti) + float(to)) + 4 * float(w)
            n = max(64, int(per / ds) + 1)
            th = np.linspace(-np.pi, np.pi, n, endpoint=False)
            P.append(surf_pt(vid, np.full(n, u), th)); U.append(np.full(n, u)); TH.append(th)
        self.P = np.concatenate(P); self.U = np.concatenate(U); self.TH = np.concatenate(TH)
        self.cover = np.cos(self.TH) >= 0          # cover side = outer half (x >= seam)
        self.tc = cKDTree(self.P[self.cover]); self.ti = cKDTree(self.P[~self.cover])
        self.ic = np.nonzero(self.cover)[0]; self.ii = np.nonzero(~self.cover)[0]

    def inside(self, P):
        return np.asarray(VA.inside_local(self.vid, np.atleast_2d(P), 0.0), bool)

    def dist(self, P, side, dmax=4.0, band=0.6):
        """distance to the cover / inner skin: coarse cloud (0.3) for all points, the fine cloud only for the points within
        `band` of the coarse minimum (the coarse cloud over-estimates by < 0.25), so the minimum is exact to the fine spacing"""
        if not hasattr(self, "coarse"):
            self.coarse = ArmSurf(self.vid, self.u0, self.u1, 0.3) if self.ds < 0.3 else None
        P = np.atleast_2d(P)
        tr, idx = (self.tc, self.ic) if side == "cover" else (self.ti, self.ii)
        if self.coarse is None:
            d, k = tr.query(P, workers=3, distance_upper_bound=dmax)
        else:
            C = self.coarse
            ctr = C.tc if side == "cover" else C.ti
            d, _ = ctr.query(P, workers=3, distance_upper_bound=dmax + 0.3)
            d = np.minimum(d, dmax)
            k = np.zeros(len(P), int)
            m = (d <= d.min() + band) & (d < dmax - 0.05)
            df, kf = tr.query(P[m], workers=3, distance_upper_bound=dmax)
            d[m] = df; k[m] = np.where(np.isfinite(df), kf, 0)
        far = ~np.isfinite(d) | (d >= dmax)
        k = np.where(far, 0, k)
        return np.where(far, dmax, d), idx[k]

    def refine(self, p, side, k0):
        """exact distance from local point p to the analytic surface half (cover / inner), started at sample k0"""
        u0, t0 = self.U[k0], self.TH[k0]
        lo, hi = ((-np.pi / 2, np.pi / 2) if side == "cover" else (np.pi / 2, 3 * np.pi / 2))
        if side != "cover" and t0 < 0:
            t0 += 2 * np.pi

        def f(v):
            u = min(max(v[0], 1e-7), 1 - 1e-7); t = min(max(v[1], lo), hi)
            return float(np.sum((surf_pt(self.vid, u, t) - p) ** 2))
        best = None
        for du, dt in ((0, 0), (1e-3, 1e-2)):
            r = minimize(f, [u0 + du, t0 + dt], method="Nelder-Mead", options=dict(xatol=1e-8, fatol=1e-10, maxiter=800))
            if best is None or r.fun < best.fun:
                best = r
        u = min(max(best.x[0], 1e-7), 1 - 1e-7); t = min(max(best.x[1], lo), hi)
        return math.sqrt(best.fun), (u, t), surf_pt(self.vid, u, t)

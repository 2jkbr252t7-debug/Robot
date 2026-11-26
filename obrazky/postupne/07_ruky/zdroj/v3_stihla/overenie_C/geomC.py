"""overenie_C/geomC.py - INDEPENDENT numeric model of shape variant C (verifier's own code, not variants.py).

Built from first principles:
  * approved T3 profile (hw, ht) = T3/shape.arm_profile(u) and the approved placement (armgeo.to_world with kt 1, dx -1)
  * the variant-C section as described in the brief / variants.py docstring:
        seam c(u) = -(1-ki) H(u), inner half (x<c): |(x-c)/ti|^ni + |y/w|^ni <= 1, outer half: same with to, no
        ti = ki ht, to = ko ht, w = kw hw, H = ht in [u1,u2], smoothstep-blended to ht(u1) (top) / hb ht(u2) (bottom)
  * a dense surface cloud from an ADAPTIVE (u, theta) parametrisation (row spacing <= 0.04 mm in every section quantity
    and in z, theta spacing <= ~0.03 mm), KD-tree nearest distance, sign from the analytic inside test.
Pure numpy + scipy (CAD venv)."""
import sys, math
sys.dont_write_bytecode = True
import numpy as np

sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T3")
sys.path.insert(0, "/home/user/Robot/obrazky/postupne/07_ruky/zdroj/geometria")
import shape as S          # approved T3 profile
import armgeo as AG        # approved placement (kt 1 => A_LOC of the approved arm), swing

L = 72.0
P_C = dict(ki=0.63, ko=0.46, kw=0.85, ni=2.2, no=2.3, u1=0.03, u2=0.50, hb=1.4, utip=0.84)
P_0 = dict(ki=1.0, ko=1.0, kw=1.0, ni=2.3, no=2.3, u1=0.04, u2=0.50, hb=1.0, utip=0.86)
DX = -1.0


def base(u):
    hw, ht = S.arm_profile(np.asarray(u, float))
    return np.asarray(hw, float), np.asarray(ht, float)


def sstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


class Shape:
    def __init__(self, p):
        self.p = p
        self.h1 = float(base(p["u1"])[1]); self.h2 = float(base(p["u2"])[1])

    def sec(self, u):
        p = self.p
        u = np.asarray(u, float)
        hw, ht = base(u)
        bt = sstep((p["u1"] - u) / p["u1"]); bb = sstep((u - p["u2"]) / (1 - p["u2"]))
        H = ht * (1 - bt) * (1 - bb) + self.h1 * bt + p["hb"] * self.h2 * bb
        c = -(1 - p["ki"]) * H
        return c, p["ki"] * ht, p["ko"] * ht, p["kw"] * hw

    def inside(self, P, inset=0.0):
        P = np.atleast_2d(P)
        u = -P[:, 2] / L
        ok = (u > 0) & (u < 1)
        c, ti, to, w = self.sec(np.clip(u, 1e-9, 1 - 1e-9))
        ti = np.maximum(ti - inset, 1e-9); to = np.maximum(to - inset, 1e-9); w = np.maximum(w - inset, 1e-9)
        dx = P[:, 0] - c
        f_o = (np.abs(dx) / to) ** self.p["no"] + (np.abs(P[:, 1]) / w) ** self.p["no"]
        f_i = (np.abs(dx) / ti) ** self.p["ni"] + (np.abs(P[:, 1]) / w) ** self.p["ni"]
        return ok & (np.where(dx >= 0, f_o, f_i) < 1)

    def ring(self, u, th):
        """surface points of the section at u for polar angles th about the seam point (outer half for cos >= 0)"""
        c, ti, to, w = (float(v) for v in self.sec(u))
        cs, sn = np.cos(th), np.sin(th)
        def r(t, n):
            return ((np.abs(cs) / t) ** n + (np.abs(sn) / w) ** n) ** (-1 / n)
        rr = np.where(cs >= 0, r(to, self.p["no"]), r(ti, self.p["ni"]))
        return np.c_[c + rr * cs, rr * sn, np.full(len(th), -L * u)]

    def u_samples(self, umin=0.0, umax=1.0, ds=0.04):
        """adaptive u stations: every section quantity and z change by <= ds between rows"""
        us = [max(umin, 1e-7)]
        u = us[0]
        while u < umax:
            du = ds / L
            for _ in range(60):
                a = np.array(self.sec(u)); b = np.array(self.sec(min(u + du, umax)))
                if np.abs(b - a).max() <= ds:
                    break
                du *= 0.5
            u = min(u + du, umax)
            us.append(u)
        return np.array(us)

    def cloud(self, umin=0.0, umax=1.0, ds=0.04, dth=0.03):
        us = self.u_samples(umin, umax, ds)
        out = []
        for u in us:
            c, ti, to, w = (float(v) for v in self.sec(u))
            per = 2 * (ti + to) + 4 * w
            n = max(16, int(per / dth))
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            out.append(self.ring(u, th))
        if umin <= 1e-6:
            c0 = float(self.sec(0.0)[0]); out.append(np.array([[c0, 0.0, 0.0]]))
        return np.concatenate(out)


SHAPE_C = Shape(P_C)
SHAPE_0 = Shape(P_0)


def to_world(P, dx=DX):
    return AG.to_world(P, 1.0, dx)


def to_local(Q, dx=DX):
    return AG.to_local(Q, 1.0, dx)


def swing(Q, deg):
    return AG.swing(Q, deg)


class SDF:
    """signed distance (neg. inside) to a shape's surface, split into the OUTER cover side (x >= seam) and the inner side.
    Two stages: a coarse cloud (0.2 / 0.15 mm) for every point, then the dense cloud (ds / dth) only for points whose coarse
    distance is < REFINE, with a search radius just above the coarse value (exact to about 0.002 mm)."""
    REFINE = 3.0

    def __init__(self, shp, umin, umax, ds=0.04, dth=0.03):
        from scipy.spatial import cKDTree
        self.shp = shp
        self.trees = {}
        for lvl, (a, b) in (("c", (0.2, 0.15)), ("f", (ds, dth))):
            C = shp.cloud(umin, umax, a, b)
            u = np.clip(-C[:, 2] / L, 0, 1)
            side = C[:, 0] >= shp.sec(u)[0] - 1e-9
            self.trees[lvl] = dict(all=cKDTree(C), out=cKDTree(C[side]), inn=cKDTree(C[~side]))
            if lvl == "f":
                self.C = C
        self.n = len(self.C)

    def query(self, P, which="all", dmax=4.0):
        P = np.atleast_2d(P)
        d, _ = self.trees["c"][which].query(P, distance_upper_bound=dmax, workers=3)
        d = np.minimum(d, dmax)
        k = d < self.REFINE
        if k.any():
            df, _ = self.trees["f"][which].query(P[k], distance_upper_bound=float(d[k].max()) + 0.01, workers=3)
            d[k] = np.minimum(d[k], df)
        ins = self.shp.inside(P)
        return np.where(ins, d, -d), ins       # wall depth: + inside (distance to that surface), - outside


if __name__ == "__main__":
    # cross-check against the designer's module (read only) on random points + placement
    sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R3/tvar")
    import variants as V
    rng = np.random.default_rng(1)
    P = np.c_[rng.uniform(-14, 10, 400000), rng.uniform(-16, 16, 400000), rng.uniform(-73, 1, 400000)]
    for vid, shp in (("C", SHAPE_C), ("0", SHAPE_0)):
        a = shp.inside(P); b = V.inside_local(vid, P, 0.0)
        print(vid, "inside mismatches", int((a != b).sum()), "of", len(P), " inside frac", a.mean().round(4))
        us = np.linspace(0, 1, 2001)
        s1 = np.array(shp.sec(us)); c2, ti2, to2, w2, _, _ = V.section(vid, us)
        print(vid, "section max dev", float(np.abs(s1 - np.array([c2, ti2, to2, w2])).max()))
    Q = rng.uniform(-20, 20, (1000, 3))
    print("placement dev", float(np.abs(to_world(Q) - V.to_world(Q, "C", -1.0)).max()))
    # key numbers
    for u in (0.0, 0.03, 0.05, 0.1, 0.18, 0.22, 0.3, 0.5, 0.84, 1.0):
        c, ti, to, w = (float(v) for v in SHAPE_C.sec(u))
        print(f"u {u:.2f}  seam {c:6.2f}  inner face {c-ti:7.2f}  outer face {c+to:6.2f}  thick {ti+to:5.2f}  width {2*w:5.2f}")
    us = np.linspace(0, 1, 20001); c, ti, to, w = SHAPE_C.sec(us)
    k = int(np.argmax(ti + to)); print("max thickness", round(float((ti + to)[k]), 3), "at u", us[k], " max width", round(float(2 * w.max()), 3))

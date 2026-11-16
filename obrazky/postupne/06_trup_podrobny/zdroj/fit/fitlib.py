"""numeric fit-study helpers: pack primitives -> surface sample points (B frame), shell inner surface distance field"""
import sys, json, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T3")
import shape as S
DZ = 129.0      # z_B = z_world - 129

def _box_pts(size, h=1.0):
    sx, sy, sz = size
    def lin(L):
        n = max(2, int(np.ceil(L / h)) + 1); return np.linspace(-L / 2, L / 2, n)
    X, Y, Z = lin(sx), lin(sy), lin(sz)
    P = []
    for x in (-sx / 2, sx / 2):
        yy, zz = np.meshgrid(Y, Z); P.append(np.stack([np.full(yy.size, x), yy.ravel(), zz.ravel()], 1))
    for y in (-sy / 2, sy / 2):
        xx, zz = np.meshgrid(X, Z); P.append(np.stack([xx.ravel(), np.full(xx.size, y), zz.ravel()], 1))
    for z in (-sz / 2, sz / 2):
        xx, yy = np.meshgrid(X, Y); P.append(np.stack([xx.ravel(), yy.ravel(), np.full(xx.size, z)], 1))
    return np.concatenate(P)

def _cyl_pts(r, hh, axis, h=1.0, ri=None):
    n = max(24, int(2 * np.pi * r / h)); th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    zs = np.linspace(-hh / 2, hh / 2, max(2, int(np.ceil(hh / h)) + 1))
    P = [np.stack([r * np.cos(t), r * np.sin(t), np.full(n, z)], 1) for z in zs for t in [th]]
    rs = np.linspace(ri or 0.0, r, max(2, int(np.ceil((r - (ri or 0)) / h)) + 1))
    for z in (-hh / 2, hh / 2):
        for rr in rs:
            P.append(np.stack([rr * np.cos(th), rr * np.sin(th), np.full(n, z)], 1))
    P = np.concatenate(P)
    if axis == "x":
        P = P[:, [2, 1, 0]]
    elif axis == "y":
        P = P[:, [0, 2, 1]]
    return P

def _inside(c, P):
    at = np.array(c.get("at", (0, 0, 0)), float); Q = P - at
    k = c["kind"]
    if k == "box":
        s = np.array(c["size"]) / 2
        return (np.abs(Q) < s - 1e-6).all(1)
    if k in ("cyl", "tube"):
        ax = "xyz".index(c.get("axis", "z")); o = [i for i in range(3) if i != ax]
        rr = np.hypot(Q[:, o[0]], Q[:, o[1]])
        m = (rr < c["r"] - 1e-6) & (np.abs(Q[:, ax]) < c["h"] / 2 - 1e-6)
        if k == "tube":
            m &= rr > c["ri"] + 1e-6
        return m
    return np.zeros(len(P), bool)

def prim_pts(c, h=1.0):
    k = c["kind"]
    if k == "box":
        P = _box_pts(c["size"], h)
    elif k in ("cyl", "tube"):
        P = _cyl_pts(c["r"], c["h"], c.get("axis", "z"), h, c.get("ri"))
    elif k in ("sblock", "sshell"):
        th = np.linspace(0, 2 * np.pi, 240, endpoint=False)
        r = S.se_r(c["a"], c["b"], c.get("n", 2.6), th)
        zs = np.linspace(-c["h"] / 2, c["h"] / 2, max(2, int(c["h"] / h) + 1))
        P = np.concatenate([np.stack([r * np.cos(th), r * np.sin(th), np.full(240, z)], 1) for z in zs])
    else:
        raise ValueError(k)
    assert not c.get("rot"), c
    return P + np.array(c.get("at", (0, 0, 0)), float)

def comp_pts(c, h=1.0):
    """surface sample points of a layout comp (adds unioned, points inside cuts removed), B frame"""
    P = [prim_pts(c, h)] + [prim_pts(a, h) for a in c.get("adds", [])]
    P = np.concatenate(P)
    for cu in c.get("cuts", []):
        P = P[~_inside(cu, P)]
    P = P.copy(); P[:, 2] -= DZ
    return P

def rotz(P, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    Q = P.copy(); Q[:, 0] = c * P[:, 0] - s * P[:, 1]; Q[:, 1] = s * P[:, 0] + c * P[:, 1]
    return Q

class Shell:
    """inner surface of the T3 shell at `inset` as a point cloud with outward normals; signed clearance of points"""
    def __init__(self, inset=2.2, ds=0.35, count=900, section=None):
        sec = section or S.section
        ss = S.stations(0.0, S.S_END, ds=ds)
        R = np.array([sec(s, inset, count) for s in ss])           # (K, N, 3)
        self.R = R
        dth = np.roll(R, -1, 1) - np.roll(R, 1, 1)
        ds_ = np.gradient(R, axis=0)
        n = np.cross(dth, ds_); n /= np.linalg.norm(n, axis=2, keepdims=True) + 1e-12
        c = R.copy(); c[..., 2] = 0
        sgn = np.sign((n[..., :2] * c[..., :2]).sum(-1) + 1e-9 * 0)
        # make normals point outward (away from the axis in xy, or by z at caps)
        flip = (n[..., 0] * R[..., 0] + n[..., 1] * R[..., 1]) < 0
        n[flip] *= -1
        self.P = R.reshape(-1, 3); self.Nn = n.reshape(-1, 3)
        self.tree = cKDTree(self.P)
        # radial table: z -> (a, b, n) of the inset section (for the fast pre-filter)
        zz = R[:, 0, 2]; a = np.abs(R[:, :, 0]).max(1); b = np.abs(R[:, :, 1]).max(1)
        nn = np.array([S.prof(s)[3] for s in ss]); k = np.argsort(zz)
        self.tab = (zz[k], a[k], b[k], nn[k]); self.zlim = (zz.min() + 5.0, zz.max() - 5.0)
    def radial_gap(self, Q):
        z, a, b, n = self.tab
        ai, bi, ni = np.interp(Q[:, 2], z, a), np.interp(Q[:, 2], z, b), np.interp(Q[:, 2], z, n)
        f = (np.abs(Q[:, 0]) / ai) ** ni + (np.abs(Q[:, 1]) / bi) ** ni
        r = np.hypot(Q[:, 0], Q[:, 1])
        return r * (np.maximum(f, 1e-9) ** (-1.0 / ni) - 1.0)
    def clearance(self, Q, far=6.0):
        """signed distance from points Q to the inner surface: + inside the cavity (points with a radial gap > far and
        well away from the top / bottom are returned with the radial gap - exact value not needed there)"""
        g = self.radial_gap(Q)
        out = np.where(g > far, g, 0.0)
        m = ~((g > far) & (Q[:, 2] > self.zlim[0]) & (Q[:, 2] < self.zlim[1]))
        idx = np.zeros(len(Q), int)
        if m.any():
            d, i = self.tree.query(Q[m], distance_upper_bound=40.0)
            i = np.minimum(i, len(self.P) - 1)
            s = ((self.P[i] - Q[m]) * self.Nn[i]).sum(1)
            out[m] = np.where(s >= 0, d, -d); idx[m] = i
        return out, idx

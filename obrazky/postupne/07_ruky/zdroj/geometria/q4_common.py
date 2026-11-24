WALL = 2.0
CASES = {"S1": (19.9, 8.8, 21.0, 4.7), "S2": (23.2, 12.2, 22.7, 5.9), "S3": (23.0, 12.0, 24.0, 6.0), "S4": (20.2, 8.5, 15.5, 4.5)}   # L, W, H, shaft from end
X_END, X_CUT = 58.756, 50.9
DV = R @ np.array([0, 0, -1.0]); DYZ = np.array([0.0, DV[1], DV[2]]); DYZ /= np.linalg.norm(DYZ)     # arm direction projected on y-z
FYZ = np.array([0.0, -DYZ[2], DYZ[1]])        # perpendicular in y-z: +FYZ = ... check sign below
if FYZ[1] > 0: FYZ = -FYZ                      # make FYZ point forward (-Y)
AXP = np.array([0.0, SH_Y, ZS])


def box_surface(o, eL, eW, eH, L_, W_, H_, s, h=0.5):
    """surface samples of the case: shaft point o on the shaft face (h = 0), length from -s .. L-s along eL, width +-W/2,
    height 0 .. H along eH.  returns points, mask of the shaft face (h = 0)"""
    ls = np.linspace(-s, L_ - s, max(2, int(L_ / h) + 1)); ws = np.linspace(-W_ / 2, W_ / 2, max(2, int(W_ / h) + 1))
    hs = np.linspace(0, H_, max(2, int(H_ / h) + 1))
    P, F = [], []
    def add(A, B, C, face0=False):
        G = np.stack(np.meshgrid(A, B, C, indexing="ij"), -1).reshape(-1, 3)
        P.append(o + G[:, 0, None] * eL + G[:, 1, None] * eW + G[:, 2, None] * eH); F.append(np.full(len(G), face0))
    add(ls, ws, [0.0], True); add(ls, ws, [H_])
    add(ls, [-W_ / 2, W_ / 2], hs); add([-s, L_ - s], ws, hs)
    return np.concatenate(P), np.concatenate(F)


def klb_profile_r(x, cut=None):
    """outer radius of T_klb at x (analytic, from the STL planes); 0 = no material"""
    x = np.asarray(x, float); r = np.zeros_like(x)
    r = np.where((x >= 38.6) & (x <= 40.6), 11.0, r)
    r = np.where((x > 40.6) & (x <= 50.156), 13.5, r)
    r = np.where((x > 50.156) & (x <= 50.956), 13.5 - (x - 50.156), r)
    r = np.where((x > 50.956) & (x <= 51.556), 11.4, r)
    r = np.where((x > 51.556) & (x <= 57.956), 11.0, r)
    r = np.where((x > 57.956) & (x <= X_END), 11.0 - (x - 57.956), r)
    if cut is not None:
        r = np.where(x > cut, 0.0, r)
    return r


def klb_clear(P, cut=None):
    """approx. clearance of points to T_klb (radial or axial, whichever smaller; negative = inside)"""
    x = P[:, 0]; rr = np.hypot(P[:, 1] - SH_Y, P[:, 2] - ZS)
    xe = X_END if cut is None else cut
    rad = rr - klb_profile_r(x, cut)
    ins = (rad < 0) & (x <= xe)
    ax = x - xe
    out = np.where(ins, -np.minimum(-rad, xe - x), np.where(x > xe, np.where(rr < 11.0, ax, np.hypot(np.maximum(ax, 0), np.maximum(rr - 11.0, 0))), rad))
    return out


def margin(P, F, kt=1.0, dx=0.0, skip_face=True):
    sd = sdf_world(P, kt, dx=dx, dmax=30.0)
    m = ~F if skip_face else np.ones(len(P), bool)
    depth = -sd[m] - WALL                 # >= 0: inside with a full wall
    pin = sd[F].max() if F.any() else np.nan     # > 0: shaft face sticks out of the pebble skin
    return float(depth.min()), float(pin), P[m][depth.argmin()]


def need(fun, lo, hi, tol=0.02):
    """smallest p in [lo, hi] with fun(p) >= 0 (monotone assumed); None if fun(hi) < 0"""
    if fun(lo) >= 0: return lo
    if fun(hi) < 0: return None
    while hi - lo > tol:
        m = 0.5 * (lo + hi)
        lo, hi = (lo, m) if fun(m) >= 0 else (m, hi)
    return hi


ORI = {"down": DYZ, "up": -DYZ, "fwd": FYZ, "back": -FYZ}

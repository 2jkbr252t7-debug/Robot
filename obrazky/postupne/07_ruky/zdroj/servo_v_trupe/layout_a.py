"""LAYOUT (a) - servo STATIC in the torso, output shaft ON the shoulder axis (direct drive), arm = passive shell on the
servo output (+ a bearing).  Question: with the case pushed as far INWARD as the pan / lift sweep allows (1.0 clearance to
PAN_ENV2), how far does it still stick out of the torso, and how far must the approved arm move outward so that its swept volume
(-45..+135 about the shoulder axis) clears the static case housing (case + 1.2 resin wall on the sides and the output face) by 0.5?
Case model: L along the long side, shaft s from one end (on the width centre line), W across, Hc along the shaft; orientation
phi = direction of the long side (from the shaft toward the far end) in the y-z plane, measured from +Y toward +Z.
Also: radius of the case corners about the axis (-> new opening in the side cap T_bok, socket today r 14.0) and the column
material that the case removes.  Writes layout_a.json."""
import sys, os, json, math
sys.dont_write_bytecode = True
import numpy as np
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/R1/geo")
sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4")
import armgeo as G  # noqa: E402
import t4_common as C  # noqa: E402
HERE = os.path.dirname(os.path.abspath(__file__))
AXY, AXZ = 3.0, -17.0
ENV = [(-47.20, -41.90, 17.50), (-41.90, -40.90, 26.50), (-40.90, -17.00, 33.40), (-17.00, -11.50, 32.20), (-11.50, 4.00, 26.50)]
SECT = [((-47.20, -39.90), 31.60), ((-41.90, -40.90), 33.40)]     # stop lug / lift-module bottom sectors (any azimuth here)


def r_env(z):
    r = 0.0
    for z0, z1, rr in ENV:
        if z0 - 1.0 <= z <= z1 + 1.0:          # 1.0 clearance also vertically: take the worse band within +-1
            r = max(r, rr)
    for (z0, z1), rr in SECT:
        if z0 - 1.0 <= z <= z1 + 1.0:
            r = max(r, rr)
    return r


def case_frame(phi):
    e = np.array([math.cos(math.radians(phi)), math.sin(math.radians(phi))])      # (y, z) long direction
    f = np.array([-e[1], e[0]])
    return e, f


def footprint(L, W, s, phi, n=40, grow=0.0):
    e, f = case_frame(phi)
    a = np.linspace(-s - grow, L - s + grow, n); b = np.linspace(-W / 2 - grow, W / 2 + grow, max(8, n // 2))
    A, B = np.meshgrid(a, b, indexing="ij")
    yz = np.stack([AXY + A * e[0] + B * f[0], AXZ + A * e[1] + B * f[1]], -1).reshape(-1, 2)
    return yz


def x_in_min(L, W, s, phi, clear=1.0):
    yz = footprint(L, W, s, phi)
    xm = 0.0
    for y, z in yz:
        rr = r_env(z) + clear
        if abs(y) < rr:
            xm = max(xm, math.sqrt(rr ** 2 - y ** 2))
    return xm


def housing_pts(L, W, Hc, s, phi, x_in, wall=1.2, h=0.6):
    """surface points of the case + wall (sides and output face; the inner end is open toward the column) for x >= 44"""
    e, f = case_frame(phi)
    a0, a1 = -s - wall, L - s + wall; b0, b1 = -W / 2 - wall, W / 2 + wall; x0, x1 = x_in, x_in + Hc + wall
    P = []
    xs = np.arange(max(x0, 44.0), x1 + 1e-9, h)
    for a in np.arange(a0, a1 + 1e-9, h):
        for b in (b0, b1):
            for x in xs:
                P.append((x, a, b))
    for b in np.arange(b0, b1 + 1e-9, h):
        for a in (a0, a1):
            for x in xs:
                P.append((x, a, b))
    for a in np.arange(a0, a1 + 1e-9, h):
        for b in np.arange(b0, b1 + 1e-9, h):
            P.append((x1, a, b))
    P = np.array(P)
    Q = np.empty_like(P)
    Q[:, 0] = P[:, 0]
    Q[:, 1] = AXY + P[:, 1] * e[0] + P[:, 2] * f[0]
    Q[:, 2] = AXZ + P[:, 1] * e[1] + P[:, 2] * f[1]
    return Q


ANG = np.arange(-45.0, 135.01, 7.5)


def arm_clear(Q, dx):
    best = 1e9
    for a in ANG:
        d = G.sdf_world(G.swing(Q, -a), dx=dx, dmax=6.0)
        best = min(best, float(d.min()))
    return best


def need_dx(Q, gap=0.5):
    lo, hi = 0.0, 30.0
    if arm_clear(Q, lo) >= gap:
        return 0.0
    for _ in range(11):
        mid = 0.5 * (lo + hi)
        if arm_clear(Q, mid) >= gap:
            hi = mid
        else:
            lo = mid
    return round(hi, 2)


SERVOS = {
    "SCS0009, case 21.5 (if 25.25 incl. shaft)": dict(L=23.2, W=12.1, Hc=21.5, s=5.9, out=3.75),
    "SCS0009, case 25.25": dict(L=23.2, W=12.1, Hc=25.25, s=5.9, out=3.35),
    "MG90S (case 22.7, spline top 28.4)": dict(L=22.8, W=12.2, Hc=22.7, s=5.9, out=5.7),
    "STS3032 (case 23.0 + boss 3.5 + spline 3.5)": dict(L=23.5, W=12.5, Hc=23.0, s=5.9, out=7.0),
    "KST X06 (20 x 7 x 16.6, shaft ~5)": dict(L=20.0, W=7.0, Hc=16.6, s=5.0, out=4.0),
}
X_SH = C.X_SH
res = {}
for name, S in SERVOS.items():
    rows = []
    for phi in ((0.0, 90.0, 180.0) if name.startswith("SCS0009, case 21.5") else (0.0,)):
        xi = x_in_min(S["L"], S["W"], S["s"], phi)
        Q = housing_pts(S["L"], S["W"], S["Hc"], S["s"], phi, xi)
        dx = need_dx(Q)
        e, f = case_frame(phi)
        corners = [np.hypot(a, b) for a in (-S["s"], S["L"] - S["s"]) for b in (-S["W"] / 2, S["W"] / 2)]
        rows.append(dict(phi=float(phi), x_in=round(xi, 2), case_out_face=round(xi + S["Hc"], 2), spline_top=round(xi + S["Hc"] + S["out"], 2),
                         beyond_shell_mm=round(xi + S["Hc"] - X_SH, 2), corner_r=round(max(corners), 2), corner_r_housing=round(max(corners) + 1.7, 2),
                         arm_shift_needed=dx))
        print(name, rows[-1])
    best = min(rows, key=lambda r: (r["arm_shift_needed"], r["x_in"]))
    res[name] = dict(best=best, all=rows)
json.dump(dict(method=__doc__, x_surface_on_axis=round(X_SH, 3), results=res), open(os.path.join(HERE, "layout_a.json"), "w"), indent=1)
print("done")

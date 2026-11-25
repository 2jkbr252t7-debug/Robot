"""K3 drive geometry (LEFT side, frame B; right = mirror x -> -x).  Pure numpy point clouds of every new part, grouped:
  ROT_V  : rotates with the vertical drive (coupler, vertical shaft, pinion)          -> must clear static + pan/lift sweep
  ROT_A  : rotates with the arm drive (gear, drive shaft, clutch parts in the arm)    -> idem
  BRG    : bearings (outer race static, inner race rotating) - treated as static solids
  SERVO  : SCS0009 standing, shaft up on the vertical drive axis
  STAT   : new static printed parts (inner boss + B1 housing tongue, plug / ring = new T_klb)
All numbers in mm.  Nothing in T4 / T3 / B is written."""
import math
import numpy as np

# ---------------------------------------------------------------- axes
YA, ZA = 3.0, -17.0                 # shoulder (arm) axis: line || X through (y 3, z -17)
XV = 39.0                           # vertical drive axis: line || Z through (x 39, y 3) -> apex O = (39, 3, -17)
# ---------------------------------------------------------------- bevel pair (straight, m0.5, 20 deg, Sigma 90)
M = 0.5; Z1, Z2 = 16, 24            # pinion (vertical) / gear (arm shaft); ratio 1.5
F = 2.4                             # face width
r1, r2 = M * Z1 / 2, M * Z2 / 2     # pitch radii 4.0 / 6.0
d1 = math.atan2(Z1, Z2); d2 = math.pi / 2 - d1
RE = math.hypot(r1, r2)             # outer cone distance 7.211
HA, HF = 1.0 * M, 1.25 * M
# ---------------------------------------------------------------- servo SCS0009 (case UNVERIFIED height 21.5; ears UNVERIFIED)
SV = dict(L=23.2, W=12.1, H=21.5, sh=5.9, theta=270.0, z_top=-45.0, ear_span=32.3, ear_t=2.5, ear_below_top=(4.3, 6.8),
          boss=(3.5, 1.0), spline=(2.0, 3.75))
# ---------------------------------------------------------------- shafts / bearings / coupler
D_VS = 3.0                          # vertical shaft
D_AS = 4.0                          # arm drive shaft
B1 = dict(d=3.0, D=6.0, B=2.5, z=(-26.35, -23.85))          # MR63ZZ under the pinion (outer race on a shoulder below)
HUB1 = None                         # hubless pinion bonded on the shaft; 0.4 shim between its back face and the B1 inner race
BOSS = dict(r_in=8.3, r_out=12.8, x=(34.4, 38.4), stop=(11.6, 12.8, 38.4, 39.1))   # inner boss (T_spodok) about the arm axis
TONGUE = dict(r_in=3.0, r_out=4.4, z=(-26.85, -24.05))     # B1 housing ring about the vertical axis (part of the boss)
A1 = dict(d=4.0, D=7.0, B=2.5, x=(44.55, 47.05))            # MR74ZZ in the plug, outboard of the gear
A2 = dict(d=4.0, D=7.0, B=2.5, x=(48.55, 51.05))            # MR74ZZ in the ring
ARMBRG = dict(d=10.0, D=15.0, B=4.0, x=(54.0, 58.0))        # 6700ZZ: arm hub on the ring end (inside the arm, dx 0)
COUPLER = dict(r=4.0, z=(SV["z_top"] + SV["boss"][1], SV["z_top"] + SV["boss"][1] + 7.0))
X_SURF = 46.756                     # torso outer surface on the shoulder axis
RING = dict(r=6.5, x0=X_SURF - 0.3, x1=53.5, seat_r=5.0, seat_x=(53.5, 58.0))
PLUG = dict(neck=(11.0, 38.6, 40.6), body=(13.5, 40.6), cav_r=6.8, cav_x=44.55, slot_y=5.0, recess=1.0)
SHAFT_END = 61.5


def _rev(profile, axis, centre, n_th=96, step=0.25):
    """surface + filled points of a solid of revolution; profile = list of (a, r) along the axis (a = axial coord),
    closed polygon in the (a, r) half plane; axis 'x' or 'z'; centre = (c1, c2) of the axis line"""
    P = np.asarray(profile, float)
    a0, a1 = P[:, 0].min(), P[:, 0].max(); rmax = P[:, 1].max()
    A, R = np.meshgrid(np.arange(a0, a1 + 1e-9, step), np.arange(0.0, rmax + 1e-9, step), indexing="ij")
    from matplotlib_path_free import inside_poly
    ok = inside_poly(np.c_[A.ravel(), R.ravel()], P)
    pts = np.c_[A.ravel()[ok], R.ravel()[ok]]
    # boundary samples
    B = []
    for i in range(len(P)):
        p, q = P[i], P[(i + 1) % len(P)]
        k = max(2, int(np.hypot(*(q - p)) / (step * 0.5)))
        t = np.linspace(0, 1, k, endpoint=False)
        B.append(p + t[:, None] * (q - p))
    pts = np.concatenate([pts, np.concatenate(B)])
    out = []
    for a, r in pts:
        k = max(1, int(2 * math.pi * r / (step * 1.2))) if r > 1e-6 else 1
        th = np.linspace(0, 2 * math.pi, min(k, n_th * 4), endpoint=False)
        c, s = r * np.cos(th), r * np.sin(th)
        if axis == "x":
            out.append(np.c_[np.full_like(th, a), centre[0] + c, centre[1] + s])
        else:
            out.append(np.c_[centre[0] + c, centre[1] + s, np.full_like(th, a)])
    return np.concatenate(out)


def cyl(axis, centre, r_in, r_out, a0, a1, step=0.25):
    return _rev([(a0, r_in), (a1, r_in), (a1, r_out), (a0, r_out)], axis, centre, step=step)


def pinion_profile():
    """(z, r) outline of the pinion envelope: toe tip -> heel crown -> heel root/back -> hub -> bore"""
    zh = ZA - r2                                   # heel pitch circle height (-23)
    crown = (zh + HA * math.sin(d1), r1 + HA * math.cos(d1))
    root = (zh - HF * math.sin(d1), r1 - HF * math.cos(d1))
    k = (RE - F) / RE
    toe_p = (ZA - k * r2, k * r1)
    toe_tip = (toe_p[0] + k * HA * math.sin(d1), toe_p[1] + k * HA * math.cos(d1))
    if HUB1 is None:
        return [(toe_tip[0], D_VS / 2), (toe_tip[0], toe_tip[1]), crown, (root[0], crown[1]), (root[0], D_VS / 2)]
    return [(toe_tip[0], D_VS / 2), (toe_tip[0], toe_tip[1]), crown, (root[0], crown[1]), (root[0], HUB1[0]),
            (HUB1[1], HUB1[0]), (HUB1[1], D_VS / 2)]


def gear_profile():
    """(x, r) outline of the arm gear envelope (teeth face -X toward the apex)"""
    xh = XV + r1                                   # heel pitch plane (43.0)
    crown = (xh - HA * math.sin(d2), r2 + HA * math.cos(d2))
    root = (xh + HF * math.sin(d2), r2 - HF * math.cos(d2))
    k = (RE - F) / RE
    toe_p = (XV + k * r1, k * r2)
    toe_tip = (toe_p[0] - k * HA * math.sin(d2), toe_p[1] + k * HA * math.cos(d2))
    back = root[0] + 0.5                          # 0.5 web behind the heel root
    return [(toe_tip[0], D_AS / 2), (toe_tip[0], toe_tip[1]), crown, (root[0], crown[1]), (root[0], root[1]),
            (back, root[1]), (back, D_AS / 2)]


def servo_points(step=0.5, ears=True):
    s = SV; c, sn = math.cos(math.radians(s["theta"])), math.sin(math.radians(s["theta"]))
    import itertools
    xs = np.arange(-s["sh"], s["L"] - s["sh"] + 1e-6, step); ys = np.arange(-s["W"] / 2, s["W"] / 2 + 1e-6, step)
    zs = np.arange(-s["H"], 1e-6, step)
    G = np.array(list(itertools.product(xs, ys, zs)))
    on = (np.isclose(G[:, 0], xs[0]) | np.isclose(G[:, 0], xs[-1]) | np.isclose(G[:, 1], ys[0]) | np.isclose(G[:, 1], ys[-1]) |
          np.isclose(G[:, 2], zs[0]) | np.isclose(G[:, 2], zs[-1]))
    P = [G[on]]
    if ears:
        e = (s["ear_span"] - s["L"]) / 2
        ex = np.arange(-s["sh"] - e, s["L"] - s["sh"] + e + 1e-6, step)
        ez = np.arange(-s["ear_below_top"][1], -s["ear_below_top"][0] + 1e-6, step)
        E = np.array(list(itertools.product(ex, ys, ez))); P.append(E[(E[:, 0] < -s["sh"]) | (E[:, 0] > s["L"] - s["sh"])])
    import itertools as it
    cx = np.arange(s["L"] - s["sh"], s["L"] - s["sh"] + 3.0 + 1e-6, step); cy = np.arange(-2.0, 2.0 + 1e-6, step)
    cz = np.arange(-s["H"], -s["H"] + 3.0 + 1e-6, step)
    P.append(np.array(list(it.product(cx, cy, cz))))
    P = np.concatenate(P)
    Q = np.c_[XV + c * P[:, 0] - sn * P[:, 1], YA + sn * P[:, 0] + c * P[:, 1], s["z_top"] + P[:, 2]]
    zt = s["z_top"]
    Q = np.concatenate([Q, cyl("z", (XV, YA), 0, s["boss"][0], zt, zt + s["boss"][1], step=0.3)])
    return Q


def parts():
    zt = SV["z_top"]
    out = {}
    out["ROT_V:coupler"] = cyl("z", (XV, YA), 0.0, COUPLER["r"], *COUPLER["z"])
    out["ROT_V:shaft_v"] = cyl("z", (XV, YA), 0.0, D_VS / 2, COUPLER["z"][0] + 3.0, pinion_profile()[0][0])
    out["ROT_V:pinion"] = _rev(pinion_profile(), "z", (XV, YA))
    out["ROT_A:gear"] = _rev(gear_profile(), "x", (YA, ZA))
    out["ROT_A:shaft_a"] = cyl("x", (YA, ZA), 0.0, D_AS / 2, gear_profile()[0][0], SHAFT_END)
    out["BRG:B1"] = cyl("z", (XV, YA), B1["d"] / 2, B1["D"] / 2, *B1["z"])
    out["BRG:A1"] = cyl("x", (YA, ZA), A1["d"] / 2, A1["D"] / 2, *A1["x"])
    out["BRG:A2"] = cyl("x", (YA, ZA), A2["d"] / 2, A2["D"] / 2, *A2["x"])
    out["SERVO"] = servo_points()
    b = BOSS
    out["STAT:boss"] = np.concatenate([cyl("x", (YA, ZA), b["r_in"], b["r_out"], *b["x"]),
                                       cyl("x", (YA, ZA), b["stop"][0], b["stop"][1], b["stop"][2], b["stop"][3])])
    out["STAT:tongue"] = cyl("z", (XV, YA), TONGUE["r_in"], TONGUE["r_out"], *TONGUE["z"])
    return out


if __name__ == "__main__":
    print("bevel: d1 %.2f deg  RE %.3f  pinion profile" % (math.degrees(d1), RE), [tuple(round(v, 2) for v in p) for p in pinion_profile()])
    print("gear profile", [tuple(round(v, 2) for v in p) for p in gear_profile()])
    P = parts()
    for k, v in P.items():
        print("%-16s n %7d  bbox %s" % (k, len(v), np.round(np.r_[v.min(0), v.max(0)], 2)))


def plug_ring_points(step=0.3):
    """black plug (new T_klb) + ring + 6700, LEFT side, for drawing / arm checks.  Plug face = approved outer surface - recess."""
    import sys
    sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4"); sys.path.insert(0, "/tmp/claude-0/gapwf/fin/T4/overenie3")
    import t4_common as C
    p = PLUG; pts = []
    for x in np.arange(p["neck"][1], 48.6, step):
        for r in np.arange(0.0, p["body"][0] + 1e-6, step):
            k = max(1, int(2 * math.pi * r / step)); th = np.linspace(0, 2 * math.pi, k, endpoint=False)
            Y = YA + r * np.cos(th); Z = ZA + r * np.sin(th)
            rmax = p["neck"][0] if x < p["neck"][2] else p["body"][0]
            if r > rmax: continue
            ok = np.ones_like(th, bool)
            # cavity: gear chamber + pinion slot + bores
            if x < p["cav_x"] and r < p["cav_r"]: ok[:] = False
            slot = (np.abs(Y - YA) <= p["slot_y"]) & (Z < ZA) & (x < 44.0)
            ok &= ~slot
            if x >= p["cav_x"] and r < A1["D"] / 2 and x <= A1["x"][1]: ok[:] = False
            if r < 2.3: ok[:] = False
            xs = np.array([C.x_surface(y, z) for y, z in zip(Y[ok], Z[ok])]) - p["recess"]
            Q = np.c_[np.full(ok.sum(), x), Y[ok], Z[ok]]
            Q = Q[Q[:, 0] <= xs]
            if len(Q): pts.append(Q)
    plug = np.concatenate(pts)
    ring = np.concatenate([cyl("x", (YA, ZA), A2["D"] / 2, RING["r"], X_SURF - 2.0, RING["x1"]),
                           cyl("x", (YA, ZA), 2.3, RING["seat_r"], *RING["seat_x"])])
    ring = ring[~((ring[:, 0] >= A2["x"][0]) & (ring[:, 0] <= A2["x"][1]) & (np.hypot(ring[:, 1] - YA, ring[:, 2] - ZA) < A2["D"] / 2))]
    b67 = cyl("x", (YA, ZA), ARMBRG["d"] / 2, ARMBRG["D"] / 2, *ARMBRG["x"])
    return dict(plug=plug, ring=ring, brg6700=b67)

#!/opt/venv/cad/bin/python
"""NOVA mini - T4 torso, module RAM: chassis + J1 + electronics + dummy base hub.

    /opt/venv/cad/bin/python t4_ram.py            build (printed parts cached by source hash), export, parts_ram.json
    /opt/venv/cad/bin/python t4_ram.py --rebuild  ignore the cache
    /opt/venv/cad/bin/python t4_ram.py --noexport build + table only

Frame / numbers: t4_common.py (B frame, rest pose).  RAM-specific numbers: t4_common.RAM ("additions by ram").
Registry: build() -> dict[name] = dict(shape, group, mat, printed, label_sk, ...)   (t4_common.part)

Printed parts   T_spodok (black resin)   bottom cap = base plate: floor, clearance pocket, spigot, tub, pads, plinth with
                                         the 6805 seat, pinion notch, skirt, stop lug, J1 FPC slot, drain holes
                T_ram (PETG)             cradle, bumper, cap / deck bosses, pan-servo posts, controller standoffs,
                                         two shoulder columns with boss, stop ring, spigot, key slot, board standoffs
                T_paluba (PETG)          deck: pivot boss, stop groove, FPC channel wall, FPC slot
                T_prichytka_fpc (PETG)   clamp of the static pan-FPC end
                Z_naboj_test (PETG)      dummy base hub / bench stand
Bought parts    servos, gears, bearing, pin, washer, boards, capacitor, foam, screws, inserts (datasheet solids).
"""
from __future__ import annotations
import os, sys, math, time, json, hashlib, inspect

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np                                    # noqa: E402
import t4_common as C                                 # noqa: E402
import build123d as bd                                # noqa: E402
from build123d import Vector                          # noqa: E402

R = C.RAM
ZF = C.Z_FLOOR                    # -82.3 top of the cap floor
ZD0, ZD1 = C.Z_DECK               # -47.8 / -46.0
YI, YO = 12.55, C.CRADLE["y"][1]  # cradle wall inner / outer face (|y|)
X0 = C.CRADLE["x"][0]             # -31.6
X1 = R["CRADLE_X1"]               # 25.8
XE = -30.0                        # inner face of the -X end wall
SHY, SHZ = C.SH_Y, C.SH_Z
TIMES = {}


# =====================================================================================================================
# helpers
# =====================================================================================================================
def one(s):
    """single Solid of a boolean result (largest solid)"""
    sol = list(s.solids()) if hasattr(s, "solids") else [q for x in s for q in x.solids()]
    return sol[0] if len(sol) == 1 else max(sol, key=lambda q: q.volume)


def fuse(shapes):
    shapes = [s for s in shapes if s is not None]
    return shapes[0] if len(shapes) == 1 else shapes[0].fuse(*shapes[1:])


def cut(base, cutters):
    cutters = [c for c in cutters if c is not None]
    return base.cut(*cutters) if cutters else base


def prism_x(pts_yz, x0, x1):
    w = bd.Wire.make_polygon([Vector(x0, y, z) for y, z in pts_yz], close=True)
    return bd.extrude(bd.Face(w), amount=x1 - x0, dir=(1, 0, 0))


def prism_y(pts_xz, y0, y1):
    w = bd.Wire.make_polygon([Vector(x, y0, z) for x, z in pts_xz], close=True)
    return bd.extrude(bd.Face(w), amount=y1 - y0, dir=(0, 1, 0))


def prism_z(pts_xy, z0, z1):
    w = bd.Wire.make_polygon([Vector(x, y, z0) for x, y in pts_xy], close=True)
    return bd.extrude(bd.Face(w), amount=z1 - z0, dir=(0, 0, 1))


def pol(r, az_deg, cx=0.0, cy=0.0):
    a = math.radians(az_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def wedge_z(r, a0, a1, z0, z1, cx=0.0, cy=0.0):
    """pie wedge (covers the arc of radius r) between the azimuths a0 < a1 (deg)"""
    n = max(2, int(math.ceil((a1 - a0) / 15.0)) + 1)
    step = (a1 - a0) / (n - 1)
    rr = r / math.cos(math.radians(step / 2)) * 1.02
    pts = [(cx, cy)] + [pol(rr, a0 + i * step, cx, cy) for i in range(n)]
    return prism_z(pts, z0, z1)


def tube_sector(ro, ri, a0, a1, z0, z1, cx=0.0, cy=0.0):
    t = C.cyl_z(ro, z0, z1, cx, cy) - C.cyl_z(ri, z0 - 0.5, z1 + 0.5, cx, cy)
    return one(t & wedge_z(ro, a0, a1, z0 - 1, z1 + 1, cx, cy))


def cyl_ax(r, a, b, p, q, axis):
    """cylinder along `axis` from a to b; (p, q) = the other two coordinates in the order of t4_common.cyl_*"""
    return {"x": C.cyl_x, "y": C.cyl_y, "z": C.cyl_z}[axis](r, a, b, p, q)


def hole(d, at, axis, sign, depth, lead=0.15):
    """plain cylindrical cutter: from `at` along axis*sign for `depth`, with a small lead on the open side"""
    k = "xyz".index(axis)
    a, b = at[k] - sign * lead, at[k] + sign * depth
    o = [at[i] for i in range(3) if i != k]
    return cyl_ax(d / 2, min(a, b), max(a, b), o[0], o[1], axis)


def insert_seat(size, at, axis, sign, deeper=0.3, pilot=0.6, mat="petg"):
    """cutter for an insert: seat (hole d for heat-set in PETG / glued in resin) + short pilot for the screw tip"""
    do, ln, dr, dp = C.INSERTS[size]
    dh = dp if mat == "petg" else dr
    c = [hole(dh, at, axis, sign, ln + deeper)]
    if pilot > 0:
        c.append(hole(C.SCREWS[size][1], at, axis, sign, ln + deeper + pilot, lead=0.0))
    return fuse(c)


def screw_cyl(d, dk, k, length, at, axis, sign):
    """cylinder-head / pan-head screw: head seat at `at`, shank along axis*sign"""
    s = bd.Pos(0, 0, -k / 2) * bd.Cylinder(dk / 2, k) + bd.Pos(0, 0, length / 2) * bd.Cylinder(d / 2, length)
    return one(bd.Pos(*at) * C._along(s, axis, sign))


def gear_profile(m, z, phase_deg=0.0, backlash=0.04, n_inv=7):
    """2-D involute spur gear outline (20 deg), tooth k centred at phase + k * 360 / z"""
    rp = m * z / 2; rb = rp * math.cos(math.radians(20.0)); ra = rp + m; rf = rp - 1.25 * m
    s = math.pi * m / 2 - backlash
    ap = math.radians(20.0)

    def inv(a):
        return math.tan(a) - a

    def half(r):
        return s / (2 * rp) + inv(ap) - inv(math.acos(min(1.0, rb / r)))
    r0 = max(rb, rf)
    rs = [r0 + (ra - r0) * i / (n_inv - 1) for i in range(n_inv)]
    pitch = 2 * math.pi / z
    out = []
    for k in range(z):
        c = math.radians(phase_deg) + k * pitch
        if rf < rb:
            out.append((rf, c - half(r0)))
        out += [(r, c - half(r)) for r in rs] + [(r, c + half(r)) for r in reversed(rs)]
        if rf < rb:
            out.append((rf, c + half(r0)))
        out.append((rf, c + pitch / 2))
    return [(r * math.cos(a), r * math.sin(a)) for r, a in out]


def gear_solid(m, z, z0, z1, cx, cy, phase_deg, backlash=0.04):
    pts = gear_profile(m, z, phase_deg, backlash)
    return prism_z([(cx + x, cy + y) for x, y in pts], z0, z1)


def timed(name):
    def deco(fn):
        def wrap(*a, **k):
            t = time.time(); r = fn(*a, **k); TIMES[name] = round(time.time() - t, 1)
            return r
        wrap.__wrapped__ = fn
        return wrap
    return deco


# =====================================================================================================================
# BOUGHT PARTS (datasheet solids; every solid = real size, seats carry the tolerance)
# =====================================================================================================================
def mk_servo_J1():
    """Feetech STS3215: case 45.2 x 24.7 x 35.0 (+-0.3), boss D12 x 2.6, spline 25T D5.9; shaft DOWN at J1_AX.
    The block at the +X end is the reserved zone of the two 5264 plugs and their cable bend."""
    S = C.STS3215
    case = C.box(*S["x"], *S["y"], *C.Z_J1)
    boss = C.cyl_z(S["boss_r"], C.Z_J1_BOSS[0], C.Z_J1_BOSS[1] + 0.5, *C.J1_AX)
    shaft = C.cyl_z(S["spline_d"] / 2, R["J1_SPLINE_Z"][0], C.Z_J1_BOSS[0] + 0.5, *C.J1_AX)
    P = S["plug"]
    plug = C.box(P["x"][0] - 0.5, P["x"][1], P["y"][0], P["y"][1], C.Z_J1[1] - P["dz"], C.Z_J1[1])
    return one(fuse([case, boss, shaft, plug]))


def mk_pastorok_J1():
    """brass spur gear m1 18T (da 20, d 18), face 3.2, hub D10 x 0.9 towards the servo, 25T female spline 2.2 deep,
    M3 countersunk from below (flush).  A tooth GAP faces the torso axis (+X)."""
    x, y = C.J1_AX
    g = gear_solid(C.M_J1, C.T_J1, C.Z_J1_GEAR[0], C.Z_J1_GEAR[1], x, y, 10.0)
    hub = C.cyl_z(5.0, C.Z_J1_HUB[0] - 0.3, C.Z_J1_HUB[1], x, y)
    body = one(fuse([g, hub]))
    spl = C.cyl_z(C.STS3215["spline_d"] / 2, R["J1_SPLINE_Z"][0], C.Z_J1_HUB[1] + 0.2, x, y)
    csk = C.screw_hole("M3c", 2.2, (x, y, C.Z_J1_GEAR[0]), "z", 1, head_len=0.3)
    return one(cut(body, [spl, csk]))


def mk_koleso_J1():
    """sun gear of the dummy hub: brass m1 18T, face 3.2, tapped M8 (screwed and bonded on the M8 core)"""
    g = gear_solid(C.M_J1, C.T_J1, C.Z_J1_GEAR[0], C.Z_J1_GEAR[1], 0.0, 0.0, 0.0)
    return one(g - C.cyl_z(4.0, C.Z_J1_GEAR[0] - 0.5, C.Z_J1_GEAR[1] + 0.5))


def mk_lozisko():
    d, D, B = C.BRG_6805
    return one(C.cyl_z(D / 2, *C.Z_BRG) - C.cyl_z(d / 2, C.Z_BRG[0] - 0.5, C.Z_BRG[1] + 0.5))


def mk_servo_pan():
    """Feetech STS3032: case 23.5 x 12.5 x 23.0, tabs 32.5 x 12.5 x 2.5 (holes D2.2 at 28.0), boss D12.4 x 3.5,
    output shaft D4 x 3.5 (in the pinion), plug zone 7 x 8 x 8 at the +X end.  Shaft UP at PAN_AX."""
    S = C.STS3032
    case = C.box(*S["x"], *S["y"], *S["z"])
    T = S["tab"]
    tabs = C.box(T["x"][0], T["x"][1], S["y"][0], S["y"][1], *T["z"])
    boss = C.cyl_z(S["boss_r"], S["boss_z"][0] - 0.5, S["boss_z"][1], *C.PAN_AX)
    sh = R["PAN_PINION"]
    shaft = C.cyl_z(sh["bore_d"] / 2, sh["shaft_z"][0] - 0.5, sh["shaft_z"][1], *C.PAN_AX)
    P = S["plug"]
    plug = C.box(P["x"][0] - 0.5, P["x"][1], *P["y"], *P["z"])
    s = one(fuse([case, tabs, boss, shaft, plug]))
    yh = C.PAN_AX[1]
    return one(cut(s, [C.cyl_z(T["hole_d"] / 2, T["z"][0] - 0.5, T["z"][1] + 0.5, hx, yh) for hx in T["hole_x"]]))


def mk_pastorok_pan():
    """spur gear m0.8 18T (da 16.0, d 14.4), face 3.2, hub D8 x 2.2 below, bore D4, M2 countersunk from above (flush).
    A tooth GAP faces the pan axis (azimuth 74.3 deg seen from PAN_AX)."""
    x, y = C.PAN_AX
    to_axis = math.degrees(math.atan2(-y, -x))
    g = gear_solid(C.M_PAN, C.T_PAN[0], C.Z_PAN_PINION[0], C.Z_PAN_PINION[1], x, y, to_axis + 10.0)
    hub = C.cyl_z(C.STS3032["hub_r"], C.STS3032["hub_z"][0], C.STS3032["hub_z"][1] + 0.3, x, y)
    sh = R["PAN_PINION"]
    bore = C.cyl_z(sh["bore_d"] / 2, sh["shaft_z"][0] - 0.2, sh["shaft_z"][1], x, y)
    csk = C.screw_hole("M2c", 2.2, (x, y, C.Z_PAN_PINION[1]), "z", -1, head_len=0.3)
    return one(cut(one(fuse([g, hub])), [bore, csk]))


def mk_cap_pan():
    """steel dowel D6 h6 x 6.5 (ISO 2338), pressed 3.5 into the deck"""
    return C.cyl_z(C.PIVOT["pin_d"] / 2, *C.PIVOT["pin_z"])


def mk_ptfe():
    """PTFE thrust washer 24 x 12.4 x 0.3"""
    return one(C.cyl_z(12.0, *C.Z_PTFE) - C.cyl_z(6.2, C.Z_PTFE[0] - 0.2, C.Z_PTFE[1] + 0.2))


def mk_riadenie():
    """carrier PCB 48 x 22 x 1.6 with the Waveshare ESP32-S3-Zero (23.5 x 18, USB-C towards -X) and connector blocks
    (indicative layout, all inside the reserved box CTRL)."""
    x0, x1 = C.CTRL["x"]; y0 = C.CTRL["y"][0]; z0, z1 = C.CTRL["z"]
    yf = y0 + C.CTRL["pcb"][2]                                   # +Y face of the carrier (17.1)
    M = R["CTRL_MODULE"]
    P = [C.box(x0, x1, y0, yf, z0, z1),
         C.box(M["x"][0], M["x"][1], yf - 0.1, yf + 1.0, M["z"][0], M["z"][1]),          # module PCB 1.0
         C.box(M["x"][0] + 4.0, M["x"][1] - 2.0, yf + 0.9, yf + 2.9, M["z"][0] + 2.5, M["z"][1] - 2.5),   # shield / parts
         C.box(x0, x0 + 7.3, yf + 0.9, yf + 4.2, M["usb"][2] - 4.5, M["usb"][2] + 4.5),  # USB-C receptacle 9 x 7.3 x 3.3
         C.box(-14.0, 15.0, yf - 0.1, yf + 2.95, z1 - 4.0, z1),                          # upper edge: JST-SH (pan FPC, LED, arm)
         C.box(3.0, x1, yf - 0.1, yf + 4.8, z0, -61.0)]                                  # GH 6p, PH 2p, 5264 3p, SH 3p field
    s = one(fuse(P))
    return one(cut(s, [C.cyl_y(1.1, y0 - 0.5, yf + 6.0, x, z) for x, z in R["F7"]["xz"]]))


def mk_menic():
    """Pololu D36V28F5 17.8 x 17.8 x 8.8 (0.7 x 0.7 x 0.35 in, Pololu drawing), on 1.0 standoffs of the right column web,
    components outward (-X).  The component block is an envelope; the two mounting-hole corners are free (screw heads)."""
    xa, xb = R["BUCK_X"]; (ya, yb), (za, zb) = C.BUCK["y"], C.BUCK["z"]
    P = [C.box(xb - 1.6, xb, ya, yb, za, zb), C.box(xa, xb - 1.5, ya + 2.0, yb - 2.0, za + 2.0, zb - 2.0)]
    s = one(fuse(P))
    N = [C.cyl_x(1.1, xb - 2.5, xb + 0.5, y, z) for y, z in BUCK_HOLES]              # 2 holes D2.18 (0.086 in), 0.53 in pattern
    N += [C.cyl_x(2.4, xa - 0.5, xb - 1.6, y, z) for y, z in BUCK_HOLES]             # the board is free of parts around them
    return one(cut(s, N))


def mk_zosilnovac():
    """Adafruit 3006 MAX98357A breakout 19.3 x 17.8 x 3.0, on 1.0 standoffs of the left column web"""
    xa, xb = R["AMP_X"]; (ya, yb), (za, zb) = C.AMP["y"], C.AMP["z"]
    P = [C.box(xa, xa + 1.6, ya, yb, za, zb), C.box(xa + 1.5, xb, ya + 3.0, yb - 3.0, za + 3.0, zb - 5.5)]
    s = one(fuse(P))
    return one(cut(s, [C.cyl_x(1.25, xa - 0.5, xa + 2.5, y, z) for y, z in AMP_HOLES]))


def mk_kondenzator():
    x, y, z = R["CAP470_AT"]
    return C.cyl_z(C.CAP470["d"] / 2, z - C.CAP470["h"] / 2, z + C.CAP470["h"] / 2, x, y)


# board hole patterns (y, z) on the column webs
BUCK_C = ((C.BUCK["y"][0] + C.BUCK["y"][1]) / 2, (C.BUCK["z"][0] + C.BUCK["z"][1]) / 2)
BUCK_HOLES = [(BUCK_C[0] - 6.73, BUCK_C[1] + 6.73), (BUCK_C[0] + 6.73, BUCK_C[1] - 6.73)]     # 0.53 in diagonal pattern
BUCK_RESTS = [(BUCK_C[0] + 6.73, BUCK_C[1] + 6.73), (BUCK_C[0] - 6.73, BUCK_C[1] - 6.73)]
AMP_C = ((C.AMP["y"][0] + C.AMP["y"][1]) / 2, (C.AMP["z"][0] + C.AMP["z"][1]) / 2)
AMP_HOLES = [(AMP_C[0] - 6.35, C.AMP["z"][1] - 2.54), (AMP_C[0] + 6.35, C.AMP["z"][1] - 2.54)]  # 0.5 in apart, 0.1 in from the edge
AMP_RESTS = [(AMP_C[0] - 6.35, C.AMP["z"][0] + 2.5), (AMP_C[0] + 6.35, C.AMP["z"][0] + 2.5)]
PAD_J1 = dict(x=(-26.9, 13.1), y=(-10.0, 10.0), z=(C.Z_J1[1], ZD0))                             # PORON 40 x 20 x 0.5
PAD_END = dict(x=(C.STS3215["x"][1], R["J1_BUMPER"]["x"][0]), y=(-10.0, 10.0), z=(-80.0, -71.0))  # PORON 1.0


# =====================================================================================================================
# T_spodok - black bottom cap / base plate
# =====================================================================================================================
def _slot_j1(r, z0, z1):
    """slot of the pinion passage: radius r about J1_AX, centres shifted +-J1_ADJ in x"""
    x, y = C.J1_AX; a = C.J1_ADJ
    return fuse([C.cyl_z(r, z0, z1, x - a, y), C.cyl_z(r, z0, z1, x + a, y), C.box(x - a, x + a, y - r, y + r, z0, z1)])


@timed("T_spodok")
def mk_spodok(verbose=True):
    def step(msg, t0):
        if verbose:
            print(f"    spodok: {msg} {time.time() - t0:.1f} s", flush=True)
    a, b, n = C.SPIGOT_SE
    zs0, zs1 = C.SPIGOT["z"]                                        # -81.5 .. -78.0
    # ---- spigot ring with a 0.6 lead-in at the top (ruled loft), fused into the cap body
    t = time.time()
    th = C.azimuths(96)
    ring_lo = C.se_prism(a, b, n, zs0 - 0.6, zs1 - 0.6)
    r1 = C.se_r(a, b, n, th); r2 = r1 - 0.6
    w1 = C._wire(np.stack([r1 * np.cos(th), r1 * np.sin(th), np.full(96, zs1 - 0.6)], 1))
    w2 = C._wire(np.stack([r2 * np.cos(th), r2 * np.sin(th), np.full(96, zs1)], 1))
    lead = bd.Solid.make_loft([w1, w2], True)
    cap = one(C.cap_blank().fuse(ring_lo, lead))
    step("cap + spigot", t)
    # ---- tub (floor top Z_FLOOR inside the spigot) and clearance pocket of the J1 servo
    t = time.time()
    tub = C.se_prism(*C.TUB_SE, ZF, zs1 + 0.5)
    Pk = R["POCKET_J1"]
    pocket = C.box(Pk["x"][0], Pk["x"][1], Pk["y"][0], Pk["y"][1], C.Z_J1[0], ZF + 0.2)
    cap = one(cap.cut(tub, pocket))
    step("- tub - pocket", t)
    # ---- pads under the 4 T_stred bosses (top z -81.0 = seat of T_stred) and spigot gaps above them
    t = time.time()
    lim = C.se_prism(a - 0.05, b - 0.05, n, ZF - 0.3, C.Z_WHITE)
    pads = [one(C.cyl_z(C.BOSS_STRED["r"], ZF - 0.3, C.Z_WHITE, x, y) & lim) for x, y in C.SCR_STRED]
    cap = one(cap.fuse(*pads))
    gaps = [C.box(min(sx * 25.0, sx * 33.0), max(sx * 25.0, sx * 33.0), min(sy * 14.0, sy * 32.0), max(sy * 14.0, sy * 32.0),
                  C.Z_WHITE, zs1 + 0.5) for sx in (1, -1) for sy in (1, -1)]
    cap = one(cap.cut(*gaps))
    step("+ pads - spigot gaps", t)
    # ---- everything under the cap: plinth (gear housing), bearing ring, skirt, stop lug  (analytic)
    t = time.time()
    zb0, zb1 = C.Z_BRG
    plinth = C.cyl_z(C.R_PLINTH, zb1, C.Z_BOT + 0.3) - C.cyl_z(C.R_FOOT_SHOULDER, zb1 - 0.5, C.Z_BOT)
    ring = C.cyl_z(C.R_FOOT_LOW, zb0, zb1 + 0.3) - C.cyl_z(C.R_FOOT_SEAT, zb0 - 0.5, zb1 + 0.5)
    ring = ring - bd.Pos(0, 0, zb0 + 0.2) * bd.Cone(C.R_FOOT_SEAT + 0.4, C.R_FOOT_SEAT, 0.4)      # entry chamfer 0.4
    skirt = C.cyl_z(C.SKIRT["r"], *C.SKIRT["z"]) - C.cyl_z(C.R_PLINTH - 0.6, C.SKIRT["z"][0] - 0.5, C.SKIRT["z"][1] + 0.5)
    ga = R["J1_PASS"]["skirt_gap_az"]                              # the skirt ends in radial faces beside the pinion passage (no feather tips)
    skirt = one(skirt - wedge_z(C.SKIRT["r"] + 2.0, ga[0], ga[1], C.SKIRT["z"][0] - 0.5, C.SKIRT["z"][1] + 0.5))
    L = C.J1_STOP_LUG
    lug = C.box(-L["w"] / 2, L["w"] / 2, L["r"][0], L["r"][1] + 1.0, L["z"][0], L["z"][1] + 0.3) & C.cyl_z(L["r"][1], L["z"][0] - 1, L["z"][1] + 1)
    under = one(fuse([plinth, ring, skirt, lug]))
    cap = one(cap.fuse(under))
    step("+ plinth, bearing ring, skirt, lug", t)
    # ---- one compound cutter: pinion passage, screw holes, FPC slot, drain holes
    #      passage = slot r 10.8 about J1_AX through plinth, skirt and floor: servo + pinion are mounted as ONE unit from above
    t = time.time()
    Pa = R["J1_PASS"]
    N = [_slot_j1(Pa["r"], Pa["z"][0], Pa["z"][1])]
    N += [C.screw_hole("M2.5c", 6.0, (x, y, R["F1"]["head_z"]), "z", 1, head_len=6.0) for x, y in C.SCR_STRED]
    N += [C.screw_hole("M2.5c", 6.0, (x, y, C.Z_BOT), "z", 1, head_len=3.0) for x, y in R["SCR_RAM"]]
    S = R["J1_FPC_SLOT"]
    N += [C.box(S["x"][0], S["x"][1], S["y"][0], S["y"][1], zb1 - 0.5, ZF + 0.5)]
    N += [C.cyl_z(1.5, C.Z_BOT - 0.5, ZF + 0.5, x, y) for x, y in C.DRAIN]
    cap = one(cap.cut(*N))
    step("- slot, screw holes, FPC slot, drains", t)
    return cap


# =====================================================================================================================
# T_ram - PETG chassis (one part)
# =====================================================================================================================
def _column(s):
    """shoulder column on side s (+1 = left, +X); returns (positive solids, cutters)"""
    def bx(xa, xb, ya, yb, za, zb):
        return C.box(min(s * xa, s * xb), max(s * xa, s * xb), ya, yb, za, zb)

    def cx(r, xa, xb, y=SHY, z=SHZ):
        return C.cyl_x(r, min(s * xa, s * xb), max(s * xa, s * xb), y, z)
    xi, xw = C.X_COL_IN, C.X_COL_IN + C.COL_WEB["t"]                # 34.4 / 36.4
    (wy0, wy1), (wz0, wz1), xr = C.COL_WEB["y"], C.COL_WEB["z"], C.COL_WEB["rib_x"]
    fx0, fx1 = R["COL_FOOT_X"]
    P, N = [], []
    P += [bx(fx0, fx1, *C.COL_FOOT["y"], ZF, wz0 + 0.2),                                     # foot in the tub
          C.cyl_z(3.0, ZF, -76.8, s * 35.5, 3.0),                                            # F2 insert boss
          bx(xi, xw, wy0, wy1, wz0, wz1), bx(xi, xw, SHY - 8.5, SHY + 8.5, wz1 - 0.2, -22.0)]  # web + neck
    for ya, yb in ((wy0, wy0 + 1.6), (wy1 - 1.6, wy1)):                                      # ribs, 45 deg run-out at the bottom
        rib = prism_y([(s * (xw - 0.2), wz0), (s * fx1, wz0), (s * xr, wz0 + (xr - fx1)), (s * xr, wz1), (s * (xw - 0.2), wz1)], ya, yb)
        P.append(rib)
    N += [insert_seat("M2.5", (s * 35.5, 3.0, ZF), "z", 1, pilot=0.2)]
    # ---- shoulder boss: disc r 11.6, backing flange + stop ring r 12.8, spigot D10, inserts, key slot
    Fl = R["COL_FLANGE"]
    boss = one(fuse([cx(C.R_COL_STOP[0], xi, Fl["x"][0] + 0.2), cx(Fl["r"], Fl["x"][0], C.X_COL_STOP)]))
    boss = one(boss.cut(cx(C.R_COL_STOP[0], C.X_COL_BOSS, C.X_COL_STOP + 0.5)))               # recess inside the stop ring
    boss = one(boss.fuse(cx(C.KLB_BUSH["spigot_d"] / 2, C.X_COL_BOSS - 0.3, C.KLB_BUSH["spigot_x"])))
    bc = [bx(C.X_COL_BOSS - 1.5, C.X_COL_STOP + 0.5, SHY + 5.3, SHY + 14.0, SHZ - 1.5, SHZ + 1.5)]   # key slot, azimuth 0
    for az in C.KLB_SCREWS["az"]:
        dy, dz = pol(C.KLB_SCREWS["pcd_r"], az)
        at = (s * C.X_COL_BOSS, SHY + dy, SHZ + dz)
        bc += [hole(C.INSERTS["M2"][3], at, "x", -s, 3.3), hole(2.2, at, "x", -s, 4.5, lead=0.0)]
    boss = one(boss.cut(*bc))
    P.append(boss)
    P.append(prism_y([(s * (xw - 0.1), -31.9), (s * C.X_COL_BOSS, -29.8), (s * C.X_COL_BOSS, -27.5), (s * (xw - 0.1), -27.5)],
                     SHY - 3.0, SHY + 3.0))                                                  # gusset under the flange
    N += [C.cyl_x(2.5, min(s * (xi - 0.3), s * (xw + 0.3)), max(s * (xi - 0.3), s * (xw + 0.3)), 9.0, -74.5)]   # wire hole D5
    so = R["BOARD_STANDOFF"]
    if s > 0:      # left: amplifier standoffs + rests, capacitor clip and saddle
        for (y, z) in AMP_HOLES + AMP_RESTS:
            P.append(C.cyl_x(2.2, xw - 0.2, xw + so, y, z))
        for (y, z) in AMP_HOLES:
            N.append(C.cyl_x(0.85, xi - 0.3, xw + so + 0.3, y, z))       # integrator: through the web (was blind, 0.5 floor)
        cxp, cyp, czp = R["CAP470_AT"]
        P.append(tube_sector(6.25, 5.05, 65.0, 295.0, -49.0, -41.0, cxp, cyp))
        N.append(C.cyl_z(5.05, czp - 6.8, czp + 6.8, cxp, cyp))
    else:          # right: buck standoffs + rests, tool hole of the J1 set screw
        for (y, z) in BUCK_HOLES + BUCK_RESTS:
            P.append(C.cyl_x(2.2, -(xw + so), -(xw - 0.2), y, z))
        for (y, z) in BUCK_HOLES:
            N.append(C.cyl_x(0.85, -(xw + so + 0.3), -(xi - 0.3), y, z))   # integrator: through the web (was blind, 0.5 floor)
    return P, N


@timed("T_ram")
def mk_ram():
    P, N = [], []
    # ---- cradle: two long walls, -X end wall, +X floor strip, bumper behind the foam pad
    P += [C.box(X0, X1, -YO, -YI, ZF, ZD0), C.box(X0, X1, YI, YO, ZF, ZD0), C.box(X0, XE, -YO, YO, ZF, ZD0)]
    P += [C.box(16.4, X1, -YO, YO, ZF, ZF + 2.0),
          C.box(R["J1_BUMPER"]["x"][0], R["J1_BUMPER"]["x"][1], -YI - 0.1, YI + 0.1, ZF, R["J1_BUMPER"]["z_top"])]
    # ---- cap bosses F2 (inserts from below)
    for x, y in R["SCR_RAM"][:4]:
        sy = 1 if y > 0 else -1
        P += [C.cyl_z(3.0, ZF, -77.3, x, y), C.box(x - 3.0, x + 3.0, min(sy * (YO - 0.2), y), max(sy * (YO - 0.2), y), ZF, -77.3)]
        N += [insert_seat("M2.5", (x, y, ZF), "z", 1, pilot=1.0)]      # integrator: through the boss top (was a 0.5 cap, K10 min feature 0.6)
    # ---- deck bosses F3 (inserts from the top) on 45 deg corbels
    for x, y in R["SCR_DECK"]:
        sy = 1 if y > 0 else -1
        body = one(fuse([C.cyl_z(2.9, -60.0, ZD0, x, y), C.box(x - 2.9, x + 2.9, min(sy * YI, y), max(sy * YI, y), -60.0, ZD0)]))
        keep = prism_x([(sy * 12.0, -58.0), (sy * 12.0, ZD0), (sy * (15.0 + ZD0 + 55.0), ZD0)], x - 3.5, x + 3.5)
        P.append(one(body & keep))
        N.append(hole(C.INSERTS["M2.5"][3], (x, y, ZD0), "z", -1, 4.5))
    # ---- pan-servo posts under the tabs (top z -58): right = column, left = C-frame around the plug zone
    Pp = R["PAN_POST"]; xa, xb = Pp["x"]; yt = C.PAN_AX[1]; zt = Pp["top"]
    P.append(prism_x([(-YO + 0.25, ZF), (-24.0, ZF), (-24.0, -77.5), (Pp["y_front"], -76.5), (Pp["y_front"], zt), (-YO + 0.25, zt)], -xb, -xa))
    yl = Pp["y_leg"][0]
    left = prism_x([(-YO + 0.25, ZF), (-24.0, ZF), (-24.0, -78.26), (yl, -78.26 + (-24.0 - yl)), (yl, zt), (-YO + 0.25, zt)], xa, xb)
    W = Pp["window"]
    P.append(one(left - C.box(xa - 0.5, xb + 0.5, W["y"][0], W["y"][1], W["z"][0], W["z"][1])))
    F4 = R["F4"]                                                   # M2x6 thread-forming: blind pilot (-X), through the shelf (+X)
    N += [hole(F4["pilot_d"], (-14.0, yt, zt), "z", -1, F4["pilot_depth"]), hole(F4["pilot_d"], (14.0, yt, zt), "z", -1, Pp["shelf"] + 0.3)]
    # ---- controller standoffs (M2 thread-forming from +Y) and rests
    yf = C.CTRL["y"][0]
    for x, z in R["F7"]["xz"]:
        P.append(C.cyl_y(2.5, YO - 0.2, yf, x, z)); N.append(hole(1.7, (x, yf, z), "y", -1, yf - YI + 0.3))
        # integrator: pilot THROUGH into the servo pocket (was blind 2.55 with a 0.4 floor, K10 min feature 0.6); the M2x4 screw
        # ends 0.55 short of the pocket face (PCB 1.6 + 2.4 of thread in 2.95 of plastic)
    for x, z in R["F7"]["rests"]:
        P.append(C.cyl_y(2.0, YO - 0.2, yf, x, z))
    # ---- columns, links, bridges
    for s in (1, -1):
        p, n = _column(s); P += p; N += n
    P += [C.box(X1 - 0.2, R["COL_FOOT_X"][0] + 0.2, *C.COL_FOOT["y"], ZF, ZF + 2.0),               # left foot link
          C.box(-C.X_COL_IN - 0.1, X0 + 0.1, *C.COL_FOOT["y"], ZF, -78.0)]                         # right foot link
    for sy in (1, -1):
        ya, yb = (YI, YO) if sy > 0 else (-YO, -YI)
        P += [C.box(X1 - 0.2, C.X_COL_IN + 0.1, ya, yb, -60.0, -50.0), C.box(-C.X_COL_IN - 0.1, X0 + 0.1, ya, yb, -60.0, -50.0)]
    # ---- J1 set screw F5: boss between the end wall and the right column, insert from the cradle side
    fx, fy, fz = R["F5"]["at"]
    xi5 = R["F5"]["insert_x"]                                      # insert mouth inside the right column web
    P.append(C.cyl_x(3.4, -C.X_COL_IN - 0.1, fx, fy, fz))
    N += [C.cyl_x(R["F5"]["tool_d"] / 2, -(C.X_COL_IN + C.COL_WEB["t"] + 0.3), xi5, fy, fz),                 # tool / iron hole
          hole(C.INSERTS["M2.5"][3], (xi5, fy, fz), "x", 1, 4.3, lead=0.05), C.cyl_x(1.4, xi5, fx + 0.2, fy, fz)]
    body = one(fuse(P))
    return one(cut(body, N)).clean()


# =====================================================================================================================
# T_paluba - deck, T_prichytka_fpc - FPC clamp
# =====================================================================================================================
@timed("T_paluba")
def mk_paluba():
    P = [C.box(-31.6, 31.6, -14.3, 15.3, ZD0, ZD1),
         one(C.cyl_z(C.FPC_PAN["wall"][1], ZD0, ZD1) & C.box(-19.9, 19.9, 0.0, 26.0, ZD0 - 1, ZD1 + 1))]
    for x, y in R["SCR_DECK"]:
        sy = 1 if y > 0 else -1
        P += [C.cyl_z(2.8, ZD0, ZD1, x, y), C.box(x - 2.8, x + 2.8, min(sy * 13.5, y), max(sy * 13.5, y), ZD0, ZD1)]
    Pv = C.PIVOT
    P.append(C.cyl_z(Pv["boss_r"], ZD1 - 0.2, Pv["boss_z"][1]))
    body = one(fuse(P))
    G = C.PAN_STOP
    N = [hole(2.8, (x, y, ZD1), "z", -1, 2.2) for x, y in R["SCR_DECK"]]
    N += [C.cyl_z(Pv["pin_d"] / 2 - 0.025, ZD0 - 0.3, Pv["boss_z"][1] + 0.3)]                 # press bore D5.95
    gz = ZD1 - G["groove_depth"]
    N += [tube_sector(G["r"] + G["groove_w"] / 2, G["r"] - G["groove_w"] / 2, G["az"][0], G["az"][1], gz, ZD1 + 0.3),
          C.cyl_z(G["groove_w"] / 2, gz, ZD1 + 0.3, G["r"], 0.0), C.cyl_z(G["groove_w"] / 2, gz, ZD1 + 0.3, -G["r"], 0.0)]
    # static FPC anchor: arc slot through the deck (tangent to the wall inner face) + pilot of the clamp screw;
    # primary side +X, mirrored spare on -X (see RAM["FPC_ANCHOR"])
    A = R["FPC_ANCHOR"]
    for m in (False, True):
        a0, a1 = A["slot_az"] if not m else (180.0 - A["slot_az"][1], 180.0 - A["slot_az"][0])
        N.append(tube_sector(A["slot_r"][1], A["slot_r"][0], a0, a1, ZD0 - 0.3, ZD1 + 0.3))
        cxp, cyp = pol(A["screw_r"], A["screw_az"] if not m else 180.0 - A["screw_az"])
        N.append(hole(A["pilot_d"], (cxp, cyp, ZD1), "z", -1, 2.2))
    body = one(cut(body, N))
    # FPC channel wall, added after the cuts: its inner face is the outer face of the arc slots
    wall = tube_sector(C.FPC_PAN["wall"][1], C.FPC_PAN["wall"][0], C.FPC_PAN["az"][0], C.FPC_PAN["az"][1], ZD1 - 0.2, C.FPC_PAN["z"][1])
    return one(body.fuse(wall)).clean()


def mk_prichytka():
    """clamp of the static FPC end: presses the strip against the wall inner face (gap 0.10 for the 0.12 FPC)"""
    A = R["FPC_ANCHOR"]
    blk = tube_sector(A["clamp_r"][1], A["clamp_r"][0], A["clamp_az"][0], A["clamp_az"][1], A["clamp_z"][0], A["clamp_z"][1])
    cxp, cyp = pol(A["screw_r"], A["screw_az"])
    return one(blk - C.screw_hole("M2c", 3.0, (cxp, cyp, A["clamp_z"][1]), "z", -1, head_len=0.3))


# =====================================================================================================================
# Z_naboj_test - dummy base hub (bench stand) + its bought parts
# =====================================================================================================================
@timed("Z_naboj_test")
def mk_naboj():
    D = R["DUMMY"]
    w, d = D["plate"]; z0, z1 = D["plate_z"]
    P = [C.rbox(-w / 2, w / 2, -d / 2, d / 2, z0, z1, 8.0, "z")]
    P += [C.cyl_z(6.0, D["feet_z"], z0 + 0.2, sx * 45.0, sy * 35.0) for sx in (1, -1) for sy in (1, -1)]
    P += [C.cyl_z(D["shoulder_r"], z1 - 0.2, C.Z_BRG[0]), C.cyl_z(D["post_r"], C.Z_BRG[0] - 0.2, C.Z_BRG[1]),
          C.cyl_z(D["stub"][0], C.Z_BRG[1] - 0.2, D["stub"][1])]
    St = D["stop"]
    P.append(tube_sector(St["r"][1], St["r"][0], St["az"] - St["half"], St["az"] + St["half"], z1 - 0.2, St["z_top"]))
    body = one(fuse(P))
    N = [C.cyl_z(4.1, z0 - 5, D["stub"][1] + 1), C.cyl_z(D["cbore_r"], D["feet_z"] - 1, D["seat_z"])]
    return one(cut(body, N)).clean()


def mk_skrutka_M8():
    """ISO 4017 M8 x 20 hex head (s 13, k 5.3): steel core of the dummy hub and shaft of the slip clutch"""
    D = R["DUMMY"]; zh = D["bolt_head_z"]
    hexa = prism_z([pol(13.0 / 2 / math.cos(math.radians(30)), 60 * i) for i in range(6)], zh - 5.3, zh)
    return one(fuse([hexa, C.cyl_z(4.0, zh - 0.2, C.Z_J1_GEAR[1])]))


def mk_pruzina(i):
    """disc spring DIN 2093 16 x 8.2 x 0.4 (modelled as a flat washer of the compressed height 0.6)"""
    D = R["DUMMY"]; z = D["bolt_head_z"] + 0.6 * i
    return one(C.cyl_z(8.0, z, z + 0.6) - C.cyl_z(4.1, z - 0.2, z + 0.8))


# =====================================================================================================================
# fasteners
# =====================================================================================================================
def fasteners():
    """dict name -> (solid, material, label, record) of every screw / insert of the RAM module"""
    F = {}

    def add(name, solid, mat, label, **rec):
        F[name] = (solid, mat, label, rec)
    for i, (x, y) in enumerate(C.SCR_STRED, 1):
        add(f"skr_F1_{i}", C.screw("M2.5c", 8, (x, y, R["F1"]["head_z"]), "z", 1), "steel", "skrutka M2,5x8 zápustná (spodok -> stred)",
            joint="F1", size="M2.5x8 csk", head=(x, y, R["F1"]["head_z"]), dir="+Z", tool_from="-Z")
    for i, (x, y) in enumerate(R["SCR_RAM"], 1):
        add(f"skr_F2_{i}", C.screw("M2.5c", 6, (x, y, C.Z_BOT), "z", 1), "steel", "skrutka M2,5x6 zápustná (spodok -> rám)",
            joint="F2", size="M2.5x6 csk", head=(x, y, C.Z_BOT), dir="+Z", tool_from="-Z")
        add(f"vl_F2_{i}", C.insert("M2.5", (x, y, ZF), "z", 1), "brass", "závitová vložka M2,5x4 (rám, zospodu)", joint="F2", at=(x, y, ZF))
    dk, k = R["F3"]["head"]
    for i, (x, y) in enumerate(R["SCR_DECK"], 1):
        add(f"skr_F3_{i}", screw_cyl(2.5, dk, k, 6, (x, y, ZD1), "z", -1), "steel", "skrutka M2,5x6 polguľatá (paluba -> rám)",
            joint="F3", size="M2.5x6 pan", head=(x, y, ZD1), dir="-Z", tool_from="+Z")
        add(f"vl_F3_{i}", C.insert("M2.5", (x, y, ZD0), "z", -1), "brass", "závitová vložka M2,5x4 (rám, zhora)", joint="F3", at=(x, y, ZD0))
    T = C.STS3032["tab"]; yt = C.PAN_AX[1]
    for i, x in enumerate(T["hole_x"], 1):
        add(f"skr_F4_{i}", screw_cyl(2.0, 3.8, 1.6, 6, (x, yt, T["z"][1]), "z", -1), "steel", "skrutka M2x6 do plastu (servo pan)",
            joint="F4", size="M2x6 thread-forming", head=(x, yt, T["z"][1]), dir="-Z", tool_from="+Z")
    fx, fy, fz = R["F5"]["at"]
    add("skr_F5", one(C.cyl_x(1.25, C.STS3215["x"][0] - 6.0, C.STS3215["x"][0], fy, fz)), "steel", "stavacia skrutka M2,5x6 (osová vzdialenosť J1)",
        joint="F5", size="M2.5x6 set", head=(C.STS3215["x"][0] - 6.0, fy, fz), dir="+X", tool_from="-X")
    add("vl_F5", C.insert("M2.5", (R["F5"]["insert_x"], fy, fz), "x", 1), "brass", "závitová vložka M2,5x4 (stavacia skrutka J1)", joint="F5",
        at=(R["F5"]["insert_x"], fy, fz))
    add("skr_F6", C.screw("M3c", 6, (*C.J1_AX, C.Z_J1_GEAR[0]), "z", 1), "steel", "skrutka M3x6 zápustná (pastorok J1)",
        joint="F6", size="M3x6 csk", head=(*C.J1_AX, C.Z_J1_GEAR[0]), dir="+Z", tool_from="-Z", bench=True)   # on the bench, before the servo goes in
    yf = C.CTRL["y"][0] + C.CTRL["pcb"][2]
    for i, (x, z) in enumerate(R["F7"]["xz"], 1):
        add(f"skr_F7_{i}", screw_cyl(2.0, 3.8, 1.4, 4, (x, yf, z), "y", -1), "steel", "skrutka M2x4 do plastu (riadiaca doska)",
            joint="F7", size="M2x4 thread-forming", head=(x, yf, z), dir="-Y", tool_from="+Y")
    xb = R["BUCK_X"][1] - 1.6
    for i, (y, z) in enumerate(BUCK_HOLES, 1):
        add(f"skr_F14_{i}", screw_cyl(2.0, 3.8, 1.4, 4, (xb, y, z), "x", 1), "steel", "skrutka M2x4 do plastu (menič)",
            joint="F14", size="M2x4 thread-forming", head=(xb, y, z), dir="+X", tool_from="-X")
    xa = R["AMP_X"][0] + 1.6
    for i, (y, z) in enumerate(AMP_HOLES, 3):
        add(f"skr_F14_{i}", screw_cyl(2.0, 3.8, 1.4, 4, (xa, y, z), "x", -1), "steel", "skrutka M2x4 do plastu (zosilňovač)",
            joint="F14", size="M2x4 thread-forming", head=(xa, y, z), dir="-X", tool_from="+X")
    Fc = R["FPC_ANCHOR"]; cxp, cyp = pol(Fc["screw_r"], Fc["screw_az"])
    add("skr_fpc", C.screw("M2c", 4, (cxp, cyp, Fc["clamp_z"][1]), "z", -1), "steel", "skrutka M2x4 zápustná do plastu (príchytka FPC)",
        joint="FPC", size="M2x4 csk thread-forming", head=(cxp, cyp, Fc["clamp_z"][1]), dir="-Z", tool_from="+Z")
    add("skr_pastorok_pan", C.screw("M2c", 5, (*C.PAN_AX, C.Z_PAN_PINION[1]), "z", -1), "steel", "skrutka M2x5 zápustná (pastorok pan)",
        joint="PAN", size="M2x5 csk", head=(*C.PAN_AX, C.Z_PAN_PINION[1]), dir="-Z", tool_from="+Z (through the collar bore)")
    for s, tag in ((1, "L"), (-1, "P")):
        for i, az in enumerate(C.KLB_SCREWS["az"], 1):
            dy, dz = pol(C.KLB_SCREWS["pcd_r"], az)
            at = (s * C.X_COL_BOSS, SHY + dy, SHZ + dz)
            add(f"vl_F8_{tag}{i}", C.insert("M2", at, "x", -s), "brass", "závitová vložka M2x3 (náboj ramena)", joint="F8", at=at)
    return F


# =====================================================================================================================
# registry
# =====================================================================================================================
PRINTED = {   # name: (builder, group, material, Slovak label)
    "T_spodok": (lambda: mk_spodok(), "T", "resin_black", "spodný kryt / základová doska s pätkou J1"),
    "T_ram": (lambda: mk_ram(), "T", "petg", "rám: kolíska serva J1, stĺpy ramien, stĺpiky serva pan"),
    "T_paluba": (lambda: mk_paluba(), "T", "petg", "paluba: čap pan, dorazová drážka, kanál FPC"),
    "T_prichytka_fpc": (lambda: mk_prichytka(), "T", "petg", "príchytka pevného konca FPC pan"),
    "Z_naboj_test": (lambda: mk_naboj(), "Z", "petg", "skúšobný náboj podstavca (stojan)"),
}
_SRC_FUNCS = {"T_spodok": [mk_spodok, _slot_j1], "T_ram": [mk_ram, _column], "T_paluba": [mk_paluba], "T_prichytka_fpc": [mk_prichytka],
              "Z_naboj_test": [mk_naboj]}


def _src_hash(name):
    src = "".join(inspect.getsource(getattr(f, "__wrapped__", f)) for f in _SRC_FUNCS[name])
    src += inspect.getsource(sys.modules[__name__]).split("# BOUGHT PARTS")[0]          # helpers
    src += json.dumps(R, sort_keys=True, default=str) + open(os.path.join(HERE, "t4_common.py")).read().split("# >>> additions by ram")[0]
    return hashlib.md5(src.encode()).hexdigest()[:10]


def printed_part(name, rebuild=False):
    fn = PRINTED[name][0]
    p = os.path.join(C.CACHE, f"ram_{name}_{_src_hash(name)}.brep")
    if os.path.exists(p) and not rebuild:
        TIMES[name] = 0.0
        return one(bd.import_brep(p))
    t = time.time(); s = fn(); TIMES[name] = round(time.time() - t, 1)
    for old in os.listdir(C.CACHE):
        if old.startswith(f"ram_{name}_") and old.endswith(".brep"):
            os.remove(os.path.join(C.CACHE, old))
    bd.export_brep(s, p)
    return s


def build(rebuild=False, verbose=False):
    """registry of the RAM module: dict[name] = t4_common.part(...)"""
    parts = {}
    for name, (fn, grp, mat, label) in PRINTED.items():
        s = printed_part(name, rebuild)
        parts[name] = C.part(s, grp, mat, True, label)
        if verbose:
            print(f"  built {name} ({TIMES.get(name, 0)} s)", flush=True)
    B = [  # name, builder, group, material, mass g (None = volume x density), label
        ("servo_J1", mk_servo_J1, "T", "bought", 55.0, "servo J1 Feetech STS3215 (hriadeľ dole)"),
        ("pastorok_J1", mk_pastorok_J1, "T", "brass", None, "pastorok J1 m1 z18, mosadz"),
        ("lozisko_6805", mk_lozisko, "T", "bought", 22.0, "ložisko 6805-2RS 25x37x7"),
        ("servo_pan", mk_servo_pan, "T", "bought", 21.0, "servo pan Feetech STS3032 (hriadeľ hore)"),
        ("pastorok_pan", mk_pastorok_pan, "T", "brass", None, "pastorok pan m0,8 z18"),
        ("cap_pan", mk_cap_pan, "T", "steel", None, "čap pan Ø6 h6 x 6,5 (oceľ)"),
        ("ptfe_podlozka", mk_ptfe, "T", "ptfe", None, "PTFE podložka 24 x 12,4 x 0,3"),
        ("DPS_riadenie", mk_riadenie, "T", "bought", 8.0, "riadiaca doska s ESP32-S3-Zero"),
        ("menic", mk_menic, "T", "bought", 2.5, "menič 5 V Pololu D36V28F5"),
        ("zosilnovac", mk_zosilnovac, "T", "bought", 1.5, "zosilňovač MAX98357A"),
        ("kondenzator", mk_kondenzator, "T", "bought", 1.8, "kondenzátor 470 µF / 10 V"),
        ("pena_J1", lambda: C.box(*PAD_J1["x"], *PAD_J1["y"], *PAD_J1["z"]), "T", "bought", 0.1, "penová podložka PORON 40x20x0,5 (nad servom J1)"),
        ("pena_J1_celo", lambda: C.box(*PAD_END["x"], *PAD_END["y"], *PAD_END["z"]), "T", "bought", 0.05, "penová podložka PORON 1,0 (čelo serva J1)"),
        ("Z_koleso_J1", mk_koleso_J1, "Z", "brass", None, "centrálne koleso J1 m1 z18, mosadz (závit M8)"),
        ("Z_skrutka_M8", mk_skrutka_M8, "Z", "steel", None, "skrutka M8x20 - oceľové jadro náboja a hriadeľ spojky"),
        ("Z_pruzina_1", lambda: mk_pruzina(0), "Z", "steel", None, "tanierová pružina 16x8,2x0,4"),
        ("Z_pruzina_2", lambda: mk_pruzina(1), "Z", "steel", None, "tanierová pružina 16x8,2x0,4"),
    ]
    for name, fn, grp, mat, mass, label in B:
        t = time.time(); s = fn(); TIMES[name] = round(time.time() - t, 2)
        extra = dict(mass=mass) if mass is not None else {}
        parts[name] = C.part(s, grp, mat, False, label, **extra)
    for name, (s, mat, label, rec) in fasteners().items():
        parts[name] = C.part(s, "T", mat, False, label, fastener=rec)
    return parts


# expected bounding boxes of the printed parts (x0, x1, y0, y1, z0, z1) - checked in main
def expected_bbox():
    a, b, _ = C.prof(C.TOP - C.Z_CAP_TOP)
    D = R["DUMMY"]
    return {
        "T_spodok": (-a, a, -b, b, C.J1_STOP_LUG["z"][0], C.SPIGOT["z"][1]),
        "T_ram": (-C.COL_WEB["rib_x"], R["CAP470_AT"][0] + 6.25 * math.cos(math.radians(65.0)), R["PAN_POST"]["y_leg"][0],
                  R["SCR_RAM"][0][1] + 3.0, ZF, SHZ + R["COL_FLANGE"]["r"]),
        "T_paluba": (-31.6, 31.6, -18.6, 25.1, ZD0, C.FPC_PAN["z"][1]),
        "Z_naboj_test": (-D["plate"][0] / 2, D["plate"][0] / 2, -D["plate"][1] / 2, D["plate"][1] / 2, D["feet_z"], D["stub"][1]),
    }


# dimension sources / tolerances of the bought parts (also written to parts_ram.json)
SOURCES = {
    "servo_J1": "Feetech STS3215: case 45.2 x 24.7 x 35.0 (+-0.3), boss D12 x 2.6, 25T spline D5.9 (listings: DFRobot, Mouser, Core Electronics). "
                "Spline length modelled 2.2 = depth available in the pinion - NOT a datasheet value, measure. Plug block 11.3 x 16 x 18 = reserved bend space.",
    "pastorok_J1": "catalogue brass spur gear m1 z18 (da 20.0, d 18.0), faced to 3.2 + hub D10 x 0.9, 25T bore 2.2 deep, M3 countersink; ISO 53 profile, backlash 0.04",
    "Z_koleso_J1": "catalogue brass spur gear m1 z18, face 3.2, tapped M8",
    "lozisko_6805": "6805-2RS, ISO 15: 25 x 37 x 7 (d 0/-0.010, D 0/-0.011); seat D37.00 +0.05/0, post D24.96",
    "servo_pan": "Feetech STS3032: case 23.5 x 12.5 x 23.0, tabs 32.5 x 2.5 at 16.2 above the bottom, holes D2.2 at 28.0, boss D12.4 x 3.5 "
                 "(listings, medium confidence, +-0.3 - verify on the purchased servo). Plug block 7 x 8 x 8 = reserved bend space.",
    "pastorok_pan": "spur gear m0.8 z18 (da 16.0, d 14.4), face 3.2, hub D8 x 2.2, bore D4 (POM or brass, catalogue)",
    "cap_pan": "dowel pin ISO 2338 D6 h6 x 6.5 (cut from x8 or x10), steel",
    "ptfe_podlozka": "PTFE sheet 0.3: washer 24 x 12.4, cut",
    "DPS_riadenie": "carrier PCB 48 x 22 x 1.6 (custom) + Waveshare ESP32-S3-Zero 23.5 x 18 (Waveshare drawing, +-0.2); connector blocks indicative",
    "menic": "Pololu D36V28F5: 17.8 x 17.8 x 8.8 (0.7 x 0.7 x 0.35 in), 2 holes D2.18 on a 0.53 in diagonal pattern (Pololu drawing)",
    "zosilnovac": "Adafruit 3006 MAX98357A: 19.3 x 17.8 x 3.0, 2 holes D2.5, 12.7 apart, 2.54 from the edge (Adafruit drawing); terminal block not fitted",
    "kondenzator": "radial electrolytic 470 uF / 10 V, envelope D10 x 13 (generic, D 8..10, L 11.5..13)",
    "pena_J1": "PORON 0.5 (0.3 / 0.5 / 0.8 selected to the measured servo height)", "pena_J1_celo": "PORON 1.0",
    "Z_skrutka_M8": "ISO 4017 M8 x 20, hex 13, k 5.3", "Z_pruzina_1": "DIN 2093 16 x 8.2 x 0.4", "Z_pruzina_2": "DIN 2093 16 x 8.2 x 0.4",
}
# assembly step (T4_spec section 11) and direction of every part of the module (for K7)
ASSEMBLY = {
    "lozisko_6805": (2, "+Z from below, CA in the seat"), "T_ram": (3, "-Z onto T_spodok, F2 from below"), "pastorok_J1": (4, "on the servo ON THE BENCH (F6), "
                    "then with the servo"), "servo_J1": (4, "-Z into the cradle, pinion through the passage r 10.8"), "pena_J1_celo": (4, "with the servo"),
    "servo_pan": (6, "-Z onto the posts, F4"), "pena_J1": (7, "on the servo"), "T_paluba": (7, "-Z, F3 (pin pressed, PTFE washer on the boss)"),
    "cap_pan": (7, "pressed into the deck on the bench"), "ptfe_podlozka": (7, "over the pivot boss"), "DPS_riadenie": (8, "-Y, F7"),
    "menic": (8, "+X onto the right column, F14"), "zosilnovac": (8, "-X onto the left column, F14"), "kondenzator": (8, "-Z into the clip"),
    "pastorok_pan": (11, "-Z through the collar bore, after T_stred"), "T_prichytka_fpc": (13, "-Z through the door / bore with the pan FPC"),
    "T_spodok": (2, "base plate"), "Z_naboj_test": (20, "bench stand, torso lowered onto it -Z"),
}
DEVIATIONS = [
    "F3 deck screws moved to (+-22.9, +-15.8) (spec (-22, +-15), (20, +-15)): insert hole clear of the 1.6 cradle wall, heads clear of the FPC wall.",
    "F2 screws: x 18.0 -> 20.5 (countersunk head sat under the plinth wall r 24); length 8 -> 6 (boss 5.0).",
    "F1 heads sunk 0.5 (z -84.0): the cap underside curves up beyond r 34.7.",
    "F4: M2x6 THREAD-FORMING screws in D1.7 pilots instead of M2 inserts (tab holes 2.25 from the STS3032 case: insert would leave a 0.6 wall).",
    "F5 set screw at z -74 (spec -65), insert heat-set from outside through a D4.6 tool hole in the right column web.",
    "F6 M3x6 (spec x8); spline engagement 2.2 (spec 3.5 does not fit a flush M3 countersunk head in a 4.1 mm pinion).",
    "PINION PASSAGE r 10.8 through plinth, skirt and floor (spec: boss slot D14.4 + notch only in the teeth zone): F6 lies under the 6805 outer "
    "ring, so the pinion is fixed on the servo on the bench and servo + pinion are mounted / serviced as one unit from above. The skirt disc is open "
    "at the pinion (C shape).",
    "J1 FPC floor slot y 21.2 .. 22.5 (spec 21.6 .. 23.0): plinth skin outside the slot 1.26 .. 1.5 instead of 0.76 .. 1.0.",
    "F7 controller screws at z -57 (spec -68, under the ESP32 module), M2x4; two rests at z -74.",
    "Static pan-FPC anchor on the +X side: arc slot az 40 .. 52 at the wall inner face + clamp az 23.5 .. 39.5 inside the channel (spec: anchor at "
    "az 150, rectangular slot x -18 .. -14). With the rotating anchor at gear azimuth 30 the rolling loop only closes with the static anchor on the "
    "same side; the deck carries the mirrored provisions as a spare.",
    "Cradle long walls end at x 25.8 (spec 23.0); cap pocket is clearance only (x -30.3 .. 16.5, y +-12.95), the T_ram walls locate the servo.",
    "Buck / amplifier stand on 1.0 standoffs: +0.8 outward; capacitor +0.1 in x; column foot widened inward to x 33.0; stop ring backed by a flange r 12.8.",
    "Integrator (K10 min feature 0.6): the pilots of F7 (controller) and F14 (buck / amplifier) and the seats of the 4 cradle F2 inserts are "
    "THROUGH holes now (were blind with 0.4 .. 0.5 floors).",
    "Dummy hub: PETG post D24.96 with an M8x20 bolt as steel core / clutch shaft and 2 disc springs (slip clutch); sun gear tapped M8; stub r 7.5. "
    "No POM collet: the torso sits on the dummy by gravity (spec 5.5).",
]
STEP_MAX = 12_000_000
STEP_SKIP = {"T_spodok": "loft-derived (B-spline faces of cap_blank): 40.7 MB measured, limit 12 MB"}


def export_step_limited(name, shape):
    """STEP only when the file stays under STEP_MAX; returns (relative path or None, bytes or None, note)"""
    path = os.path.join(HERE, "step", name + ".step")
    if name in STEP_SKIP:
        if os.path.exists(path):
            os.remove(path)
        return None, None, STEP_SKIP[name]
    bd.export_step(shape, path)
    n = os.path.getsize(path)
    if n > STEP_MAX:
        os.remove(path)
        return None, n, f"deleted: {n / 1e6:.1f} MB > {STEP_MAX / 1e6:.0f} MB"
    return f"step/{name}.step", n, ""


def main(argv):
    rebuild = "--rebuild" in argv
    T0 = time.time()
    print("== t4_ram: build ==", flush=True)
    parts = build(rebuild, verbose=True)
    print(f"build {time.time() - T0:.1f} s, {len(parts)} parts", flush=True)
    exp = expected_bbox()
    recs, bad = [], []
    print(f"{'part':22s} {'grp':3s} {'mat':11s} valid sol {'volume':>10s}  bbox x / y / z{'':38s} build s")
    for name, p in parts.items():
        r = C.check_part(name, p)
        if name in exp:
            r["bbox_expected"] = [round(v, 3) for v in exp[name]]
            r["bbox_ok"] = all(abs(u - v) <= 0.06 for u, v in zip(r["bbox"], exp[name]))
            r["ok"] = r["ok"] and r["bbox_ok"]
        r["build_s"] = TIMES.get(name, 0.0)
        b = r["bbox"]
        print(f"{name:22s} {p['group']:3s} {p['mat']:11s} {str(r['valid'])[0]}     {r['n_solids']}  {r['volume']:10.1f}  "
              f"{b[0]:7.2f}..{b[1]:7.2f} / {b[2]:7.2f}..{b[3]:7.2f} / {b[4]:8.2f}..{b[5]:7.2f}  {r['build_s']:5.1f}"
              + ("" if r["ok"] else "   <-- NOT OK"), flush=True)
        if not r["ok"]:
            bad.append(name)
        recs.append((name, p, r))
    if "--noexport" in argv:
        print("not exported; NOT OK:", bad)
        return 1 if bad else 0
    t = time.time()
    pj = os.path.join(HERE, "parts_ram.json")
    old_names = [e["name"] for e in json.load(open(pj))["parts"]] if os.path.exists(pj) else []
    os.makedirs(os.path.join(HERE, "stl"), exist_ok=True); os.makedirs(os.path.join(HERE, "step"), exist_ok=True)
    out, n_step = [], 0
    for name, p, r in recs:
        e = C.export_part(name, p, HERE, step=False)
        e["stl"] = f"stl/{name}.stl"
        e["step"], e["step_bytes"], note = export_step_limited(name, p["shape"])
        if note:
            e["step_note"] = note
        n_step += e["step"] is not None
        e["build_s"] = r["build_s"]
        for k in ("bbox_expected", "bbox_ok"):
            if k in r:
                e[k] = r[k]
        e["ok"] = bool(e["ok"] and r["ok"])
        if "fastener" in p:
            e["fastener"] = p["fastener"]
        if name in SOURCES:
            e["source"] = SOURCES[name]
        if name in ASSEMBLY:
            e["assembly_step"], e["assembly_dir"] = ASSEMBLY[name]
        out.append(e)
    stale = [n for n in old_names if n not in parts]                  # exports of parts this module no longer has
    for n in stale:
        for sub, ext in (("stl", ".stl"), ("step", ".step")):
            f = os.path.join(HERE, sub, n + ext)
            if os.path.exists(f):
                os.remove(f)
    doc = dict(module="ram", generated=time.strftime("%Y-%m-%d %H:%M:%S"), frame="B frame, mm, rest pose", n_parts=len(out),
               all_ok=not bad, not_ok=bad, step_limit_bytes=STEP_MAX, removed_parts=stale, deviations=DEVIATIONS, parts=out,
               additions=json.loads(json.dumps(R, default=str)))
    json.dump(doc, open(pj, "w"), indent=1, ensure_ascii=False)
    mass = {}
    for e in out:
        if e.get("mass_g") is not None:
            mass[e["group"]] = mass.get(e["group"], 0.0) + e["mass_g"]
    print(f"exported {len(out)} STL + {n_step} STEP (no STEP: {[e['name'] for e in out if e['step'] is None]}) in {time.time() - t:.1f} s "
          f"-> parts_ram.json; removed stale exports {stale}; mass by group (g): " + ", ".join(f"{g} {m:.1f}" for g, m in mass.items()))
    print("NOT OK:", bad if bad else "none", f"| total {time.time() - T0:.1f} s")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""
NOVA mini – KRK, návrh B "os v hlave" (user 2026-11-04: "krk hladký kužeľ – dole hrubší, hore tenší, spodok
prispôsobený zaoblenému trupu, krk v strede hlavy"; chose B: tilt axis inside the head, bigger drum, no ear pivots;
chose bearings – parts are printed in RESIN, so no resin-on-resin sliding anywhere).

Coordinates: mm, torso top (flat centre of the domed KLASIK torso) z = 0, robot front = -Y, robot right = -X.

Parts
  N1   neck – ONE visible piece: smooth trumpet cone (base follows the torso dome, 0.6 mm gap) + tilt drum Ø36 x 26
       (axis 8 mm ABOVE the head bottom, i.e. inside the head) + two stub axles on the drum ends.  Hollow (cable path:
       head -> left stub bore -> drum -> cone -> N3 -> torso).  The drum is stationary; the head turns around it.
  L1   2x ball bearing 6700-2RS (10 x 15 x 4) on the stubs.
  N5-P / N5-Z  front / back bezel half (black) – the head bottom around the drum (the drum is wider than any opening
       it could pass, so the head gets a big bottom opening closed by these two halves).  Together they form the
       split housings of both bearings; 2x M2 along Y join them, 4x M2 fix them to the head (all from inside).
  S1   tilt servo MG90S in the HEAD (right side), shaft on the drum axis; its arm (trimmed to Ø10) sits in a slot in the
       right stub end -> servo turns the head around the stationary drum.  The bearing carries the load, the servo
       only the torque.
  N3   drive plate inside the cone base (pan servo arm), 2x M2 countersunk into inserts in N1.
Tilt ±40°: the head bottom/bezel opening is coaxial with the drum (0.5 mm gap stays constant); the cone stays outside
the space the tilting head bottom sweeps (checked numerically).
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from build123d import (Axis, Box, BuildSketch, Cylinder, Edge, Face, GeomType, Location, Plane, Pos,  # noqa: E402
                       RectangleRounded, Rot, Solid, Vector, Wire, extrude, fillet, revolve)

# ---- head placement ------------------------------------------------------------------------------------------------
HB = 30.0                        # head bottom above the torso top
H_AX = 8.2                       # tilt axis above the head bottom (inside the head)
AX_Z = HB + H_AX                 # 38.2
TILT = 40.0
# ---- drum (part of N1) ---------------------------------------------------------------------------------------------
R_D, L_D, D_FIL, D_WALL, END_WALL = 18.0, 26.0, 3.0, 1.8, 2.0
GAP = 0.5                        # head / bezel to drum
# ---- bearings + stubs ----------------------------------------------------------------------------------------------
BRG_D, BRG_OD, BRG_W, BRG_OUT_ID = 10.0, 15.0, 4.0, 13.9
SH_OD, SH_T = 12.0, 1.0          # shoulder on the drum end face -> bearing inner ring
X_B0 = L_D / 2 + SH_T            # 14.0 bearing inner face
X_B1 = X_B0 + BRG_W              # 18.0
LIP_T = 0.4                      # housing lips on both sides of the outer ring
X_H0, X_H1 = X_B0 - LIP_T, X_B1 + LIP_T     # housing 13.6 .. 18.4
X_STUB = X_H1 + 2.0              # 20.4 stub end
SLOT_W = 5.6                     # right stub end: slot for the servo arm
STUB_ID = 7.0                    # cable bore
# ---- servo (in the head, right side, shaft +X) ---------------------------------------------------------------------
SV_CASE = (22.5, 12.2, 22.8)
SV_SHAFT_FROM_END = 5.9
SV_TOWER_R, SV_TOWER_H = 5.9, 3.0
SV_SPLINE_R, SV_SPLINE_H = 2.4, 2.7
ARM_T, ARM_W, ARM_R, HUB_R, HUB_L = 1.5, 5.2, 5.0, 3.5, 3.0
X_ARM1 = -X_STUB                 # arm flush with the right stub end, fully inside its slot
X_ARM0 = X_ARM1 + ARM_T
X_TOWER_TOP = X_ARM1 - HUB_L - 0.3
X_CASE_TOP = X_TOWER_TOP - SV_TOWER_H
X_CASE_BOT = X_CASE_TOP - SV_CASE[0]
# ---- cone (part of N1) ---------------------------------------------------------------------------------------------
CONE_R0, CONE_S1, CONE_P, CONE_GAP, WALL = 25.0, 6.8, 1.6, 0.6, 1.8
# ---- head bottom opening / bezel -----------------------------------------------------------------------------------
OPEN_X, OPEN_Y, OPEN_R = 29.0, 26.0, 8.0     # half sizes of the big bottom opening in the head
BZ_SEAM = 0.2
FL_H = 6.0                                   # flange height above the floor (head flange + bezel flange)
HEAD_FLOOR = 2.0


# ------------------------------------------------------------------------------------------------ torso dome
def _torso_profile():
    from nova_v8 import klasik as KL
    secs = [(a, z - 117.0) for a, b, n, z in KL.torso_secs()]
    secs = sorted([s for s in secs if s[1] > -30], key=lambda s: s[0])
    return secs


_TP = None


def z_dome(r):
    """height of the torso surface at radius r (x direction = highest; flat top r <= 21)"""
    global _TP
    if _TP is None:
        _TP = _torso_profile()
    if r <= _TP[0][0]:
        return 0.0
    for (a0, z0), (a1, z1) in zip(_TP, _TP[1:]):
        if a0 <= r <= a1:
            return z0 + (z1 - z0) * (r - a0) / (a1 - a0)
    return _TP[-1][1]


# ------------------------------------------------------------------------------------------------ N1
def cone_s(z, z_top):
    """outer radius of the trumpet at height z"""
    zb = z_dome(CONE_R0) + CONE_GAP + 1.0
    u = min(1.0, max(0.0, (z_top - z) / (z_top - zb)))
    return CONE_S1 + (CONE_R0 - CONE_S1) * u ** CONE_P


def _revolve_profile(pts_rz):
    """closed (r, z) polyline profile -> solid of revolution about Z (hidden inner cavities only)"""
    edges = []
    for (r0, z0), (r1, z1) in zip(pts_rz, pts_rz[1:] + pts_rz[:1]):
        if abs(r0 - r1) + abs(z0 - z1) > 1e-6:
            edges.append(Edge.make_line(Vector(r0, 0, z0), Vector(r1, 0, z1)))
    return revolve(Face(Wire(edges)), Axis.Z, 360)


def _dedupe(pts):
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > 1e-4:
            out.append(p)
    return out


def cone_top():
    """cone top height: inside the drum also in the y direction (no exposed top face)"""
    return AX_Z - math.sqrt(R_D ** 2 - CONE_S1 ** 2) + 0.9


def cone_outer(z_top):
    """smooth trumpet (B-spline profile, revolved): underside follows the torso dome + CONE_GAP, rounded rim"""
    n = 48
    zb = z_dome(CONE_R0) + CONE_GAP + 1.0
    flare = [Vector(cone_s(zb + (z_top - zb) * i / n, z_top), 0, zb + (z_top - zb) * i / n) for i in range(n + 1)]
    flare[0] = Vector(CONE_R0, 0, zb)
    under = [Vector(CONE_R0 * (1 - i / 24), 0, z_dome(CONE_R0 * (1 - i / 24)) + CONE_GAP) for i in range(25)]
    e_under = Edge.make_spline(under)                                  # rim -> axis
    e_axis = Edge.make_line(under[-1], Vector(0, 0, z_top))
    e_top = Edge.make_line(Vector(0, 0, z_top), flare[-1])
    e_flare = Edge.make_spline(list(reversed(flare)))                   # top -> rim
    e_rim = Edge.make_line(flare[0], under[0])
    s = revolve(Face(Wire([e_under, e_axis, e_top, e_flare, e_rim])), Axis.Z, 360)
    for r in (0.8, 0.5, 0.3):
        try:
            es = [e for e in s.edges() if e.geom_type == GeomType.CIRCLE and abs(e.radius - CONE_R0) < 0.05]
            ns = fillet(es, r)
            if ns.is_valid:
                return ns
        except Exception:  # noqa: BLE001
            continue
    return s


def drum_outer():
    d = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(R_D, L_D)
    return fillet(d.edges(), D_FIL)


def stubs():
    s = None
    for sx in (-1, 1):
        sh = Pos(sx * (L_D / 2 + SH_T / 2 - 0.1), 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SH_OD / 2, SH_T + 0.2)
        tube = Pos(sx * (L_D / 2 + (X_STUB - L_D / 2) / 2 - 0.1), 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BRG_D / 2, X_STUB - L_D / 2 + 0.2)
        part = sh + tube
        s = part if s is None else s + part
    return s


def outer_body(verbose=False):
    z_top = cone_top()
    b = cone_outer(z_top) + drum_outer()
    # blend cone -> drum (small radius: the tilting head bottom passes close by)
    def junction(e):
        c = e.center()
        return abs(c.Z - (AX_Z - math.sqrt(max(0.0, R_D ** 2 - CONE_S1 ** 2)))) < 1.5 and math.hypot(c.X, c.Y) < CONE_S1 + 1.5
    r_ok = None
    for r in (1.2, 0.8, 0.5):
        es = [e for e in b.edges() if junction(e)]
        try:
            nb = fillet(es, r)
            if nb.is_valid:
                b, r_ok = nb, r
                break
        except Exception:  # noqa: BLE001
            continue
    b = b + stubs()
    if verbose:
        print(f"  cone-drum fillet r={r_ok}")
    return b


def body(outer=None):
    o = outer if outer is not None else outer_body()
    z_top = cone_top()
    # cavities: drum inside, cone inside, connection, stub bores
    drum_in = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(R_D - D_WALL, L_D - 2 * END_WALL)
    drum_in = fillet(drum_in.edges(), 1.5)
    n = 40
    zb = z_dome(CONE_R0) + CONE_GAP
    zi0 = zb + 2.6                                   # N3 ledge level inside the base
    inner = [(max(cone_s(zi0 + (z_top - 1.0 - zi0) * i / n, z_top) - WALL, 3.6), zi0 + (z_top - 1.0 - zi0) * i / n)
             for i in range(n + 1)]
    pts = [(0.0, zb - 1.0), (inner[0][0] - 1.6, zb - 1.0), (inner[0][0] - 1.6, zi0)] + inner + [(0.0, z_top - 1.0)]
    cone_in = _revolve_profile(_dedupe(pts))
    link = Pos(0, 0, AX_Z - R_D + 0.5) * Cylinder(3.5, 6.0)
    bores = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(STUB_ID / 2, 2 * X_STUB + 2)
    n1 = o - drum_in - cone_in - link - bores
    # right stub end: slot for the servo arm (vertical, across the tube end)
    n1 = n1 - Pos(-(X_STUB - 1.0 + 0.05), 0, AX_Z) * Box(2.1, SLOT_W, BRG_D + 2)
    # N3 bosses with M2 inserts (Ø3.3 x 4)
    for sx in (-1, 1):
        boss = Pos(sx * 15.0, 0, zi0 + 3.0) * Cylinder(3.0, 6.0)
        n1 = (n1 + (boss & o)) - Pos(sx * 15.0, 0, zi0 + 2.0) * Cylinder(1.65, 4.0)
    return n1


def drive_plate():
    """N3 – inside the cone base on the flat torso top: pan servo arm (4x r 7 + centre hole), cable hole,
    2x M2 countersunk into the N1 bosses."""
    zb = z_dome(CONE_R0) + CONE_GAP
    r = cone_s(zb + 2.6, cone_top()) - WALL - 1.6 - 0.2
    p = Pos(0, 0, zb + 1.3) * Cylinder(r, 2.6)
    p = p - Pos(9.0 / math.sqrt(2), 9.0 / math.sqrt(2), zb + 1.3) * Cylinder(2.5, 4.0)
    p = p - Pos(0, 0, zb + 1.3) * Cylinder(2.75, 4.0)
    for sx in (-1, 1):
        p = p - Pos(sx * 15.0, 0, zb + 1.3) * Cylinder(1.1, 4.0)
        p = p - Solid.make_cone(2.1, 1.0, 1.1, Plane.XY.offset(zb - 0.001).move(Location((sx * 15.0, 0, 0))))
    for k in range(4):
        a = k * math.pi / 2
        p = p - Pos(7.0 * math.cos(a), 7.0 * math.sin(a), zb + 1.3) * Cylinder(1.1, 4.0)
    return p


def bearings():
    out = None
    for sx in (-1, 1):
        x0, x1 = sx * X_B0, sx * X_B1
        b = Pos((x0 + x1) / 2, 0, AX_Z) * Rot(0, 90, 0) * (Cylinder(BRG_OD / 2, BRG_W) - Cylinder(BRG_D / 2, BRG_W))
        out = b if out is None else out + b
    return out


# ------------------------------------------------------------------------------------------------ servo
SV_EAR_X = X_CASE_BOT + 15.9                      # ear plane (MG90S: 15.9 from the case bottom)
SV_Y0, SV_Y1 = -SV_SHAFT_FROM_END, SV_CASE[2] - SV_SHAFT_FROM_END   # case lies toward the back: y -5.9 .. 16.9


def servo():
    """S1 – MG90S lying in the head: shaft on the drum axis (+X), case toward the back, ears screwed to 2 posts."""
    cx = (X_CASE_TOP + X_CASE_BOT) / 2
    case = fillet((Pos(cx, (SV_Y0 + SV_Y1) / 2, AX_Z) * Box(SV_CASE[0], SV_CASE[2], SV_CASE[1])).edges(), 0.5)
    for y0, y1 in ((SV_Y0 - 4.85, SV_Y0), (SV_Y1, SV_Y1 + 4.85)):
        case = case + Pos(SV_EAR_X - 1.25, (y0 + y1) / 2, AX_Z) * Box(2.5, y1 - y0, SV_CASE[1])
    tower = Pos(X_CASE_TOP + SV_TOWER_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_TOWER_R, SV_TOWER_H)
    spline = Pos(X_TOWER_TOP + SV_SPLINE_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_SPLINE_R, SV_SPLINE_H)
    s = case + tower + spline
    arm = Pos((X_ARM0 + X_ARM1) / 2, 0, AX_Z) * Box(ARM_T, ARM_W, 2 * ARM_R)
    arm = arm & (Pos((X_ARM0 + X_ARM1) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(ARM_R, ARM_T))
    hub = Pos(X_ARM1 - HUB_L / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HUB_R, HUB_L)
    horn = (arm + hub) - spline
    return s, horn


# ------------------------------------------------------------------------------------------------ head interface
def drum_envelope(c=GAP):
    d = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(R_D + c, L_D + 2 * c)
    return fillet(d.edges(), D_FIL + c)


def _rrect(hx, hy, r, z0, z1):
    with BuildSketch(Plane.XY.offset(z0)) as sk:
        RectangleRounded(2 * hx, 2 * hy, r)
    return extrude(sk.sketch, amount=z1 - z0)


BZ_TABS = [(sx, y) for sx in (-1, 1) for y in (-16.0, 22.0)]   # bezel -> head screw points (x side, y)


def bezel():
    """N5-P (front, y<0) and N5-Z (back, y>0): head bottom around the drum + split bearing housings; 4 vertical tabs
    with horizontal M2 screws into inserts in head bosses (from inside the head)."""
    plate = _rrect(OPEN_X - BZ_SEAM, OPEN_Y - BZ_SEAM, OPEN_R - BZ_SEAM, HB, HB + HEAD_FLOOR)
    tabs = None
    for sx, y in BZ_TABS:
        t = Pos(sx * (OPEN_X - BZ_SEAM - 0.8), y, HB + HEAD_FLOOR + FL_H / 2) * Box(1.6, 6.0, FL_H)
        tabs = t if tabs is None else tabs + t
    hs = None
    for sx in (-1, 1):
        xa, xb = sx * X_H0, sx * X_H1
        blk = Pos((xa + xb) / 2, 0, (HB + HEAD_FLOOR + AX_Z) / 2) * Box(abs(xb - xa), 21.0, AX_Z - HB - HEAD_FLOOR + 0.2)
        top = Pos((xa + xb) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(10.5, abs(xb - xa))
        h = blk + top
        h = h - Pos(sx * (X_B0 + X_B1) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BRG_OD / 2, BRG_W)
        h = h - Pos((xa + xb) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BRG_OUT_ID / 2, abs(xb - xa) + 1)
        hs = h if hs is None else hs + h
    bz = (plate + tabs + hs) - drum_envelope()
    for sx in (-1, 1):                                   # joining screws along Y above the bearings
        xc = sx * (X_H0 + X_H1) / 2
        bz = bz - Pos(xc, 5.0, AX_Z + 8.6) * Rot(90, 0, 0) * Cylinder(1.1, 12.0)
    for sx, y in BZ_TABS:                                # tab screws along X (clearance)
        bz = bz - Pos(sx * (OPEN_X - BZ_SEAM - 0.8), y, HB + HEAD_FLOOR + FL_H / 2) * Rot(0, 90, 0) * Cylinder(1.1, 4.0)
    front = bz & (Pos(0, -50, AX_Z) * Box(200, 100, 200))
    back = bz & (Pos(0, 50, AX_Z) * Box(200, 100, 200))
    for sx in (-1, 1):
        xc = sx * (X_H0 + X_H1) / 2
        front = front - Pos(xc, -1.75, AX_Z + 8.6) * Rot(90, 0, 0) * Cylinder(1.65, 3.5)   # insert pocket
    return front, back


def head():
    """Head návrh 5 in these coordinates (bottom at HB): big bottom opening, 4 insert bosses for the bezel tabs,
    2 posts for the servo ears."""
    from nova_mini import hlava_skrupina as HS
    s = HS.build_common().moved(Location((0, 0, HB)))
    s = s - _rrect(OPEN_X, OPEN_Y, OPEN_R, HB - 1.0, HB + HEAD_FLOOR + 0.01)
    zc = HB + HEAD_FLOOR + FL_H / 2
    for sx, y in BZ_TABS:
        b = Pos(sx * (OPEN_X + 2.0), y, zc) * Box(4.0, 6.0, FL_H)
        b = b - Pos(sx * (OPEN_X + 1.75), y, zc) * Rot(0, 90, 0) * Cylinder(1.65, 3.6)
        s = s + b
    for y in (SV_Y0 - 2.4, SV_Y1 + 2.4):                # servo ear posts (inserts along X)
        post = Pos(SV_EAR_X - 2.5 - 1.6, y, (HB + HEAD_FLOOR + AX_Z + 6.0) / 2) * Box(3.2, 4.0, AX_Z + 6.0 - HB - HEAD_FLOOR)
        post = post - Pos(SV_EAR_X - 2.5 - 1.8, y, AX_Z) * Rot(0, 90, 0) * Cylinder(1.65, 3.6)
        s = s + post
    return s


def build_all(verbose=True):
    import time
    t0 = time.time()
    o = outer_body(verbose=verbose)
    n1 = body(o)
    n3 = drive_plate()
    brg = bearings()
    bf, bb = bezel()
    sv, horn = servo()
    P = dict(N1=n1, N3=n3, L1=brg, N5P=bf, N5Z=bb, S1=sv, HORN=horn)
    if verbose:
        for k, s in P.items():
            bb_ = s.bounding_box()
            print(f"  {k:5s} valid={s.is_valid} solids={len(s.solids())} x[{bb_.min.X:.1f},{bb_.max.X:.1f}] "
                  f"y[{bb_.min.Y:.1f},{bb_.max.Y:.1f}] z[{bb_.min.Z:.1f},{bb_.max.Z:.1f}] vol={s.volume:.0f}")
        print(f"  built in {time.time() - t0:.1f}s")
    return P


if __name__ == "__main__":
    P = build_all()
    names = list(P)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            x = P[a] & P[b]
            v = x.volume if x is not None else 0.0
            if v > 1e-3:
                print(f"  INT {a} & {b} = {v:.3f}")

"""
NOVA mini – KRK, návrh "jeden celok" (podľa R04), user feedback 2026-11-03:
  "golier, plášť krku a kryt náklonu má byť JEDEN celok, nie tri časti; golier nesmie vyzerať naklonený;
   ako sa bude hlava nakláňať? boky nech sú otočné a upevnené v hlave; 100 % hladké, žiadne zuby/hrany"

Parts (this file, coordinates: mm, torso top z = 0, robot front = -Y, robot right = -X):
  N1   krk – ONE visible piece: level oval collar + bell neck + middle of the tilt barrel, blended with fillets.
       Hollow (wall 1.4 / 1.5).  Barrel core is a tube Ø17 bore, open at both ends (the caps' spigots ride in it =
       plain bearings).  On top of the barrel there is an assembly opening for the tilt servo that is ALWAYS under
       the head (hidden over the whole ±40° range; the head stops against the servo at ~42°); its +X end is the
       servo's end stop.
  N2-P right end cap – rotates; fixed in the head (head pocket + 1x M2 from inside the head); carries the servo arm
       (stock cross arm trimmed to Ø14 in a form-fit cross pocket)
  N2-L left end cap  – rotates; fixed in the head; its hollow spigot is the left bearing AND the cable passage:
       head cable -> hole in the head saddle -> radial hole in the cap -> along the tilt axis -> neck (only twists ±40°)
  N3   drive plate (hidden in the collar underside): pan-servo arm mount + cable hole, 2x M2 countersunk into N1 bosses
  S1   tilt servo MG90S (mounting ears cut off): held by N1 (4 crush ribs, 2 support ribs, +X end stop), shaft on the axis,
       body standing UP into the head (the head turns around it, its saddle has a window for that); the horn is
       screwed into the right cap, so servo -> horn -> right cap -> head
Tilt: head + both caps turn together about the barrel axis, ±40°; the head bottom groove is coaxial with the
barrel, so the 0.5 mm gap stays constant.  Pan: N1 turns with N3 on the pan servo in the torso (later part).
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from build123d import (Axis, Box, Cylinder, Edge, Face, GeomType, Location, Plane, Pos, Rot, Solid, Vector,  # noqa: E402
                       Wire, extrude, fillet)

from nova.cad.common import superellipse_pts  # noqa: E402

# ---- collar (level, centred on the pan axis) ----------------------------------------------------------------------
C_A, C_B, C_H = 25.5, 19.0, 4.5
C_LIP = 2.8                                      # thin flared lip (R04): rim 2.8 high, top slopes up to a level plateau
# ---- neck (bell: steep sides, long front ramp) ---------------------------------------------------------------------
N_H = 14.0
NX_TOP, NX_BOT = 13.8, 20.5
NYF_TOP, NYF_BOT = -7.8, -15.5
NYB_TOP, NYB_BOT = 7.8, 13.5
WALL = 1.4
# ---- tilt barrel ---------------------------------------------------------------------------------------------------
B_R, B_LEN = 10.0, 49.0
CAP_L, CAP_GAP = 7.8, 0.6
CAP_DOME_R = 3.0                                 # rounded rim of the flat cap end (flat face Ø14, R04 look)
CORE_L = B_LEN - 2 * (CAP_L + CAP_GAP)          # 32.2 – part of N1
BORE_R = 8.5                                     # core bore (wall 1.5)
SPIGOT_R, SPIGOT_IN, SPIGOT_L = 8.35, 7.0, 3.0   # cap spigot = plain bearing in the bore (2.4 mm engaged)
Z_N0 = C_H - 0.4
Z_N1 = Z_N0 + N_H
AX_Z = Z_N1 + B_R - 2.0                          # barrel axis 26.1 above the torso top
HEAD_GAP = 0.5
HEAD_Z0 = AX_Z + 1.0                             # head bottom (the head groove hides the barrel top ±84°)
POCKET_C = 0.2                                   # head cap pocket = cap envelope + 0.2 (FDM)
TILT = 40.0
# ---- assembly opening on the barrel top (always under the head at ±40°) --------------------------------------------
OPEN_Y = 6.3
# ---- tilt servo MG90S (ears cut off), shaft -X on the axis ---------------------------------------------------------
SV_CASE = (22.5, 12.2, 22.8)                     # along shaft (x), width (y), length (z)
SV_SHAFT_FROM_END = 5.9                          # shaft axis from the upper end of the case
SV_TOWER_R, SV_TOWER_H = 5.9, 3.0
SV_SPLINE_R, SV_SPLINE_H = 2.4, 2.7
HORN_R, HORN_T, HORN_HUB_R, HORN_ARM_W = 7.0, 1.5, 3.5, 5.2
X_CAP_IN = CORE_L / 2 + CAP_GAP                  # 16.7 – inner face of a cap
HORN_SINK = 2.0                                  # servo arm sits 2 mm deep in the right cap -> servo 2 mm to -X
X_HORN_HUB_END = -(X_CAP_IN - 3.0 + HORN_SINK)   # -15.7 (tower top)
X_CASE_TOP = X_HORN_HUB_END + SV_TOWER_H         # -12.7
X_CASE_BOT = X_CASE_TOP + SV_CASE[0]             # 9.8 (3.9 mm cable passage to the left spigot)
OPEN_X1 = X_CASE_BOT + 0.3                       # opening ends 0.3 behind the servo -> +X end stop
CAP_SCREW_X = X_CAP_IN + CAP_L / 2 + 1.4         # 22.0 – head->cap M2 position (both caps)


def _w(a, b, z, n=2.0, cy=0.0, count=128):
    """periodic spline section; FIXED parameters -> every section shares one knot vector, so lofts stay compact
    (~130 poles instead of ~2700) and smooth, and the STEP stays small"""
    pts = [Vector(x, cy + y, z) for x, y in superellipse_pts(a, b, n, count)]
    return Wire([Edge.make_spline(pts, periodic=True, parameters=[i / len(pts) for i in range(len(pts) + 1)])])


def _prof(z):
    """outer neck section at height z -> (half width x, front y, back y)"""
    t = min(1.0, max(0.0, (z - Z_N0) / N_H))
    kx, ky = (1 - t) ** 3.0, (1 - t) ** 1.6
    a, yf, yb = NX_TOP + (NX_BOT - NX_TOP) * kx, NYF_TOP + (NYF_BOT - NYF_TOP) * ky, NYB_TOP + (NYB_BOT - NYB_TOP) * kx
    # shoulder: the neck runs into the barrel without a waist (±9 below the barrel), back to ±7.8 where the head
    # groove lip passes at ±40° tilt
    u = min(1.0, max(0.0, (z - AX_Z + 10.3) / 3.3))
    d = NYB_TOP + 1.2 * (1 - (3 * u * u - 2 * u ** 3))
    return a, min(yf, -d), max(yb, d)


def _sec(a, yf, yb, z):
    return _w(a, (yb - yf) / 2, z, n=2.15, cy=(yb + yf) / 2)


def collar():
    """level oval collar, centred; R04 look: thin rounded lip (2.8 mm) whose top slopes up to a level plateau where
    the neck starts (plateau reaches inset 3.3, outside the neck foot).  The profile is resampled at an even 0.3 mm arc
    length before lofting, so the B-spline loft cannot overshoot (no fold at the bottom round)."""
    P = [(1 - math.sin(a), 1 - math.cos(a)) for a in (i / 30 * math.pi / 2 for i in range(31))]
    P.append((0.0, C_LIP - 0.9))
    al = math.radians(60)
    P += [(1 - math.cos(i / 30 * al), C_LIP - 0.9 + math.sin(i / 30 * al)) for i in range(1, 31)]
    d0, z0 = P[-1]
    P += [(d0 + (3.3 - d0) * u, z0 + (C_H - z0) * (1.5 * u - 0.5 * u ** 3)) for u in (i / 80 for i in range(1, 81))]
    L = [0.0]
    for (a, b), (c, d) in zip(P, P[1:]):
        L.append(L[-1] + math.hypot(c - a, d - b))
    n = max(2, round(L[-1] / 0.3))
    pts, j = [], 0
    for k in range(n + 1):
        sk = L[-1] * k / n
        while j < len(L) - 2 and L[j + 1] < sk:
            j += 1
        t = (sk - L[j]) / max(L[j + 1] - L[j], 1e-12)
        pts.append((P[j][0] + (P[j + 1][0] - P[j][0]) * t, P[j][1] + (P[j + 1][1] - P[j][1]) * t))
    return Solid.make_loft([_w(C_A - d, C_B - d, z) for d, z in pts])


def neck_outer():
    zs = [Z_N0 + (AX_Z - Z_N0) * i / 30 for i in range(31)]
    return Solid.make_loft([_sec(*_prof(z), z) for z in zs])


def neck_inner():
    """cavity: the outer profile shifted 2.5 mm up and inset 1.4 -> constant-ish wall also on the flaring bottom"""
    zs = [1.6 + (AX_Z - 1.6) * i / 14 for i in range(15)]
    secs = []
    for z in zs:
        a, yf, yb = _prof(z + 2.5)
        secs.append(_sec(a - WALL, yf + WALL, yb - WALL, z))
    return Solid.make_loft(secs)


def core_outer():
    c = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R, CORE_L)
    return fillet(c.edges(), 0.8)


def _fillet_between(b, pred, radii):
    for r in radii:
        es = [e for e in b.edges() if pred(e)]
        if not es:
            return b, None
        try:
            nb = fillet(es, r)
            if nb.is_valid:
                return nb, r
        except Exception:  # noqa: BLE001
            continue
    return b, None


def outer_body(verbose=False):
    """N1 outer form (solid) – collar + neck + core, both junctions blended."""
    b = collar() + neck_outer()
    # collar top -> neck : the intersection lies on the flat collar top (z = C_H)
    b, r1 = _fillet_between(b, lambda e: abs(e.center().Z - C_H) < 0.05 and abs(e.bounding_box().size.Z) < 0.05
                            and e.bounding_box().max.X < 22.5 and e.length > 5, (1.6, 1.2, 0.8))
    b = b + core_outer()
    # neck -> barrel core : edges whose both ends lie on the core cylinder surface and below the axis
    def on_core(e):
        if e.center().Z > AX_Z - 1.0 or e.center().Z < AX_Z - B_R - 0.5:
            return False
        p0, p1 = e.position_at(0), e.position_at(1)
        r0 = math.hypot(p0.Y, p0.Z - AX_Z)
        rc = math.hypot(e.center().Y, e.center().Z - AX_Z)
        return (abs(r0 - B_R) < 0.05 and abs(rc - B_R) < 0.05 and abs(e.center().X) < CORE_L / 2 - 0.5 and e.length > 3
                and e.geom_type != GeomType.CIRCLE and e.geom_type != GeomType.LINE)
    b, r2 = _fillet_between(b, on_core, (3.0, 2.5, 2.0, 1.5))
    if verbose:
        print(f"  collar fillet r={r1}  core fillet r={r2}  faces={len(b.faces())}")
    return b


def opening_box(shrink=0.0):
    x0, x1 = -CORE_L / 2 - 2.0, OPEN_X1 - shrink
    return Pos((x0 + x1) / 2, 0, AX_Z + 8.0) * Box(x1 - x0, 2 * (OPEN_Y - shrink), 6.0)


def body(outer=None):
    """N1 – one piece: hollow, open bore, servo opening on top, crush ribs + support ribs + end stop for the servo,
    2 screw bosses for N3."""
    o = outer if outer is not None else outer_body()
    cav = neck_inner() + Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BORE_R, CORE_L + 4)
    recess = Solid.make_loft([_w(C_A - 3.0, C_B - 3.0, z) for z in (-1.0, 2.0)])
    n1 = o - cav - recess - opening_box()
    try:                                       # soften the opening rim (hidden in the head, still no knife edges)
        rim = [e for e in n1.edges() if abs(abs(e.center().Y) - OPEN_Y) < 0.05 and e.center().Z > AX_Z + 5.0
               and math.hypot(e.center().Y, e.center().Z - AX_Z) > B_R - 0.1]
        n1r = fillet(rim, 0.15)
        if n1r.is_valid:
            n1 = n1r
    except Exception:  # noqa: BLE001
        pass
    env = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R - 0.15, CORE_L - 1.0)
    ribs = None
    for xr in (-8.0, 8.0):                     # crush ribs: crest 0.05 into the 12.2 case, from its bottom to the rim
        for sy in (-1, 1):
            r = Pos(xr, sy * (SV_CASE[1] / 2 - 0.05 + 0.8), AX_Z + 0.9) * Box(0.8, 1.6, 13.0)
            ribs = r if ribs is None else ribs + r
    ribs = ribs & env
    for xr in (-7.0, 7.0):                     # support ribs: the case bottom sits on them
        top = AX_Z - SV_SHAFT_FROM_END
        ribs = ribs + (Pos(xr, 0, top - 1.85) * Box(2.0, 20.0, 3.7) & o)
    for sy in (-1, 1):                         # +X end stop pads (lower half of the case end face)
        ribs = ribs + (Pos(OPEN_X1 + 0.5, sy * 6.25, AX_Z - 4.45) * Box(1.0, 3.5, 2.9) & env)
    ann = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * (Cylinder(B_R - 0.15, CORE_L) - Cylinder(6.2, CORE_L))
    for sx in (-1, 1):                         # thrust pads at the bore bottom: spigot ends 0.1 away -> head axial play ±0.1
        ribs = ribs + (Pos(sx * (CORE_L / 2 - SPIGOT_L + CAP_GAP - 0.1 - 0.4), 0, AX_Z - 7.35) * Box(0.8, 8.0, 2.3) & ann)
    n1 = n1 + ribs
    for sx in (-1, 1):                         # bosses for the 2x M2 from N3 (fully inside the neck)
        boss = (Pos(sx * 13.5, 0, 6.0) * Cylinder(2.5, 8.0) + Pos(sx * 16.5, 0, 6.0) * Box(6.0, 2.0, 8.0)) & o
        n1 = n1 + boss
        n1 = n1 - Pos(sx * 13.5, 0, 5.5) * Cylinder(0.8, 7.0)
    return n1


def cap_envelope(sx, c=0.0, x_in_extra=0.0):
    x_in, x_out = sx * (X_CAP_IN - x_in_extra), sx * (X_CAP_IN + CAP_L + c)
    e = Pos((x_in + x_out) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + c, abs(x_out - x_in))
    return fillet([ed for ed in e.edges() if abs(ed.center().X - x_out) < 0.01], CAP_DOME_R + c)


CABLE_X = X_CAP_IN + 2.6                         # radial cable hole in the left cap, fully inside the cap body
CABLE_ANG = 45.0                                 # from the top towards the back (+Y)


def caps():
    """[N2-P right (-X), N2-L left (+X)] – end caps with bearing spigots; fixed to the head."""
    out = []
    for sx in (-1, 1):
        x_in = sx * X_CAP_IN
        c = cap_envelope(sx)
        c = fillet([e for e in c.edges() if abs(e.center().X - x_in) < 0.01], 0.8)
        sp = Pos(x_in - sx * SPIGOT_L / 2, 0, AX_Z) * Rot(0, 90, 0) * (Cylinder(SPIGOT_R, SPIGOT_L) - Cylinder(SPIGOT_IN, SPIGOT_L))
        c = c + sp
        if sx < 0:   # right: form-fit cross pocket for the stock cross arm trimmed to Ø14
            arms = (Box(1.6, 2 * (HORN_R + 0.2), HORN_ARM_W + 0.3) + Box(1.6, HORN_ARM_W + 0.3, 2 * (HORN_R + 0.2)))
            dp = HORN_SINK + HORN_T + 0.1                       # cross slot from the inner face down to the arm seat
            arms = (Box(dp, 2 * (HORN_R + 0.2), HORN_ARM_W + 0.3) + Box(dp, HORN_ARM_W + 0.3, 2 * (HORN_R + 0.2)))
            pocket = Pos(x_in - dp / 2, 0, AX_Z) * arms & (Pos(x_in - dp / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_R + 0.2, dp))
            c = c - pocket - Pos(x_in - dp / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_HUB_R + 0.3, dp)
        else:        # left: round recess + radial cable hole (cable along the axis through the hollow spigot)
            c = c - Pos(x_in + 1.45, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_R + 0.2, 2.9)
            a = math.radians(CABLE_ANG)
            hole = Pos(CABLE_X, 6.0 * math.sin(a), AX_Z + 6.0 * math.cos(a)) * Rot(-CABLE_ANG, 0, 0) * Cylinder(1.75, 12.0)
            c = c - hole
        # M2 pilot hole from the top (the head screws into the cap from inside the head)
        c = c - Pos(sx * CAP_SCREW_X, 0, AX_Z + 7.5) * Cylinder(0.8, 5.5)
        try:   # round the spigot's inner end edges (the cable slides over the left one)
            e_in = [e for e in c.edges() if abs(e.center().X - (x_in - sx * SPIGOT_L)) < 0.01 and e.geom_type == GeomType.CIRCLE]
            c2 = fillet(e_in, 0.5)
            if c2.is_valid:
                c = c2
        except Exception:  # noqa: BLE001
            pass
        out.append(c)
    return out


def drive_plate():
    """N3 – in the collar underside recess (hidden on the torso): pan-servo arm mount (centre hole for the arm screw,
    4 arm screws at r 7), cable hole, 2x M2 countersunk flat-head screws into the N1 bosses."""
    p = Pos(0, 0, 1.0) * Solid.make_loft([_w(C_A - 3.2, C_B - 3.2, z) for z in (-1.0, 1.0)])
    p = p - Pos(9.0 / math.sqrt(2), 9.0 / math.sqrt(2), 1.0) * Cylinder(2.5, 4.0)   # cable hole (between the arm limbs)
    p = p - Pos(0, 0, 1.0) * Cylinder(2.75, 4.0)                     # centre: arm screw from above
    for xh in (-13.5, 13.5):                                         # 2x M2 flat head (countersunk from below)
        p = p - Pos(xh, 0, 1.0) * Cylinder(1.1, 4.0)
        p = p - Solid.make_cone(2.1, 1.0, 1.1, Plane.XY.offset(-0.001).move(Location((xh, 0, 0))))
    for k in range(4):                                               # pan-servo arm screws (cross arm, r 7)
        a = k * math.pi / 2
        p = p - Pos(7.0 * math.cos(a), 7.0 * math.sin(a), 1.0) * Cylinder(0.6, 4.0)
    return p


def servo():
    """S1 – MG90S envelope (ears removed) + cross arm trimmed to Ø14. Returns (servo, arm)."""
    cx = (X_CASE_TOP + X_CASE_BOT) / 2
    z_bot = AX_Z - SV_SHAFT_FROM_END                                 # body stands UP from the axis into the head
    case = Pos(cx, 0, z_bot + SV_CASE[2] / 2) * Box(*SV_CASE)
    case = fillet(case.edges(), 0.5)
    tower = Pos(X_CASE_TOP - SV_TOWER_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_TOWER_R, SV_TOWER_H)
    spline = Pos(X_HORN_HUB_END - SV_SPLINE_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_SPLINE_R, SV_SPLINE_H)
    s = case + tower + spline
    xa = -(X_CAP_IN + HORN_SINK + HORN_T / 2)
    arms = Pos(xa, 0, AX_Z) * (Box(HORN_T, 2 * HORN_R, HORN_ARM_W) + Box(HORN_T, HORN_ARM_W, 2 * HORN_R))
    horn = arms & (Pos(xa, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_R, HORN_T))
    horn = horn + Pos(-(X_CAP_IN + HORN_SINK - 1.35), 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_HUB_R, 2.7)   # 0.3 to the tower
    horn = horn - Pos(X_HORN_HUB_END - SV_SPLINE_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_SPLINE_R, SV_SPLINE_H)
    return s, horn


def head_saddle_cut():
    """What the head bottom needs (head coordinates are the same as here):
    saddle (solid to ADD inside the head) and cut (groove around the core 0.5 mm + cap-shaped pockets (cap + 0.1)
    + cable hole to the left cap + 2x M2 holes into the caps + the space the servo needs while the head tilts)."""
    saddle = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + 2.6, 2 * (X_CAP_IN + CAP_L + 0.3 + 2.2))
    saddle = saddle & (Pos(0, 0, HEAD_Z0 + 20) * Box(80, 40, 40))
    groove = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + HEAD_GAP, CORE_L + 2 * CAP_GAP + 0.2)
    cut = groove
    for sx in (-1, 1):
        cut = cut + cap_envelope(sx, POCKET_C, x_in_extra=0.1)
        cut = cut + Pos(sx * CAP_SCREW_X, 0, AX_Z + 11.0) * Cylinder(1.2, 4.0)
    a = math.radians(CABLE_ANG)
    cut = cut + Pos(CABLE_X, 11.0 * math.sin(a), AX_Z + 11.0 * math.cos(a)) * Rot(-CABLE_ANG, 0, 0) * Cylinder(2.0, 5.0)
    cut = cut + servo_sweep()
    return saddle, cut


def _rect_rho(alpha, y1, z0, z1):
    """radial distance from the axis to the edge of the rectangle |y|<=y1, z0<=z'<=z1 in direction alpha
    (alpha from +z' towards +y)"""
    import numpy as np
    sa, ca = np.sin(alpha), np.cos(alpha)
    big = 1e9
    ty = np.where(np.abs(sa) > 1e-12, y1 / np.maximum(np.abs(sa), 1e-12), big)
    tz = np.where(ca > 1e-12, z1 / np.maximum(ca, 1e-12), np.where(ca < -1e-12, z0 / np.minimum(ca, -1e-12), big))
    return np.minimum(ty, tz)


def servo_sweep(clear=0.4, tilt=None, n=1440):
    """EXACT space the servo case needs inside the head while the head tilts ±tilt (head frame): the swept outline
    of the case cross-section (radial max over the tilt range), extruded along the case length -> smooth surface."""
    import numpy as np
    tilt = TILT if tilt is None else tilt
    y1 = SV_CASE[1] / 2 + clear
    z0 = -SV_SHAFT_FROM_END - clear
    z1 = SV_CASE[2] - SV_SHAFT_FROM_END + clear
    al = np.linspace(-np.pi, np.pi, n, endpoint=False)
    phis = np.radians(np.linspace(-tilt, tilt, int(4 * tilt) + 1))
    rho = np.max(np.stack([_rect_rho(al - ph, y1, z0, z1) for ph in phis]), axis=0) + 0.02
    pts = [Vector(X_CASE_TOP - clear, float(r * np.sin(a)), float(AX_Z + r * np.cos(a))) for a, r in zip(al, rho)]
    face = Face(Wire.make_polygon(pts, close=True))
    return extrude(face, amount=(X_CASE_BOT - X_CASE_TOP) + 2 * clear, dir=(1, 0, 0))


def head(head_shell_fn=None):
    """Head shell návrh 4 in THESE coordinates (bottom at HEAD_Z0)."""
    from build123d import Location
    from nova_mini import hlava_skrupina as HS
    s = HS.build_common().moved(Location((0, 0, HEAD_Z0)))
    saddle, cut = head_saddle_cut()
    return (s + saddle) - cut


def build_all(verbose=True):
    import time
    t0 = time.time()
    o = outer_body(verbose=verbose)
    n1 = body(o)
    cr, cl = caps()
    n3 = drive_plate()
    sv, horn = servo()
    if verbose:
        for nm, s in (("N1 krk", n1), ("N2-P", cr), ("N2-L", cl), ("N3", n3), ("S1 servo", sv),
                      ("horn", horn)):
            bb = s.bounding_box()
            print(f"  {nm:9s} valid={s.is_valid} x[{bb.min.X:.1f},{bb.max.X:.1f}] y[{bb.min.Y:.1f},{bb.max.Y:.1f}] "
                  f"z[{bb.min.Z:.1f},{bb.max.Z:.1f}] vol={s.volume:.0f}")
        print(f"  built in {time.time() - t0:.1f}s")
    return dict(N1=n1, N2P=cr, N2L=cl, N3=n3, S1=sv, HORN=horn)


if __name__ == "__main__":
    P = build_all()
    # interference checks (should all be ~0)
    pairs = [("S1", "N1"), ("HORN", "N1"), ("N2P", "N1"), ("N2L", "N1"), ("N3", "N1"), ("S1", "N2P"), ("HORN", "S1"),
             ("HORN", "N2P")]
    for a, b in pairs:
        x = P[a] & P[b]
        v = x.volume if x is not None else 0.0
        print(f"  {a:5s} & {b:5s} = {v:.2f} mm3")

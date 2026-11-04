"""
NOVA mini – KRK v3 (2026-11-04, user: "pôvodný krk upravený na ložiská, nie ihlan; valec v hlave 50/50; kĺb na stred
spodnej steny hlavy"; earlier: "hladko, bez schodíkov, spodok prispôsobený zaoblenému trupu"; parts are RESIN):
  * collar + bell neck = ONE smooth loft (no plateau / no steps), ellipse sections, level & centred; the underside follows
    the domed torso top (0.6 mm gap, surface of revolution -> panning keeps the gap)
  * head bottom passes through the tilt axis -> barrel 50 % in the head, 50 % below
  * head moved 5 mm back relative to the neck -> the joint sits nearer the middle of the head's flat bottom
    (more is not possible: the tilt servo would touch the back of the display while tilting)
  * left cap turns on a ball bearing MR128-2RS (8x12x3.5) seated in the cap, on a hollow N1 stub (cable inside);
    right cap is carried by the servo shaft (servo has its own output bearing) -> no resin-on-resin sliding
  * all screws go into glued brass inserts M2 (resin does not take self-tapping screws)
(v2 notes below)
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
                       Wire, extrude, fillet, revolve)

from nova.cad.common import superellipse_pts  # noqa: E402

# ---- collar (level, centred on the pan axis) ----------------------------------------------------------------------
C_A, C_B = 27.0, 20.5                            # collar rim half sizes (a bit larger: it hugs the torso dome)
RIM_H, RIM_R = 2.0, 2.0                          # rim height above z = 0 and its round
FLARE_ANG = 31.0                                 # the bell starts at 31° above horizontal (tangent to the rim round)
# ---- neck (bell: one smooth curve from the rim to the neck top, long front ramp) -----------------------------------
NX_TOP, NY_TOP = 12.5, 7.0                       # neck top half sizes (ellipse; 12.5 lets the junction blend r2)
T0_X, T0_F, T0_B, T1_ALL = 10.0, 15.0, 7.0, 9.0  # bell Hermite tangents (front ramp longest, back steepest)
CN = 2.0                                         # section exponent (pure ellipse -> soft, not boxy)
Z_N1 = 18.1                                      # neck top (straight above, into the barrel)
WALL = 1.4
# ---- tilt barrel ---------------------------------------------------------------------------------------------------
B_R, B_LEN = 10.0, 49.0
CAP_L, CAP_GAP = 7.8, 0.6
CAP_DOME_R = 4.0                                 # rounded rim of the flat cap end (flat face Ø12)
CORE_L = B_LEN - 2 * (CAP_L + CAP_GAP)          # 32.2 – part of N1
BORE_R = 8.5                                     # core bore (wall 1.5)
SKIRT_R, SKIRT_IN, SKIRT_L = 8.0, 7.2, 2.0      # right cap skirt: closes the view into the bore, NO contact (0.5)
BRG_D, BRG_OD, BRG_W = 8.0, 12.0, 3.5            # MR128-2RS in the left cap
STUB_ID = 5.0                                    # hollow N1 stub (cable)
AX_Z = Z_N1 + B_R - 2.0                          # barrel axis 26.1 above the torso top
HEAD_GAP = 0.5
HEAD_Z0 = AX_Z                                   # head bottom through the axis: barrel 50 % in the head
HEAD_DY = 5.0                                    # head moved back -> joint nearer the middle of the flat head bottom
POCKET_C = 0.2                                   # head cap pocket = cap envelope + 0.2
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
HORN_SINK = 1.0                                  # servo arm sits 1 mm deep in the right cap
X_HORN_HUB_END = -(X_CAP_IN - 3.0 + HORN_SINK)   # -15.7 (tower top)
X_CASE_TOP = X_HORN_HUB_END + SV_TOWER_H         # -12.7
X_CASE_BOT = X_CASE_TOP + SV_CASE[0]             # 10.8 (3.8 mm cable passage to the left end wall)
OPEN_X1 = X_CASE_BOT + 0.3                       # opening ends 0.3 behind the servo -> +X end stop
CAP_SCREW_X = X_CAP_IN + CAP_L / 2 + 1.0         # 21.6 – head->cap M2 (into a glued insert in the cap top)
X_ENDW0, X_ENDW1 = 14.6, 15.6                    # left end wall of the core (N1)
INSERT_D = 3.3                                   # hole for an M2 brass insert (glued)


def _w(a, b, z, n=2.0, cy=0.0, count=128):
    """periodic spline section; FIXED parameters -> every section shares one knot vector, so lofts stay compact
    (~130 poles instead of ~2700) and smooth, and the STEP stays small"""
    pts = [Vector(x, cy + y, z) for x, y in superellipse_pts(a, b, n, count)]
    return Wire([Edge.make_spline(pts, periodic=True, parameters=[i / len(pts) for i in range(len(pts) + 1)])])


def _hermite(p0, p1, t0, t1, n=240):
    out = []
    for i in range(n + 1):
        u = i / n
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        out.append((h00 * p0[0] + h10 * t0[0] + h01 * p1[0] + h11 * t1[0], h00 * p0[1] + h10 * t0[1] + h01 * p1[1] + h11 * t1[1]))
    return out


_PROF = None


def _profiles():
    """(inset, z) curves for the x side, the front and the back: vertical rim -> round -> bell (Hermite) -> neck top"""
    global _PROF
    if _PROF is not None:
        return _PROF
    beta = math.radians(90.0 - FLARE_ANG)
    rnd = [(RIM_R * (1 - math.cos(beta * i / 40)), RIM_H + RIM_R * math.sin(beta * i / 40)) for i in range(41)]
    e1, z1 = rnd[-1]
    ca, sa = math.cos(math.radians(FLARE_ANG)), math.sin(math.radians(FLARE_ANG))
    out = {}
    for key, E, L0 in (("x", C_A - NX_TOP, T0_X), ("f", C_B - NY_TOP, T0_F), ("b", C_B - NY_TOP, T0_B)):
        fl = _hermite((e1, z1), (E, Z_N1), (L0 * ca, L0 * sa), (0.0, T1_ALL))
        pts = [(0.0, -3.0), (0.0, RIM_H)] + rnd[1:] + fl[1:] + [(E, AX_Z + 1.0)]
        zs = [p[1] for p in pts]
        assert all(b > a for a, b in zip(zs, zs[1:])), key
        out[key] = pts
    _PROF = out
    return out


def _inset(key, z):
    import numpy as np
    pts = _profiles()[key]
    return float(np.interp(z, [p[1] for p in pts], [p[0] for p in pts]))


def _prof(z):
    """outer neck section at height z -> (half width x, front y, back y)"""
    return C_A - _inset("x", z), -(C_B - _inset("f", z)), C_B - _inset("b", z)


def _sec(a, yf, yb, z):
    return _w(a, (yb - yf) / 2, z, n=CN, cy=(yb + yf) / 2)


def _zs_by_arclength(z0, z1, step=0.45):
    """section heights spaced evenly along the x-side profile (no loft overshoot on the round)"""
    pts = [(p[0], p[1]) for p in _profiles()["x"] if z0 + 1e-9 < p[1] < z1 - 1e-9]
    pts = [(_inset("x", z0), z0)] + pts + [(_inset("x", z1), z1)]
    L = [0.0]
    for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(a1 - a0, b1 - b0))
    n = max(2, round(L[-1] / step))
    zs, j = [], 0
    for k in range(n + 1):
        sk = L[-1] * k / n
        while j < len(L) - 2 and L[j + 1] < sk:
            j += 1
        t = (sk - L[j]) / max(L[j + 1] - L[j], 1e-12)
        zs.append(pts[j][1] + (pts[j + 1][1] - pts[j][1]) * t)
    out = []
    for z in zs:
        if not out or z - out[-1] > 0.05:
            out.append(z)
    return out


def neck_outer():
    """collar + bell + neck top as ONE loft from below the torso dome up to the barrel axis"""
    zs = _zs_by_arclength(-2.0, Z_N1) + [Z_N1 + 2.0 * k for k in range(1, 5)]
    if zs[-1] < AX_Z - 0.05:
        zs.append(AX_Z)
    return Solid.make_loft([_sec(*_prof(z), z) for z in zs])


def neck_inner():
    """cavity: the outer profile shifted 2.5 mm up and inset 1.4 (thicker on the flaring part), from the N3 recess up"""
    zs = [2.6 + (AX_Z - 2.6) * i / 20 for i in range(21)]
    secs = []
    for z in zs:
        a, yf, yb = _prof(z + 2.5)
        secs.append(_sec(a - WALL, yf + WALL, yb - WALL, z))
    return Solid.make_loft(secs)


DOME_FLAT_R, DOME_RHO = 21.0, 15.25              # torso top: flat to r 21, then a torus R15.25 (fits KLASIK within 0.05)


def dome_cutter(gap=0.6):
    """torso top + gap as a solid of revolution made of analytic faces (plane + torus + cylinder) -> robust booleans"""
    z0 = gap
    c = Vector(DOME_FLAT_R, 0, z0 - DOME_RHO)
    a0 = Vector(DOME_FLAT_R, 0, z0)
    a2 = Vector(DOME_FLAT_R + DOME_RHO, 0, z0 - DOME_RHO)
    a1 = c + Vector(math.cos(math.radians(45)) * DOME_RHO, 0, math.sin(math.radians(45)) * DOME_RHO)
    zb = z0 - DOME_RHO - 6.0
    w = Wire([Edge.make_line(Vector(0, 0, z0), a0), Edge.make_three_point_arc(a0, a1, a2),
              Edge.make_line(a2, Vector(a2.X, 0, zb)), Edge.make_line(Vector(a2.X, 0, zb), Vector(0, 0, zb)),
              Edge.make_line(Vector(0, 0, zb), Vector(0, 0, z0))])
    return revolve(Face(w), Axis.Z, 360)


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
    """N1 outer form (solid) – collar/bell loft + barrel core blended; underside follows the torso dome."""
    b = neck_outer() + core_outer()
    def on_core(e):
        if e.center().Z > AX_Z - 1.0 or e.center().Z < AX_Z - B_R - 0.5:
            return False
        p0 = e.position_at(0)
        r0 = math.hypot(p0.Y, p0.Z - AX_Z)
        rc = math.hypot(e.center().Y, e.center().Z - AX_Z)
        return (abs(r0 - B_R) < 0.05 and abs(rc - B_R) < 0.05 and abs(e.center().X) < CORE_L / 2 - 0.5 and e.length > 3
                and e.geom_type != GeomType.CIRCLE and e.geom_type != GeomType.LINE)
    b, r2 = _fillet_between(b, on_core, (2.0, 1.5, 1.0))
    b = b - dome_cutter()
    r3 = None
    for r in (0.6, 0.4):                       # soften the rim's bottom edge (where it meets the domed underside)
        try:
            es = [e for e in b.edges() if e.center().Z < 1.0 and math.hypot(e.center().X / C_A, e.center().Y / C_B) > 0.9]
            nb = fillet(es, r)
            if nb.is_valid:
                b, r3 = nb, r
                break
        except Exception:  # noqa: BLE001
            continue
    if verbose:
        print(f"  core fillet r={r2}  rim-bottom round r={r3}  faces={len(b.faces())}")
    return b


def opening_box(shrink=0.0):
    x0, x1 = -CORE_L / 2 - 2.0, OPEN_X1 - shrink
    return Pos((x0 + x1) / 2, 0, AX_Z + 8.0) * Box(x1 - x0, 2 * (OPEN_Y - shrink), 6.0)


def body(outer=None):
    """N1 – one piece: hollow, servo opening on top (always under the head), guide + support ribs + end stop for the
    servo, left end wall with the hollow bearing stub (cable), 2 insert bosses for N3, recess for N3 underneath."""
    o = outer if outer is not None else outer_body()
    cav = neck_inner() + Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BORE_R, CORE_L + 4)
    recess = Solid.make_loft([_w(C_A - 4.2, C_B - 4.2, z) for z in (-2.0, 2.6)])
    n1 = o - cav - recess - opening_box()
    try:                                       # soften the opening rim (hidden in the head)
        rim = [e for e in n1.edges() if abs(abs(e.center().Y) - OPEN_Y) < 0.05 and e.center().Z > AX_Z + 5.0
               and math.hypot(e.center().Y, e.center().Z - AX_Z) > B_R - 0.1]
        n1r = fillet(rim, 0.15)
        if n1r.is_valid:
            n1 = n1r
    except Exception:  # noqa: BLE001
        pass
    env = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R - 0.15, CORE_L - 1.0)
    ribs = None
    for xr in (-8.0, 8.0):                     # guide ribs 0.1 off the 12.2 case (resin: no crush ribs)
        for sy in (-1, 1):
            r = Pos(xr, sy * (SV_CASE[1] / 2 + 0.1 + 0.8), AX_Z + 0.9) * Box(0.8, 1.6, 13.0)
            ribs = r if ribs is None else ribs + r
    ribs = ribs & env
    for xr in (-7.0, 7.0):                     # support ribs: the case bottom sits on them
        top = AX_Z - SV_SHAFT_FROM_END
        ribs = ribs + (Pos(xr, 0, top - 1.85) * Box(2.0, 20.0, 3.7) & o)
    for sy in (-1, 1):                         # +X end stop pads (lower half of the case end face)
        ribs = ribs + (Pos(OPEN_X1 + 0.5, sy * 6.25, AX_Z - 4.45) * Box(1.0, 3.5, 2.9) & env)
    n1 = n1 + ribs
    # left end wall + hollow stub for the MR128 in the left cap (+ shoulder for its inner ring)
    endw = Pos((X_ENDW0 + X_ENDW1) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BORE_R + 0.3, X_ENDW1 - X_ENDW0)
    x_st1 = X_CAP_IN + BRG_W - 0.1
    stub = Pos((X_ENDW1 + x_st1) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BRG_D / 2, x_st1 - X_ENDW1 + 0.02)
    shoulder = Pos((X_ENDW1 + X_CAP_IN - 0.1) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BRG_D / 2 + 0.8, X_CAP_IN - 0.1 - X_ENDW1)
    n1 = (n1 + endw + stub + shoulder) - Pos((X_ENDW0 + x_st1) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(STUB_ID / 2, x_st1 - X_ENDW0 + 2)
    for sx in (-1, 1):                         # bosses for 2x M2 from N3, with glued brass inserts
        boss = (Pos(sx * 13.5, 0, 6.6) * Cylinder(3.0, 8.0) + Pos(sx * 16.5, 0, 6.6) * Box(6.0, 2.0, 8.0)) & o
        n1 = n1 + boss
        n1 = n1 - Pos(sx * 13.5, 0, 2.6 + 2.0) * Cylinder(INSERT_D / 2, 4.0)
    return n1


def cap_envelope(sx, c=0.0, x_in_extra=0.0):
    x_in, x_out = sx * (X_CAP_IN - x_in_extra), sx * (X_CAP_IN + CAP_L + c)
    e = Pos((x_in + x_out) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + c, abs(x_out - x_in))
    return fillet([ed for ed in e.edges() if abs(ed.center().X - x_out) < 0.01], CAP_DOME_R + c)


CABLE_X = X_CAP_IN + 5.3                         # 22.0 – radial cable hole in the left cap (behind the bearing)
CABLE_ANG = 60.0                                 # from the top towards the back (+Y), inside the head pocket


def caps():
    """[N2-P right (-X), N2-L left (+X)] – end caps fixed in the head (1x M2 into a glued insert on top).
    right: cross pocket for the servo arm + a skirt that only hides the bore (no contact);
    left: seat for the MR128 ball bearing (on the hollow N1 stub) + cable chamber + radial cable hole."""
    out = []
    for sx in (-1, 1):
        x_in = sx * X_CAP_IN
        c = cap_envelope(sx)
        c = fillet([e for e in c.edges() if abs(e.center().X - x_in) < 0.01], 0.8)
        if sx < 0:
            sk = Pos(x_in + SKIRT_L / 2, 0, AX_Z) * Rot(0, 90, 0) * (Cylinder(SKIRT_R, SKIRT_L) - Cylinder(SKIRT_IN, SKIRT_L))
            c = c + sk
            dp = HORN_SINK + HORN_T + 0.1
            arms = (Box(dp, 2 * (HORN_R + 0.2), HORN_ARM_W + 0.3) + Box(dp, HORN_ARM_W + 0.3, 2 * (HORN_R + 0.2)))
            pocket = Pos(x_in - dp / 2, 0, AX_Z) * arms & (Pos(x_in - dp / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_R + 0.2, dp))
            c = c - pocket - Pos(x_in - dp / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_HUB_R + 0.3, dp)
        else:
            c = c - Pos(x_in + BRG_W / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BRG_OD / 2, BRG_W)          # bearing seat
            c = c - Pos(x_in + BRG_W + 0.6, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BRG_D / 2 + 1.2, 1.2)     # chamber
            a = math.radians(CABLE_ANG)
            c = c - Pos(CABLE_X, 6.0 * math.sin(a), AX_Z + 6.0 * math.cos(a)) * Rot(-CABLE_ANG, 0, 0) * Cylinder(1.75, 12.0)
            c = c - Pos(x_in + BRG_W + 1.2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(2.6, 1.2)                # chamber->hole link
        c = c - Pos(sx * CAP_SCREW_X, 0, AX_Z + 8.6) * Cylinder(INSERT_D / 2, 3.0)                       # insert pocket
        out.append(c)
    return out


def bearing():
    """L1 – MR128-2RS (8 x 12 x 3.5) in the left cap"""
    return Pos(X_CAP_IN + BRG_W / 2, 0, AX_Z) * Rot(0, 90, 0) * (Cylinder(BRG_OD / 2, BRG_W) - Cylinder(BRG_D / 2, BRG_W))


def drive_plate():
    """N3 – in the collar underside recess (on the flat torso top, 0.6 mm gap): pan-servo arm (4x M2 + nuts at r 7,
    centre hole for the arm screw), cable hole, 2x M2 countersunk into the inserts in N1."""
    p = Solid.make_loft([_w(C_A - 4.4, C_B - 4.4, z) for z in (0.6, 2.6)])
    p = p - Pos(9.0 / math.sqrt(2), 9.0 / math.sqrt(2), 1.6) * Cylinder(2.5, 4.0)
    p = p - Pos(0, 0, 1.6) * Cylinder(2.75, 4.0)
    for xh in (-13.5, 13.5):
        p = p - Pos(xh, 0, 1.6) * Cylinder(1.1, 4.0)
        p = p - Solid.make_cone(2.1, 1.0, 1.1, Plane.XY.offset(0.6 - 0.001).move(Location((xh, 0, 0))))
    for k in range(4):
        a = k * math.pi / 2
        p = p - Pos(7.0 * math.cos(a), 7.0 * math.sin(a), 1.6) * Cylinder(1.1, 4.0)
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
        cut = cut + Pos(sx * CAP_SCREW_X, 0, AX_Z + 11.4) * Cylinder(1.2, 4.0)
    a = math.radians(CABLE_ANG)
    cut = cut + Pos(CABLE_X, 11.4 * math.sin(a), AX_Z + 11.4 * math.cos(a)) * Rot(-CABLE_ANG, 0, 0) * Cylinder(2.0, 5.0)
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
    """Head shell návrh 5 in THESE coordinates (bottom at HEAD_Z0 = the axis, moved back HEAD_DY)."""
    from nova_mini import hlava_skrupina as HS
    s = HS.build_common().moved(Location((0, HEAD_DY, HEAD_Z0)))
    saddle, cut = head_saddle_cut()
    return (s + saddle) - cut


def display_envelope():
    """Waveshare ESP32-S3-Touch-LCD-3.5B incl. back components (assumed 9 mm) behind the 4 mm front frame – head-fixed"""
    from nova_mini import hlava_skrupina as HS
    y0 = HS.Y0 + 2.0 + HEAD_DY                   # glass/LCD front 2 mm behind the frame face
    return Pos(0, y0 + 4.5, HEAD_Z0 + HS.H / 2) * Box(85.5, 9.0, 55.5)


def build_all(verbose=True):
    import time
    t0 = time.time()
    o = outer_body(verbose=verbose)
    n1 = body(o)
    cr, cl = caps()
    n3 = drive_plate()
    sv, horn = servo()
    brg = bearing()
    if verbose:
        for nm, s in (("N1 krk", n1), ("N2-P", cr), ("N2-L", cl), ("N3", n3), ("S1 servo", sv),
                      ("horn", horn), ("L1 brg", brg)):
            bb = s.bounding_box()
            print(f"  {nm:9s} valid={s.is_valid} x[{bb.min.X:.1f},{bb.max.X:.1f}] y[{bb.min.Y:.1f},{bb.max.Y:.1f}] "
                  f"z[{bb.min.Z:.1f},{bb.max.Z:.1f}] vol={s.volume:.0f}")
        print(f"  built in {time.time() - t0:.1f}s")
    return dict(N1=n1, N2P=cr, N2L=cl, N3=n3, S1=sv, HORN=horn, L1=brg)


if __name__ == "__main__":
    P = build_all()
    # interference checks (should all be ~0)
    names = list(P)
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
    for a, b in pairs:
        x = P[a] & P[b]
        v = x.volume if x is not None else 0.0
        if v > 1e-3:
            print(f"  INT {a:5s} & {b:5s} = {v:.3f} mm3")

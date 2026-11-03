"""
NOVA mini – KRK, návrh "jeden celok" (podľa R04), user feedback 2026-11-03:
  "golier, plášť krku a kryt náklonu má byť JEDEN celok, nie tri časti; golier nesmie vyzerať naklonený;
   ako sa bude hlava nakláňať? boky nech sú otočné a upevnené v hlave; 100 % hladké, žiadne zuby/hrany"

Parts (this file, coordinates: mm, torso top z = 0, robot front = -Y, robot right = -X):
  N1   krk – ONE visible piece: level oval collar + bell neck + middle of the tilt barrel, blended with fillets.
       Hollow (wall 1.4 / 1.5).  Barrel core is a tube Ø17 bore, open at both ends (the caps' spigots ride in it =
       plain bearings).  On top of the barrel there is an assembly opening that is ALWAYS under the head (±40°
       tilt included): the tilt servo stands in it and the head cables pass through it.
  N2-P right end cap – rotates; fixed in the head (head pocket + 1x M2 from inside the head); carries the servo horn
  N2-L left end cap  – rotates; fixed in the head; its spigot is the left bearing
  N3   drive plate (hidden in the collar underside): pan-servo horn mount + cable hole
  S1   tilt servo MG90S (mounting ears cut off): held by N1 (guide ribs + 2 support ribs), shaft on the barrel axis,
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
from build123d import (Axis, Box, Cylinder, Edge, GeomType, Pos, Rot, Solid, Vector, Wire,  # noqa: E402
                       fillet)

from nova.cad.common import superellipse_pts  # noqa: E402

# ---- collar (level, centred on the pan axis) ----------------------------------------------------------------------
C_A, C_B, C_H = 25.5, 19.0, 4.5
C_R_TOP, C_R_BOT = 1.6, 0.6
# ---- neck (bell: steep sides, long front ramp) ---------------------------------------------------------------------
N_H = 14.0
NX_TOP, NX_BOT = 13.8, 20.5
NYF_TOP, NYF_BOT = -7.8, -15.5
NYB_TOP, NYB_BOT = 7.8, 13.5
WALL = 1.4
# ---- tilt barrel ---------------------------------------------------------------------------------------------------
B_R, B_LEN = 10.0, 49.0
CAP_L, CAP_GAP = 7.8, 0.6
CAP_DOME_R = 4.5                                 # rounded rim of the flat cap end (R04 look)
CORE_L = B_LEN - 2 * (CAP_L + CAP_GAP)          # 32.2 – part of N1
BORE_R = 8.5                                     # core bore (wall 1.5)
SPIGOT_R, SPIGOT_IN, SPIGOT_L = 8.3, 7.0, 2.0    # cap spigot = plain bearing in the bore
Z_N0 = C_H - 0.4
Z_N1 = Z_N0 + N_H
AX_Z = Z_N1 + B_R - 2.0                          # barrel axis 26.1 above the torso top
HEAD_GAP = 0.5
HEAD_Z0 = AX_Z + 1.5                             # head bottom (the head groove hides the barrel top ±81°)
TILT = 40.0
# ---- assembly opening on the barrel top (always under the head at ±40°) --------------------------------------------
OPEN_Y = 6.4
OPEN_X1 = 14.4                                   # from the right core end (-X) to x = 14.4 (cables beside the servo)
# ---- tilt servo MG90S (ears cut off), shaft -X on the axis ---------------------------------------------------------
SV_CASE = (22.5, 12.2, 22.8)                     # along shaft (x), width (y), length (z)
SV_SHAFT_FROM_END = 5.9                          # shaft axis from the upper end of the case
SV_TOWER_R, SV_TOWER_H = 5.9, 3.0
SV_SPLINE_R, SV_SPLINE_H = 2.4, 2.7
HORN_R, HORN_T, HORN_HUB_R = 7.0, 1.5, 3.5
X_CAP_IN = CORE_L / 2 + CAP_GAP                  # 16.7 – inner face of a cap
X_HORN_HUB_END = -(X_CAP_IN - 3.0)               # -13.7 (tower top)
X_CASE_TOP = X_HORN_HUB_END + SV_TOWER_H         # -10.7
X_CASE_BOT = X_CASE_TOP + SV_CASE[0]             # 11.8


def _w(a, b, z, n=2.0, cy=0.0, count=128):
    return Wire([Edge.make_spline([Vector(x, cy + y, z) for x, y in superellipse_pts(a, b, n, count)], periodic=True)])


def _prof(z):
    """outer neck section at height z -> (half width x, front y, back y)"""
    t = min(1.0, max(0.0, (z - Z_N0) / N_H))
    kx, ky = (1 - t) ** 3.0, (1 - t) ** 1.6
    return (NX_TOP + (NX_BOT - NX_TOP) * kx, NYF_TOP + (NYF_BOT - NYF_TOP) * ky, NYB_TOP + (NYB_BOT - NYB_TOP) * kx)


def _sec(a, yf, yb, z):
    return _w(a, (yb - yf) / 2, z, n=2.15, cy=(yb + yf) / 2)


def collar():
    secs = [_w(C_A - C_R_BOT, C_B - C_R_BOT, 0.0)]
    for t in (0.5, 1.0):
        e = C_R_BOT * (1 - math.sin(t * math.pi / 2))
        secs.append(_w(C_A - e, C_B - e, C_R_BOT * (1 - math.cos(t * math.pi / 2))))
    secs.append(_w(C_A, C_B, C_H - C_R_TOP))
    for t in (0.25, 0.5, 0.75, 1.0):
        e = C_R_TOP * (1 - math.cos(t * math.pi / 2))
        secs.append(_w(C_A - e, C_B - e, C_H - C_R_TOP + C_R_TOP * math.sin(t * math.pi / 2)))
    return Solid.make_loft(secs)


def neck_outer():
    zs = [Z_N0 + N_H * i / 17 for i in range(18)] + [Z_N1 + 2.0, Z_N1 + 4.0, Z_N1 + 6.0, AX_Z]
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
    b, r2 = _fillet_between(b, on_core, (2.0, 1.5, 1.0))
    if verbose:
        print(f"  collar fillet r={r1}  core fillet r={r2}  faces={len(b.faces())}")
    return b


def opening_box(shrink=0.0):
    x0, x1 = -CORE_L / 2 - 2.0, OPEN_X1 - shrink
    return Pos((x0 + x1) / 2, 0, AX_Z + 8.0) * Box(x1 - x0, 2 * (OPEN_Y - shrink), 6.0)


def body(outer=None):
    """N1 – one piece: hollow, open bore, assembly opening on top + inner guide ribs and support ribs for the servo."""
    o = outer if outer is not None else outer_body()
    cav = neck_inner() + Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BORE_R, CORE_L + 4)
    recess = Solid.make_loft([_w(C_A - 3.0, C_B - 3.0, z) for z in (-1.0, 2.0)])
    n1 = o - cav - recess - opening_box()
    bore_env = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(BORE_R + 0.3, CORE_L - 1.0)
    ribs = None
    for xr in (-8.0, 9.0):
        for sy in (-1, 1):                       # guide ribs at the servo flanks (torque reaction)
            r = Pos(xr, sy * 7.6, AX_Z) * Box(2.0, 2.7, 11.0)
            ribs = r if ribs is None else ribs + r
    ribs = ribs & bore_env
    for xr in (-7.0, 7.0):                       # support ribs under the servo (bridge across the neck top)
        ribs = ribs + (Pos(xr, 0, AX_Z - 7.85) * Box(2.0, 20.0, 3.5) & o)
    return n1 + ribs


def caps():
    """[N2-P right (-X), N2-L left (+X)] – domed end caps with bearing spigots; fixed to the head."""
    out = []
    for sx in (-1, 1):
        x_in, x_out = sx * X_CAP_IN, sx * (X_CAP_IN + CAP_L)
        c = Pos((x_in + x_out) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R, CAP_L)
        c = fillet([e for e in c.edges() if abs(e.center().X - x_out) < 0.01], CAP_DOME_R)
        c = fillet([e for e in c.edges() if abs(e.center().X - x_in) < 0.01], 0.8)
        sp = Pos(x_in - sx * SPIGOT_L / 2, 0, AX_Z) * Rot(0, 90, 0) * (Cylinder(SPIGOT_R, SPIGOT_L) - Cylinder(SPIGOT_IN, SPIGOT_L))
        c = c + sp
        # horn recess (right) / weight-saving recess (left) – same on both so they look identical from inside
        c = c - Pos(x_in + sx * 0.75, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_R + 0.2, 1.6)
        # M2 pilot hole from the top (the head screws into the cap from inside the head)
        c = c - Pos(sx * (X_CAP_IN + CAP_L / 2), 0, AX_Z + 7.5) * Cylinder(0.8, 5.5)
        out.append(c)
    return out


def drive_plate():
    """N3 – in the collar underside recess (hidden on the torso): pan-servo horn mount, 2x M2 into N1, cable hole."""
    p = Pos(0, 0, 1.0) * Solid.make_loft([_w(C_A - 3.2, C_B - 3.2, z) for z in (-1.0, 1.0)])
    p = p - Pos(0, 9.0, 1.0) * Cylinder(2.5, 4.0)                    # cable hole
    for xh in (-20.8, 20.8):                                         # 2x M2 into the collar ring
        p = p - Pos(xh, 0, 1.0) * Cylinder(1.1, 4.0)
    for k in range(4):                                               # pan-servo horn screws
        a = k * math.pi / 2 + math.pi / 4
        p = p - Pos(4.5 * math.cos(a), 4.5 * math.sin(a), 1.0) * Cylinder(0.75, 4.0)
    return p


def servo():
    """S1 – MG90S envelope (ears removed) + round horn. Returns (servo, horn)."""
    cx = (X_CASE_TOP + X_CASE_BOT) / 2
    z_bot = AX_Z - SV_SHAFT_FROM_END                                 # body stands UP from the axis into the head
    case = Pos(cx, 0, z_bot + SV_CASE[2] / 2) * Box(*SV_CASE)
    case = fillet(case.edges(), 0.5)
    tower = Pos(X_CASE_TOP - SV_TOWER_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_TOWER_R, SV_TOWER_H)
    spline = Pos(X_HORN_HUB_END - SV_SPLINE_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_SPLINE_R, SV_SPLINE_H)
    s = case + tower + spline
    horn = Pos(-(X_CAP_IN + HORN_T / 2), 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_R, HORN_T)
    horn = horn + Pos(-(X_CAP_IN - 1.5), 0, AX_Z) * Rot(0, 90, 0) * Cylinder(HORN_HUB_R, 3.0)
    horn = horn - Pos(X_HORN_HUB_END - SV_SPLINE_H / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(SV_SPLINE_R, SV_SPLINE_H)
    return s, horn


def head_saddle_cut():
    """What the head bottom needs (head coordinates are the same as here):
    saddle (solid to ADD inside the head) and cut (groove around the core 0.5 mm + tight cap pockets + cable window
    + 2x M2 holes into the caps)."""
    saddle = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + 2.6, 2 * (X_CAP_IN + CAP_L + 0.3 + 2.2))
    saddle = saddle & (Pos(0, 0, HEAD_Z0 + 20) * Box(80, 40, 40))
    groove = Pos(0, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + HEAD_GAP, CORE_L + 2 * CAP_GAP + 0.2)
    cut = groove
    for sx in (-1, 1):
        x0, x1 = sx * (X_CAP_IN - 0.1), sx * (X_CAP_IN + CAP_L + 0.3)
        cut = cut + Pos((x0 + x1) / 2, 0, AX_Z) * Rot(0, 90, 0) * Cylinder(B_R + 0.05, abs(x1 - x0))
        cut = cut + Pos(sx * (X_CAP_IN + CAP_L / 2), 0, AX_Z + 11.0) * Cylinder(1.1, 4.0)
    cut = cut + Pos(13.2, 0, AX_Z + 10.0) * Box(3.2, 2 * 8.6, 9.0)   # cable window beside the servo (inside only)
    cut = cut + servo_sweep()
    return saddle, cut


def servo_sweep(clear=0.6, step=4.0):
    """space the servo needs inside the head while the head tilts ±TILT (head-fixed frame)"""
    cx = (X_CASE_TOP + X_CASE_BOT) / 2
    z_bot = AX_Z - SV_SHAFT_FROM_END
    box = Pos(cx, 0, z_bot + SV_CASE[2] / 2) * Box(SV_CASE[0] + 2 * clear, SV_CASE[1] + 2 * clear, SV_CASE[2] + 2 * clear)
    ax = Axis((0, 0, AX_Z), (1, 0, 0))
    n = int(round(2 * (TILT + 2) / step))
    sw = None
    for k in range(n + 1):
        b = box.rotate(ax, -(TILT + 2) + k * step)
        sw = b if sw is None else sw + b
    return sw


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
    pairs = [("S1", "N1"), ("HORN", "N1"), ("N2P", "N1"), ("N2L", "N1"), ("N3", "N1"), ("S1", "N2P"), ("HORN", "S1")]
    for a, b in pairs:
        x = P[a] & P[b]
        v = x.volume if x is not None else 0.0
        print(f"  {a:5s} & {b:5s} = {v:.2f} mm3")
